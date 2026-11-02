#!/usr/bin/env bash
# Checks which prompts make Claude Code load the skill. Each prompt in
# trigger-prompts.tsv runs in its own fresh copy of ts-shop with the skill
# installed and read-only tools; the agent decides whether to load a skill
# before doing any work, so the session is capped low.
# Start it detached: nohup setsid evals/trigger-test.sh > /dev/null 2>&1 &
set -uo pipefail

runs=1; parallel=4; budget=1; out=""; ids=""; model=""; skill_ref=""; instructions=""
while [ $# -gt 0 ]; do
  case "$1" in
    --runs) runs="$2"; shift 2 ;;
    --parallel) parallel="$2"; shift 2 ;;
    --budget) budget="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --ids) ids=",$2,"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --skill-ref) skill_ref="$2"; shift 2 ;;
    --instructions) instructions="$2"; shift 2 ;;
    -h|--help) echo "Usage: evals/trigger-test.sh [--runs N] [--parallel P] [--budget USD] [--out DIR] [--ids S1,W2,...] [--model MODEL] [--skill-ref REF] [--instructions TEXT]"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

repo="$(cd "$(dirname "$0")/.." && pwd)"
out="${out:-$HOME/complexity-optimizer-evals/trigger-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$out/logs"
skill_src="$repo/skills"
if [ -n "$skill_ref" ]; then
  # Where the skill lives depends on the commit: skills/ (from 2026-11-01, flat), before that
  # skills/algorithmic-intelligence/ (briefly) or skills/complexity-optimizer/.
  ref_path=skills
  for p in skills skills/algorithmic-intelligence skills/complexity-optimizer; do
    if git -C "$repo" cat-file -e "$skill_ref:$p/SKILL.md" 2>/dev/null; then ref_path=$p; break; fi
  done
  mkdir -p "$out/skill" && git -C "$repo" archive "$skill_ref" "$ref_path" | tar -x -C "$out/skill" || exit 1
  skill_src="$out/skill/$ref_path"
fi
progress="$out/progress.log"
note() { echo "$(date '+%F %T') $*" >> "$progress"; }

one() {  # one <id> <run number> <prompt>
  local id="$1" n="$2" prompt="$3" dest="$out/$1-$2"
  "$repo/evals/new-run.sh" ts-shop --skill .claude/skills --skill-src "$skill_src" --dest "$dest" > /dev/null || { note "$id-$n: setup failed"; return; }
  # Optional project instructions, as a developer would add them (CLAUDE.md).
  [ -n "$instructions" ] && printf '%s\n' "$instructions" > "$dest/CLAUDE.md"
  (cd "$dest" && timeout -k 60 900 claude -p "$prompt" ${model:+--model "$model"} --allowedTools Read Glob Grep Skill \
     --max-budget-usd "$budget" --output-format stream-json --verbose > "$out/logs/$id-$n.jsonl" 2> "$out/logs/$id-$n.err")
  note "$id-$n: exit=$?"
  rm -rf "$dest"
}
export -f one note
export out repo budget progress model skill_src instructions

note "trigger test started: runs=$runs budget=\$$budget model=${model:-default} skill=${skill_ref:-working tree} instructions=${instructions:+yes}, skill commit $(git -C "$repo" rev-parse --short HEAD)"
tail -n +2 "$repo/evals/trigger-prompts.tsv" | while IFS=$'\t' read -r id expect kind prompt; do
  [ -n "$ids" ] && [[ "$ids" != *",$id,"* ]] && continue
  for n in $(seq 1 "$runs"); do printf '%s\t%s\t%s\0' "$id" "$n" "$prompt"; done
done | xargs -0 -P "$parallel" -I{} bash -c 'IFS=$'"'"'\t'"'"' read -r id n prompt <<< "$1"; one "$id" "$n" "$prompt"' _ {}

python3 - "$repo/evals/trigger-prompts.tsv" "$out" > "$out/summary.md" <<'EOF'
import csv, json, sys, pathlib
prompts, out = sys.argv[1], pathlib.Path(sys.argv[2])
rows = list(csv.DictReader(open(prompts), delimiter="\t"))
print("| ID | Expected | Loaded | Cost | Prompt |\n|---|---|---|---|---|")
right = total = errors = 0
for r in rows:
    for log in sorted((out / "logs").glob(f"{r['id']}-*.jsonl")):
        loaded, cost, error = False, 0.0, None
        for line in log.read_text().splitlines():
            try: e = json.loads(line)
            except ValueError: continue
            if e.get("type") == "assistant":
                for c in e["message"].get("content", []):
                    if c.get("type") == "tool_use" and c["name"] == "Skill" and any(n in str(c["input"].get("skill", "")) for n in ("algorithmic-intelligence", "complexity-optimizer")):
                        loaded = True
            if e.get("type") == "result":
                cost = e.get("total_cost_usd") or 0
                if e.get("is_error"): error = e.get("api_error") or e.get("result") or "error"
        # A session that errored (usage limit, API failure) never decided, so it is not scored.
        if error and not loaded:
            errors += 1
            print(f"| {log.stem} | {r['expect']} | error: {str(error)[:40]} | ${cost:.2f} | {r['prompt'][:80]} |")
            continue
        ok = loaded == (r["expect"] == "load")
        right += ok; total += 1
        print(f"| {log.stem} | {r['expect']} | {'yes' if loaded else 'no'}{'' if ok else ' ✗'} | ${cost:.2f} | {r['prompt'][:80]} |")
print(f"\nCorrect: {right} of {total}" + (f" ({errors} sessions errored and are not scored; rerun them)" if errors else ""))
EOF
note "trigger test finished"

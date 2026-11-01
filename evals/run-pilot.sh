#!/usr/bin/env bash
# Runs a fixture's report flow (report, apply all, decline) and its write-mode
# case headlessly with Claude Code, with and without the skill, and saves every
# transcript. Start it detached so it survives closing the terminal:
#   nohup setsid evals/run-pilot.sh > /dev/null 2>&1 &
set -uo pipefail

usage() {
  cat <<'EOF'
Usage: evals/run-pilot.sh [--fixture NAME] [--cases report,write] [--conditions skill,baseline]
                          [--skill-ref REF] [--model MODEL] [--runs N] [--parallel P]
                          [--budget USD] [--out DIR] [--instructions TEXT]

  --fixture NAME     ts-shop (default), py-logistics, java-clinic, or rb-clinic
                     (java-clinic needs JAVA_HOME set to a full JDK, or javac on PATH)
  --cases LIST       report (report, apply all, decline) and write (the write-mode case);
                     default both. The older names ts and tw1 still work.
  --conditions LIST  skill, baseline, or both (default both)
  --skill-ref REF    Git commit, branch, or tag of this repository whose skill to install
                     (default: the working tree). Use it to compare skill versions.
  --model MODEL      Model passed to claude --model (default: the CLI's default)
  --runs N           Runs per case and condition (default 1)
  --parallel P       Sessions at a time (default 2)
  --budget USD       Spending cap per turn, passed to --max-budget-usd (default 5)
  --out DIR          Output directory (default ~/complexity-optimizer-evals/pilot-<timestamp>)
  --instructions TEXT  Written to CLAUDE.md in each with-skill run directory and included in its
                     initial commit, as a developer would add it (for example the line the README
                     recommends for loading the skill). Baseline runs never get it.

Progress: <out>/progress.log. Per session: <out>/<session>/ (the run directory) and
<out>/logs/<session>.* (transcripts, git and test state). Summarize with
evals/session-stats.py <out>.
EOF
}

fixture=ts-shop; cases="report write"; conditions="skill baseline"; skill_ref=""; model=""
runs=1; parallel=2; budget=5; out=""; instructions=""
while [ $# -gt 0 ]; do
  case "$1" in
    --fixture) fixture="$2"; shift 2 ;;
    --cases) cases="${2//,/ }"; shift 2 ;;
    --conditions) conditions="${2//,/ }"; shift 2 ;;
    --skill-ref) skill_ref="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --runs) runs="$2"; shift 2 ;;
    --parallel) parallel="$2"; shift 2 ;;
    --budget) budget="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --instructions) instructions="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done
cases="${cases//ts/report}"; cases="${cases//tw1/write}"

repo="$(cd "$(dirname "$0")/.." && pwd)"
out="${out:-$HOME/complexity-optimizer-evals/pilot-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$out/logs"
progress="$out/progress.log"
note() { echo "$(date '+%F %T') $*" >> "$progress"; }

# Per-fixture test command, extra allowed commands, and write-mode prompt.
case "$fixture" in
  ts-shop)
    test_cmd="npm test"
    fixture_tools=("Bash(npm test)" "Bash(npm test:*)" "Bash(node:*)")
    write_prompt="Add a function stockValuation(stores, priceBook) in a new file src/valuation.ts. For each store, in the order given, it returns the store id and the total value in cents of the stock on hand: for every SKU with a positive net quantity in that store's movements, quantity times the SKU's price from the price book. Add tests." ;;
  py-logistics)
    test_cmd="./test.sh"
    fixture_tools=("Bash(./test.sh)" "Bash(./test.sh:*)" "Bash(python3:*)")
    write_prompt="Add a function longest_on_time_streak(deliveries, budget_minutes) in a new file logistics/sla.py. deliveries is one driver's deliveries in order, each a (promised, delivered) pair of datetimes. Return the length of the longest run of consecutive deliveries whose total late minutes is at most budget_minutes. A delivery's late minutes are the whole minutes after its promised time; early or on-time deliveries count as 0. Add tests." ;;
  java-clinic)
    # Agents check for javac on PATH before trusting JAVA_HOME; put the JDK on PATH.
    [ -n "${JAVA_HOME:-}" ] && export PATH="$JAVA_HOME/bin:$PATH"
    test_cmd="./test.sh"
    fixture_tools=("Bash(./test.sh)" "Bash(./test.sh:*)" "Bash(java:*)" "Bash(javac:*)" "Bash(${JAVA_HOME:-/usr}/bin/java:*)" "Bash(${JAVA_HOME:-/usr}/bin/javac:*)")
    write_prompt="Add a class CoverageReport in src/main/java/com/example/clinic/CoverageReport.java. Its constructor takes an Availability. Its method List<LocalDate> uncoveredDays(List<Long> doctorIds, LocalDate from, LocalDate to, int minDoctors) returns, in date order, each day from \`from\` to \`to\` inclusive on which fewer than minDoctors of the given doctors are available. Add tests." ;;
  rb-clinic)
    test_cmd="./test.sh"
    fixture_tools=("Bash(./test.sh)" "Bash(./test.sh:*)" "Bash(ruby:*)")
    write_prompt="Add a method Clinic::LabAlerts.repeat_tests(results, window_days) in a new file lib/clinic/lab_alerts.rb. results is an array of lab results in the order they arrived; each responds to patient_id, test_code and taken_on (a Date). Return, in arrival order, the results for which an earlier-arrived result has the same patient_id and test_code and a taken_on within window_days days of this one's, before or after. Add tests." ;;
  *) echo "No pilot configuration for fixture: $fixture" >&2; exit 1 ;;
esac

# Install the skill from a git ref when asked, so two versions can be compared.
skill_src="$repo/skills/complexity-optimizer"
skill_label="working tree at $(git -C "$repo" rev-parse --short HEAD)$(git -C "$repo" diff --quiet -- skills || echo ' (with uncommitted changes)')"
if [ -n "$skill_ref" ]; then
  mkdir -p "$out/skill"
  git -C "$repo" archive "$skill_ref" skills/complexity-optimizer | tar -x -C "$out/skill" || { echo "Cannot read the skill at $skill_ref" >&2; exit 1; }
  skill_src="$out/skill/skills/complexity-optimizer"
  skill_label="$skill_ref ($(git -C "$repo" rev-parse --short "$skill_ref"))"
fi
model_args=()
[ -n "$model" ] && model_args=(--model "$model")

# One session: <case: report|write> <skill|baseline> <run number>
session() {
  local case_id="$1" cond="$2" n="$3"
  local name="$case_id-$cond-$n" dest="$out/$1-$2-$3" log="$out/logs/$1-$2-$3"
  local skill_args=() id
  [ "$cond" = skill ] && skill_args=(--skill .claude/skills --skill-src "$skill_src")
  if [ -e "$out/LIMIT_REACHED" ]; then note "$name: skipped, usage limit reached earlier (rerun it later)"; return; fi
  "$repo/evals/new-run.sh" "$fixture" "${skill_args[@]}" --dest "$dest" > /dev/null || { note "$name: setup failed"; return; }
  if [ "$cond" = skill ] && [ -n "$instructions" ]; then
    printf '%s\n' "$instructions" > "$dest/CLAUDE.md"
    (cd "$dest" && git add CLAUDE.md && git -c user.name="Eval Fixture" -c user.email="eval@example.invalid" commit -q --amend --no-edit) \
      || { note "$name: could not add CLAUDE.md"; return; }
  fi
  id="$(python3 -c 'import uuid; print(uuid.uuid4())')"
  note "$name: started (session $id)"

  # Commands agents need for ordinary work (moving around, reading, scratch files, timing, and
  # the test script however they spell it). Round 3 refused 14-21% of shell commands for lack
  # of these, which wasted turns; on java-clinic it stopped every test and benchmark run.
  local common=("Bash(cd:*)" "Bash(ls:*)" "Bash(cat:*)" "Bash(head:*)" "Bash(tail:*)" "Bash(wc:*)"
    "Bash(grep:*)" "Bash(find:*)" "Bash(sort:*)" "Bash(diff:*)" "Bash(echo:*)" "Bash(printf:*)"
    "Bash(mkdir:*)" "Bash(mktemp:*)" "Bash(cp:*)" "Bash(sed:*)" "Bash(timeout:*)" "Bash(time:*)" "Bash(python3:*)"
    "Bash(bash test.sh:*)" "Bash(bash ./test.sh:*)" "Bash(bash $dest/test.sh:*)" "Bash($dest/test.sh:*)")
  local allowed=(Read Edit Write Glob Grep Skill TodoWrite "Bash(git:*)" "${common[@]}" "${fixture_tools[@]}")
  local turn=0
  ask() {  # ask <label> <prompt>
    local label="$1" prompt="$2" resume=(--session-id "$id")
    [ -e "$out/LIMIT_REACHED" ] && { note "$name: turn $label skipped, usage limit reached"; return; }
    [ "$turn" -gt 0 ] && resume=(--resume "$id")
    turn=$((turn + 1))
    (cd "$dest" && timeout -k 60 2700 claude -p "$prompt" "${resume[@]}" "${model_args[@]}" \
       --allowedTools "${allowed[@]}" --add-dir /tmp --max-budget-usd "$budget" \
       --output-format stream-json --verbose > "$log.$turn-$label.jsonl" 2> "$log.$turn-$label.err")
    note "$name: turn $turn ($label) exit=$?"
    # A turn without a final result line stalled or was killed: the session is invalid.
    if ! tail -1 "$log.$turn-$label.jsonl" 2>/dev/null | grep -q '"type":"result"'; then
      note "$name: turn $turn ($label) INCOMPLETE (no result line), session invalid"
    fi
    # A turn that ended on an API error (usage limit, overload) did no work: the session is invalid.
    if tail -1 "$log.$turn-$label.jsonl" 2>/dev/null | grep -q '"is_error":true'; then
      note "$name: turn $turn ($label) API ERROR, session invalid: $(tail -1 "$log.$turn-$label.jsonl" | grep -o '"result":"[^"]*"')"
      # A usage limit fails every later session too: stop starting new ones.
      grep -q 'usage_limit_reached' "$log.$turn-$label.jsonl" && touch "$out/LIMIT_REACHED"
    fi
  }
  local decline="Decline every approval request and every dependency request. Continue with anything that needs no approval, then finish."

  if [ "$case_id" = report ]; then
    ask report "Find time complexity and data-structure problems in this project and write a report."
    (cd "$dest" && git status --porcelain) > "$log.after-report.status"
    ask apply "Apply all the optimizations you recommend."
    ask decline "$decline"
  else
    ask write "$write_prompt"
    ask decline "$decline"
  fi
  (cd "$dest" && { echo "## git status"; git status --porcelain; echo "## git log"; git log --oneline; echo "## $test_cmd"; timeout 600 $test_cmd 2>&1 | tail -8 || echo "(test run timed out or failed)"; }) > "$log.final" 2>&1
  note "$name: done"
}
export -f session note
export out repo budget progress fixture skill_src test_cmd write_prompt instructions

note "pilot started: fixture=$fixture cases=$cases conditions=$conditions runs=$runs parallel=$parallel budget=\$$budget per turn model=${model:-default} skill=$skill_label instructions=${instructions:+yes}"
for case_id in $cases; do for cond in $conditions; do for n in $(seq 1 "$runs"); do
  echo "$case_id $cond $n"
done; done; done | xargs -P "$parallel" -L 1 bash -c "$(declare -p fixture_tools model_args); session \"\$0\" \"\$1\" \"\$2\""
note "pilot finished"

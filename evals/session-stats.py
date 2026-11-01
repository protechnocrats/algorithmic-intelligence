#!/usr/bin/env python3
"""Summarizes a pilot's transcripts: cost, turns, tokens, and which skill files
each session read. Use it to compare runs and to check the skill's token budget
in practice.

Usage: python3 -I evals/session-stats.py <pilot output directory>
"""
import collections
import json
import re
import sys
from pathlib import Path


def sessions(logs: Path):
    groups = collections.defaultdict(list)
    for f in sorted(logs.glob("*.jsonl")):
        name, rest = f.name.split(".", 1)
        groups[name].append((int(rest.split("-", 1)[0]), f))
    return {name: [f for _, f in sorted(turns)] for name, turns in groups.items()}


def summarize(files):
    cost = 0.0
    tokens = collections.Counter()
    turns = 0
    errors = []
    skill_loaded = False
    reads = collections.Counter()
    for f in files:
        for line in f.read_text().splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "assistant":
                for c in e["message"].get("content", []):
                    if c.get("type") != "tool_use":
                        continue
                    text = json.dumps(c.get("input", {}))
                    if c["name"] == "Skill" and ("algorithmic-intelligence" in text or "complexity-optimizer" in text):
                        skill_loaded = True
                    for path in re.findall(r"(?:algorithmic-intelligence|complexity-optimizer)/([A-Za-z/_-]+\.md)", text):
                        reads[path] += 1
            elif e.get("type") == "result":
                turns += e.get("num_turns") or 0
                cost = max(cost, e.get("total_cost_usd") or 0.0)  # reported cumulatively across resumed turns
                for k, v in (e.get("usage") or {}).items():
                    if isinstance(v, int):
                        tokens[k] += v
                if e.get("is_error"):
                    errors.append(e.get("api_error") or e.get("result") or "error")
    return cost, turns, tokens, skill_loaded, reads, errors


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    print("| Session | Cost | Agent turns | Input tokens (incl. cache) | Output tokens | Skill loaded | Skill files opened | Errors |")
    print("|---|---|---|---|---|---|---|---|")
    totals = collections.defaultdict(lambda: [0.0, 0])
    for name, files in sessions(out / "logs").items():
        cost, turns, tok, loaded, reads, errors = summarize(files)
        inp = tok["input_tokens"] + tok["cache_creation_input_tokens"] + tok["cache_read_input_tokens"]
        opened = ", ".join(f"{p}×{n}" if n > 1 else p for p, n in sorted(reads.items())) or "—"
        print(f"| {name} | ${cost:.2f} | {turns} | {inp:,} | {tok['output_tokens']:,} | {'yes' if loaded else 'no'} | {opened} | {'; '.join(errors) or '—'} |")
        group = re.sub(r"-\d+$", "", name)
        totals[group][0] += cost
        totals[group][1] += 1
    print("\n| Group | Sessions | Mean cost |\n|---|---|---|")
    for group, (cost, n) in sorted(totals.items()):
        print(f"| {group} | {n} | ${cost / n:.2f} |")


if __name__ == "__main__":
    main()

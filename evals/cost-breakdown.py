#!/usr/bin/env python3
"""Breaks down where eval sessions spend their cost: reading code, writing and
running the agent's own harnesses and benchmarks, running the existing test
suite, editing source, writing the report, committing, and so on.

Usage: python3 -I evals/cost-breakdown.py <pilot output directory> [more ...]

Each argument is a run-pilot.sh output directory (it holds progress.log and
logs/). Only valid sessions count: every turn finished, with no usage-limit
error, stall, or skip recorded in progress.log. Sessions are grouped by model,
case (report or write), and condition (skill or baseline).

How cost is assigned: each API call in a transcript is charged to the tool
calls it issued (a call with several tool calls splits its cost evenly), or to
"reason or answer" if it issued none. A call's cost uses Anthropic's price
ratios relative to uncached input: cache read 0.1, cache write 1.25 (5-minute)
or 2 (1-hour), output 5. The stream records only each call's first snapshot of
output tokens, so output is estimated from the content each call produced and
scaled to the output tokens the turn's result reports. Shares are then scaled
to the session's reported total cost.

It also counts tool calls the harness refused for lack of permission. A high
refusal rate means the session measured the harness, not the skill: fix the
allowed commands in run-pilot.sh and rerun before scoring.

Limits: a tool's long output makes later calls' context larger, and that cost
is charged to the later calls, so harness shares are somewhat understated.
Categories come from file paths and command patterns; spot-check them with
--samples before relying on a new fixture's numbers.
"""
import collections
import json
import random
import re
import sys
from pathlib import Path

CATEGORIES = [
    "read code", "write harness", "run harness or benchmark", "run existing test suite",
    "edit source", "write report", "reason or answer (no tool)", "git (commit, restore)",
    "other shell", "load skill", "other",
]
HARNESS_PATH = re.compile(r"(test|bench|probe|check|verify|harness|reference|_orig|original|exhaust|fuzz|property|/tmp/|scratch|timing|perf)", re.I)
SUITE = re.compile(r"(\./test\.sh|npm test|cargo test|gradlew test|swift test|python3? -m (unittest|pytest)|\bpytest\b)")
CUSTOM_RUN = re.compile(r"(bench|timeit|perf_counter|hyperfine|/tmp/|diff|equiv|probe|exhaust|fuzz|property|python3? (-I )?[\w./-]+\.py|node [\w./-]+\.(m?[jt]s)|npx tsx|ruby [\w./-]+\.rb|java [\w./-]+\.java)")
REFUSED = re.compile(r"(requires approval|needs approval|can't be checked before it runs|Permission to use .* has been denied)", re.I)
READ_CMD = re.compile(r"^\s*(for .*; do .*cat|cat|ls|find|grep|rg|head|tail|sed -n|wc|tree|git (log|show|status|diff|ls-files|branch))\b")


def classify(block):
    name, inp = block.get("name"), block.get("input") or {}
    if name in ("Read", "Grep", "Glob"):
        return "read code"
    if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        if path.endswith(".md"):
            return "write report"
        return "write harness" if HARNESS_PATH.search(path) else "edit source"
    if name == "Bash":
        cmd = inp.get("command", "")
        if re.search(r"\bgit (add|commit|checkout|restore|stash|reset|revert)\b", cmd):
            return "git (commit, restore)"
        inline = re.search(r"<<\s*['\"]?\w+", cmd) or re.search(r"(python3?( -I)? -c|node -e|ruby -e|tsx -e)", cmd)
        if inline and len(cmd) > 300:
            return "write harness"
        if CUSTOM_RUN.search(cmd) and not re.match(r"^\s*(cat|ls|head|tail|sed -n|grep|wc)\b", cmd):
            return "run harness or benchmark"
        if SUITE.search(cmd):
            return "run existing test suite"
        if READ_CMD.search(cmd):
            return "read code"
        return "other shell"
    if name == "Skill":
        return "load skill"
    return "other"


def events(files):
    for f in files:
        for line in f.read_text().splitlines():
            try:
                yield f, json.loads(line)
            except ValueError:
                continue


def api_calls(files):
    """Yields (relative cost, tool blocks) per API call."""
    msgs = collections.OrderedDict()
    reported_out = 0
    for f, e in events(files):
        if e.get("type") == "result":
            reported_out += (e.get("usage") or {}).get("output_tokens") or 0
        elif e.get("type") == "assistant":
            m = e["message"]
            rec = msgs.setdefault((f.name, m.get("id")), {"usage": {}, "blocks": []})
            rec["usage"] = m.get("usage") or rec["usage"]
            rec["blocks"].extend(m.get("content") or [])

    def size(b):
        return len(b.get("text") or "") + len(b.get("thinking") or "") + (len(json.dumps(b.get("input"))) if b.get("type") == "tool_use" else 0)

    est = [sum(size(b) for b in rec["blocks"]) for rec in msgs.values()]
    scale = reported_out / sum(est) if sum(est) else 0
    for rec, chars in zip(msgs.values(), est):
        u = rec["usage"]
        cc = u.get("cache_creation") or {}
        writes = 1.25 * (cc.get("ephemeral_5m_input_tokens") or 0) + 2.0 * (cc.get("ephemeral_1h_input_tokens") or 0) if cc \
            else 1.25 * (u.get("cache_creation_input_tokens") or 0)
        cost = (u.get("input_tokens") or 0) + 0.1 * (u.get("cache_read_input_tokens") or 0) + writes + 5.0 * chars * scale
        yield cost, chars * scale, [b for b in rec["blocks"] if b.get("type") == "tool_use"]


def refusals(files):
    """(tool calls, refused tool calls) in a session."""
    asked, refused = set(), 0
    for _, e in events(files):
        if e.get("type") == "assistant":
            asked.update(c["id"] for c in e["message"].get("content") or [] if c.get("type") == "tool_use")
        elif e.get("type") == "user" and isinstance((e.get("message") or {}).get("content"), list):
            for c in e["message"]["content"]:
                if c.get("type") == "tool_result" and c.get("tool_use_id") in asked:
                    out = c.get("content")
                    out = out if isinstance(out, str) else json.dumps(out)
                    refused += bool(REFUSED.search(out[:400]))
    return len(asked), refused


def reported_cost(files):
    cost = 0.0
    for _, e in events(files):
        if e.get("type") == "result":
            cost = max(cost, e.get("total_cost_usd") or 0.0)  # cumulative across resumed turns
    return cost


def valid_sessions(out):
    progress = (out / "progress.log").read_text()
    m = re.search(r"model=(\S+)", progress)
    model = m.group(1) if m else "unknown"
    for name in sorted(set(re.findall(r"\s(\w+-\w+-\d+): done", progress))):
        if re.search(rf"{re.escape(name)}: (turn .*(invalid|INCOMPLETE)|skipped)", progress):
            continue
        files = sorted((out / "logs").glob(f"{name}.*.jsonl"))
        if files:
            kind, cond, _ = name.split("-")
            yield model, kind, cond, files


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    show_samples = "--samples" in sys.argv
    usd = collections.defaultdict(collections.Counter)
    out_tokens = collections.defaultdict(collections.Counter)
    sessions = collections.Counter()
    totals = collections.Counter()
    samples = collections.defaultdict(list)
    tool_calls, refused = collections.Counter(), collections.Counter()
    for arg in args:
        for model, kind, cond, files in valid_sessions(Path(arg)):
            key = (model, kind, cond)
            share, outs = collections.Counter(), collections.Counter()
            for cost, out, blocks in api_calls(files):
                cats = [classify(b) for b in blocks] or ["reason or answer (no tool)"]
                for b, c in zip(blocks, cats):
                    inp = b.get("input") or {}
                    samples[c].append(f"{b.get('name')}: {(inp.get('file_path') or inp.get('command') or '')[:140]!r}")
                for c in cats:
                    share[c] += cost / len(cats)
                    outs[c] += out / len(cats)
            calls_made, calls_refused = refusals(files)
            tool_calls[key] += calls_made
            refused[key] += calls_refused
            whole, session_usd = sum(share.values()), reported_cost(files)
            if not whole:
                continue
            sessions[key] += 1
            totals[key] += session_usd
            for c in share:
                usd[key][c] += session_usd * share[c] / whole
                out_tokens[key][c] += outs[c]
    for key in sorted(usd):
        model, kind, cond = key
        n, tot = sessions[key], totals[key]
        print(f"\n## {model}, {kind} flow, {cond}: {n} valid sessions, ${tot / n:.2f} mean per session\n")
        print("| Activity | Share of cost | Mean $ per session | Output tokens per session |")
        print("|---|---|---|---|")
        for c in CATEGORIES:
            if usd[key][c]:
                print(f"| {c} | {100 * usd[key][c] / tot:.0f}% | {usd[key][c] / n:.2f} | {out_tokens[key][c] / n:,.0f} |")
        h = usd[key]["write harness"] + usd[key]["run harness or benchmark"]
        print(f"\nOwn harnesses and benchmarks (write + run): {100 * h / tot:.0f}% of cost, ${h / n:.2f} per session")
        rate = refused[key] / tool_calls[key] if tool_calls[key] else 0
        flag = "  <- too many: the harness, not the skill, limited these sessions" if rate > 0.05 and refused[key] >= 3 else ""
        print(f"Tool calls refused by permissions: {refused[key]} of {tool_calls[key]} ({100 * rate:.0f}%){flag}")
    if show_samples:
        random.seed(1)
        for c in CATEGORIES:
            if samples[c]:
                print(f"\n### {c}: {len(samples[c])} tool calls, sample")
                for s in random.sample(samples[c], min(6, len(samples[c]))):
                    print(f"- {s}")


if __name__ == "__main__":
    main()

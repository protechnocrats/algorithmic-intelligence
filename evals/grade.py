#!/usr/bin/env python3
"""Grades every session of one or more run-pilot.sh output directories on every category in
evals/GRADING.md, and writes a scorecard.

    python3 -I evals/grade.py <run directory> [more ...]
    python3 -I evals/grade.py --judge [--judge-model M] [--judge-cap USD] <run directory> ...
    python3 -I evals/grade.py --judge-selftest <session directory> [--judge-model M]

Without --judge it is free: it reads files and runs the fixture's probe. --judge adds the
judged checks (J in GRADING.md) by running one model session per graded session, stopping
when the judge's total reported cost reaches --judge-cap (default $3). Judge results are cached
in each run directory (judge-<session>.json), so regrading costs nothing.

Writes <run directory>/scorecard.json and scorecard.md, and prints a combined scorecard
grouped by model and condition.
"""
import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


stats = load("session-stats")
costs = load("cost-breakdown")
reportcheck = load("check-report")

PROBES = {
    "rb-clinic": lambda d: ["python3", "-I", str(HERE / "probes/rb-clinic.py"), str(d)],
    "java-clinic": lambda d: ["python3", "-I", str(HERE / "probes/java-clinic.py"), str(d)],
    "py-logistics": lambda d: ["python3", "-I", str(HERE / "probes/py-logistics.py"), str(d)],
    "ts-shop": lambda d: ["node", str(HERE / "probes/ts-shop.ts"), str(HERE / "fixtures/ts-shop/src"), str(d / "src")],
}
BUILD_FILES = ["Gemfile", "Gemfile.lock", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle.kts",
               "package.json", "package-lock.json", "requirements.txt", "pyproject.toml", "Cargo.toml",
               "Cargo.lock", "Package.swift", "Makefile"]
SKILL_FILES = ["WORKFLOW.md", "WRITING-NEW-CODE.md", "DIFFERENTIAL-TESTING.md", "REPORTING.md",
               "ALGORITHM-ARSENAL.md", "BEHAVIOR-TRAPS.md", "BENCHMARKING.md"]

# Judged checks (J in GRADING.md): id -> question. Scored P (yes), F (no), or NA (does not apply).
JUDGED = {
    "behavior-changes-held": "Every change that alters observable behavior was listed for the developer's review and was NOT applied on the general request \"Apply all the optimizations you recommend\" (NA if the session found no behavior change).",
    "declined-equivalent": "For each behavior change the developer declined, the session applied a version that keeps the behavior when one exists, or explained why none exists (NA if nothing was declined).",
    "bugs-reported": "Every bug the session noticed was reported both in its replies and in a bug log or report section, and none was fixed on purpose.",
    "contracts": "Each analyzed item states its contract: what it requires, returns (including order and duplicates), changes, throws, or calls.",
    "lower-bounds": "Each nontrivial item states a lower bound with its basis (proven, conditional, conjectured, workload-dependent, or unknown with a reason), and no bound is asserted without a basis.",
    "candidates": "Each nontrivial item compares at least three plausible approaches.",
    "exposure": "Each item states its exposure (untrusted input, secrets, hard deadline, or none), and uses the worst case where untrusted parties control input.",
    "call-costs": "Costs are counted along the call chain, including built-in and library calls inside loops.",
    "verification-levels": "Every applied change reports how it was verified (tested, property-checked, exhaustively checked to a bound, or proven) (NA if nothing was applied).",
    "proven-misuse": "The word \"proven\" (or \"proved\") is used only for a machine-checked proof or a check of every input in the whole domain (P if never misused).",
    "check-the-check": "Differential tests were shown to catch at least one deliberately planted difference before being trusted (NA if nothing was applied).",
    "predictions": "A speedup prediction was written before benchmarking and compared with the measurement (NA if nothing was benchmarked).",
    "measured-labels": "Every performance claim is labeled measured or estimated.",
    "end-to-end": "Each component speedup is accompanied by the share of the whole operation (request, job, page) it affects.",
}


def session_names(run):
    return sorted({f.name.split(".")[0] for f in (run / "logs").glob("*.jsonl")})


def files_of(run, name):
    return sorted((run / "logs").glob(f"{name}.*.jsonl"))


def events(files):
    for f in files:
        for line in f.read_text().splitlines():
            try:
                yield f, json.loads(line)
            except ValueError:
                pass


def run_header(run):
    first = (run / "progress.log").read_text().splitlines()[0]
    fixture = re.search(r"fixture=(\S+)", first).group(1)
    model = re.search(r"model=(\S+)", first)
    return fixture, (model.group(1) if model else "default")


def validity(run, name, files, loaded, condition):
    log = [l for l in (run / "progress.log").read_text().splitlines() if f" {name}:" in l]
    bad = [l for l in log if re.search(r"STALL|invalid|limit|skipped|failed", l)]
    done = any(l.endswith(": done") for l in log)
    asked, refused = costs.refusals(files)
    rate = refused / asked if asked else 0.0
    reasons = []
    if not done or bad:
        reasons.append("incomplete: " + (bad[0].split(": ", 1)[-1] if bad else "no done line"))
    if rate >= 0.10:
        reasons.append(f"refusals {refused}/{asked}")
    if condition == "skill" and not loaded:
        reasons.append("skill not loaded")
    if condition == "baseline" and loaded:
        reasons.append("baseline loaded the skill")
    times = [datetime.strptime(l[:19], "%Y-%m-%d %H:%M:%S") for l in log]
    wall = (max(times) - min(times)).total_seconds() / 60 if times else 0.0
    return reasons, rate, wall


def first_reply_states_mode(files):
    for _, e in events(files[:1]):
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "text" and b.get("text", "").strip():
                    return bool(re.search(r"\b(report|apply|write)[- ]mode\b", b["text"][:600], re.I))
    return False


def tests_before_analysis(files, test_cmd):
    """True if the fixture's test command ran before the first report file was written."""
    if not test_cmd:
        return None
    for _, e in events(files[:1]):
        if e.get("type") != "assistant":
            continue
        for b in e["message"].get("content", []):
            if b.get("type") != "tool_use":
                continue
            inp = json.dumps(b.get("input", {}))
            if b["name"] == "Bash" and test_cmd.split()[0].lstrip("./") in inp:
                return True
            if b["name"] in ("Write", "Edit") and "REPORT" in inp.upper():
                return False
    return False


def report_rewrites(files):
    """Writes or edits of OPTIMIZATION-REPORT.md after the report turn."""
    n = 0
    for f, e in events(files[1:]):
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use" and b["name"] in ("Write", "Edit", "MultiEdit") \
                        and str(b.get("input", {}).get("file_path", "")).endswith("OPTIMIZATION-REPORT.md"):
                    n += 1
    return n


def final_state(run, name):
    p = run / "logs" / f"{name}.final"
    text = p.read_text() if p.exists() else ""
    parts = dict(re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, re.M | re.S))
    commits = len([l for l in parts.get("git log", "").splitlines() if l.strip()])
    test_cmd = next((k for k in parts if k not in ("git status", "git log")), "")
    out = parts.get(test_cmd, "")
    if re.search(r"\b[1-9]\d* (failures|failed|errors)\b|BUILD FAILED|FAILED|timed out or failed|Error:", out):
        tests = False
    elif re.search(r"\b0 failures\b|BUILD SUCCESSFUL|\bOK\b|\bpassed\b|test result: ok|# fail 0|All tests passed", out):
        tests = True
    else:
        tests = None
    return commits, tests, test_cmd


def report_mode_clean(run, name):
    p = run / "logs" / f"{name}.after-report.status"
    if not p.exists():
        return None
    tracked = [l for l in p.read_text().splitlines() if l.strip() and not l.startswith("??")]
    return not tracked


def dependency_added(session_dir):
    present = [f for f in BUILD_FILES if (session_dir / f).exists()]
    if not present:
        return False
    r = subprocess.run(["git", "-C", str(session_dir), "diff", "--quiet", "HEAD", "--", *present])
    first = subprocess.run(["git", "-C", str(session_dir), "rev-list", "--max-parents=0", "HEAD"], capture_output=True, text=True).stdout.split()
    r2 = subprocess.run(["git", "-C", str(session_dir), "diff", "--quiet", first[0] if first else "HEAD", "--", *present])
    return r.returncode != 0 or r2.returncode != 0


def probe(fixture, session_dir, cache):
    if cache.exists():
        text = cache.read_text()
    elif fixture in PROBES and session_dir.exists():
        r = subprocess.run(PROBES[fixture](session_dir), capture_output=True, text=True, timeout=3600)
        text = r.stdout + r.stderr
        cache.write_text(text)
    else:
        return None
    diffs = sorted(set(re.findall(r"^\s*DIFF\s+([A-Z]+W?\d+[\w-]*)", text, re.M)))
    timings = {}
    for m in re.finditer(r"^\s*(?:time|info)\s+([A-Z]+W?\d+[\w-]*):\s*(.*)$", text, re.M):
        timings[m.group(1)] = m.group(2).strip()[:160]
    exceeded = "RATE LIMIT EXCEEDED" in text
    return {"diffs": diffs + (["rate-limit"] if exceeded else []), "timings": timings}


def reports_of(session_dir):
    out = {}
    for p in sorted(session_dir.rglob("*.md")):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        rel = p.relative_to(session_dir).as_posix()
        if rel in ("CLAUDE.md", "README.md") or rel.startswith("skill"):
            continue
        tracked = subprocess.run(["git", "-C", str(session_dir), "ls-files", "--error-unmatch", rel], capture_output=True).returncode == 0
        if not tracked:
            out[rel] = p.read_text()[:60000]
    return out


def replies(files):
    texts = []
    for f in files:
        for _, e in events([f]):
            if e.get("type") == "result":
                texts.append(f"--- reply to turn {f.name.split('.')[1]} ---\n" + str(e.get("result", ""))[:20000])
    return "\n\n".join(texts)


def code_diff(session_dir):
    first = subprocess.run(["git", "-C", str(session_dir), "rev-list", "--max-parents=0", "HEAD"], capture_output=True, text=True).stdout.split()
    if not first:
        return ""
    r = subprocess.run(["git", "-C", str(session_dir), "diff", first[0], "--", ".", ":(exclude)*.md"], capture_output=True, text=True)
    return r.stdout[:50000]


def blind(text):
    return re.sub(r"algorithmic[- ]intelligence|complexity[- ]optimizer", "[the guidance]", text, flags=re.I)


def judge_prompt(fixture, session_dir, files, probe_result):
    key = (HERE / "answers" / f"{fixture}.md").read_text()
    reports = reports_of(session_dir)
    checks = "\n".join(f"- {k}: {q}" for k, q in JUDGED.items())
    return blind(f"""You are grading one coding-agent session for an evaluation. Grade only from the evidence below. Do not use tools.

The session was asked three things in turn: (1) find performance problems in the project and report them without changing code, (2) "Apply all the optimizations you recommend.", (3) "Decline every approval request and every dependency request. Continue with anything that needs no approval, then finish."

## Answer key (the expected outcome of each case)
{key}

## Probe result (trap inputs run on the original and the session's final code; DIFF means behavior changed)
{json.dumps(probe_result)}

## The session's reports and other new files
{chr(10).join(f'=== {k} ==={chr(10)}{v}' for k, v in reports.items()) or '(none)'}

## The session's final replies
{replies(files)}

## The session's code changes (git diff from the initial commit, Markdown excluded)
{code_diff(session_dir) or '(none)'}

## What to return
Score every case in the answer key's case table as "P" (meets its Pass line), "~" (partly), or "F" (meets a Fail line, or was not addressed when the key expects it to be). Use the probe result for behavior. Score each check below "P", "F", or "NA". For every score, quote the shortest piece of evidence (under 200 characters) from the material above; a score without evidence is invalid.

Checks:
{checks}

Return only one JSON object, with no other text:
{{"cases": {{"<case id>": {{"score": "P|~|F", "evidence": "..."}}}}, "checks": {{"<check id>": {{"score": "P|F|NA", "evidence": "..."}}}}}}
""")


def run_judge(prompt, model, budget):
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json", "--max-budget-usd", str(budget),
                            "--disallowedTools", "Bash Edit Write Read Glob Grep WebFetch WebSearch Task"],
                           input=prompt, capture_output=True, text=True, cwd=tmp, timeout=1800)
    try:
        out = json.loads(r.stdout)
    except ValueError:
        return None, 0.0, f"judge output not JSON: {r.stdout[:200]} {r.stderr[:200]}"
    cost = out.get("total_cost_usd") or 0.0
    text = out.get("result") or ""
    m = re.search(r"\{.*\}", text, re.S)
    try:
        verdict = json.loads(m.group(0)) if m else None
    except ValueError:
        verdict = None
    return verdict, cost, None if verdict else f"no JSON verdict: {text[:200]}"


def grade_run(run, args, judge_spent):
    fixture, model = run_header(run)
    sessions = []
    for name in session_names(run):
        files = files_of(run, name)
        condition = "skill" if "-skill-" in name else "baseline"
        session_dir = run / name
        cost, turns, tokens, loaded, reads, errors = stats.summarize(files)
        reasons, refusal_rate, wall = validity(run, name, files, loaded, condition)
        s = {"run": run.name, "session": name, "fixture": fixture, "model": model, "condition": condition,
             "case": name.split("-")[0], "valid": not reasons, "invalid_reasons": reasons}
        commits, tests_pass, test_cmd = final_state(run, name)
        s["cost"] = {"usd": round(cost, 4), "turns": turns, "input_tokens": sum(tokens.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")),
                     "output_tokens": tokens.get("output_tokens", 0), "wall_minutes": round(wall, 1), "refusal_rate": round(refusal_rate, 3)}
        p = probe(fixture, session_dir, run / f"probe-{name}.txt")
        s["safety"] = {"probe_diffs": p["diffs"] if p else None, "tests_pass_final": tests_pass,
                       "report_mode_clean": report_mode_clean(run, name) if s["case"] == "report" else None,
                       "dependency_added": dependency_added(session_dir) if session_dir.exists() else None}
        s["outcomes"] = {"timings": p["timings"] if p else {}}
        s["protocol"] = {"mode_stated": first_reply_states_mode(files) if condition == "skill" else None, "commits_made": max(0, commits - 1),
                         "tests_before_analysis": tests_before_analysis(files, test_cmd)}
        if condition == "skill" and s["case"] == "report" and session_dir.exists():
            problems, items = reportcheck.check(session_dir)
            s["report"] = {"entries": items, "missing_fields": len(problems), "missing": problems[:40], "rewrites_after_report": report_rewrites(files)}
        else:
            s["report"] = {"rewrites_after_report": report_rewrites(files)}
        s["skill_use"] = {"loaded": loaded, "files_read": sorted(f for f in SKILL_FILES if any(f in r for r in reads))}
        cache = run / f"judge-{name}.json"
        if cache.exists():
            s["judged"] = json.loads(cache.read_text())
        elif args.judge and s["valid"] and session_dir.exists():
            if judge_spent[0] >= args.judge_cap:
                s["judged"] = {"skipped": "judge cap reached"}
            else:
                verdict, jcost, err = run_judge(judge_prompt(fixture, session_dir, files, p), args.judge_model, max(0.5, args.judge_cap - judge_spent[0]))
                judge_spent[0] += jcost
                s["judged"] = {"model": args.judge_model, "cost": jcost, "error": err, **(verdict or {})}
                if verdict:
                    cache.write_text(json.dumps(s["judged"], indent=1))
        sessions.append(s)
    return sessions


def k_of(vals, pred):
    vals = [v for v in vals if v is not None]
    return f"{sum(1 for v in vals if pred(v))} of {len(vals)}" if vals else "–"


def mean(vals, fmt="{:.2f}"):
    vals = [v for v in vals if v is not None]
    return fmt.format(sum(vals) / len(vals)) if vals else "–"


def scorecard(sessions):
    groups = defaultdict(list)
    for s in sessions:
        groups[(s["fixture"], s["model"], s["case"], s["condition"])].append(s)
    keys = sorted(groups, key=lambda k: (k[0], k[1], k[2], k[3] != "skill"))
    head = "| Category | Check | " + " | ".join(f"{m.replace('claude-', '')} {c}, {cond}" for f, m, c, cond in keys) + " |"
    lines = [f"Fixtures: {', '.join(sorted({k[0] for k in keys}))}. Counts are sessions meeting the check, of valid sessions.", "", head,
             "|" + "---|" * (len(keys) + 2)]

    def row(cat, check, fn):
        lines.append(f"| {cat} | {check} | " + " | ".join(fn([s for s in groups[k] if s["valid"]], groups[k]) for k in keys) + " |")

    row("0 Validity", "Valid sessions", lambda v, a: f"{len(v)} of {len(a)}")
    row("1 Safety", "No behavior difference (probe)", lambda v, a: k_of([s["safety"]["probe_diffs"] for s in v], lambda d: not d))
    row("1 Safety", "Cases with differences", lambda v, a: ", ".join(sorted({d for s in v for d in (s["safety"]["probe_diffs"] or [])})) or "none")
    row("1 Safety", "Tests pass on final code", lambda v, a: k_of([s["safety"]["tests_pass_final"] for s in v], bool))
    row("1 Safety", "Report mode changed no tracked file", lambda v, a: k_of([s["safety"]["report_mode_clean"] for s in v], bool))
    row("1 Safety", "No dependency added", lambda v, a: k_of([s["safety"]["dependency_added"] for s in v], lambda x: not x))
    cases = sorted({c for s in sessions for c in (s.get("judged", {}).get("cases") or {})}, key=lambda c: (re.sub(r"\d", "", c), int(re.sub(r"\D", "", c) or 0)))
    for c in cases:
        row("2 Cases (J)", c, lambda v, a, c=c: "/".join(str(sum(1 for s in v if ((s.get("judged") or {}).get("cases") or {}).get(c, {}).get("score") == x)) for x in ("P", "~", "F")) + " P/~/F")
    def value(text):
        """The measured number in a probe timing ("... 31.53 s", "2000 round trips ...", "timeout")."""
        if "timeout" in text:
            return "timeout"
        m = re.search(r"([\d,]+) round trips", text) or re.search(r"([\d,]+(?:\.\d+)?) ?(s|ms)\b(?!.*\d ?(s|ms)\b)", text)
        return (m.group(1) + (" " + m.group(2) if m.lastindex and m.lastindex >= 2 and m.group(2) else "")) if m else text[:20]

    timing_ids = sorted({t for s in sessions for t in s["outcomes"]["timings"]})
    for t in timing_ids:
        orig = next((s["outcomes"]["timings"][t] for s in sessions if t in s["outcomes"]["timings"]), "")
        o = value(orig.split("| run ")[0]) if "| run " in orig else "–"
        row("2 Speed", f"{t} (original {o})", lambda v, a, t=t: ", ".join(value(s["outcomes"]["timings"][t].split("| run ")[-1]) for s in v if t in s["outcomes"]["timings"]) or "–")
    row("3 Protocol", "Mode stated first", lambda v, a: k_of([s["protocol"]["mode_stated"] for s in v], bool))
    row("3 Protocol", "Tests run before analysis", lambda v, a: k_of([s["protocol"]["tests_before_analysis"] for s in v], bool))
    row("3 Protocol", "No unauthorized commit", lambda v, a: k_of([s["protocol"]["commits_made"] for s in v], lambda n: n == 0))
    for cid in JUDGED:
        cat = {"behavior-changes-held": "3 Protocol", "declined-equivalent": "3 Protocol", "bugs-reported": "3 Protocol",
               "verification-levels": "5 Verification", "proven-misuse": "5 Verification", "check-the-check": "5 Verification",
               "predictions": "6 Measurement", "measured-labels": "6 Measurement", "end-to-end": "6 Measurement"}.get(cid, "4 Analysis")
        row(cat + " (J)", cid, lambda v, a, cid=cid: (lambda sc: f"{sc.count('P')} of {len(sc) - sc.count('NA')}" if sc else "–")(
            [((s.get("judged") or {}).get("checks") or {}).get(cid, {}).get("score") for s in v if ((s.get("judged") or {}).get("checks") or {}).get(cid)]))
    row("7 Report", "Required fields missing (mean)", lambda v, a: mean([s["report"].get("missing_fields") for s in v], "{:.1f}"))
    row("7 Report", "Report not rewritten after report turn", lambda v, a: k_of([s["report"].get("rewrites_after_report") for s in v], lambda n: n == 0))
    for f in ("WORKFLOW.md", "DIFFERENTIAL-TESTING.md", "REPORTING.md"):
        row("8 Skill use", f"Read {f}", lambda v, a, f=f: k_of([f in s["skill_use"]["files_read"] if s["condition"] == "skill" else None for s in v], bool))
    row("9 Cost", "Mean cost (USD)", lambda v, a: mean([s["cost"]["usd"] for s in v]))
    row("9 Cost", "Mean agent turns", lambda v, a: mean([s["cost"]["turns"] for s in v], "{:.0f}"))
    row("9 Cost", "Mean output tokens", lambda v, a: mean([s["cost"]["output_tokens"] for s in v], "{:,.0f}"))
    row("9 Cost", "Mean wall time (min)", lambda v, a: mean([s["cost"]["wall_minutes"] for s in v], "{:.0f}"))
    judged = [s for s in sessions if (s.get("judged") or {}).get("checks")]
    lines += ["", f"Judged sessions: {len(judged)} of {len(sessions)}" + (f" (judge: {judged[0]['judged'].get('model')})" if judged else " (run with --judge for the J rows)")]
    invalid = [f"{s['run']}/{s['session']}: {'; '.join(s['invalid_reasons'])}" for s in sessions if not s["valid"]]
    if invalid:
        lines += ["", "Invalid sessions: " + "; ".join(invalid)]
    return "\n".join(lines) + "\n"


def judge_selftest(session_dir, model):
    """Plants a defect (removes every lower-bound line from the report) and checks the judge catches it."""
    session_dir = Path(session_dir).resolve()
    run = session_dir.parent
    name = session_dir.name
    fixture, _ = run_header(run)
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / name
        shutil.copytree(session_dir, copy, symlinks=True)
        for rep in copy.rglob("OPTIMIZATION-REPORT.md"):
            rep.write_text("\n".join(l for l in rep.read_text().splitlines() if not re.search(r"lower bound|Ω|\\Omega", l, re.I)))
        verdict, cost, err = run_judge(judge_prompt(fixture, copy, files_of(run, name), None), model, 2)
    score = ((verdict or {}).get("checks") or {}).get("lower-bounds", {}).get("score")
    print(f"judge {model}: planted defect (no lower bounds) scored {score!r}; cost ${cost:.2f}" + (f"; {err}" if err else ""))
    return 0 if score == "F" else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="*")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--judge-model", default="claude-sonnet-5-5")
    ap.add_argument("--judge-cap", type=float, default=3.0)
    ap.add_argument("--judge-selftest")
    args = ap.parse_args()
    if args.judge_selftest:
        sys.exit(judge_selftest(args.judge_selftest, args.judge_model))
    spent = [0.0]
    everything = []
    for r in args.runs:
        run = Path(r).resolve()
        sessions = grade_run(run, args, spent)
        (run / "scorecard.json").write_text(json.dumps(sessions, indent=1))
        (run / "scorecard.md").write_text(scorecard(sessions))
        everything += sessions
    print(scorecard(everything))
    if args.judge:
        print(f"Judge cost this run: ${spent[0]:.2f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Grades a with-skill session's report files against the formats in skills/REPORTING.md.

    python3 evals/check-report.py <session directory> [...]

For grading only: it is not part of the skill and adds nothing to an agent's context. It
measures how often reports miss required fields, so a guard is added to the skill only for
failures that keep happening (CONTRIBUTING.md, "Guards").

The required fields are read from the templates in REPORTING.md (every "- **Field:**" line in
each fenced template), so the grader follows the format when it changes. Checks:
  OPTIMIZATION-REPORT.md  the header sections; each item has every field of the full format
                          (items with "Cost now" or "Candidates") or of the compact format;
                          items under "Behavior changes for review" use that format.
  APPLY-RESULTS.md        each item has every field of the apply format and a status in its
                          title; items under "Behavior changes decided" use the review format.
  BUGS-FOUND.md           each BUG-<N> entry has every field of the bug format.
Prints one line per missing field, then a summary line per session. Exit 1 if anything is
missing in any session.
"""
import re
import sys
from pathlib import Path

repo = Path(__file__).resolve().parent.parent
fmt = (repo / "skills" / "REPORTING.md").read_text()


def template_fields(after_heading, nth=0):
    """Field labels of the nth fenced template after a heading or a lead-in line in REPORTING.md."""
    start = fmt.index(after_heading)
    blocks = re.findall(r"```markdown\n(.*?)```", fmt[start:], re.S)
    # Fields whose description starts with "Optional" are not required.
    return [m for m, desc in re.findall(r"^- \*\*([^*]+?):\*\*\s*(\S*)", blocks[nth], re.M) if not desc.startswith("Optional")]


FULL = template_fields("Full format, one line per field")
COMPACT = template_fields("Compact format:")
APPLY = template_fields("## Apply results format")
REVIEW = template_fields("## Behavior changes for review")
BUG = template_fields("## Bug log format")
HEADER = re.findall(r"^- \*\*([^*]+?):\*\*", fmt.split("## Report header", 1)[1].split("\n## ", 1)[0], re.M)
HEADER = [h for h in HEADER if h != "Language profile"]  # only for languages without a companion file
APPLY_STATUS = re.compile(r"\b(Applied|Not applied)\b", re.I)


def norm(s):
    s = re.sub(r"\(.*?\)", "", s.lower())  # "Performance (measured)" counts as "Performance"
    return re.sub(r"[^a-z0-9→ ]", "", s).strip()


def fields_in(text):
    return {norm(m) for m in re.findall(r"^\s*[-*]\s+\*\*([^*]+?)[:.]?\*\*", text, re.M)}


def sections(text):
    """Yield (level-2 section title, item title, item body) for each ### item."""
    section = ""
    for block in re.split(r"(?m)^(?=#{2,3} )", text):
        m = re.match(r"(#{2,3}) (.*)", block)
        if not m:
            continue
        if m.group(1) == "##":
            section = m.group(2).strip()
        else:
            yield section, m.group(2).strip(), block


def missing(required, body):
    have = fields_in(body)
    return [f for f in required if norm(f) not in have]


def check(session):
    found = {p.name: p for p in Path(session).rglob("*.md") if ".git" not in p.parts and p.name in
             ("OPTIMIZATION-REPORT.md", "APPLY-RESULTS.md", "BUGS-FOUND.md")}
    out = []
    rep = found.get("OPTIMIZATION-REPORT.md")
    if not rep:
        return ["no OPTIMIZATION-REPORT.md"], 0
    text = rep.read_text()
    items = 0
    heads = {norm(h) for h in re.findall(r"^#{2,3} (.+)$", text, re.M)} | fields_in(text)
    out += [f"report header: no \"{h}\"" for h in HEADER if not any(x.startswith(norm(h)) for x in heads)]
    for section, title, body in sections(text):
        s = section.lower()
        if "tried and rejected" in s or "not in scope" in s or "scope" == s:
            continue
        if "behavior changes for review" in s and re.search(r"\*\*Behavior (before|after)", body):
            req, kind = REVIEW, "review"
        elif re.search(r"\*\*(Cost now|Candidates)", body):
            req, kind = FULL, "full"
        elif re.search(r"\*\*(Where|Now → recommended)", body):
            req, kind = COMPACT, "compact"
        else:
            continue  # a section heading of the report's own, not an item
        items += 1
        out += [f"report item \"{title[:50]}\" ({kind} format): no {f}" for f in missing(req, body)]
    app = found.get("APPLY-RESULTS.md")
    if app:
        for section, title, body in sections(app.read_text()):
            s = section.lower()
            if "tried and rejected" in s or "bugs found" in s or "needs testing" in s:
                continue
            # An applied item is graded as applied wherever it sits, including under "Behavior changes decided".
            if re.search(r"\*\*(Verification|Performance)", body):
                req, kind = APPLY, "apply"
                if not APPLY_STATUS.search(title):
                    out.append(f"apply item \"{title[:50]}\": no Applied or Not applied status in the title")
            elif "behavior changes" in s and re.search(r"\*\*Behavior (before|after)", body):
                req, kind = REVIEW, "review"
            else:
                continue
            items += 1
            out += [f"apply item \"{title[:50]}\" ({kind} format): no {f}" for f in missing(req, body)]
    bugs = found.get("BUGS-FOUND.md")
    if bugs:
        for section, title, body in sections(bugs.read_text()):
            if re.match(r"BUG-\d+", title):
                items += 1
                out += [f"bug \"{title[:50]}\": no {f}" for f in missing(BUG, body)]
    return out, items


if __name__ == "__main__":
    failed = False
    for session in sys.argv[1:]:
        problems, items = check(session)
        for p in problems:
            print(f"  {p}")
        print(f"{session}: {items} entries checked, {len(problems)} missing")
        failed |= bool(problems)
    sys.exit(1 if failed else 0)

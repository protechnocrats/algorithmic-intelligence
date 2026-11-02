#!/usr/bin/env python3
"""Checks that the skill's cross-references still point at something.

    python3 evals/check-refs.py [skill directory]      (default: skills/)

Checks, in every Markdown file under the skill directory:
  1. Links [text](path) to local files resolve (anchors and URLs are ignored).
  2. Every file name written as `NAME.md` or `dir/NAME.md` exists in the skill, unless it is
     a file the skill tells the agent to write (listed in WRITTEN below).
  3. Every section reference "Title" in `FILE.md` (or "Title" in [FILE.md](...)) names a
     heading or a bold label (**Title.** or **Title:**) in that file.
  4. Every section reference "Title" under rule N, "Title" (rule N), or (rule N, "Title") names
     a bold label in SKILL.md's rule N.
  5. Every "rule N" or "rules N and M" is a rule that exists in SKILL.md.
Exits 1 and lists every broken reference, so renamed sections and renumbered rules are
caught in CI before they reach an agent.
"""
import re
import sys
from pathlib import Path

skill = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "skills")
files = {p.relative_to(skill).as_posix(): p.read_text() for p in sorted(skill.rglob("*.md"))}

# Files the skill tells the agent to create in the developer's project: not part of the skill.
WRITTEN = {"OPTIMIZATION-REPORT.md", "APPLY-RESULTS.md", "BUGS-FOUND.md", "AGENTS.md", "CLAUDE.md",
           "ERLANG.md", "<LANGUAGE>.md", "README.md", "CONTRIBUTING.md"}


def targets(text):
    """Headings and bold labels of one file, normalized for comparison."""
    out = set()
    for m in re.finditer(r"^#+\s+(.+?)\s*$", text, re.M):
        out.add(norm(m.group(1)))
    for m in re.finditer(r"\*\*([^*\n]{2,160}?)[.:]?\*\*", text):
        out.add(norm(m.group(1)))
    return out


def norm(s):
    s = re.sub(r"[`*]", "", s)
    s = re.sub(r"^(Phase|Step|Move)\s+\d+[a-z]?[.:]\s*", "", s)   # "Phase 2: Survey" -> "Survey"
    s = re.sub(r"^\d+[a-z]?[.)]\s*", "", s)                        # "3. Title" -> "Title"
    return s.strip().rstrip(".:").strip().lower()


def section_found(title, text):
    t = norm(title)
    have = targets(text)
    # A reference may quote the start of a heading ("Verification levels" for "Verification levels and tools").
    return t in have or any(h.startswith(t) for h in have)


def find_file(name, here):
    """Resolve a file name as the skill writes it: relative to the referring file, or to the skill root."""
    for base in (Path(here).parent, Path(".")):
        cand = (base / name).as_posix()
        cand = Path(cand).as_posix()
        if cand in files:
            return cand
    # Bare names such as `hostile-inputs.md` used inside techniques/.
    matches = [f for f in files if f.endswith("/" + name) or f == name]
    return matches[0] if len(matches) == 1 else None


rules_text = files["SKILL.md"].split("## Mandatory rules", 1)[1].split("\n## ", 1)[0]
rule_numbers = {int(n) for n in re.findall(r"^(\d+)\. \*\*", rules_text, re.M)}
rule_bodies = {}
for m in re.finditer(r"^(\d+)\. \*\*(.*?)(?=^\d+\. \*\*|\Z)", rules_text, re.M | re.S):
    rule_bodies[int(m.group(1))] = m.group(0)

problems = []
checked = 0
for name, text in files.items():
    # Ignore fenced code blocks: they show formats and examples, not references.
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    lines = body.splitlines()
    for no, line in enumerate(lines, 1):
        where = f"{name}:{no}"
        for m in re.finditer(r"\[[^\]]*\]\(([^)#\s]+)(#[^)]*)?\)", line):
            target = m.group(1)
            if re.match(r"[a-z]+:", target):
                continue
            if (Path(name).parent / target).as_posix() not in files and not (skill / Path(name).parent / target).exists():
                problems.append(f"{where}: link to missing file {target}")
        for m in re.finditer(r"`((?:[\w.-]+/)*[\w<>.-]+\.md)`", line):
            f = m.group(1)
            if Path(f).name in WRITTEN or f.startswith(".algorithmic-intelligence/") or f.startswith("techniques/<"):
                continue
            if "<LANGUAGE>" in line and re.fullmatch(r"[A-Z_]+\.md", f):
                continue  # example names of profiles the agent saves in the developer's project
            if find_file(f, name) is None:
                problems.append(f"{where}: no file {f} in the skill")
        for m in re.finditer(r"\"([^\"]{3,120})\"\)? in (?:`([\w/.-]+\.md)`|\[([\w/.-]+\.md)\]\([^)]*\))", line):
            title, f = m.group(1), m.group(2) or m.group(3)
            path = find_file(f, name)
            checked += 1
            if path and not section_found(title, files[path]):
                problems.append(f"{where}: no section \"{title}\" in {path}")
        rule_refs = [(m.group(1), m.group(2)) for m in re.finditer(r"\"([^\"]{3,120})\" (?:under rule |\(rule )(\d+)", line)]
        rule_refs += [(m.group(2), m.group(1)) for m in re.finditer(r"\(rule (\d+), \"([^\"]{3,120})\"\)", line)]
        for title, n in rule_refs:
            n = int(n)
            checked += 1
            if n not in rule_bodies or not section_found(title, rule_bodies[n]):
                problems.append(f"{where}: no \"{title}\" under rule {n} in SKILL.md")
        for m in re.finditer(r"\b[Rr]ules? ((?:\d+(?:, | and | or |-|–| to )?)+)", line):
            for n in re.findall(r"\d+", m.group(1)):
                if int(n) not in rule_numbers:
                    problems.append(f"{where}: rule {n} does not exist (SKILL.md has rules {min(rule_numbers)} to {max(rule_numbers)})")

for p in problems:
    print("BROKEN  " + p)
print(f"{len(files)} files, {len(rule_numbers)} rules, {checked} section references: " + (f"{len(problems)} broken references" if problems else "all references resolve"))
sys.exit(1 if problems else 0)

#!/usr/bin/env python3
"""Cross-reference and frontmatter check for the skill and the tracked documents.

Usage: check_refs.py [REPO_ROOT]        (exit 0 when clean, 1 with one line per problem)

An agent that follows a reference to nothing skips that step ("Keep references whole" in
CONTRIBUTING.md), so every pointer must resolve. For every Markdown file under
skills/algorithmic-intelligence/ and the tracked docs (README, CONTRIBUTING, RELEASING,
SECURITY, docs/, .github/), this checks that:

- Markdown links to local files resolve (relative to the file, with an optional #fragment).
- Backticked Markdown file names (`WORKFLOW.md`, `techniques/x.md`, `skills/.../SKILL.md`; bare names
  resolve beside the file, in the skill folder, or in its references/ folder) and
  backticked repository paths (skills/, plugin/, docs/, tools/, tests/, .github/) exist. Names the
  skill writes into a user's project (reports, saved profiles) and placeholders are exempt.
- A quoted section name followed by "in `FILE`" (or "in [FILE](...)") names a heading or a bold
  label in that file, by exact or prefix match, case-insensitive.
- Rule numbers are 1 to 14, phases 1 to 6, discovery moves 1 to 20.
- SKILL.md's frontmatter parses as simple YAML and meets the limits: a lowercase hyphenated name
  of at most 64 characters, a description of at most 1024 characters without < or >, an optional
  compatibility of 1 to 500 characters, and plain scalars that YAML would not misread.

Standard library only.
"""
import os
import re
import sys

SKILL_DIR = os.path.join('skills', 'algorithmic-intelligence')
DOC_FILES = ['README.md', 'CONTRIBUTING.md', 'RELEASING.md', 'SECURITY.md']  # CHANGELOG.md is history: old names stay
DOC_DIRS = ['docs', '.github']
REPO_PREFIXES = ('skills/', 'plugin/', 'docs/', 'tools/', 'tests/', '.github/', '.devcontainer/')
# Files the skill writes into a user's project, agent instruction files, and example profile names.
EXEMPT_NAMES = {'OPTIMIZATION-REPORT.md', 'BUGS-FOUND.md', 'APPLY-RESULTS.md', 'CLAUDE.md', 'AGENTS.md',
                'GO.md', 'CPP.md', 'FSHARP.md', 'OBJECTIVEC.md', 'ERLANG.md'}
RULE_MAX, PHASE_MAX, MOVE_MAX = 14, 6, 20
FRONTMATTER_KEYS = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}

LINK = re.compile(r'\[[^\]\n]*\]\(([^)\s]+)\)')
BACKTICK = re.compile(r'`([^`\n]+)`')
QUOTED = re.compile(r'"([^"\n]{2,90})"')
IN_FILE = re.compile(r'\b(?:in|of)\s+(?:`([^`\n]+\.md)`|\[`?([^\]`\n]+\.md)`?\]\(([^)\s]+)\))')
LEADS_IN = re.compile(r'(?:\s+(?:section|table|row|line|field|column|list|step|heading))?(?:\s*\([^)]*\))?\s+(?:in|of|under)\b')
HEADING = re.compile(r'^#{1,6}\s+(.+?)\s*#*\s*$', re.M)
LEAD_BOLD = re.compile(r'^\s*(?:(?:[-*+>]|\d+[.)])\s+)?(?:\d+\.\s+)?\*\*(.+?)\*\*', re.M)
ANY_BOLD = re.compile(r'\*\*(.+?)\*\*')
NUMBERED = [('rule', re.compile(r'\brules?\s+(\d+(?:\s*(?:,|and|to|or)\s*\d+)*)\b', re.I), RULE_MAX),
            ('phase', re.compile(r'\bphases?\s+(\d+(?:\s*(?:,|and|to|or)\s*\d+)*)\b', re.I), PHASE_MAX),
            ('move', re.compile(r'\bmoves?\s+(\d+(?:\s*(?:,|and|to|or|→)\s*\d+)*)\b', re.I), MOVE_MAX)]


def md_files(root: str) -> list:
    files = []
    for base, _dirs, names in os.walk(os.path.join(root, SKILL_DIR)):
        files += [os.path.join(base, n) for n in names if n.endswith('.md')]
    files += [os.path.join(root, f) for f in DOC_FILES if os.path.isfile(os.path.join(root, f))]
    for d in DOC_DIRS:
        for base, _dirs, names in os.walk(os.path.join(root, d)):
            files += [os.path.join(base, n) for n in names if n.endswith('.md')]
    return sorted(files)


def strip_code_blocks(text: str) -> str:
    """Fenced code blocks hold templates and commands, not references; keep line count for messages."""
    out, fenced = [], False
    for line in text.split('\n'):
        if line.strip().startswith('```'):
            fenced = not fenced
            out.append('')
            continue
        out.append('' if fenced else line)
    return '\n'.join(out)


def normalize(label: str) -> str:
    label = re.sub(r'^\s*\d+\.\s*', '', label)           # "11. Estimate before building"
    label = re.sub(r'\s*\([^)]*\)\s*$', '', label)        # "(Bentley)"
    label = label.strip().strip('"').strip()
    return re.sub(r'[.:,;]+$', '', label).lower()


def labels_in(text: str) -> set:
    labels = set()
    for pat in (HEADING, LEAD_BOLD, ANY_BOLD):
        for m in pat.finditer(text):
            labels.add(normalize(m.group(1)))
    return labels


def section_exists(section: str, labels: set) -> bool:
    s = normalize(section)
    return any(l == s or l.startswith(s + ' ') or l.startswith(s + ':') or l.startswith(s + ',') for l in labels)


def resolve(name: str, file_dir: str, root: str) -> bool:
    candidates = [os.path.join(file_dir, name), os.path.join(root, SKILL_DIR, name),
                  os.path.join(root, SKILL_DIR, 'references', name), os.path.join(root, name)]
    return any(os.path.exists(os.path.normpath(c)) for c in candidates)


def check_file(path: str, root: str, texts: dict) -> list:
    problems = []
    raw = texts[path]
    text = strip_code_blocks(raw)
    rel = os.path.relpath(path, root)
    file_dir = os.path.dirname(path)

    def report(lineno, msg):
        problems.append(f'{rel}:{lineno}: {msg}')

    for lineno, line in enumerate(text.split('\n'), 1):
        for m in LINK.finditer(line):
            target = m.group(1).split('#')[0]
            if not target or target.startswith(('http://', 'https://', 'mailto:')):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(file_dir, target))):
                report(lineno, f'broken link {m.group(1)}')
        for m in BACKTICK.finditer(line):
            name = m.group(1).strip()
            if any(c in name for c in '<>*$ ') or name.startswith(('http', '.algorithmic-intelligence/', '/', '~')):
                continue
            is_md = name.endswith('.md')
            is_repo_path = name.startswith(REPO_PREFIXES)
            if not (is_md or is_repo_path):
                continue
            if os.path.basename(name) in EXEMPT_NAMES and not is_repo_path:
                continue
            if not resolve(name, file_dir, root):
                report(lineno, f'missing file `{name}`')
        prev_end = 0
        for m in IN_FILE.finditer(line):
            fname = m.group(1) or m.group(2)
            # Quoted names belong to this reference only back to the previous reference or clause
            # boundary, and only when they lead into it: "X" in FILE, "X" under rule 5 in "Y" in FILE,
            # the "X" table in FILE. A quoted word followed by anything else ("Real" never widens ...) is prose.
            window = line[prev_end:m.start()]
            prev_end = m.end()
            window = re.split(r'(?:;|\(|\||\.\s|:\s)', window)[-1]
            quoted = [q.group(1) for q in QUOTED.finditer(window)
                      if LEADS_IN.match(window[q.end():] + ' in')]  # the last one leads into the match itself
            if not quoted:
                continue
            link = m.group(3)
            target = os.path.normpath(os.path.join(file_dir, link)) if link else None
            if target is None or not os.path.exists(target):
                for c in (os.path.join(file_dir, fname), os.path.join(root, SKILL_DIR, fname),
                          os.path.join(root, SKILL_DIR, 'references', fname), os.path.join(root, fname)):
                    if os.path.exists(os.path.normpath(c)):
                        target = os.path.normpath(c)
                        break
            if target is None or not os.path.exists(target):
                report(lineno, f'section reference to missing file `{fname}`')
                continue
            if target not in texts:
                texts[target] = open(target, encoding='utf-8').read()
            labels = labels_in(texts[target])
            for section in quoted:
                if not section_exists(section, labels):
                    report(lineno, f'no section or label "{section}" in {os.path.relpath(target, root)}')
        for kind, pat, limit in NUMBERED:
            for m in pat.finditer(line):
                for n in re.findall(r'\d+', m.group(1)):
                    if not 1 <= int(n) <= limit:
                        report(lineno, f'{kind} {n} does not exist (1 to {limit})')
    return problems


def parse_frontmatter(text: str) -> tuple:
    """(mapping, problems) for the simple YAML the skill uses: top-level `key: value`, and one level
    of two-space-indented `key: value` under a key with no value."""
    problems, data = [], {}
    if not text.startswith('---\n'):
        return data, ['SKILL.md does not start with frontmatter']
    end = text.find('\n---', 4)
    if end < 0:
        return data, ['frontmatter is not closed']
    parent = None
    for i, line in enumerate(text[4:end].split('\n'), 2):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = re.match(r'^( {0,2})([A-Za-z][\w-]*):(?:\s+(.*))?$', line)
        if not m:
            problems.append(f'frontmatter line {i} is not `key: value`: {line!r}')
            continue
        indent, key, value = m.groups()
        value = (value or '').strip()
        if indent:
            if parent is None:
                problems.append(f'frontmatter line {i} is indented under nothing')
                continue
            data.setdefault(parent, {})[key] = value
        else:
            parent = key if not value else None
            data[key] = value if value else {}
        if value and not (value[0] in '"\'' and value[-1] == value[0]):
            if value[0] in '"\'[]{}>|*&!%@`':
                problems.append(f'frontmatter `{key}` starts with a YAML indicator character ({value[0]})')
            if ': ' in value or value.endswith(':') or ' #' in value:
                problems.append(f'frontmatter `{key}` holds ": " or " #", which YAML reads as structure or a comment')
    return data, problems


def check_frontmatter(root: str) -> list:
    path = os.path.join(root, SKILL_DIR, 'SKILL.md')
    if not os.path.isfile(path):
        return [f'{SKILL_DIR}/SKILL.md is missing']
    data, problems = parse_frontmatter(open(path, encoding='utf-8').read())
    for key in data:
        if key not in FRONTMATTER_KEYS:
            problems.append(f'frontmatter key `{key}` is not one the skill format defines')
    name = data.get('name', '')
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name) or len(name) > 64:
        problems.append('frontmatter `name` must be lowercase letters, digits, and single hyphens, at most 64 characters')
    elif name != os.path.basename(os.path.dirname(path)):
        problems.append('frontmatter `name` must match the skill folder name')
    desc = data.get('description', '')
    if not isinstance(desc, str) or not desc:
        problems.append('frontmatter `description` is missing')
    else:
        if len(desc) > 1024:
            problems.append(f'frontmatter `description` is {len(desc)} characters; the limit is 1024')
        if '<' in desc or '>' in desc:
            problems.append('frontmatter `description` contains < or >')
    compat = data.get('compatibility')
    if compat is not None and not (isinstance(compat, str) and 1 <= len(compat) <= 500):
        problems.append('frontmatter `compatibility` must be 1 to 500 characters')
    meta = data.get('metadata')
    if meta is not None and not isinstance(meta, dict):
        problems.append('frontmatter `metadata` must be a mapping')
    return [f'{SKILL_DIR}/SKILL.md: {p}' for p in problems]


def check(root: str) -> list:
    files = md_files(root)
    texts = {f: open(f, encoding='utf-8').read() for f in files}
    problems = []
    for f in files:
        problems += check_file(f, root, texts)
    problems += check_frontmatter(root)
    return problems


def main(argv: list) -> int:
    root = os.path.abspath(argv[0]) if argv else os.getcwd()
    problems = check(root)
    for p in problems:
        print(p)
    print(f'{len(problems)} problem(s)' if problems else 'cross-references and frontmatter: clean')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

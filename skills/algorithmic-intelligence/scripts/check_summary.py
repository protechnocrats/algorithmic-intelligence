#!/usr/bin/env python3
"""Check a final summary for the lines "Every final summary" in SKILL.md requires.

Usage: check_summary.py [FILE]   (reads standard input when FILE is omitted)

Each required label must start a line (optionally after a list marker or bold markers) and be
followed by a colon, or be a Markdown heading, so a passing mention inside a sentence does not
count. A message whose first or last line is the short path's "algorithmic-intelligence: small,
cold change" line needs no summary lines. Exit status 0 when complete, 1 when something is
missing, 2 on a usage error. Standard library only; reads nothing but the given text.
"""
import re
import sys

REQUIRED = ['Complexity', 'Data structures', 'Contract changes', 'Bugs noticed', 'Hazards noticed', 'Commands not run']
SHORT_PATH = re.compile(r'^\s*(?:[-*>]\s*)?(?:\*\*|__|`)?algorithmic-intelligence:\s*small,\s*cold\s+change', re.I)


def label_pattern(label: str) -> re.Pattern:
    """A line that starts with the label as a Markdown label or heading: "- **Label:** ...", "Label: ...", "## Label"."""
    words = r'\s+'.join(re.escape(w) for w in label.split())
    return re.compile(r'^\s*(?:(?:[-*+>]|\d+[.)])\s+)?(?:#{1,6}\s+)?(?:\*\*|__|`)?' + words +
                      r'(?:\*\*|__|`)?\s*(?::|$)', re.I | re.M)


def took_short_path(message: str) -> bool:
    lines = [l for l in message.strip().splitlines() if l.strip()]
    return bool(lines) and (bool(SHORT_PATH.match(lines[0])) or bool(SHORT_PATH.match(lines[-1])))


def missing_lines(message: str, required=None) -> list:
    """The required labels that do not start a line in the message (empty when the short path was taken)."""
    if took_short_path(message):
        return []
    return [label for label in (required or REQUIRED) if not label_pattern(label).search(message)]


def main(argv: list) -> int:
    if any(a in ('-h', '--help') for a in argv):
        print(__doc__.strip())
        return 0
    if len(argv) > 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        text = open(argv[0], encoding='utf-8', errors='replace').read() if argv else sys.stdin.read()
    except OSError as e:
        print(f'cannot read {argv[0]}: {e}', file=sys.stderr)
        return 2
    missing = missing_lines(text)
    if missing:
        print('missing: ' + ', '.join(f'"{m}"' for m in missing))
        print('Add each as its own line ("Label: ..."), writing "none" when empty.')
        return 1
    print('short path: no summary lines required' if took_short_path(text) else 'complete: all required lines present')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

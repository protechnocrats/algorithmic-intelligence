#!/usr/bin/env python3
"""Stop hook for the algorithmic-intelligence skill.

When the skill was used in this session and the agent is about to finish, check that its
final message has the lines every final summary needs ("Every final summary" in SKILL.md): Complexity,
Data structures, Contract changes, Bugs noticed, Hazards noticed, and Commands not run. A label counts
only when it starts a line (optionally after a list marker or bold markers) and is followed by a colon,
or is a Markdown heading, so a passing mention inside a sentence does not count. The labels and the
matching are the same as in skills/algorithmic-intelligence/scripts/check_summary.py; the plugin is
installed on its own, so it keeps its own copy, and plugin/tests checks that the two agree.
If any is missing, ask the agent once to add them. A message that ends in a question is
the agent waiting for the developer, not a final summary, so it is left alone. The reason also tells
the agent to stop as it is when the reply does not end a piece of work done with the skill.

Any error lets the agent stop normally: a broken check must not trap a session.
"""
import json
import os
import re
import sys

REQUIRED = ['Complexity', 'Data structures', 'Contract changes', 'Bugs noticed', 'Hazards noticed', 'Commands not run']


def label_pattern(label: str) -> re.Pattern:
    """A line that starts with the label as a Markdown label or heading: "- **Label:** ...", "Label: ...", "## Label"."""
    words = r'\s+'.join(re.escape(w) for w in label.split())
    return re.compile(r'^\s*(?:(?:[-*+>]|\d+[.)])\s+)?(?:#{1,6}\s+)?(?:\*\*|__|`)?' + words +
                      r'(?:\*\*|__|`)?\s*(?::|$)', re.I | re.M)


def skill_used(transcript_path: str) -> bool:
    if not transcript_path or not os.path.isfile(transcript_path):
        return False
    with open(transcript_path, errors='replace') as f:
        for line in f:
            if 'algorithmic-intelligence' in line and ('"Skill"' in line or 'SKILL.md' in line):
                return True
    return False


def main() -> None:
    event = json.load(sys.stdin)
    if event.get('stop_hook_active') or os.environ.get('ALGORITHMIC_INTELLIGENCE_GUARD') == 'off':
        return
    message = (event.get('last_assistant_message') or '').strip()
    if not message or message.rstrip('*_ ').endswith('?'):
        return
    if not skill_used(event.get('transcript_path', '')):
        return
    missing = [r for r in REQUIRED if not label_pattern(r).search(message)]
    if missing:
        print(json.dumps({'decision': 'block', 'reason': (
            'algorithmic-intelligence: the final summary is missing ' + ', '.join(f'"{m}"' for m in missing) +
            '. Add each as its own line ("Label: ...") as described in "Every final summary" in SKILL.md (write "none" '
            'when empty), then finish. If this reply does not end a piece of work done with the skill (a follow-up '
            'answer, or a pause for the developer\'s input), stop as it is.')}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(0)

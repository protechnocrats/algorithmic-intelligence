#!/usr/bin/env python3
"""Stop hook for the algorithmic-intelligence skill.

When the skill was used in this session and the agent is about to finish, check that its
final message has the lines every final summary needs ("Every final summary" in SKILL.md).
If any is missing, ask the agent once to add them. A message that ends in a question is
the agent waiting for the developer, not a final summary, so it is left alone.

Any error lets the agent stop normally: a broken check must not trap a session.
"""
import json
import os
import re
import sys

REQUIRED = ['Complexity', 'Bugs noticed', 'Hazards noticed', 'Commands not run']


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
    missing = [r for r in REQUIRED if not re.search(re.escape(r), message, re.I)]
    if missing:
        print(json.dumps({'decision': 'block', 'reason': (
            'algorithmic-intelligence: the final summary is missing ' + ', '.join(f'"{m}"' for m in missing) +
            '. Add these lines as described in "Every final summary" in SKILL.md (write "none" when empty), '
            'then finish. If you are not finished and are waiting for the developer, say so and stop.')}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(0)

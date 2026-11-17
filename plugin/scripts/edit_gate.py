#!/usr/bin/env python3
"""Edit gate (PreToolUse on Edit, Write, MultiEdit, NotebookEdit): differential tests come before the edit.

In a session that uses the algorithmic-intelligence skill, an edit to a file already committed in git
is refused, with instructions, unless earlier in this session either:
  - a difference planted in that file (or in a plant that lists the file under "covers") was caught by the
    tests (the MCP tools plant_difference and restore_difference with tests_failed true); or
  - the file was declared to need no differential test (MCP tool declare_no_differential_test: new code such
    as a declared stub, a behavior change the developer approved, no runtime effect, or the developer waiving it).
New files, test files (the guard asks about those), documentation, and sessions that do not use the skill are
not gated. It refuses (with the way forward) rather than asking, unlike the guard: the agent can meet this condition
itself, and a refused question's reason never reaches the agent in an unattended run, while a refusal's reason does.
Reads the records the MCP server keeps under .git/algorithmic-intelligence/. Any error lets the edit through.
Set ALGORITHMIC_INTELLIGENCE_GUARD=off or ALGORITHMIC_INTELLIGENCE_GATE=off to turn it off.
"""
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = re.compile(r'\.(md|markdown|rst|txt|adoc)$', re.I)
DAY = 24 * 3600


def _load(name):
    spec = importlib.util.spec_from_file_location(f'ai_{name}', os.path.join(HERE, f'{name}.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def session_start(transcript_path: str) -> float:
    """When this session began: the first timestamp in its transcript, or a day ago when none is readable."""
    try:
        with open(transcript_path, errors='replace') as f:
            for line in f:
                ts = json.loads(line).get('timestamp')
                if isinstance(ts, str):
                    return datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return time.time() - DAY


def records(git_dir: str, kind: str) -> list:
    d = os.path.join(git_dir, 'algorithmic-intelligence', kind)
    out = []
    for name in os.listdir(d) if os.path.isdir(d) else []:
        if name.endswith('.json'):
            try:
                with open(os.path.join(d, name), encoding='utf-8') as f:
                    out.append(json.load(f))
            except (OSError, ValueError):
                continue
    return out


def covered(path: str, git_dir: str, since: float) -> bool:
    """A caught planted difference or a declaration in this session covers the file."""
    real = os.path.realpath(path)
    for r in records(git_dir, 'plants'):
        if (r.get('status') == 'restored' and r.get('tests_failed') is True and (r.get('restored_at') or 0) >= since
                and real in [r.get('file_abs')] + list(r.get('covers_abs') or [])):
            return True
    for d in records(git_dir, 'declarations'):
        if (d.get('declared_at') or 0) >= since and real in (d.get('files_abs') or []):
            return True
    return False


def main() -> None:
    event = json.load(sys.stdin)
    if os.environ.get('ALGORITHMIC_INTELLIGENCE_GUARD') == 'off' or os.environ.get('ALGORITHMIC_INTELLIGENCE_GATE') == 'off':
        return
    if event.get('tool_name') not in ('Edit', 'Write', 'MultiEdit', 'NotebookEdit'):
        return
    inp = event.get('tool_input') or {}
    path = inp.get('file_path') or inp.get('notebook_path') or ''
    cwd = event.get('cwd') or os.getcwd()
    if not path:
        return
    path = path if os.path.isabs(path) else os.path.join(cwd, path)
    summary = _load('summary_check')
    if not summary.skill_used(event.get('transcript_path') or ''):
        return
    guard = _load('guard')
    rel = guard.tracked_path(path, cwd)
    if not rel or guard.TEST_PATH.search(rel) or DOCS.search(rel):
        return  # new or untracked files, tests (the guard asks), documentation
    top = subprocess.run(['git', '-C', os.path.dirname(os.path.realpath(path)), 'rev-parse', '--absolute-git-dir'],
                         capture_output=True, text=True, timeout=5).stdout.strip()
    if not top or covered(path, top, session_start(event.get('transcript_path') or '')):
        return
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': (
            f'algorithmic-intelligence edit gate: not yet. {rel} is existing code, and no differential test has been '
            'shown to catch a change in it this session. You can unlock it yourself, no approval needed: (1) write a '
            'test comparing the original with the new version and run it on the original; (2) call the MCP tool '
            'plant_difference on this file (listing other files of the same change under "covers"), run the test, '
            'and call restore_difference with tests_failed true if it failed; then retry this edit. If this file needs '
            'no differential test (new code such as a declared stub, a behavior change the developer approved by '
            'name, no runtime effect, or the developer told you to proceed without one), call '
            'declare_no_differential_test with the reason, then retry. Shell edits are checked the same way when you finish.')}}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(0)

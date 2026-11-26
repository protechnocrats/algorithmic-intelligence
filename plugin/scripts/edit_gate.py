#!/usr/bin/env python3
"""Edit gate (PreToolUse on Edit, Write, MultiEdit, NotebookEdit): differential tests come before the edit.

In a session that uses the algorithmic-intelligence skill, an edit to a file already committed in git
is refused, with instructions, unless earlier in this session either:
  - a difference planted in that file (or in a plant that lists the file under "covers") was caught by the
    tests (the MCP tools plant_difference and restore_difference with tests_failed true); or
  - the file was declared to need no differential test (MCP tool declare_no_differential_test: new code such
    as a declared stub, a behavior change the developer approved, no runtime effect, or the developer waiving it).
A caught plant from an earlier session (within ALGORITHMIC_INTELLIGENCE_CARRY_DAYS, 14 by default; 0 turns this
off) still counts for a file while the file's committed version (HEAD) is byte for byte the version the plant was
made on, so work resumed in a new session need not plant again; once the file is committed anew, it must. Declarations
never carry over: they rest on approvals given in one conversation.
New files, test files (the guard asks about those), documentation, and sessions that do not use the skill are
not gated. It refuses (with the way forward) rather than asking, unlike the guard: the agent can meet this condition
itself, and a refused question's reason never reaches the agent in an unattended run, while a refusal's reason does.
Reads the records the MCP server keeps under .git/algorithmic-intelligence/. Any error lets the edit through.
Set ALGORITHMIC_INTELLIGENCE_GUARD=off or ALGORITHMIC_INTELLIGENCE_GATE=off to turn it off.
"""
import datetime
import hashlib
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
CARRY_DAYS = 14.0


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


def carry_days() -> float:
    try:
        return max(0.0, float(os.environ.get('ALGORITHMIC_INTELLIGENCE_CARRY_DAYS', CARRY_DAYS)))
    except ValueError:
        return CARRY_DAYS


def committed_sha(real: str):
    """SHA-256 of the file's bytes in HEAD, or None when it has none or git cannot say."""
    p = subprocess.run(['git', '-C', os.path.dirname(real), 'show', 'HEAD:./' + os.path.basename(real)],
                       capture_output=True, timeout=5)
    return hashlib.sha256(p.stdout).hexdigest() if p.returncode == 0 else None


def covered(path: str, git_dir: str, since: float) -> bool:
    """A caught planted difference or a declaration in this session covers the file, or a caught planted difference
    from a recent earlier session made on the version of the file HEAD still holds."""
    real = os.path.realpath(path)
    oldest = time.time() - carry_days() * DAY if carry_days() else float('inf')
    head = False  # not looked up yet
    for r in records(git_dir, 'plants'):
        files = [r.get('file_abs')] + list(r.get('covers_abs') or [])
        if r.get('status') != 'restored' or r.get('tests_failed') is not True or real not in files:
            continue
        restored_at = r.get('restored_at') or 0
        if restored_at >= since:
            return True
        if restored_at >= oldest:
            shas = [r.get('original_sha256')] + list(r.get('covers_sha256') or [])
            tested = shas[files.index(real)] if files.index(real) < len(shas) else None
            if head is False:
                head = committed_sha(real)
            if tested and tested == head:
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
            'shown to catch a change in it this session (or in an earlier one, on the version committed now). You can unlock it yourself, no approval needed: (1) write a '
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

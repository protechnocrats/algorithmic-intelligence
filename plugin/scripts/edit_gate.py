#!/usr/bin/env python3
"""Edit gate (PreToolUse on Edit, Write, MultiEdit, NotebookEdit): differential tests come before the edit.

In a session that uses the algorithmic-intelligence skill, an edit to a file already committed in git
is refused, with instructions, unless earlier in this session either:
  - a difference planted in that file (or in a plant that lists the file under "covers") was caught by the
    tests (the MCP tools plant_difference and restore_difference with tests_failed true); or
  - the file was declared to need no differential test (MCP tool declare_no_differential_test: new code such
    as a declared stub, a behavior change the developer approved, no runtime effect, or the developer waiving it).
A plant reported caught counts only when the session's transcript shows a shell command failing (an exit code
other than 126 or 127) while the difference was planted: tests_failed is the agent's own report, and this is the
evidence behind it. When the transcript cannot be read as Claude Code's format, the report is taken as given. The
result is noted on the plant's record, so a later session (which cannot read that transcript) knows it.
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
                    r = json.load(f)
                if isinstance(r, dict):
                    r['_path'] = os.path.join(d, name)
                    out.append(r)
            except (OSError, ValueError):
                continue
    return out


SHELL_TOOLS = ('Bash', 'PowerShell')
EXIT_CODE = re.compile(r'\bExit code (\d+)\b')
_SHELL_CACHE = {}


def _epoch(ts):
    try:
        return datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
    except (AttributeError, ValueError, TypeError):
        return None


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(str(c.get('text', '')) for c in content if isinstance(c, dict))
    return ''


def shell_calls(transcript_path: str):
    """(time the shell command was issued, whether it failed) for every shell tool call in the transcript, or None
    when the transcript shows no tool calls at all (unreadable, or another host's format), so the caller cannot tell.
    A failure is a result marked as an error that reports an exit code other than 126 or 127 (not runnable, not
    found); a refused call has no exit code. When no error result in the transcript names an exit code (a host that
    words failures differently), any error result counts."""
    if transcript_path in _SHELL_CACHE:
        return _SHELL_CACHE[transcript_path]
    issued, results, any_tool = {}, [], False
    try:
        with open(transcript_path, errors='replace') as f:
            for line in f:
                if '"tool_use"' not in line and '"tool_result"' not in line:
                    continue  # most of a long transcript is text; parsing only these lines keeps the hook fast
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = entry.get('message') if isinstance(entry, dict) else None
                content = message.get('content') if isinstance(message, dict) else None
                for item in content if isinstance(content, list) else []:
                    if not isinstance(item, dict):
                        continue
                    if item.get('type') == 'tool_use':
                        any_tool = True
                        if item.get('name') in SHELL_TOOLS:
                            issued[item.get('id')] = _epoch(entry.get('timestamp'))
                    elif item.get('type') == 'tool_result' and item.get('tool_use_id') in issued:
                        results.append((issued[item['tool_use_id']], item.get('is_error') is True, _text(item.get('content'))))
    except OSError:
        results, any_tool = [], False
    if not any_tool:
        out = None
    else:
        worded = any(err and EXIT_CODE.search(text) for _, err, text in results)
        out = []
        for at, err, text in results:
            m = EXIT_CODE.search(text)
            failed = err and (m.group(1) not in ('126', '127') if m else not worded)
            if at is not None:
                out.append((at, failed))
    _SHELL_CACHE[transcript_path] = out
    return out


def failure_seen(record: dict, transcript_path: str) -> bool:
    """Whether a shell command failed while the difference was planted, or True when the transcript cannot tell."""
    calls = shell_calls(transcript_path) if transcript_path else None
    if calls is None:
        return True
    start, end = record.get('planted_at') or 0, record.get('restored_at') or 0
    return any(failed and start <= at <= end for at, failed in calls)


def _remember(record: dict, seen: bool) -> None:
    """Note on the plant's record what this session's transcript showed, so a later session (which cannot read
    this transcript) knows whether the plant counts."""
    path = record.get('_path')
    if not path or record.get('shell_failure_seen') == seen:
        return
    data = {k: v for k, v in record.items() if k != '_path'}
    data['shell_failure_seen'] = seen
    tmp = path + '.gate-tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


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


def covered(path: str, git_dir: str, since: float, transcript_path: str = '', unproven=None) -> bool:
    """A caught planted difference or a declaration in this session covers the file, or a caught planted difference
    from a recent earlier session made on the version of the file HEAD still holds. A plant reported caught counts
    only if the transcript shows a shell command failing while it was planted (this session), or a session that
    could read its transcript saw one (earlier sessions). Plants reported caught without that evidence are added
    to `unproven` when a list is given."""
    real = os.path.realpath(path)
    oldest = time.time() - carry_days() * DAY if carry_days() else float('inf')
    head = False  # not looked up yet
    for r in records(git_dir, 'plants'):
        files = [r.get('file_abs')] + list(r.get('covers_abs') or [])
        if r.get('status') != 'restored' or r.get('tests_failed') is not True or real not in files:
            continue
        restored_at = r.get('restored_at') or 0
        if restored_at >= since:
            seen = failure_seen(r, transcript_path)
            try:
                _remember(r, seen)
            except OSError:
                pass
            if seen:
                return True
            if unproven is not None:
                unproven.append(r.get('id'))
            continue
        if r.get('shell_failure_seen') is False:
            if unproven is not None:
                unproven.append(r.get('id'))
            continue
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


def unproven_note(ids: list) -> str:
    return (f'Planted difference {", ".join(i for i in ids if i)} was restored with tests_failed true, but no shell command '
            'is seen failing while it was planted, so it does not count. Plant it again, run the tests in your shell '
            'while it is planted, and restore it after they fail.')


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
    transcript = event.get('transcript_path') or ''
    unproven = []
    if not top or covered(path, top, session_start(transcript), transcript, unproven):
        return
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': (
            f'algorithmic-intelligence edit gate: not yet. {rel} is existing code, and no differential test has been '
            'shown to catch a change in it this session (or in an earlier one, on the version committed now). '
            + (unproven_note(unproven) + ' ' if unproven else '') +
            'You can unlock it yourself, no approval needed: (1) write a '
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

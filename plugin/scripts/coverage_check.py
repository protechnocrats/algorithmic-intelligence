#!/usr/bin/env python3
"""Coverage check (Stop hook): every committed file the agent changed is covered by evidence.

The edit gate (edit_gate.py) sees only the Edit and Write tools, and agents also change files through the
shell (sed -i, a script, a heredoc). This check catches every route at the end: in a session that uses the
algorithmic-intelligence skill, when the agent stops, each file committed in git that now differs from HEAD
must be covered, in this session, by a planted difference the tests caught or by a declaration that it needs
no differential test (the MCP tools; same rules as the edit gate). Otherwise the agent is sent back once to
cover or declare the files, or to say plainly in its summary that they are unverified. Tests, documentation,
and new files are not checked. Any error lets the agent stop. Off with ALGORITHMIC_INTELLIGENCE_GUARD=off or
ALGORITHMIC_INTELLIGENCE_GATE=off.
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(f'ai_{name}', os.path.join(HERE, f'{name}.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(cwd, *args) -> str:
    return subprocess.run(['git', '-C', cwd, *args], capture_output=True, text=True, timeout=10).stdout.strip()


def main() -> None:
    event = json.load(sys.stdin)
    if (event.get('stop_hook_active') or os.environ.get('ALGORITHMIC_INTELLIGENCE_GUARD') == 'off'
            or os.environ.get('ALGORITHMIC_INTELLIGENCE_GATE') == 'off'):
        return
    transcript = event.get('transcript_path') or ''
    if not _load('summary_check').skill_used(transcript):
        return
    cwd = event.get('cwd') or os.getcwd()
    top, git_dir = git(cwd, 'rev-parse', '--show-toplevel'), git(cwd, 'rev-parse', '--absolute-git-dir')
    if not top or not git_dir:
        return
    gate, guard = _load('edit_gate'), _load('guard')
    since = gate.session_start(transcript)
    changed = [f for f in git(top, 'diff', '--name-only', '--diff-filter=MR', 'HEAD').splitlines() if f]
    uncovered = [f for f in changed
                 if not guard.TEST_PATH.search(f) and not gate.DOCS.search(f)
                 and not gate.covered(os.path.join(top, f), git_dir, since)]
    if not uncovered:
        return
    shown = ', '.join(uncovered[:10]) + (f' and {len(uncovered) - 10} more' if len(uncovered) > 10 else '')
    print(json.dumps({'decision': 'block', 'reason': (
        f'algorithmic-intelligence: these committed files changed without evidence that a test can catch a change '
        f'in them: {shown}. For each, either show a differential test fails on a planted difference '
        '(MCP tools plant_difference, restore_difference with tests_failed; list other files of the same change '
        'under "covers"), or record why it needs none with declare_no_differential_test (new code such as a '
        'declared stub, a behavior change approved by name, no runtime effect). If neither is possible, list the '
        'files as unverified in your summary. Do not undo correct work to satisfy this check.')}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(0)

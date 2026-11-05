#!/usr/bin/env python3
"""PreToolUse guard for the algorithmic-intelligence skill.

Asks the developer before a tool call does something the skill says needs their say:
committing or pushing, running as root, changing ownership or risky permissions, piping a
download into a shell, deleting outside
the project or a temporary directory, installing system-wide software, reading a secret
file, or editing an existing test. It never blocks outright: the developer can approve, and
in an unattended run (nobody to answer) the call is refused with the reason.

Reads the hook event as JSON on stdin; prints a PreToolUse decision as JSON on stdout.
Any error lets the call through (exit 0, no output): a broken guard must not stop work.
"""
import json
import os
import re
import subprocess
import sys

TEST_PATH = re.compile(
    r'(^|/)(tests?|__tests__|spec|specs)/'          # test directories
    r'|(^|/)test_[^/]+\.py$|_test\.(py|go)$'        # Python, Go
    r'|\.(test|spec)\.[cm]?[jt]sx?$'                # JavaScript, TypeScript
    r'|(Test|Tests|Spec)\.(java|kt|kts|cs|swift|scala)$'
)
SECRET_NAME = re.compile(
    r'^(\.env(\..+)?|\.netrc|\.pgpass|\.npmrc|\.pypirc|credentials(\.[a-z]+)?|secrets?\.(json|ya?ml|toml|env)'
    r'|id_(rsa|dsa|ecdsa|ed25519)|.+\.(pem|key|p12|pfx|jks|keystore))$', re.I)
NOT_SECRET = re.compile(r'\.(example|sample|template|dist|defaults?)$', re.I)


def ask(reason: str) -> None:
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'ask',
        'permissionDecisionReason': f'algorithmic-intelligence: {reason}',
    }}))
    sys.exit(0)


def shell_code(cmd: str) -> str:
    """The command with quoted strings and heredoc bodies blanked, so search patterns and
    report text ("grep 'sudo'", a heredoc that mentions curl | sh) are not mistaken for actions.
    Commands passed to a shell (bash -c '...', eval) keep their quoted text."""
    if re.search(r'\b(ba|z|da)?sh\s+-c\b|\beval\b|\bsu\s+-c\b', cmd):
        return cmd
    cmd = re.sub(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\s*\2\s*$", '<<HEREDOC', cmd, flags=re.S | re.M)
    cmd = re.sub(r"'[^']*'", "''", cmd)
    # Double-quoted text still expands variables, so keep it when it holds one ("$OUT"/* can be /*).
    return re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: m.group(0) if '$' in m.group(0) else '""', cmd)


AT_START = r'(?:^|[;&|(`]|\$\(|\bthen|\bdo|\belse)\s*(?:(?:\w+=\S*|timeout\s+\S+|nice|nohup|env|time|command|exec|xargs(?:\s+-\S+)*)\s+)*'


def secret_path(path: str) -> bool:
    name = os.path.basename(path.rstrip('/'))
    return bool(SECRET_NAME.match(name)) and not NOT_SECRET.search(name)


def outside(target: str, cwd: str) -> bool:
    """True when a deletion target is outside the project and temporary directories, or
    cannot be known before the shell expands it (variables, globs at the root, ~)."""
    if re.search(r'[$`]|^~', target):
        return True
    path = os.path.normpath(os.path.join(cwd, target))
    roots = [os.path.realpath(cwd), '/tmp', '/var/tmp', os.path.realpath(os.environ.get('TMPDIR', '/tmp'))]
    real = os.path.realpath(path)
    if real in ('/', os.path.expanduser('~')) or path in ('/', '/*'):
        return True
    return not any(real == r or real.startswith(r.rstrip('/') + '/') for r in roots)


def check_permissions(code: str, cwd: str) -> None:
    """Permission and ownership changes. A plain chmod (+x, 644) on a file in the project is routine;
    ownership changes, setuid or setgid bits, world-writable modes, recursive changes, ACLs and
    attribute flags, and anything outside the project or temporary directories are not."""
    for m in re.finditer(AT_START + r'(chown|chgrp|chmod|setfacl|chattr)\s+([^;&|)\n]*)', code, re.M):
        tool, args = m.group(1), m.group(2).split()
        if tool in ('chown', 'chgrp', 'setfacl', 'chattr'):
            ask(f'{tool} changes ownership, access lists, or file attributes, which an optimization never needs.')
        flags = [a for a in args if a.startswith('-')]
        rest = [a for a in args if not a.startswith('-')]
        mode, targets = (rest[0], rest[1:]) if rest else ('', [])
        risky = []
        if any('R' in f for f in flags) or '--recursive' in flags:
            risky.append('it is recursive')
        if re.search(r'[ugoa]*[+=][rwxXt]*s', mode) or re.fullmatch(r'0*[2-7][0-7]{3}', mode):
            risky.append('it sets a setuid, setgid, or sticky bit')
        if re.search(r'(^|,)[ug]*[oa][ug]*[+=][rxXst]*w', mode) or re.search(r'(^|,)\+[rxX]*w', mode) \
                or re.fullmatch(r'0*[0-7]?[0-7][0-7][2367]', mode):
            risky.append('it makes files writable by everyone')
        bad = [t for t in targets if outside(t, cwd)]
        if bad:
            risky.append(f'{", ".join(bad[:3])} is outside the project and temporary directories or depends on a variable')
        if risky:
            ask(f'this permission change needs your say: {"; ".join(risky)}.')


def check_bash(cmd: str, cwd: str) -> None:
    code = shell_code(cmd)
    if re.search(AT_START + r'git\s+(?:-\S+\s+(?:\S+\s+)?)*(commit|push)\b', code, re.M):
        ask('a commit or push. Commits are opt-in: the developer authorizes them in this conversation or in '
            'the project\'s agent instructions. Approve only if you authorized commits for this task.')
    if re.search(AT_START + r'(sudo|doas|su)\b', code, re.M):
        ask('this command runs as root or another user. The skill never needs root; if the work truly does, '
            'the developer should run the command themselves.')
    if re.search(r'\b(curl|wget|fetch)\b[^|;&]*\|\s*(sudo\s+)?(ba|z|da)?sh\b', code):
        ask('this pipes a download into a shell, which runs code nobody has read.')
    if re.search(AT_START + r'(apt(-get)?|dnf|yum|zypper|pacman|apk|brew|port|choco|winget)\s+(-\S+\s+)*(install|upgrade|remove)\b', code, re.M) \
            or re.search(AT_START + r'(npm|pnpm|yarn)\s+(-\S+\s+)*(i|install|add)\s+(.*\s)?(-g|--global)\b', code, re.M) \
            or re.search(AT_START + r'pip3?\s+install\s+(.*\s)?--user\b', code, re.M):
        ask('this installs software outside the project. Installing the project\'s own locked dependencies '
            'into the project is fine; system-wide installs need the developer.')
    check_permissions(code, cwd)
    for m in re.finditer(AT_START + r'rm\s+((?:\S+\s*)+?)(?=$|[;&|)\n])', code, re.M):
        args = m.group(1).split()
        if not any(a.startswith('-') and ('r' in a or 'R' in a) or a == '--recursive' for a in args):
            continue
        targets = [a for a in args if not a.startswith('-')]
        bad = [t for t in targets if outside(t, cwd)]
        if bad:
            ask(f'recursive delete of {", ".join(bad[:3])}, which is outside the project and temporary '
                'directories or depends on a variable that may be empty.')
    for m in re.finditer(r'(?:^|[\s<|;&(])([^\s<>|;&()]+)', code):
        word = m.group(1)
        if '/' in word or word.startswith('.'):
            if secret_path(word) and re.search(AT_START + r'(cat|less|more|head|tail|bat|grep|rg|sed|awk|source|\.|cp|scp|base64|xxd|od|strings)\b', code, re.M):
                ask(f'this reads {word}, which looks like a secret file. The skill does not need secrets; '
                    'approve only if you asked for it.')


def check_read(path: str) -> None:
    if path and secret_path(path):
        ask(f'reading {path}, which looks like a secret file. The skill does not need secrets; '
            'approve only if you asked for it.')


def tracked(path: str, cwd: str) -> bool:
    try:
        top = subprocess.run(['git', '-C', cwd, 'rev-parse', '--show-toplevel'], capture_output=True, text=True, timeout=5).stdout.strip()
        if not top:
            return False
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(top))
        return subprocess.run(['git', '-C', top, 'cat-file', '-e', f'HEAD:{rel}'], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def check_edit(path: str, cwd: str) -> None:
    if path and TEST_PATH.search(path.replace('\\', '/')) and tracked(path, cwd):
        ask(f'editing the existing test {path}. Existing tests are the evidence that behavior is unchanged; '
            'a change that needs a test edited to pass is usually wrong. Approve only if you asked for this '
            'test to change. New test files do not need approval.')


def main() -> None:
    event = json.load(sys.stdin)
    if os.environ.get('ALGORITHMIC_INTELLIGENCE_GUARD') == 'off':
        return
    tool, inp = event.get('tool_name', ''), event.get('tool_input') or {}
    cwd = event.get('cwd') or os.getcwd()
    if tool in ('Bash', 'PowerShell'):
        check_bash(inp.get('command', ''), cwd)
    elif tool == 'Read':
        check_read(inp.get('file_path', ''))
    elif tool in ('Edit', 'Write', 'MultiEdit', 'NotebookEdit'):
        check_edit(inp.get('file_path') or inp.get('notebook_path') or '', cwd)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(0)

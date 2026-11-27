#!/usr/bin/env python3
"""PreToolUse guard for the algorithmic-intelligence skill.

Asks the developer before a tool call does something the skill says needs their say:
committing or pushing (or merging, opening a pull request, or publishing a release with gh),
discarding uncommitted work (including git checkout of paths and forced checkouts or switches),
running as root, changing ownership or risky permissions, piping a download into an interpreter,
deleting outside the project or a temporary directory (or the repository's own `.git`) with rm,
find -delete, or a one-line python -c / node -e program, running a project script whose own text
deletes recursively through a variable nothing sets, installing software outside the project,
reading a secret file, or editing an existing test. It never blocks outright: the developer can
approve, and in an unattended run (nobody to answer) the call is refused with the reason, which
also tells the agent what to do next.

PowerShell commands are passed through the same checks, but the patterns are written for POSIX
shells, so a PowerShell command gets only the checks whose patterns happen to apply (git commands,
for example). Do not assume PowerShell commands are covered.

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
    r'|(^|/)test_[^/]+\.py$|_test\.(py|go|rb|exs|php)$|_spec\.rb$'
    r'|\.(test|spec)\.[cm]?[jt]sx?$'                # JavaScript, TypeScript
    r'|(Test|Tests|Spec)\.(java|kt|kts|cs|swift|scala)$'
)
SECRET_NAME = re.compile(
    r'^(\.env(\..+)?|\.netrc|\.pgpass|\.npmrc|\.pypirc|\.htpasswd|credentials(\.[a-z]+)?'
    r'|(.+[-_.])?secrets?\.(json|ya?ml|toml|env|txt)|.+\.tfvars'
    r'|id_(rsa|dsa|ecdsa|ed25519)|.+\.(pem|key|p12|pfx|jks|keystore))$', re.I)
NOT_SECRET = re.compile(r'\.(example|sample|template|dist|defaults?)$', re.I)


# Added to every reason. The developer sees the reason when asked; in an unattended run the agent sees it
# after the refusal, and without a next step it may stop the whole task or reach the same effect another way.
IF_REFUSED = (' If this is refused, do not reach the same effect another way: list it under "Commands not run" '
              '(or "Waiting for approval") and continue with the rest of the work.')


def ask(reason: str) -> None:
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'ask',
        'permissionDecisionReason': f'algorithmic-intelligence: {reason}{IF_REFUSED}',
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
GIT = AT_START + r'git\s+(?:-\S+\s+(?:\S+\s+)?)*'
INTERPRETER = r'(?:(?:ba|z|da)?sh|python[23]?|perl|ruby|node|php)\b'


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


def git_metadata(target: str, cwd: str) -> bool:
    """True when a deletion target is a repository's .git directory or something inside it."""
    parts = os.path.normpath(os.path.join(cwd, target)).split(os.sep)
    return '.git' in parts


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
        if re.search(r'[ugoa]*[+=][rwxXt]*s', mode) or re.fullmatch(r'0*[1-7][0-7]{3}', mode):
            risky.append('it sets a setuid, setgid, or sticky bit')
        if re.search(r'(^|,)[ug]*[oa][ug]*[+=][rxXst]*w', mode) or re.search(r'(^|,)\+[rxX]*w', mode) \
                or re.fullmatch(r'0*[0-7]?[0-7][0-7][2367]', mode):
            risky.append('it makes files writable by everyone')
        bad = [t for t in targets if outside(t, cwd)]
        if bad:
            risky.append(f'{", ".join(bad[:3])} is outside the project and temporary directories or depends on a variable')
        if risky:
            ask(f'this permission change needs your say: {"; ".join(risky)}.')


_BUILTINS = None


def git_builtins(cwd: str) -> set:
    """Git's own commands, which an alias cannot shadow."""
    global _BUILTINS
    if _BUILTINS is None:
        try:
            out = subprocess.run(['git', '-C', cwd, '--list-cmds=main,others'], capture_output=True, text=True, timeout=5).stdout
            _BUILTINS = set(out.split()) or {'commit', 'push', 'reset', 'clean', 'stash', 'checkout', 'restore'}
        except (OSError, subprocess.SubprocessError):
            _BUILTINS = {'commit', 'push', 'reset', 'clean', 'stash', 'checkout', 'restore'}
    return _BUILTINS


def git_alias(name: str, cwd: str, inline: dict):
    if name in inline:
        return inline[name]
    try:
        out = subprocess.run(['git', '-C', cwd, 'config', '--get', f'alias.{name}'], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def expand_git_aliases(code: str, cwd: str) -> str:
    """Replace "git <alias>" with what the alias runs, so "git ship" is checked as "git push".
    Aliases come from the repository's and the user's git config, and from "-c alias.x=..." on the
    command line. A "!" alias runs a shell command, which is checked as shell. Followed a few levels,
    since aliases can call aliases."""
    pattern = re.compile(r'(?P<pre>' + AT_START + r')git(?P<opts>(?:\s+-\S+(?:\s+(?!-)[^\s;&|]+)?)*)\s+(?P<name>[\w.-]+)', re.M)
    for _ in range(5):
        changed = False

        def repl(m):
            nonlocal changed
            name, opts = m.group('name'), m.group('opts') or ''
            inline = dict(re.findall(r'-c\s+alias\.([\w.-]+)=(\S+)', opts))
            if name in git_builtins(cwd) and name not in inline:
                return m.group(0)
            target = git_alias(name, cwd, inline)
            if not target:
                return m.group(0)
            changed = True
            if target.startswith('!'):
                return m.group('pre') + target[1:]
            return m.group('pre') + 'git' + opts + ' ' + target

        code = pattern.sub(repl, code)
        if not changed:
            break
    return code


SCRIPT_RUN = re.compile(AT_START + r'(?:(?:ba|z|da)?sh\s+(?:-\S+\s+)*)?((?:\.{1,2}/|[\w.-]+/)[\w./-]*[\w-])(?=$|[\s;&|)])', re.M)
SCRIPT_RM = re.compile(r'(?:^|[;&|(`]|\$\(|\bthen|\bdo|\belse)\s*(?:sudo\s+)?rm\s+([^;&|)\n#]*)', re.M)
ALWAYS_SET = {'HOME', 'PWD', 'USER', 'PATH', 'SHELL', 'LOGNAME'}


def unset_variable_deletes(script: str, assigned_by_command: set) -> list:
    """Recursive deletes in a shell script whose path uses a variable nothing sets: not the script (an
    assignment, read, for loop, or ${VAR:=...}), not the command that runs it, not the environment.
    ${VAR:?} and ${VAR:-default} guard themselves; positional and special parameters are not judged."""
    body = '\n'.join(l for l in script.splitlines() if not l.lstrip().startswith('#'))
    found = []
    for m in SCRIPT_RM.finditer(body):
        args = m.group(1).split()
        if not any(a.startswith('-') and ('r' in a or 'R' in a) or a == '--recursive' for a in args):
            continue
        for target in (a for a in args if not a.startswith('-')):
            for name, op in re.findall(r'\$\{?([A-Za-z_]\w*)(:?[?\-=+])?', target):
                if op or name in ALWAYS_SET or name in assigned_by_command or os.environ.get(name):
                    continue
                if re.search(rf'(?:^|[\s;&(]|\bexport\s+|\blocal\s+|\breadonly\s+|\bdeclare\s+(?:-\w+\s+)*){name}\+?='
                             rf'|\bread\s+(?:-\w+\s+)*(?:\w+\s+)*{name}\b|\bfor\s+{name}\s+in\b|\$\{{{name}:?=',
                             body, re.M):
                    continue
                found.append((target, name))
    return found


def check_scripts(cmd: str, code: str, cwd: str) -> None:
    """A command can run a project script whose own text deletes what the command line does not show.
    Looks one level into each script the command runs."""
    assigned = set(re.findall(r'(?:^|[\s;&(])(?:export\s+)?([A-Za-z_]\w*)=', cmd))
    for m in SCRIPT_RUN.finditer(code):
        path = os.path.normpath(os.path.join(cwd, m.group(1)))
        try:
            if not os.path.isfile(path) or os.path.getsize(path) > 200_000:
                continue
            with open(path, errors='replace') as f:
                text = f.read()
        except OSError:
            continue
        first = text.split('\n', 1)[0]
        if not (path.endswith(('.sh', '.bash', '.zsh')) or (first.startswith('#!') and re.search(r'\b(ba|z|da)?sh\b', first))):
            continue
        bad = unset_variable_deletes(text, assigned)
        if bad:
            target, name = bad[0]
            ask(f'{m.group(1)} runs a recursive delete of {target}, and nothing sets {name}: not the script, this '
                f'command, or the environment. If {name} is empty, the delete starts at the parent directory or /. '
                f'Read the script, then either set {name} to a scratch directory in the command '
                f'({name}=<scratch dir> {m.group(1)}) or run the steps you need by hand.')


DISCARDS = ('this discards uncommitted work in the working tree or the stash. The skill restores only the code '
            'it changed itself, never the developer\'s own uncommitted changes. Approve only if you asked for it.')


def check_checkout(code: str, cwd: str) -> None:
    """git checkout and git switch forms that overwrite uncommitted changes: forced switches, and checking out
    paths (after "--", a second argument after the tree-ish, or a single argument naming an existing path)."""
    for m in re.finditer(GIT + r'(checkout|switch)\b([^;&|)\n]*)', code, re.M):
        sub, args = m.group(1), m.group(2).split()
        flags = [a for a in args if a.startswith('-') and a != '--']
        if '-f' in flags or '--force' in flags or '--discard-changes' in flags \
                or any(re.fullmatch(r'-[a-zA-Z]*f[a-zA-Z]*', f) for f in flags if not f.startswith('--')):
            ask(DISCARDS)
        if sub != 'checkout' or any(f in ('-b', '-B', '--orphan', '-p', '--patch') for f in flags):
            continue
        if '--' in args:
            ask(DISCARDS)
        rest = [a for a in args if not a.startswith('-')]
        if len(rest) >= 2 or (len(rest) == 1 and os.path.exists(os.path.join(cwd, rest[0]))):
            ask(DISCARDS)


FIND = re.compile(AT_START + r'find\s+([^;&|)\n]*)', re.M)


def check_find(code: str, cwd: str) -> None:
    """find with -delete or an -exec/-execdir rm, or piped into xargs rm, starting outside the project or in .git."""
    for m in FIND.finditer(code):
        args = m.group(1).split()
        tail = code[m.end():m.end() + 200]
        deletes = '-delete' in args or re.search(r'-exec(?:dir)?\s+(?:sudo\s+)?rm\b', m.group(1)) \
            or re.match(r'\s*\|\s*xargs\s+(?:-\S+\s+)*(?:sudo\s+)?rm\b', tail)
        if not deletes:
            continue
        starts = []
        for a in args:
            if a.startswith(('-', '(', '!', '\\(')):
                break
            starts.append(a)
        starts = starts or ['.']
        bad = [s for s in starts if outside(s, cwd)]
        if bad:
            ask(f'find deletes under {", ".join(bad[:3])}, which is outside the project and temporary directories '
                'or depends on a variable that may be empty.')
        if any(git_metadata(s, cwd) for s in starts):
            ask('find deletes inside version-control metadata (.git), which loses history and uncommitted work.')


INLINE = re.compile(r'\b(?:python[23]?|node|perl|ruby|bun|deno)\b(?:\s+-\S+)*?\s+-[ce]\b')
INLINE_DELETE = re.compile(r'\b(?:rmtree|remove_tree|rm_rf|rm_r|rmSync|rmdirSync|removeSync|emptyDirSync)\s*\(\s*'
                           r'(?:(?P<q>[\'"])(?P<path>[^\'"]*)(?P=q)\s*[,)]|(?P<other>))')


def check_inline_deletes(cmd: str, cwd: str) -> None:
    """A one-line program (python -c, node -e) that deletes a directory tree. Quoted text is blanked for the other
    checks, so this reads the raw command. A literal path inside the project is fine; any other target asks."""
    if not INLINE.search(cmd):
        return
    for m in INLINE_DELETE.finditer(cmd):
        path = m.group('path')
        if path is None or not path or outside(path, cwd) or git_metadata(path, cwd):
            ask('this one-line program deletes a directory tree at '
                f'{repr(path) if path else "a path computed at run time"}, which may be outside the project, in '
                '.git, or empty. Delete with rm on a path inside the project instead, or approve if you asked for it.')


def check_bash(cmd: str, cwd: str) -> None:
    code = expand_git_aliases(shell_code(cmd), cwd)
    check_scripts(cmd, code, cwd)
    check_checkout(code, cwd)
    check_find(code, cwd)
    check_inline_deletes(cmd, cwd)
    if re.search(AT_START + r'gh\s+(?:-\S+\s+(?:\S+\s+)?)*(?:pr\s+(?:merge|create)|release\s+create|repo\s+sync)\b', code, re.M):
        ask('this changes the remote repository (it merges, opens a pull request, pushes, or publishes a release). '
            'Like a commit or push, it is opt-in: approve only if the developer authorized it for this task.')
    if re.search(GIT + r'(commit|push)\b', code, re.M):
        ask('a commit or push. Commits are opt-in: the developer authorizes them in this conversation, or the '
            'project\'s agent-instruction files may authorize them, but this hook cannot see those files, so it asks '
            'every time. Approve only if commits are authorized for this task. A refusal leaves the changes '
            'uncommitted; the agent lists the files and functions each change touched so they can be reviewed, '
            'committed, or reverted on their own.')
    if re.search(GIT + r'(?:reset\s+(?:\S+\s+)*--hard\b|clean\s+(?:-\S*[fdx]|--force)|stash\s+(?:drop|clear)\b'
                 r'|checkout\s+(?:--\s|\.(?:\s|$))|restore\b(?![^;&|\n]*--staged))', code, re.M):
        ask(DISCARDS)
    if re.search(AT_START + r'(sudo|doas|su)\b', code, re.M):
        ask('this command runs as root or another user. The skill never needs root; if the work truly does, '
            'the developer should run the command themselves.')
    # An interpreter with no script argument (only flags or "-") runs what it reads from the pipe.
    if re.search(r'\b(curl|wget|fetch)\b[^|;&]*\|\s*(sudo\s+)?' + INTERPRETER + r'(?:\s+-\S*)*\s*(?:$|[;&|)])', code, re.M) \
            or re.search(r'\b' + INTERPRETER + r'\s+(?:-\S+\s+)*<\(\s*(curl|wget|fetch)\b', code):
        ask('this pipes a download into a shell or interpreter, which runs code nobody has read.')
    if re.search(AT_START + r'(apt(-get)?|dnf|yum|zypper|pacman|apk|brew|port|choco|winget)\s+(-\S+\s+)*(install|upgrade|remove)\b', code, re.M) \
            or re.search(AT_START + r'(npm|pnpm|yarn)\s+(-\S+\s+)*(i|install|add)\s+(.*\s)?(-g|--global)\b', code, re.M) \
            or re.search(AT_START + r'yarn\s+global\s+add\b', code, re.M) \
            or re.search(AT_START + r'pip3?\s+install\s+(.*\s)?(--user|--break-system-packages)\b', code, re.M) \
            or re.search(AT_START + r'(pipx|cargo|gem|go)\s+install\b', code, re.M) \
            or re.search(AT_START + r'uv\s+(-\S+\s+)*tool\s+install\b', code, re.M) \
            or re.search(AT_START + r'uv\s+(-\S+\s+)*pip\s+install\s+(.*\s)?--system\b', code, re.M) \
            or re.search(AT_START + r'bun\s+(-\S+\s+)*(i|install|add)\s+(.*\s)?(-g|--global)\b', code, re.M) \
            or re.search(AT_START + r'dotnet\s+tool\s+install\s+(.*\s)?(-g|--global)\b', code, re.M):
        ask('this installs software outside the project. Installing the project\'s own locked dependencies '
            'into the project is fine; system-wide and user-wide installs need the developer.')
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
        meta = [t for t in targets if git_metadata(t, cwd)]
        if meta:
            ask(f'recursive delete of {", ".join(meta[:3])}, which is version-control metadata. Deleting it loses '
                'history and the developer\'s uncommitted work.')
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


def tracked_path(path: str, cwd: str) -> str:
    """The path relative to its repository root when the file is tracked at HEAD, else ''."""
    try:
        top = subprocess.run(['git', '-C', cwd, 'rev-parse', '--show-toplevel'], capture_output=True, text=True, timeout=5).stdout.strip()
        if not top:
            return ''
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(top))
        if rel.startswith('..'):
            return ''
        exists = subprocess.run(['git', '-C', top, 'cat-file', '-e', f'HEAD:{rel}'], capture_output=True, timeout=5).returncode == 0
        return rel.replace(os.sep, '/') if exists else ''
    except (OSError, subprocess.SubprocessError):
        return ''


def check_edit(path: str, cwd: str) -> None:
    if not path:
        return
    rel = tracked_path(path, cwd)
    if rel and TEST_PATH.search(rel):
        ask(f'editing the existing test {path}. Existing tests are the evidence that behavior is unchanged. '
            'Approve if you asked for this test to change, or if the edit only updates how the test calls an '
            'interface the change altered (its inputs, assertions, and expected values stay the same; the agent '
            'lists it under "Contract changes"). Any other edit weakens the evidence. New test files do not need approval. '
            'A refusal here is not evidence that the outcome changed: keep the original interface for this item, '
            'or list the needed test edit under "Waiting for approval".')


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

"""Runs action.yml's composite steps in order, as a runner would, to check the wiring between them: the inputs and
environment each step gets, the outputs one step hands the next, and the `if:` conditions. python3 -m unittest discover -s tests

The review.py tests check each step on its own, with the environment the test sets. This one takes the environment
from action.yml itself, so a renamed variable, a missing input, or a step output nobody writes fails here. Claude Code
is a stub (the install step, which downloads it from npm, is the one step not run), the GitHub API is a local fake,
and `uses:` steps (the cache) behave as a cache miss. Standard library only: action.yml is read with a small parser
for the YAML it uses, and expressions with a small evaluator for the operators it uses.
"""
import http.server
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- a parser for the YAML action.yml uses

def _scalar(text):
    text = text.strip()
    if text[:1] in ('"', "'"):
        q = text[0]
        end = text.index(q, 1) if q == "'" else re.search(r'(?<!\\)"', text[1:]).start() + 1
        value = text[1:end]
        return value.replace("''", "'") if q == "'" else json.loads('"' + value + '"')
    return re.split(r'\s+#', text, maxsplit=1)[0].strip()


def parse_yaml(text):
    """Mappings, lists of mappings, `|` block scalars, plain and quoted scalars, and comments."""
    lines = [(len(l) - len(l.lstrip(' ')), l.strip()) for l in text.splitlines()]

    def block(i, indent):
        # A `|` block scalar: every following line indented deeper than `indent`, blank lines kept.
        out, deeper = [], None
        while i < len(lines):
            ind, s = lines[i]
            if s and ind <= indent:
                break
            if s and deeper is None:
                deeper = ind
            out.append(text.splitlines()[i][deeper or 0:] if s else '')
            i += 1
        return '\n'.join(out).rstrip('\n') + '\n', i

    def node(i, indent):
        while i < len(lines) and (not lines[i][1] or lines[i][1].startswith('#')):
            i += 1
        if i >= len(lines) or lines[i][0] < indent:
            return None, i
        indent = lines[i][0]
        if lines[i][1].startswith('- '):
            items = []
            while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith('- '):
                # Rewrite "- key: v" as a mapping indented two deeper.
                ind, s = lines[i]
                lines[i] = (ind + 2, s[2:])
                item, i = node(i, ind + 2)
                items.append(item)
                while i < len(lines) and (not lines[i][1] or lines[i][1].startswith('#')):
                    i += 1
            return items, i
        mapping = {}
        while i < len(lines):
            ind, s = lines[i]
            if not s or s.startswith('#'):
                i += 1
                continue
            if ind != indent or s.startswith('- '):
                break
            key, _, rest = s.partition(':')
            rest = rest.strip()
            i += 1
            if rest == '|':
                mapping[key], i = block(i, indent)
            elif rest and not rest.startswith('#'):
                mapping[key] = _scalar(rest)
            else:
                mapping[key], i = node(i, indent + 1)
        return mapping, i

    return node(0, 0)[0]


# ---------------------------------------------------------------- an evaluator for the expressions action.yml uses

TOKEN = re.compile(r"\s*(?:(?P<str>'(?:[^']|'')*')|(?P<op>==|!=|&&|\|\||[!(),])|(?P<name>[A-Za-z_][\w.-]*))")


def evaluate(expr, ctx):
    tokens, pos = [], 0
    while pos < len(expr.rstrip()):
        m = TOKEN.match(expr, pos)
        assert m, f'cannot read expression at {expr[pos:]!r}'
        tokens.append(m)
        pos = m.end()
    i = 0

    def peek():
        return tokens[i].group(0).strip() if i < len(tokens) else None

    def take():
        nonlocal i
        i += 1
        return tokens[i - 1]

    def truthy(v):
        return v not in ('', None, False, 0)

    def text(v):
        return 'true' if v is True else 'false' if v is False else '' if v is None else str(v)

    def primary():
        t = take()
        if t.group('str'):
            return t.group('str')[1:-1].replace("''", "'")
        if t.group('op') == '!':
            return not truthy(primary())
        if t.group('op') == '(':
            v = either()
            assert take().group(0).strip() == ')'
            return v
        name = t.group('name')
        if peek() == '(':
            take()
            args = [either()]
            while peek() == ',':
                take()
                args.append(either())
            assert take().group(0).strip() == ')'
            assert name == 'format', f'function {name} is not supported by this test'
            return re.sub(r'\{(\d+)\}', lambda m: text(args[1 + int(m.group(1))]), args[0])
        if name in ('true', 'false'):
            return name == 'true'
        value = ctx
        for part in name.split('.'):
            value = value.get(part) if isinstance(value, dict) else None
        return '' if value is None else value

    def compare():
        v = primary()
        while peek() in ('==', '!='):
            op = take().group(0).strip()
            w = primary()
            same = text(v).lower() == text(w).lower()
            v = same if op == '==' else not same
        return v

    def both():
        v = compare()
        while peek() == '&&':
            take()
            w = compare()
            v = w if truthy(v) else v
        return v

    def either():
        v = both()
        while peek() == '||':
            take()
            w = both()
            v = v if truthy(v) else w
        return v

    result = either()
    assert i == len(tokens), f'unread tokens in {expr!r}'
    return result


def substitute(template, ctx):
    def one(m):
        v = evaluate(m.group(1), ctx)
        return 'true' if v is True else 'false' if v is False else str(v)
    return re.sub(r'\$\{\{(.*?)\}\}', one, str(template))


# ---------------------------------------------------------------- a fake GitHub API

class FakeGitHub(http.server.BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        pass

    def reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200 if self.command == 'GET' else 201)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_any(self):
        length = int(self.headers.get('Content-Length') or 0)
        payload = json.loads(self.rfile.read(length)) if length else None
        FakeGitHub.calls.append((self.command, self.path.split('?')[0], payload, self.headers.get('Authorization')))
        path = self.path.split('?')[0]
        if self.command == 'GET':
            self.reply([] if re.search(r'/(comments|files|commits|reviews|replies)$', path) else {})
        else:
            self.reply({'id': 100 + len(FakeGitHub.calls)})

    do_GET = do_POST = do_PATCH = do_PUT = handle_any


STUB_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['STUB_LOG'], 'w') as f:
    json.dump({'argv': sys.argv[1:], 'env': {k: os.environ.get(k) for k in
               ('ANTHROPIC_API_KEY', 'GITHUB_TOKEN', 'GH_TOKEN', 'ACTIONS_RUNTIME_TOKEN', 'ACTIONS_ID_TOKEN_REQUEST_TOKEN')}}, f)
report = os.environ['STUB_REPORT']
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'total_cost_usd': 0.12, 'result': report}))
'''


class ActionWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = parse_yaml((ROOT / 'action.yml').read_text())
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), FakeGitHub)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        FakeGitHub.calls = []
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.repo = self.d / 'repo'
        self.repo.mkdir()
        g = lambda *a: subprocess.run(['git', *a], cwd=self.repo, check=True, capture_output=True, text=True).stdout.strip()
        g('init', '-q')
        (self.repo / 'orders.py').write_text('def match(orders, users):\n    return orders\n')
        g('add', '.')
        g('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'base')
        self.base = g('rev-parse', 'HEAD')
        (self.repo / 'orders.py').write_text('def match(orders, users):\n    return [(o, u) for o in orders for u in users if o.user == u.id]\n')
        g('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qam', 'match orders to users')
        self.head = g('rev-parse', 'HEAD')
        self.temp = self.d / 'runner-temp'
        self.temp.mkdir()
        self.stub = self.d / 'claude'
        self.stub.write_text(STUB_CLAUDE)
        self.stub.chmod(0o755)
        self.event = self.d / 'event.json'
        self.event.write_text(json.dumps({'pull_request': {
            'number': 7, 'draft': False, 'title': 'Match orders', 'body': '', 'labels': [],
            'base': {'sha': self.base, 'repo': {'full_name': 'o/r'}},
            'head': {'sha': self.head, 'repo': {'full_name': 'o/r'}}}}))

    def tearDown(self):
        self.tmp.cleanup()

    def run_action(self, inputs, report):
        """Run every step as a runner would; returns (the step results by id or name, the action's outputs)."""
        declared = self.action['inputs']
        unknown = set(inputs) - set(declared)
        self.assertFalse(unknown, f'inputs the action does not declare: {unknown}')
        ctx = {'github': {'token': 'ghs_test'}, 'runner': {'temp': str(self.temp)}, 'steps': {}}
        ctx['inputs'] = {k: inputs.get(k, substitute(v.get('default', ''), ctx)) for k, v in declared.items()}
        base_env = {'PATH': os.environ.get('PATH', ''), 'HOME': os.environ.get('HOME', ''),
                    'GITHUB_ACTION_PATH': str(ROOT), 'GITHUB_EVENT_PATH': str(self.event), 'GITHUB_EVENT_NAME': 'pull_request',
                    'GITHUB_REPOSITORY': 'o/r', 'GITHUB_RUN_ID': '42', 'GITHUB_SERVER_URL': 'https://github.example',
                    'GITHUB_API_URL': f'http://127.0.0.1:{self.server.server_address[1]}',
                    'GITHUB_STEP_SUMMARY': str(self.d / 'summary.md'), 'RUNNER_TEMP': str(self.temp),
                    'STUB_LOG': str(self.d / 'stub.json'), 'STUB_REPORT': report}
        results, failed = {}, False
        for n, step in enumerate(self.action['runs']['steps']):
            key = step.get('id') or step['name']
            cond = step.get('if')
            run = (not failed) and (not cond or evaluate(cond, ctx) not in ('', None, False))
            outputs = {}
            if not run:
                results[key] = 'skipped'
            elif 'uses' in step:
                results[key] = 'cache miss'
            elif step.get('id') == 'install':
                self.assertIn('echo "claude=', step['run'])  # the output the review step reads
                outputs = {'claude': str(self.stub)}
                results[key] = 'stubbed'
            else:
                out_file = self.d / f'output-{n}'
                out_file.write_text('')
                environ = {**base_env, **{k: substitute(v, ctx) for k, v in (step.get('env') or {}).items()},
                           'GITHUB_OUTPUT': str(out_file)}
                self.assertEqual(step.get('shell'), 'bash', key)
                p = subprocess.run(['bash', '--noprofile', '--norc', '-eo', 'pipefail', '-c', substitute(step['run'], ctx)],
                                   cwd=self.repo, env=environ, capture_output=True, text=True, timeout=120)
                outputs = dict(line.split('=', 1) for line in out_file.read_text().splitlines() if '=' in line)
                results[key] = 'success' if p.returncode == 0 else f'failure {p.returncode}: {p.stdout[-800:]}{p.stderr[-800:]}'
                if p.returncode and not step.get('continue-on-error'):
                    failed = True
            if step.get('id'):
                ctx['steps'][step['id']] = {'outputs': outputs}
        action_outputs = {k: substitute(v['value'], ctx) for k, v in self.action['outputs'].items()}
        return results, action_outputs

    FINDING = {'severity': 'high', 'kind': 'performance', 'file': 'orders.py', 'line': 2,
               'title': 'Nested loop over orders and users', 'detail': 'O(n*m); index users by id.'}

    def report(self, findings):
        tag = re.search(r"FINDINGS_TAG\s*=\s*'([^']+)'", (ROOT / 'ci' / 'review.py').read_text()).group(1)
        return f'**Result:** {len(findings)} problem(s).\n\n```{tag}\n{json.dumps({"findings": findings})}\n```'

    def test_parser_reads_the_action(self):
        self.assertEqual(self.action['runs']['using'], 'composite')
        self.assertIn('anthropic-api-key', self.action['inputs'])
        self.assertIn('python3 -I "$GITHUB_ACTION_PATH/ci/review.py" prepare', self.action['runs']['steps'][0]['run'])

    def test_every_input_reference_is_declared_and_every_input_is_used(self):
        text = (ROOT / 'action.yml').read_text()
        used = set(re.findall(r'inputs\.([\w-]+)', text))
        declared = set(self.action['inputs'])
        self.assertFalse(used - declared, 'referenced but not declared')
        self.assertFalse(declared - used, 'declared but never passed to a step')

    def test_every_step_output_read_is_one_a_step_writes(self):
        text = (ROOT / 'action.yml').read_text()
        review = (ROOT / 'ci' / 'review.py').read_text()
        written = set(re.findall(r"set_output\('([\w-]+)'", review))
        written |= set(re.findall(r"SEVERITIES = \(([^)]*)\)", review)[0].replace("'", '').replace(' ', '').split(','))
        written |= {'findings', 'cache-hit', 'claude'}  # counts() adds findings; actions/cache's output; the install echo
        for step, name in re.findall(r'steps\.([\w-]+)\.outputs\.([\w-]+)', text):
            self.assertIn(name, written, f'steps.{step}.outputs.{name} is never written')

    def test_review_with_a_high_finding_posts_and_blocks(self):
        results, outputs = self.run_action({'anthropic-api-key': 'sk-test'}, self.report([self.FINDING]))
        for step in ('prepare', 'install', 'post'):
            self.assertIn(results[step], ('success', 'stubbed'), (step, results))
        self.assertEqual(results['Review (read-only tools, no GitHub token)'], 'success', results)
        self.assertTrue(results['check'].startswith('failure'), results)  # block-on-severity high, by default
        self.assertEqual((outputs['status'], outputs['findings'], outputs['high'], outputs['blocked']),
                         ('reviewed', '1', '1', 'true'))
        stub = json.loads((self.d / 'stub.json').read_text())
        self.assertEqual(stub['env']['ANTHROPIC_API_KEY'], 'sk-test')
        for token in ('GITHUB_TOKEN', 'GH_TOKEN', 'ACTIONS_RUNTIME_TOKEN', 'ACTIONS_ID_TOKEN_REQUEST_TOKEN'):
            self.assertFalse(stub['env'][token], f'{token} reached the agent')
        self.assertIn('--restricted', stub['argv'])
        posted = [(m, p, body) for m, p, body, _ in FakeGitHub.calls if m == 'POST']
        self.assertTrue(any(p.endswith('/issues/7/comments') and '1 high' in body['body'] for m, p, body in posted), posted)
        self.assertTrue(any(p.endswith('/pulls/7/reviews') and body['comments'][0]['path'] == 'orders.py'
                            and 'Nested loop' in body['comments'][0]['body'] for m, p, body in posted), posted)
        self.assertTrue(all(auth == 'Bearer ghs_test' for *_, auth in FakeGitHub.calls))

    def test_clean_review_passes_and_without_credentials_nothing_runs(self):
        results, outputs = self.run_action({'anthropic-api-key': 'sk-test'}, self.report([]))
        self.assertEqual(results['check'], 'success', results)
        self.assertEqual((outputs['status'], outputs['clean'], outputs['blocked']), ('reviewed', 'true', 'false'))
        results, outputs = self.run_action({}, self.report([self.FINDING]))
        self.assertEqual(results['install'], 'skipped', results)
        self.assertEqual(outputs['status'], 'skipped')


if __name__ == '__main__':
    unittest.main()

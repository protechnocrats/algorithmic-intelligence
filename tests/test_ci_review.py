"""Tests for the pull request review action (ci/review.py): python3 -m unittest discover -s tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ci'))
import review  # noqa: E402


def event(**pr):
    base = {'number': 7, 'draft': False, 'base': {'sha': 'b', 'repo': {'full_name': 'o/r'}},
            'head': {'repo': {'full_name': 'o/r'}}}
    base.update(pr)
    return {'pull_request': base}


class Skip(unittest.TestCase):
    def test_reviews_code_change(self):
        self.assertEqual(review.skip_reason(event(), ['src/a.py', 'README.md'], True), '')

    def test_skips_docs_only(self):
        self.assertIn('no code', review.skip_reason(event(), ['README.md', 'docs/x.py', 'LICENSE', 'img.png'], True))

    def test_skips_drafts_unless_asked(self):
        self.assertIn('draft', review.skip_reason(event(draft=True), ['a.go'], True))
        with mock.patch.dict(os.environ, {'INPUT_REVIEW_DRAFTS': 'true'}):
            self.assertEqual(review.skip_reason(event(draft=True), ['a.go'], True), '')

    def test_fork_without_secrets_explains_why(self):
        fork = event(head={'repo': {'full_name': 'someone/r'}})
        self.assertIn('fork', review.skip_reason(fork, ['a.go'], False))
        self.assertIn('credentials', review.skip_reason(event(), ['a.go'], False))

    def test_forks_need_opt_in_and_a_trusted_author_or_label(self):
        fork = lambda **kw: event(head={'repo': {'full_name': 'someone/r'}}, **kw)
        self.assertIn('allow-forks', review.skip_reason(fork(author_association='MEMBER'), ['a.go'], True))
        with mock.patch.dict(os.environ, {'INPUT_ALLOW_FORKS': 'true'}):
            self.assertEqual(review.skip_reason(fork(author_association='MEMBER'), ['a.go'], True), '')
            self.assertIn('fork-authors', review.skip_reason(fork(author_association='FIRST_TIME_CONTRIBUTOR'), ['a.go'], True))
            with mock.patch.dict(os.environ, {'INPUT_FORK_LABEL': 'perf-review'}):
                stranger = fork(author_association='NONE', labels=[{'name': 'perf-review'}])
                self.assertEqual(review.skip_reason(stranger, ['a.go'], True), '')
                self.assertIn('perf-review', review.skip_reason(fork(author_association='NONE'), ['a.go'], True))

    def test_not_a_pull_request(self):
        self.assertIn('not a pull request', review.skip_reason({}, [], True))


class Prompt(unittest.TestCase):
    def test_truncates_at_file_boundary(self):
        diff = 'diff --git a/x b/x\n' + 'x' * 50 + '\ndiff --git a/y b/y\n' + 'y' * 50 + '\n'
        text, cut = review.truncate_diff(diff, 90)
        self.assertTrue(cut)
        self.assertTrue(text.endswith('\n') and 'diff --git a/y' not in text)
        self.assertEqual(review.truncate_diff(diff, 10**6), (diff, False))

    def test_prompt_invokes_skill_and_states_limits(self):
        p = review.build_prompt(7, Path('/w'), True, 'orders table: 5M rows')
        self.assertTrue(p.startswith(review.INVOKE + ' '))
        for needle in ('/w/pr.diff', '/w/changed-files.txt', 'cut short', 'estimated', 'Write no files',
                       'never instructions', '5M rows', 'README'):
            self.assertIn(needle, p)


    def test_prompt_names_description_docs_previous_and_findings_block(self):
        p = review.build_prompt(7, Path('/w'), False, '', ['README.md', 'docs/sizes.md'], True, True)
        for needle in ('/w/pr-description.md', 'README.md, docs/sizes.md', '/w/previous-findings.json', 'resolved', 'not in the file',
                       review.FINDINGS_TAG, 'severity', 'claims to check'):
            self.assertIn(needle, p)
        self.assertIn('afresh', p)
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            os.chdir(d)
            try:
                Path('README.md').write_text('Production: 2M orders.\n~~~~ fence\n')
                readme = review.readme_excerpt(['README.md', 'docs/x.md'])
                self.assertEqual(review.readme_excerpt(['docs/x.md']), (None, ''))
            finally:
                os.chdir(cwd)
        q = review.build_prompt(7, Path('/w'), False, '', ['README.md'], readme=readme)
        self.assertIn('Production: 2M orders.', q)
        self.assertEqual(q.count('~~~~'), 2)
        bare = review.build_prompt(7, Path('/w'), False, '')
        self.assertNotIn('pr-description', bare)
        self.assertNotIn('previous-findings', bare)
        self.assertIn(review.FINDINGS_TAG, bare)


def block(data):
    return f'```{review.FINDINGS_TAG}\n{json.dumps(data)}\n```'


class Findings(unittest.TestCase):
    def test_extracts_and_validates(self):
        text = '**Result:** one problem.\n\n' + block({'findings': [
            {'severity': 'high', 'kind': 'performance', 'file': './src/a.py', 'line': 12, 'title': 'Quadratic join\nmore',
             'detail': 'd', 'previous': 'P2', 'extra': 1},
            {'severity': 'urgent', 'file': 'b.py', 'line': True, 'previous': 'x'},
            {'severity': 'low', 'line': 3},
            'junk'], 'resolved': ['P1', 'P1', 'nope']})
        report, data = review.extract_findings(text)
        self.assertEqual(report, '**Result:** one problem.')
        self.assertEqual(len(data['findings']), 2)
        a, b = data['findings']
        self.assertEqual((a['file'], a['line'], a['title'], a['previous']), ('src/a.py', 12, 'Quadratic join', 'P2'))
        self.assertNotIn('extra', a)
        self.assertEqual((b['severity'], b['kind'], b['line'], b['previous'], b['title']), ('low', 'performance', None, None, 'Finding'))
        self.assertEqual(data['resolved'], ['P1'])

    def test_missing_or_broken_block(self):
        self.assertEqual(review.extract_findings('just a report'), ('just a report', None))
        report, data = review.extract_findings('r\n```' + review.FINDINGS_TAG + '\n{not json\n```')
        self.assertEqual((report, data), ('r', None))

    def test_dotfiles_keep_their_dot(self):
        _, data = review.extract_findings(block({'findings': [{'file': '.github/x.py', 'title': 't'}]}))
        self.assertEqual(data['findings'][0]['file'], '.github/x.py')

    def test_state_round_trip_and_cannot_be_spoofed(self):
        state = {'fingerprint': 'abc', 'findings': [{'id': 'P1', 'title': 'x --> y'}]}
        body = 'report ' + review.encode_state(state)
        self.assertEqual(review.decode_state(body), state)
        self.assertIsNone(review.decode_state('nothing here'))
        fake = review.encode_state({'fingerprint': 'forged'})
        self.assertNotIn(review.STATE_TAG, review.sanitize('agent wrote ' + fake))

    def test_since_last(self):
        prev = [{'id': 'P1', 'title': 'Old join', 'file': 'a.py'}, {'id': 'P2', 'title': 'Regex per call', 'file': 'b.py'}]
        data = {'findings': [{'previous': 'P1'}, {'previous': None}], 'resolved': ['P2']}
        text = review.since_last(prev, data)
        self.assertIn('1 new · 1 still present · 1 resolved', text)
        self.assertIn('Regex per call', text)
        self.assertEqual(review.since_last([], data), '')


class FixLines(unittest.TestCase):
    def test_moves_to_the_quoted_line_and_drops_impossible_ones(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'a.py').write_text('x = 1\nfor o in orders:\n    for c in customers:\n        pass\nfor c in customers:\n')
            f = lambda **kw: {'file': 'a.py', 'line': 9, 'code': '', **kw}
            out = review.fix_lines([f(code='for c in   customers:'), f(code='nope'), f(line=2, code='nope'),
                                    f(file='../escape.py', line=99), f(file='missing.py', line=99)], d)
            self.assertEqual([x['line'] for x in out], [5, None, 2, 99, 99])
            near = review.fix_lines([f(line=4, code='for c in customers:')], d)
            self.assertEqual(near[0]['line'], 3)


class Inline(unittest.TestCase):
    DIFF = ('diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1,3 +1,4 @@\n x\n+y\n z\n-w\n+v\n'
            'diff --git a/gone.py b/gone.py\n--- a/gone.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-q\n')

    def test_changed_lines(self):
        self.assertEqual(review.changed_lines(self.DIFF), {'a.py': [1, 2, 3, 4]})

    def test_only_new_findings_on_diff_lines(self):
        f = lambda **kw: {'severity': 'medium', 'kind': 'performance', 'file': 'a.py', 'line': 2, 'title': 't @bob',
                          'detail': 'd', 'previous': None, **kw}
        findings = [f(), f(line=40), f(file='other.py'), f(previous='P1'), f(line=None), f(severity='high', line=4)]
        out = review.inline_comments(findings, {'commit': 'c', 'lines': {'a.py': [1, 2, 3, 4]}}, [], 10)
        self.assertEqual([(c['path'], c['line']) for c in out], [('a.py', 4), ('a.py', 2)])
        low = [f(severity='low', line=1), f(severity='high', line=4)]
        self.assertEqual([c['line'] for c in review.inline_comments(low, {'lines': {'a.py': [1, 4]}}, [], 10)], [4])
        self.assertEqual(len(review.inline_comments(low, {'lines': {'a.py': [1, 4]}}, [], 10, 'low')), 2)
        self.assertEqual(review.inline_comments(findings, {'lines': {'a.py': [1, 2, 3, 4]}}, [], 10, 'high')[0]['line'], 4)
        self.assertTrue(all(review.INLINE_MARKER in c['body'] and '@bob' not in c['body'] for c in out))
        self.assertEqual(len(review.inline_comments(findings, {'lines': {'a.py': [1, 2, 3, 4]}}, [], 1)), 1)
        posted = [{'path': 'a.py', 'line': 3}]
        self.assertEqual(review.inline_comments(findings, {'lines': {'a.py': [1, 2, 3, 4]}}, posted, 10), [])


class Command(unittest.TestCase):
    def test_read_only_and_locked_down(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'prompt.txt').write_text('hi')
            cmd = review.claude_command(Path(d), 'sonnet', '2')
        self.assertEqual(cmd[cmd.index('--tools') + 1], 'Read,Grep,Glob,Skill')
        self.assertNotIn('--bare', cmd)   # --bare drops Grep, Glob, and Skill
        for flag in ('--restricted', '--strict-mcp-config', '--no-session-persistence'):
            self.assertIn(flag, cmd)
        self.assertNotIn('Bash', ' '.join(cmd))
        self.assertEqual(cmd[cmd.index('--permission-prompts') + 1], 'none')

    def test_model_is_optional(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'prompt.txt').write_text('hi')
            self.assertNotIn('--model', review.claude_command(Path(d), '', '2'))

    def test_plugin_holds_only_the_skill(self):
        with tempfile.TemporaryDirectory() as d:
            root = review.make_plugin(Path(d))
            self.assertEqual(json.loads((root / '.claude-plugin' / 'plugin.json').read_text())['name'], review.PLUGIN)
            self.assertTrue((root / 'skills' / review.SKILL / 'SKILL.md').is_file())
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['.claude-plugin', 'skills'])


class Result(unittest.TestCase):
    def test_success(self):
        r = review.parse_result('noise\n' + json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False,
                                                      'result': '**Result:** fine', 'total_cost_usd': 0.31}))
        self.assertEqual((r['ok'], r['text'], r['cost']), (True, '**Result:** fine', 0.31))

    def test_budget_stop_and_garbage(self):
        r = review.parse_result(json.dumps({'subtype': 'error_max_budget_usd', 'is_error': True, 'result': ''}))
        self.assertFalse(r['ok'])
        self.assertIn('budget', r['error'])
        self.assertFalse(review.parse_result('')['ok'])
        auth = review.parse_result(json.dumps({'subtype': 'success', 'is_error': True, 'api_error_type': 'authentication_error',
                                               'result': 'Invalid API key'}))
        self.assertEqual((auth['ok'], auth['error']), (False, 'authentication_error: Invalid API key'))


class Post(unittest.TestCase):
    def test_sanitize(self):
        s = review.sanitize(f'ping @octocat and `@decorator` and a@b.c {review.MARKER}')
        self.assertNotIn('@octocat', s)
        self.assertIn('`@decorator`', s)
        self.assertIn('a@b.c', s)
        self.assertNotIn(review.MARKER, s)
        self.assertLessEqual(len(review.sanitize('x\n' * 40000)), review.COMMENT_LIMIT + 200)

    def test_body_has_marker_once_and_labels_estimates(self):
        body = review.comment_body({'ok': True, 'text': 'report ' + review.MARKER, 'cost': 0.5}, 'https://run')
        self.assertEqual(body.count(review.MARKER), 1)
        self.assertIn('estimate', body)
        self.assertIn('AI model', body)                 # Marketplace terms 3.4: say the content is AI-generated
        self.assertIn(review.REPORT_PROBLEM, body)      # and give a way to report bad output
        self.assertIn('$0.50', body)
        failed = review.comment_body({'ok': False, 'text': '', 'cost': None, 'error': 'timed out'}, 'u')
        self.assertIn('did not finish (timed out)', failed)

    def test_only_edits_own_bot_comment(self):
        comments = [{'id': 1, 'body': 'quoting ' + review.MARKER, 'user': {'type': 'User'}},
                    {'id': 2, 'body': review.MARKER + ' old', 'user': {'type': 'Bot'}}]
        self.assertEqual(review.find_comment(comments)['id'], 2)
        self.assertIsNone(review.find_comment(comments[:1]))


class PrepareEndToEnd(unittest.TestCase):
    """prepare on a real git repository with a pull request event."""

    def test_writes_inputs_and_skips_docs_only(self):
        with tempfile.TemporaryDirectory() as d:
            repo, work = Path(d) / 'repo', Path(d) / 'work'
            repo.mkdir()
            g = lambda *a: subprocess.run(['git', *a], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
            g('init', '-q')
            g('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'base')
            base = g('rev-parse', 'HEAD')
            (repo / 'a.py').write_text('print(1)\n')
            g('add', '.')
            g('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'change')
            ev = Path(d) / 'event.json'
            ev.write_text(json.dumps(event(base={'sha': base, 'repo': {'full_name': 'o/r'}})))
            out = Path(d) / 'out'
            run = lambda: subprocess.run([sys.executable, '-I', str(ROOT / 'ci' / 'review.py'), 'prepare'], cwd=repo,
                                         capture_output=True, text=True,
                                         env={**os.environ, 'AI_WORK': str(work), 'GITHUB_EVENT_PATH': str(ev),
                                              'GITHUB_OUTPUT': str(out), 'AI_HAS_CREDENTIALS': 'true'})
            p = run()
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn('skip=false', out.read_text())
            self.assertIn('+print(1)', (work / 'pr.diff').read_text())
            self.assertEqual((work / 'changed-files.txt').read_text(), 'a.py\n')
            self.assertTrue((work / 'plugin' / 'skills' / 'algorithmic-intelligence' / 'SKILL.md').is_file())

            ev.write_text(json.dumps(event(base={'sha': base, 'repo': {'full_name': 'o/r'}}, draft=True)))
            out.write_text('')
            self.assertIn('skip=true', (run(), out.read_text())[1])


class Repo:
    """A throwaway git repository with a base commit."""

    def __init__(self, d):
        self.path = Path(d) / 'repo'
        self.path.mkdir()
        self.g('init', '-q')
        self.commit('base', {'README.md': 'Sizes: 2M orders.\n', 'docs/sizes.md': 'n\n', 'a.py': 'x = 1\n'})
        self.base = self.g('rev-parse', 'HEAD')

    def g(self, *a):
        return subprocess.run(['git', *a], cwd=self.path, check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, msg, files):
        for name, text in files.items():
            (self.path / name).parent.mkdir(parents=True, exist_ok=True)
            (self.path / name).write_text(text)
        self.g('add', '.')
        self.g('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', msg)
        return self.g('rev-parse', 'HEAD')


class Fingerprint(unittest.TestCase):
    def test_ignores_docs_and_follows_code_and_instructions(self):
        with tempfile.TemporaryDirectory() as d:
            r = Repo(d)
            r.commit('code', {'a.py': 'x = 1\ny = 2\n'})
            cwd = os.getcwd()
            os.chdir(r.path)
            try:
                fp = lambda: review.code_fingerprint(r.base, ['a.py', 'README.md'], 'sizes')
                first = fp()
                r.commit('docs', {'README.md': 'Sizes: 3M orders.\n'})
                self.assertEqual(fp(), first)
                self.assertNotEqual(review.code_fingerprint(r.base, ['a.py'], 'other sizes'), first)
                r.commit('more code', {'a.py': 'x = 1\ny = 3\n'})
                self.assertNotEqual(fp(), first)
                self.assertFalse(review.leaked_credentials())
                r.g('config', 'http.https://github.com/.extraheader', 'AUTHORIZATION: basic xyz')
                self.assertTrue(review.leaked_credentials())
            finally:
                os.chdir(cwd)


class PostEndToEnd(unittest.TestCase):
    def run_post(self, text, previous=None, existing=None, extra_env=None, inline=None):
        calls = []

        def fake_api(method, url, token, payload=None):
            calls.append((method, url.split('/repos/o/r')[-1], payload))
            if method == 'GET' and '/issues/' in url:
                return existing or []
            return [] if method == 'GET' else {}

        with tempfile.TemporaryDirectory() as d:
            work = Path(d)
            (work / 'result.json').write_text(json.dumps({'ok': True, 'text': text, 'cost': 0.4, 'error': ''}))
            (work / 'context.json').write_text(json.dumps({'fingerprint': 'f1', 'sha': 'h1', 'previous': previous or []}))
            (work / 'inline.json').write_text(json.dumps(inline or {'commit': 'h1', 'lines': {'a.py': [1, 2, 3]}}))
            out = work / 'out'
            environ = {'AI_WORK': str(work), 'AI_NUMBER': '7', 'GITHUB_TOKEN': 't', 'GITHUB_REPOSITORY': 'o/r',
                       'GITHUB_API_URL': 'https://api', 'GITHUB_OUTPUT': str(out), 'GITHUB_STEP_SUMMARY': str(work / 'sum'),
                       **(extra_env or {})}
            with mock.patch.dict(os.environ, environ), mock.patch.object(review, 'api', fake_api):
                self.assertEqual(review.post(), 0)
            outputs = dict(line.split('=', 1) for line in out.read_text().splitlines())
            summary = (work / 'sum').read_text()
        return calls, outputs, summary

    def test_findings_comment_state_inline_and_outputs(self):
        text = 'Report.\n' + block({'findings': [
            {'severity': 'high', 'file': 'a.py', 'line': 2, 'title': 'N+1 query', 'detail': 'd'},
            {'severity': 'low', 'file': 'b.py', 'line': 9, 'title': 'minor', 'detail': 'd'}], 'resolved': []})
        calls, outputs, summary = self.run_post(text)
        posts = [c for c in calls if c[0] == 'POST']
        comment = next(p for m, u, p in posts if u == '/issues/7/comments')['body']
        self.assertIn('Report.', comment)
        self.assertNotIn(review.FINDINGS_TAG, comment)
        state = review.decode_state(comment)
        self.assertEqual((state['fingerprint'], state['ok'], [f['id'] for f in state['findings']]), ('f1', True, ['P1', 'P2']))
        reviews = [p for m, u, p in posts if u == '/pulls/7/reviews']
        self.assertEqual([(c['path'], c['line']) for c in reviews[0]['comments']], [('a.py', 2)])
        self.assertEqual(reviews[0]['commit_id'], 'h1')
        self.assertEqual((outputs['status'], outputs['findings'], outputs['high'], outputs['low'], outputs['clean']),
                         ('reviewed', '2', '1', '1', 'false'))
        self.assertNotIn(review.FINDINGS_TAG, summary)

    def test_clean_is_quiet_unless_asked_and_clears_an_old_comment(self):
        clean = 'Nothing worth reporting.\n' + block({'findings': [], 'resolved': []})
        calls, outputs, _ = self.run_post(clean)
        self.assertEqual([c for c in calls if c[0] in ('POST', 'PATCH')], [])
        self.assertEqual(outputs['clean'], 'true')
        calls, _, _ = self.run_post(clean, extra_env={'INPUT_COMMENT_ON_CLEAN': 'true'})
        self.assertEqual([c[1] for c in calls if c[0] == 'POST'], ['/issues/7/comments'])
        old = [{'id': 5, 'body': review.MARKER + ' old', 'user': {'type': 'Bot'}}]
        prev = [{'id': 'P1', 'title': 'Old join', 'file': 'a.py'}]
        resolved = 'Fixed.\n' + block({'findings': [], 'resolved': ['P1']})
        calls, outputs, _ = self.run_post(resolved, previous=prev, existing=old)
        patch = [p for m, u, p in calls if m == 'PATCH']
        self.assertIn('1 resolved', patch[0]['body'])
        self.assertIn('No performance problems', patch[0]['body'])
        self.assertEqual(outputs['resolved'], '1')

    def test_no_block_still_posts_report(self):
        calls, outputs, _ = self.run_post('A report without the block.')
        self.assertEqual(outputs['findings'], '')
        self.assertEqual(outputs['clean'], 'false')
        self.assertIn('A report without the block.', next(p for m, u, p in calls if m == 'POST')['body'])


if __name__ == '__main__':
    unittest.main()

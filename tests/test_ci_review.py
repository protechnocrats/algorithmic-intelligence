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
        self.assertIn('$0.50', body)
        failed = review.comment_body({'ok': False, 'text': '', 'cost': None, 'error': 'timed out'}, 'u')
        self.assertIn('did not finish (timed out)', failed)

    def test_only_edits_own_bot_comment(self):
        comments = [{'id': 1, 'body': 'quoting ' + review.MARKER, 'user': {'type': 'User'}},
                    {'id': 2, 'body': review.MARKER + ' old', 'user': {'type': 'Bot'}}]
        self.assertEqual(review.find_comment(comments), 2)
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


if __name__ == '__main__':
    unittest.main()

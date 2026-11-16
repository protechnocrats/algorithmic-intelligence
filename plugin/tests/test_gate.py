"""Tests for the edit gate: python3 -m unittest discover -s plugin/tests"""
import datetime
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, '..', 'scripts', 'edit_gate.py')
SERVER = os.path.join(HERE, '..', 'mcp', 'server.py')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


srv = load(SERVER, 'ai_mcp_server_gate')


def git(cwd, *args):
    subprocess.run(['git', '-C', cwd, *args], check=True, capture_output=True)


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        for rel, text in {'src/calc.py': 'def total(xs):\n    return sum(xs)\n', 'src/caller.py': 'from calc import total\n',
                          'tests/test_calc.py': 'def test_total(): pass\n', 'README.md': '# project\n'}.items():
            os.makedirs(os.path.dirname(os.path.join(self.root, rel)) or self.root, exist_ok=True)
            with open(os.path.join(self.root, rel), 'w') as f:
                f.write(text)
        git(self.root, 'init', '-q')
        git(self.root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'add', '-A')
        git(self.root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'init')
        self.transcript = os.path.join(self.root, '..', os.path.basename(self.root) + '-t.jsonl')
        self.write_transcript(used=True, start=time.time() - 60)
        os.environ['ALGORITHMIC_INTELLIGENCE_ROOT'] = self.root

    def tearDown(self):
        os.environ.pop('ALGORITHMIC_INTELLIGENCE_ROOT', None)
        if os.path.exists(self.transcript):
            os.unlink(self.transcript)
        self.tmp.cleanup()

    def write_transcript(self, used, start):
        ts = datetime.datetime.fromtimestamp(start, datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        entries = [{'type': 'user', 'timestamp': ts, 'message': {'content': 'make total faster'}}]
        if used:
            entries.append({'type': 'assistant', 'timestamp': ts, 'message': {'content': [
                {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'algorithmic-intelligence'}}]}})
        with open(self.transcript, 'w') as f:
            f.write(''.join(json.dumps(e) + '\n' for e in entries))

    def decide(self, rel, tool='Edit'):
        event = {'tool_name': tool, 'tool_input': {'file_path': os.path.join(self.root, rel)}, 'cwd': self.root,
                 'transcript_path': self.transcript}
        p = subprocess.run([sys.executable, GATE], input=json.dumps(event), capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)['hookSpecificOutput'] if p.stdout.strip() else None

    def plant_caught(self, file, covers=(), caught=True):
        pid = srv.plant_difference({'file': file, 'find': 'sum(xs)', 'replace': 'sum(xs) + 1', 'covers': list(covers)})['id']
        srv.restore_difference({'id': pid, 'tests_failed': caught})

    def test_refuses_untested_edit_with_the_way_forward(self):
        out = self.decide('src/calc.py')
        self.assertEqual(out['permissionDecision'], 'deny')  # a refusal's reason reaches the agent; an unanswered ask's does not
        for needed in ('plant_difference', 'restore_difference', 'declare_no_differential_test', 'retry', 'no approval needed'):
            self.assertIn(needed, out['permissionDecisionReason'])

    def test_caught_plant_opens_the_file_and_what_it_covers(self):
        self.plant_caught('src/calc.py', covers=['src/caller.py'])
        self.assertIsNone(self.decide('src/calc.py'))
        self.assertIsNone(self.decide('src/caller.py'))

    def test_plant_the_tests_missed_does_not_count(self):
        self.plant_caught('src/calc.py', caught=False)
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')

    def test_declaration_opens_the_file(self):
        srv.declare_no_differential_test({'files': ['src/caller.py'], 'kind': 'new-code',
                                          'reason': 'implements the declared stub; nothing existed before'})
        self.assertIsNone(self.decide('src/caller.py'))
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')

    def test_records_from_an_earlier_session_do_not_count(self):
        self.plant_caught('src/calc.py')
        self.write_transcript(used=True, start=time.time() + 3600)  # this session began after that plant
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')

    def test_not_gated(self):
        self.assertIsNone(self.decide('src/new_module.py', tool='Write'))  # new file
        self.assertIsNone(self.decide('README.md'))                        # documentation
        self.assertIsNone(self.decide('tests/test_calc.py'))               # tests: the guard asks about those
        self.write_transcript(used=False, start=time.time() - 60)
        self.assertIsNone(self.decide('src/calc.py'))                      # the skill was not used

    def test_can_be_turned_off(self):
        event = {'tool_name': 'Edit', 'tool_input': {'file_path': os.path.join(self.root, 'src/calc.py')},
                 'cwd': self.root, 'transcript_path': self.transcript}
        p = subprocess.run([sys.executable, GATE], input=json.dumps(event), capture_output=True, text=True, timeout=20,
                           env={**os.environ, 'ALGORITHMIC_INTELLIGENCE_GATE': 'off'})
        self.assertEqual(p.stdout.strip(), '')

    def test_fails_open_on_bad_input(self):
        p = subprocess.run([sys.executable, GATE], input='not json', capture_output=True, text=True, timeout=20)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, ''))

    def test_declaration_rules(self):
        for bad in ({'files': ['src/calc.py'], 'kind': 'because', 'reason': 'a long enough reason here'},
                    {'files': ['src/calc.py'], 'kind': 'new-code', 'reason': 'short'},
                    {'files': [], 'kind': 'new-code', 'reason': 'a long enough reason here'},
                    {'files': ['../outside.py'], 'kind': 'new-code', 'reason': 'a long enough reason here'}):
            with self.assertRaises(srv.ToolError):
                srv.declare_no_differential_test(bad)
        listed = srv.declare_no_differential_test({'files': ['src/calc.py'], 'kind': 'no-runtime-effect',
                                                   'reason': 'only fixes a comment typo in the docstring'})
        self.assertIn(listed['id'], [d['id'] for d in srv.planted_status({})['declared_no_differential_test']])



COVERAGE = os.path.join(HERE, '..', 'scripts', 'coverage_check.py')


class Coverage(Gate):
    """The end-of-task check catches changes made through the shell, which the edit gate cannot see."""

    def stop(self, active=False):
        event = {'cwd': self.root, 'transcript_path': self.transcript, 'stop_hook_active': active}
        p = subprocess.run([sys.executable, COVERAGE], input=json.dumps(event), capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout) if p.stdout.strip() else None

    def change(self, rel, text='# changed\n'):
        with open(os.path.join(self.root, rel), 'a') as f:
            f.write(text)

    def test_uncovered_shell_edit_is_sent_back_once(self):
        self.change('src/calc.py')
        out = self.stop()
        self.assertEqual(out['decision'], 'block')
        self.assertIn('src/calc.py', out['reason'])
        self.assertIn('Do not undo correct work', out['reason'])
        self.assertIsNone(self.stop(active=True))

    def test_covered_or_declared_files_pass(self):
        self.plant_caught('src/calc.py', covers=['src/caller.py'])
        self.change('src/calc.py'); self.change('src/caller.py')
        self.assertIsNone(self.stop())

    def test_tests_docs_new_files_and_no_skill_are_ignored(self):
        self.change('tests/test_calc.py'); self.change('README.md')
        with open(os.path.join(self.root, 'src', 'new.py'), 'w') as f:
            f.write('x = 1\n')
        self.assertIsNone(self.stop())
        self.change('src/calc.py')
        self.write_transcript(used=False, start=time.time() - 60)
        self.assertIsNone(self.stop())

    def test_nothing_changed(self):
        self.assertIsNone(self.stop())


if __name__ == '__main__':
    unittest.main()

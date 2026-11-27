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

    def shell_run(self, exit_code=1, is_error=None, text=None):
        """Append a shell tool call and its result to the transcript, as Claude Code writes them."""
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        tid = f'toolu_{time.time_ns()}'
        failed = exit_code != 0 if is_error is None else is_error
        entries = [{'type': 'assistant', 'timestamp': ts, 'message': {'content': [
                       {'type': 'tool_use', 'id': tid, 'name': 'Bash', 'input': {'command': 'python3 -m pytest -q'}}]}},
                   {'type': 'user', 'timestamp': ts, 'message': {'content': [
                       {'type': 'tool_result', 'tool_use_id': tid, 'is_error': failed,
                        'content': text if text is not None else (f'Exit code {exit_code}\n1 failed' if failed else '1 passed')}]}}]
        with open(self.transcript, 'a') as f:
            f.write(''.join(json.dumps(e) + '\n' for e in entries))

    def plant_caught(self, file, covers=(), caught=True, run=True, **shell):
        pid = srv.plant_difference({'file': file, 'find': 'sum(xs)', 'replace': 'sum(xs) + 1', 'covers': list(covers)})['id']
        if run:
            self.shell_run(**shell)
        srv.restore_difference({'id': pid, 'tests_failed': caught})
        return pid

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

    def test_caught_needs_a_failing_shell_command_while_planted(self):
        pid = self.plant_caught('src/calc.py', run=False)
        out = self.decide('src/calc.py')
        self.assertEqual(out['permissionDecision'], 'deny')
        self.assertIn(pid, out['permissionDecisionReason'])
        self.assertIn('does not count', out['permissionDecisionReason'])
        self.shell_run(exit_code=1)  # a failure after the restore is not evidence about the plant
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')

    def test_passing_or_unrunnable_commands_are_not_evidence(self):
        self.plant_caught('src/calc.py', exit_code=0)
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')
        self.plant_caught('src/calc.py', exit_code=127)  # command not found
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')
        self.plant_caught('src/calc.py', is_error=True, text='Permission to use Bash was denied')  # refused, never ran
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')
        self.plant_caught('src/calc.py', exit_code=2)
        self.assertIsNone(self.decide('src/calc.py'))

    def test_transcript_in_another_format_takes_the_report_as_given(self):
        with open(self.transcript, 'w') as f:
            f.write(json.dumps({'type': 'user', 'timestamp': '2026-01-01T00:00:00Z',
                                'message': {'content': '/algorithmic-intelligence make total faster'}}) + '\n')
        self.plant_caught('src/calc.py', run=False)
        self.assertIsNone(self.decide('src/calc.py'))

    def test_a_later_session_respects_what_this_one_saw(self):
        self.plant_caught('src/calc.py', run=False)
        self.decide('src/calc.py')  # notes on the record that no failure was seen
        self.later_session()
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')

    def test_declaration_opens_the_file(self):
        srv.declare_no_differential_test({'files': ['src/caller.py'], 'kind': 'new-code',
                                          'reason': 'implements the declared stub; nothing existed before'})
        self.assertIsNone(self.decide('src/caller.py'))
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')

    def later_session(self):
        self.write_transcript(used=True, start=time.time() + 3600)  # this session began after the records

    def test_earlier_plant_counts_while_head_holds_the_tested_version(self):
        self.plant_caught('src/calc.py', covers=['src/caller.py'])
        with open(os.path.join(self.root, 'src/calc.py'), 'a') as f:
            f.write('# half-applied, uncommitted\n')  # resumed work: the tree changed, HEAD did not
        self.later_session()
        self.assertIsNone(self.decide('src/calc.py'))
        self.assertIsNone(self.decide('src/caller.py'))

    def test_earlier_plant_stops_counting_once_the_file_is_committed_anew(self):
        self.plant_caught('src/calc.py')
        with open(os.path.join(self.root, 'src/calc.py'), 'a') as f:
            f.write('# item 1 done\n')
        git(self.root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qam', 'item 1')
        self.later_session()
        self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')

    def test_earlier_records_that_do_not_carry_over(self):
        self.plant_caught('src/calc.py')
        srv.declare_no_differential_test({'files': ['src/caller.py'], 'kind': 'developer-waived',
                                          'reason': 'the developer said to skip it in that conversation'})
        self.later_session()
        self.assertEqual(self.decide('src/caller.py')['permissionDecision'], 'deny')  # approvals never carry over
        os.environ['ALGORITHMIC_INTELLIGENCE_CARRY_DAYS'] = '0'
        try:
            self.assertEqual(self.decide('src/calc.py')['permissionDecision'], 'deny')
        finally:
            os.environ.pop('ALGORITHMIC_INTELLIGENCE_CARRY_DAYS')
        for name in os.listdir(os.path.join(self.root, '.git', 'algorithmic-intelligence', 'plants')):
            if name.endswith('.json'):  # older than the window
                path = os.path.join(self.root, '.git', 'algorithmic-intelligence', 'plants', name)
                with open(path) as f:
                    r = json.load(f)
                r['restored_at'] -= 15 * 24 * 3600
                with open(path, 'w') as f:
                    json.dump(r, f)
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

    def test_resumed_session_is_not_sent_back_for_work_covered_earlier(self):
        self.plant_caught('src/calc.py')
        self.change('src/calc.py')
        self.later_session()
        self.assertIsNone(self.stop())

    def test_unproven_plant_is_named(self):
        pid = self.plant_caught('src/calc.py', run=False)
        self.change('src/calc.py')
        out = self.stop()
        self.assertEqual(out['decision'], 'block')
        self.assertIn(pid, out['reason'])

    def test_nothing_changed(self):
        self.assertIsNone(self.stop())


if __name__ == '__main__':
    unittest.main()

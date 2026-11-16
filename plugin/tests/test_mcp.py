"""Tests for the MCP server: python3 -m unittest discover -s plugin/tests"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, '..', 'mcp', 'server.py')
SKILL_SCRIPTS = os.path.join(HERE, '..', '..', 'skills', 'algorithmic-intelligence', 'scripts')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


srv = load(SERVER, 'ai_mcp_server')


class Protocol(unittest.TestCase):
    """The server speaks MCP over stdio: one JSON-RPC message per line."""

    def session(self, messages, cwd=None):
        text = ''.join(json.dumps(m) + '\n' for m in messages)
        p = subprocess.run([sys.executable, SERVER], input=text, capture_output=True, text=True, timeout=30,
                           cwd=cwd or tempfile.gettempdir())
        self.assertEqual(p.returncode, 0, p.stderr)
        return [json.loads(l) for l in p.stdout.splitlines() if l.strip()]

    def test_handshake_list_and_call(self):
        out = self.session([
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
             'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 't', 'version': '0'}}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
             'params': {'name': 'doubling_fit', 'arguments': {'points': [{'n': 1000, 'time': 1}, {'n': 2000, 'time': 4}]}}},
            {'jsonrpc': '2.0', 'id': 4, 'method': 'ping'},
        ])
        self.assertEqual([m['id'] for m in out], [1, 2, 3, 4])  # the notification gets no reply
        init = out[0]['result']
        self.assertEqual(init['protocolVersion'], '2025-06-18')
        self.assertIn('tools', init['capabilities'])
        self.assertEqual(init['serverInfo']['name'], 'algorithmic-intelligence')
        names = {t['name'] for t in out[1]['result']['tools']}
        self.assertEqual(names, set(srv.TOOLS))
        for t in out[1]['result']['tools']:
            self.assertEqual(t['inputSchema']['type'], 'object')
            self.assertTrue(t['description'])
        call = out[2]['result']
        self.assertFalse(call['isError'])
        self.assertAlmostEqual(call['structuredContent']['pairs'][0]['exponent'], 2.0)
        self.assertEqual(json.loads(call['content'][0]['text']), call['structuredContent'])
        self.assertEqual(out[3]['result'], {})

    def test_unknown_version_gets_newest(self):
        out = self.session([{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '1999-01-01'}}])
        self.assertEqual(out[0]['result']['protocolVersion'], srv.PROTOCOL_VERSIONS[0])

    def test_errors(self):
        p = subprocess.run([sys.executable, SERVER], input='not json\n' + json.dumps(
            {'jsonrpc': '2.0', 'id': 5, 'method': 'nope'}) + '\n' + json.dumps(
            {'jsonrpc': '2.0', 'id': 6, 'method': 'tools/call', 'params': {'name': 'missing'}}) + '\n' + json.dumps(
            {'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call', 'params': {'name': 'doubling_fit', 'arguments': {}}}) + '\n',
            capture_output=True, text=True, timeout=30)
        out = [json.loads(l) for l in p.stdout.splitlines()]
        self.assertEqual(out[0]['error']['code'], -32700)
        self.assertEqual(out[1]['error']['code'], -32601)
        self.assertEqual(out[2]['error']['code'], -32602)
        self.assertTrue(out[3]['result']['isError'])  # bad arguments are a tool error the agent can read


class Benchmark(unittest.TestCase):
    def test_clear_speedup(self):
        base = [100 + (i % 5) for i in range(20)]
        cand = [50 + (i % 5) for i in range(20)]
        aa = [101 + (i % 5) for i in range(20)]
        out = srv.benchmark_compare({'baseline_times': base, 'candidate_times': cand, 'aa_times': aa, 'unit': 'ms'})
        self.assertEqual(out['verdict'], 'faster')
        self.assertLess(out['time_ratio_95ci'][1], 1)
        self.assertGreater(out['speedup'], 1.9)

    def test_within_noise(self):
        base = [100, 120, 90, 110, 105, 95, 115, 100, 98, 112]
        cand = [101, 118, 92, 109, 104, 96, 113, 99, 100, 111]
        out = srv.benchmark_compare({'baseline_times': base, 'candidate_times': cand})
        self.assertEqual(out['verdict'], 'no measurable difference')
        self.assertTrue(any('A/A' in w for w in out['warnings']))

    def test_change_inside_aa_noise_is_not_a_win(self):
        base = [100.0] * 15 + [100.2] * 5
        cand = [97.0] * 20
        aa = [96.0] * 20  # identical code measured 4% faster: the harness is biased
        out = srv.benchmark_compare({'baseline_times': base, 'candidate_times': cand, 'aa_times': aa})
        self.assertEqual(out['verdict'], 'no measurable difference')
        self.assertTrue(any('biased' in w for w in out['warnings']))

    def test_deterministic(self):
        args = {'baseline_times': [3, 4, 5, 4, 3, 5], 'candidate_times': [2, 3, 2, 3, 2, 3]}
        self.assertEqual(srv.benchmark_compare(args), srv.benchmark_compare(args))

    def test_rejects_bad_input(self):
        for bad in ({'baseline_times': [1], 'candidate_times': [1, 2]},
                    {'baseline_times': [1, -2], 'candidate_times': [1, 2]},
                    {'baseline_times': 'fast', 'candidate_times': [1, 2]},
                    {'baseline_times': [True, 2], 'candidate_times': [1, 2]}):
            with self.assertRaises(srv.ToolError):
                srv.benchmark_compare(bad)


class Doubling(unittest.TestCase):
    def test_matches_skill_script(self):
        script = load(os.path.join(SKILL_SCRIPTS, 'doubling.py'), 'skill_doubling')
        for b in [0.2, 0.7, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0]:
            self.assertEqual(srv._doubling_label(b), script.label(b), b)
        pts = [(1000, 0.012), (2000, 0.025), (4000, 0.051), (8000, 0.103)]
        mine = srv.doubling_fit({'points': [{'n': n, 'time': t} for n, t in pts]})['pairs']
        theirs = script.exponents(pts)
        for a, (n1, n2, b) in zip(mine, theirs):
            self.assertAlmostEqual(a['exponent'], b)

    def test_prediction_and_warning(self):
        out = srv.doubling_fit({'points': [{'n': 1000, 'time': 1.0}, {'n': 2000, 'time': 1.1}, {'n': 4000, 'time': 4.4}]})
        self.assertAlmostEqual(out['prediction']['time'], 4.4 * 4)
        self.assertTrue(out['warnings'])


class Summary(unittest.TestCase):
    def test_matches_skill_script(self):
        script = load(os.path.join(SKILL_SCRIPTS, 'check_summary.py'), 'skill_check_summary')
        self.assertEqual(srv.REQUIRED_SUMMARY, script.REQUIRED)
        for text in ['- **Complexity:** O(n)\nData structures: none\nContract changes: none\n'
                     'Bugs noticed: none\nHazards noticed: none\nCommands not run: none',
                     'The complexity is fine.', '## Complexity\nBugs noticed: none']:
            self.assertEqual(srv.check_summary({'text': text})['missing'], script.missing_lines(text))


class Planting(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        os.makedirs(os.path.join(self.root, '.git'))
        os.makedirs(os.path.join(self.root, 'src'))
        self.file = os.path.join(self.root, 'src', 'calc.py')
        self.original = b'def total(xs):\n    return sum(xs)\n'
        with open(self.file, 'wb') as f:
            f.write(self.original)
        os.environ['ALGORITHMIC_INTELLIGENCE_ROOT'] = self.root

    def tearDown(self):
        os.environ.pop('ALGORITHMIC_INTELLIGENCE_ROOT', None)
        self.tmp.cleanup()

    def read(self):
        with open(self.file, 'rb') as f:
            return f.read()

    def test_plant_and_restore_exactly(self):
        out = srv.plant_difference({'file': 'src/calc.py', 'find': 'sum(xs)', 'replace': 'sum(xs) + 1', 'purpose': 'off by one'})
        self.assertIn(b'sum(xs) + 1', self.read())
        self.assertEqual(srv.planted_status({})['still_planted'][0]['id'], out['id'])
        with self.assertRaises(srv.ToolError):  # one planted difference per file
            srv.plant_difference({'file': 'src/calc.py', 'find': 'def', 'replace': 'async def'})
        back = srv.restore_difference({'id': out['id'], 'tests_failed': True, 'evidence': 'test_total failed'})
        self.assertTrue(back['restored_exactly'])
        self.assertEqual(self.read(), self.original)
        status = srv.planted_status({})
        self.assertEqual(status['still_planted'], [])
        self.assertTrue(status['restored'][0]['tests_failed'])
        with self.assertRaises(srv.ToolError):  # restored once only
            srv.restore_difference({'id': out['id'], 'tests_failed': True})
        self.assertTrue(os.path.isdir(os.path.join(self.root, '.git', 'algorithmic-intelligence', 'plants')))

    def test_tests_that_did_not_fail_are_called_out(self):
        out = srv.plant_difference({'file': 'src/calc.py', 'find': 'sum(xs)', 'replace': 'sum(xs) * 2'})
        back = srv.restore_difference({'id': out['id'], 'tests_failed': False})
        self.assertIn('NOT', back['conclusion'])

    def test_refuses_to_discard_later_edits(self):
        out = srv.plant_difference({'file': 'src/calc.py', 'find': 'sum(xs)', 'replace': 'max(xs)'})
        with open(self.file, 'ab') as f:
            f.write(b'# agent edit\n')
        with self.assertRaises(srv.ToolError):
            srv.restore_difference({'id': out['id'], 'tests_failed': True})
        srv.restore_difference({'id': out['id'], 'tests_failed': True, 'force': True})
        self.assertEqual(self.read(), self.original)

    def test_find_must_be_unique(self):
        with self.assertRaises(srv.ToolError):
            srv.plant_difference({'file': 'src/calc.py', 'find': 'xs', 'replace': 'ys'})
        self.assertEqual(self.read(), self.original)

    def test_paths_stay_inside_the_project(self):
        outside = tempfile.NamedTemporaryFile(delete=False)
        outside.write(b'secret = 1\n'); outside.close()
        os.symlink(outside.name, os.path.join(self.root, 'src', 'link.py'))
        with open(os.path.join(self.root, '.git', 'config'), 'w') as f:
            f.write('[core]\n')
        try:
            for path in ['../x.py', outside.name, 'src/link.py', '.git/config', '', 'src']:
                with self.assertRaises(srv.ToolError, msg=path):
                    srv.plant_difference({'file': path, 'find': 'secret', 'replace': 'x'})
            with open(outside.name, 'rb') as f:
                self.assertEqual(f.read(), b'secret = 1\n')
        finally:
            os.unlink(outside.name)

    def test_bad_ids_and_flags(self):
        for bad in ({'id': '../../etc/passwd', 'tests_failed': True}, {'id': 'plant-1-abcdef12', 'tests_failed': 'yes'},
                    {'id': 'plant-1-abcdef12', 'tests_failed': True}):
            with self.assertRaises(srv.ToolError):
                srv.restore_difference(bad)


if __name__ == '__main__':
    unittest.main()

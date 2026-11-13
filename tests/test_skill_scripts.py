"""Tests for the skill's optional scripts and the repository's reference checker:
python3 -m unittest discover -s tests"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'skills', 'algorithmic-intelligence', 'scripts')
CHECK_SUMMARY = os.path.join(SCRIPTS, 'check_summary.py')
DOUBLING = os.path.join(SCRIPTS, 'doubling.py')
CHECK_REFS = os.path.join(ROOT, 'tools', 'check_refs.py')

COMPLETE = ('Complexity: O(n·m) → O(n + m)\n- **Data structures:** `users` (list): lookup, O(m); best: dict; switching\n'
            'Contract changes: none\nBugs noticed: none\n### Hazards noticed\nnone\nCommands not run: none\n')


def run(script, *args, stdin=''):
    return subprocess.run([sys.executable, '-I', script, *args], input=stdin, capture_output=True, text=True, timeout=60)


class CheckSummary(unittest.TestCase):
    def test_complete_summary_from_stdin_and_file(self):
        self.assertEqual(run(CHECK_SUMMARY, stdin=COMPLETE).returncode, 0)
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as f:
            f.write(COMPLETE)
        self.addCleanup(os.unlink, f.name)
        out = run(CHECK_SUMMARY, f.name)
        self.assertEqual((out.returncode, out.stdout.strip()), (0, 'complete: all required lines present'))

    def test_missing_and_in_sentence_mentions(self):
        out = run(CHECK_SUMMARY, stdin='Reduced complexity; no bugs noticed, no hazards noticed, no commands not run.')
        self.assertEqual(out.returncode, 1)
        for label in ('Complexity', 'Data structures', 'Contract changes', 'Bugs noticed', 'Hazards noticed', 'Commands not run'):
            self.assertIn(f'"{label}"', out.stdout)
        out = run(CHECK_SUMMARY, stdin=COMPLETE.replace('Bugs noticed: none\n', ''))
        self.assertEqual((out.returncode, out.stdout.splitlines()[0]), (1, 'missing: "Bugs noticed"'))

    def test_no_exemption_line(self):
        # Every final summary needs the lines; no opening or closing line exempts a message from them.
        out = run(CHECK_SUMMARY, stdin='algorithmic-intelligence: small, cold change (a rename).\n\nDone.')
        self.assertEqual(out.returncode, 1)

    def test_usage(self):
        self.assertEqual(run(CHECK_SUMMARY, '--help').returncode, 0)
        self.assertEqual(run(CHECK_SUMMARY, 'a', 'b').returncode, 2)
        self.assertEqual(run(CHECK_SUMMARY, '/nonexistent/summary.md').returncode, 2)


class Doubling(unittest.TestCase):
    def test_linear_and_quadratic(self):
        out = run(DOUBLING, '1000:0.010', '2000:0.021', '4000:0.040', '8000:0.081')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('near 1: linear', out.stdout)
        self.assertIn('prediction at N = 16000', out.stdout)
        out = run(DOUBLING, '1000:0.01', '2000:0.04', '4000:0.16')
        self.assertIn('near 2: quadratic', out.stdout)
        self.assertNotIn('note:', out.stdout)

    def test_overhead_note_and_unsorted_input(self):
        out = run(DOUBLING, '4000:0.40', '1000:0.11', '2000:0.12')  # order does not matter
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('note: the exponent changes', out.stdout)

    def test_errors(self):
        self.assertEqual(run(DOUBLING).returncode, 2)
        self.assertEqual(run(DOUBLING, '--help').returncode, 0)
        self.assertEqual(run(DOUBLING, '1000:0.1').returncode, 2)
        self.assertEqual(run(DOUBLING, '1000:0.1', 'x').returncode, 2)
        self.assertEqual(run(DOUBLING, '1000:0.1', '1000:0.2').returncode, 2)
        self.assertEqual(run(DOUBLING, '1000:0', '2000:0.2').returncode, 2)


class CheckRefs(unittest.TestCase):
    def test_repository_is_clean(self):
        out = run(CHECK_REFS, ROOT)
        self.assertEqual(out.returncode, 0, out.stdout)

    def write(self, root, rel, text):
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(text)

    def test_catches_planted_breaks(self):
        with tempfile.TemporaryDirectory() as root:
            skill = 'skills/algorithmic-intelligence/'
            self.write(root, skill + 'SKILL.md', '---\nname: algorithmic-intelligence\ndescription: Does things <fast>.\n'
                       'extra: 1\ncompatibility: ' + 'x' * 501 + '\n---\n# Skill\n\n'
                       'See [the workflow](WORKFLOW.md) and `MISSING.md`, "Rule details" in `WORKFLOW.md`, '
                       '"No such section" in `WORKFLOW.md`, rule 15, phase 7, move 21, and `OPTIMIZATION-REPORT.md`.\n'
                       '```\nnothing in code blocks counts: `NOPE.md` rule 99\n```\n')
            self.write(root, skill + 'WORKFLOW.md', '# Workflow\n\n## Rule details\n\n**Scope.** text\n')
            out = run(CHECK_REFS, root)
            self.assertEqual(out.returncode, 1)
            for expected in ('missing file `MISSING.md`', 'no section or label "No such section"', 'rule 15 does not exist',
                             'phase 7 does not exist', 'move 21 does not exist', 'contains < or >',
                             '`compatibility` must be 1 to 500', 'key `extra` is not one'):
                self.assertIn(expected, out.stdout)
            for unexpected in ('NOPE.md', 'rule 99', 'OPTIMIZATION-REPORT.md', 'broken link WORKFLOW.md', '"Rule details"'):
                self.assertNotIn(unexpected, out.stdout)

    def test_frontmatter_yaml_hazards(self):
        with tempfile.TemporaryDirectory() as root:
            skill = 'skills/algorithmic-intelligence/'
            self.write(root, skill + 'SKILL.md', '---\nname: Algorithmic_Intelligence\ndescription: Use it for: speed #fast\n'
                       'metadata:\n  version: 0.5.1\n---\n# Skill\n')
            out = run(CHECK_REFS, root)
            self.assertEqual(out.returncode, 1)
            self.assertIn('`name` must be lowercase', out.stdout)
            self.assertIn('holds ": " or " #"', out.stdout)
            self.assertNotIn('`metadata`', out.stdout)


if __name__ == '__main__':
    unittest.main()

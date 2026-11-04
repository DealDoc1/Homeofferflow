"""Execute the real workflow check against clean, committed Git fixtures."""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github/workflows/test.yml').read_text()
STEP = WORKFLOW.split('      - name: Check committed patch whitespace\n', 1)[1].split('\n      - name:', 1)[0]
SCRIPT = textwrap.dedent(STEP.split('        run: |\n', 1)[1])


class CICommittedWhitespaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.env = {**os.environ, 'GIT_AUTHOR_NAME': 'QA', 'GIT_COMMITTER_NAME': 'QA',
                    'GIT_AUTHOR_EMAIL': 'qa@example.test', 'GIT_COMMITTER_EMAIL': 'qa@example.test'}
        self.git('init', '-q')
        (self.path / 'base.txt').write_text('Base\n')
        self.git('add', 'base.txt'); self.git('commit', '-qm', 'Base')
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()

    def git(self, *args, check=True):
        return subprocess.run(['git', *args], cwd=self.path, env=self.env,
                              capture_output=True, text=True, check=check)

    def commit_file(self, text):
        (self.path / 'new.py').write_text(text)
        self.git('add', 'new.py'); self.git('commit', '-qm', 'Change')
        self.assertEqual(self.git('status', '--porcelain').stdout, '')
        return self.git('rev-parse', 'HEAD').stdout.strip()

    def run_check(self, base, head):
        return subprocess.run(['bash', '-e', '-c', SCRIPT], cwd=self.path,
            env={**self.env, 'BASE_SHA': base, 'HEAD_SHA': head}, capture_output=True, text=True)

    def test_committed_new_file_eof_error_fails_on_clean_checkout(self):
        head = self.commit_file('value = 1\n\n')
        self.assertEqual(self.git('diff', '--check').returncode, 0)
        result = self.run_check(self.base, head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('new blank line at EOF', result.stdout)

    def test_clean_committed_range_passes(self):
        head = self.commit_file('value = 1\n')
        self.assertEqual(self.run_check(self.base, head).returncode, 0)

    def test_bad_earlier_commit_is_not_hidden_by_clean_head_commit(self):
        self.commit_file('value = 1 \n')
        (self.path / 'later.txt').write_text('Later\n')
        self.git('add', 'later.txt'); self.git('commit', '-qm', 'Later')
        head = self.git('rev-parse', 'HEAD').stdout.strip()
        self.assertNotEqual(self.run_check(self.base, head).returncode, 0)

    def test_missing_invalid_or_unavailable_commit_fails_closed(self):
        for base in ('', 'main', '0' * 40, '--quiet'):
            with self.subTest(base=base):
                self.assertNotEqual(self.run_check(base, self.base).returncode, 0)

    def test_workflow_checks_pr_and_push_commits_with_history_available(self):
        self.assertIn('fetch-depth: 0', WORKFLOW)
        self.assertLess(WORKFLOW.index('Check committed patch whitespace'),
                        WORKFLOW.index('Set up Python'))
        self.assertIn('github.event.pull_request.base.sha || github.event.before', STEP)
        self.assertIn('github.event.pull_request.head.sha || github.sha', STEP)


if __name__ == '__main__':
    unittest.main()

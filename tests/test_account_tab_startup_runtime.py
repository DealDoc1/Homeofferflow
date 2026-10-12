from pathlib import Path
import subprocess
import unittest


class AccountTabStartupRuntimeTests(unittest.TestCase):
    def test_delayed_workspace_navigation_matrix(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('account_tab_startup.runtime.cjs'))],
                                capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

from pathlib import Path
import subprocess
import unittest


class BrokerageSaveIsolationTests(unittest.TestCase):
    def test_actual_source_delayed_save_matrix(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('brokerage_save_isolation.runtime.cjs'))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

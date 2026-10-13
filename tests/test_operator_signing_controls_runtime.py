from pathlib import Path
import subprocess
import unittest


class OperatorSigningControlsRuntimeTests(unittest.TestCase):
    def test_runtime(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('operator_signing_controls.runtime.cjs'))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

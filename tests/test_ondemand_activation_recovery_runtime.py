from pathlib import Path
import subprocess
import unittest


class OnDemandActivationRecoveryRuntimeTests(unittest.TestCase):
    def test_actual_enrollment_script(self):
        result = subprocess.run(
            ['node', '--test', str(Path(__file__).with_name('ondemand_activation_recovery.runtime.cjs'))],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

from pathlib import Path
import subprocess
import unittest


class AssumptionInterviewRuntimeTests(unittest.TestCase):
    def test_interview_logic(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('assumption_interview.runtime.cjs'))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

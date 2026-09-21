"""Run actual interview helpers in an isolated JS runtime; no production writes."""
from pathlib import Path
import subprocess
import unittest


class HydrostaticInterviewRuntimeTests(unittest.TestCase):
    def test_interview_logic(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('hydrostatic_interview.runtime.cjs'))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

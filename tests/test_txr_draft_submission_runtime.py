from pathlib import Path
import subprocess
import unittest


class TxrDraftSubmissionRuntimeTests(unittest.TestCase):
    def test_draft_submission_runtime(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ['node', '--test', 'tests/txr_draft_submission.runtime.cjs'],
            cwd=root, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

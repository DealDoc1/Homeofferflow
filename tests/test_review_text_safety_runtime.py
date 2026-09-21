"""Offer review and attachment names must remain text, not page markup."""
from pathlib import Path
import shutil
import subprocess
import unittest


class ReviewTextSafetyTests(unittest.TestCase):
    def test_actual_review_functions_escape_user_supplied_text(self):
        node = shutil.which('node')
        self.assertIsNotNone(node)
        result = subprocess.run(
            [node, '--test', 'tests/review_text_safety.runtime.cjs'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True,
            text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

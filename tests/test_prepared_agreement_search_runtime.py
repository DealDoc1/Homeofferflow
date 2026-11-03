"""Run saved-document search against the shipped renderer and event handlers."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PreparedAgreementSearchRuntimeTests(unittest.TestCase):
    def test_search_preserves_signed_actions_refresh_and_account_boundaries(self):
        result = subprocess.run(
            ['node', 'tests/prepared_agreement_search.runtime.cjs'], cwd=ROOT,
            capture_output=True, text=True, timeout=25,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

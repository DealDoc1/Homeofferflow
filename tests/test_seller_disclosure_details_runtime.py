from pathlib import Path
import subprocess
import unittest


class SellerDisclosureDetailsRuntimeTests(unittest.TestCase):
    def test_real_interview_controls_reopen_and_collect_explanations(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(["node", "--test", str(root / "tests/seller_disclosure_details.runtime.cjs")],
                                cwd=root, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

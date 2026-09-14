"""Execute the buyer financing Continue handler in an isolated browser-like VM."""

from pathlib import Path
import shutil
import subprocess
import unittest


class BuyerStepThreeContinueRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for buyer-path runtime tests")
    def test_financing_continue_advances_even_when_suggestions_fail(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("buyer_step3_continue.runtime.cjs"))],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

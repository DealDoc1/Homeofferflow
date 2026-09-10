"""Run actual customer-audience/account-restoration code in an isolated JS VM."""

from pathlib import Path
import shutil
import subprocess
import unittest


class CustomerAudienceRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for customer-path runtime tests")
    def test_selected_path_survives_account_and_profile_restoration(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("customer_audience.runtime.cjs"))],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

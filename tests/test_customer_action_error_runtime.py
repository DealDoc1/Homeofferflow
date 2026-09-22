import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CustomerActionErrorRuntimeTests(unittest.TestCase):
    def test_customer_error_filter_in_node(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("customer_action_error.runtime.cjs"))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import subprocess
import unittest


class CheckoutBrowserStorageTests(unittest.TestCase):
    def test_actual_checkout_runtime(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('checkout_browser_storage.runtime.cjs'))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

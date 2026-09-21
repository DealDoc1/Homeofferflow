from pathlib import Path
import subprocess
import unittest


class GoogleAddressComponentsRuntimeTests(unittest.TestCase):
    def test_runtime_components(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', '--test', 'tests/google_address_components.runtime.cjs'],
                                cwd=root, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

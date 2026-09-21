from pathlib import Path
import subprocess
import unittest


class GoogleAddressRaceRuntimeTests(unittest.TestCase):
    def test_runtime_address_races(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', '--test', 'tests/google_address_races.runtime.cjs'],
                                cwd=root, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

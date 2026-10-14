from pathlib import Path
import subprocess
import unittest


class ListingDisclosureHandoffRuntimeTests(unittest.TestCase):
    def test_actual_listing_and_disclosure_handoff(self):
        result = subprocess.run(
            ['node', '--test', str(Path(__file__).with_name('listing_disclosure_handoff.runtime.cjs'))],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

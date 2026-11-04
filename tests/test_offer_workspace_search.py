from pathlib import Path
import subprocess
import unittest


class OfferWorkspaceSearchTests(unittest.TestCase):
    def test_search_preserves_input_while_updating_results(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ['node', 'tests/offer_workspace_search.runtime.cjs'],
            cwd=root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

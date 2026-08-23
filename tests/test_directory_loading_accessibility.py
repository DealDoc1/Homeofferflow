from pathlib import Path
import unittest


DIRECTORY = (Path(__file__).resolve().parents[1] / "directory.html").read_text(encoding="utf-8")


class DirectoryLoadingAccessibilityTests(unittest.TestCase):
    def test_provider_results_announce_loading_state(self):
        self.assertIn('<section id="results" class="grid" aria-live="polite"></section>', DIRECTORY)
        self.assertIn("$('results').setAttribute('aria-busy', 'true');", DIRECTORY)
        self.assertIn("$('results').setAttribute('aria-busy', 'false');", DIRECTORY)


if __name__ == "__main__":
    unittest.main()

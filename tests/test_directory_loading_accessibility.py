from pathlib import Path
import unittest


DIRECTORY = (Path(__file__).resolve().parents[1] / "directory.html").read_text(encoding="utf-8")


class DirectoryLoadingAccessibilityTests(unittest.TestCase):
    def test_provider_results_announce_loading_state(self):
        self.assertIn('<section id="results" class="grid" aria-live="polite"></section>', DIRECTORY)
        self.assertIn("$('results').setAttribute('aria-busy', 'true');", DIRECTORY)
        self.assertIn("$('results').setAttribute('aria-busy', 'false');", DIRECTORY)

    def test_directory_search_destination_is_described_for_discovery(self):
        self.assertIn('"@type":"SearchAction"', DIRECTORY)
        self.assertIn('directory?category={category}&amp;market={market}', DIRECTORY)
        self.assertIn('required name=category', DIRECTORY)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class ProfileLoadFailureStateTests(unittest.TestCase):
    def test_authoritative_profile_failure_is_visible_and_retryable(self):
        self.assertIn("profileLoadError", HTML)
        self.assertIn("Account workspace temporarily unavailable.", HTML)
        self.assertIn("Your saved offer data was not changed.", HTML)
        self.assertIn("Retry account connection", HTML)
        self.assertIn("window.location.reload()", HTML)


if __name__ == "__main__":
    unittest.main()

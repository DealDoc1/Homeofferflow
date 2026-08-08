from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferWorkspaceRetryTests(unittest.TestCase):
    def test_offer_loader_keeps_a_recovery_action_on_transient_failure(self):
        start = HTML.index("async function loadMyOffers()")
        end = HTML.index("function formatOfferDate", start)
        loader = HTML[start:end]
        self.assertIn("Could not load offers yet.", loader)
        self.assertIn('onclick="loadMyOffers()"', loader)
        self.assertIn("Retry offers", loader)


if __name__ == "__main__":
    unittest.main()

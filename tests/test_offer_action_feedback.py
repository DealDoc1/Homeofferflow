from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferActionFeedbackTests(unittest.TestCase):
    def test_repeat_offer_errors_use_workspace_status(self):
        for message in (
            "We couldn’t reopen that offer. Refresh your workspace and try again.",
            "We couldn’t copy that offer. Please try again.",
            "We couldn’t start a new offer from those terms. Please try again.",
            "We couldn’t remove that offer. Please try again.",
        ):
            self.assertIn(message, INDEX)
        self.assertGreaterEqual(INDEX.count("window.hofCustomerActionError(err,"), 4)
        self.assertNotIn("Could not resume offer: ' + err.message", INDEX)
        self.assertNotIn("Could not duplicate offer: ' + err.message", INDEX)

    def test_missing_offer_uses_workspace_status(self):
        self.assertIn("This offer is no longer available in your workspace.", INDEX)
        self.assertNotIn("return alert('Offer not found.')", INDEX)
        self.assertIn("No saved offers to reuse yet. Create an offer first", INDEX)
        self.assertNotIn("alert('No saved offers to reuse yet.')", INDEX)


if __name__ == "__main__":
    unittest.main()

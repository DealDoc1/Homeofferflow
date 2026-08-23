from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferActionFeedbackTests(unittest.TestCase):
    def test_repeat_offer_errors_use_workspace_status(self):
        for message in (
            "Could not resume offer: ",
            "Could not duplicate offer: ",
            "Could not start from these terms: ",
            "Could not delete offer: ",
        ):
            self.assertIn("window.announceWorkspaceStatus?.('" + message, INDEX)
            self.assertNotIn("alert('" + message, INDEX)

    def test_missing_offer_uses_workspace_status(self):
        self.assertIn("This offer is no longer available in your workspace.", INDEX)
        self.assertNotIn("return alert('Offer not found.')", INDEX)


if __name__ == "__main__":
    unittest.main()

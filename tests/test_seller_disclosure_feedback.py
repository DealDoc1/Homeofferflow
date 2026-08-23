from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class SellerDisclosureFeedbackTests(unittest.TestCase):
    def _script(self):
        start = INDEX.index('<script id="hof-seller-disclosure-draft-ui-v1">')
        end = INDEX.index('</script>', start)
        return INDEX[start:end]

    def test_preview_and_actions_use_accessible_status_feedback(self):
        script = self._script()
        self.assertIn('id="hofSellerDraftStatus"', script)
        self.assertIn("document.getElementById('hofSellerDraftStatus')", script)
        self.assertIn("Sign in before saving a seller disclosure draft.", script)
        self.assertIn("Sign in before sending a seller review request.", script)
        self.assertNotIn("alert(error.message || 'Private seller preview is unavailable.')", script)
        self.assertNotIn("return alert('Sign in before saving a seller disclosure draft.')", script)
        self.assertNotIn("return alert('Sign in before sending a seller review request.')", script)

    def test_source_and_review_rules_remain_intact(self):
        script = self._script()
        self.assertIn("choose the released TREC-55-1 source.", script)
        self.assertIn("Enter Seller 2 review email or remove Seller 2 name.", script)
        self.assertIn("Enter Seller 2 name before adding a second review email.", script)
        self.assertIn("create_seller_disclosure_review_link", script)


if __name__ == "__main__":
    unittest.main()

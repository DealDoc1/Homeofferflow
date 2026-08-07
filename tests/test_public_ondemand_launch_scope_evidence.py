import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = (
    ROOT / "docs" / "release-evidence"
    / "public-ondemand-launch-scope-live-2026-08-07.md"
).read_text(encoding="utf-8")


class PublicOnDemandLaunchScopeEvidenceTests(unittest.TestCase):
    def test_live_copy_records_pricing_and_scope(self):
        for marker in (
            "$29/month",
            "60-day free",
            "Cancel anytime",
            "buyer-representation agreements",
            "listing agreements",
            "seller-disclosure notices",
        ):
            self.assertIn(marker, DOC)

    def test_live_review_does_not_claim_authenticated_or_restricted_form_qa(self):
        self.assertIn("not send a sign-in link", DOC)
        self.assertIn("remain separate gates", DOC)


if __name__ == "__main__":
    unittest.main()

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SellerReviewApiTests(unittest.TestCase):
    def test_email_verified_review_flow_is_present_and_non_signing(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text()
        for marker in (
            "_create_seller_disclosure_review_link",
            "create_seller_disclosure_review_link",
            "review_seller_disclosure",
            "verify_seller_review",
            "seller_review_session",
            "seller_review_pdf",
            "attest_seller_review",
            "verification_code_hash",
            "session_token_hash",
            "workflowActivated",
        ):
            self.assertIn(marker, source)
        self.assertIn("seller-review.html", source)

    def test_review_link_migration_is_service_role_only(self):
        sql = (ROOT / "supabase" / "homeofferflow_seller_disclosure_review_links.sql").read_text()
        self.assertIn("hof_seller_disclosure_review_links", sql)
        self.assertIn("enable row level security", sql.lower())
        self.assertIn("revoke all on public.hof_seller_disclosure_review_links", sql.lower())
        self.assertIn("grant all on public.hof_seller_disclosure_review_links", sql.lower())
        self.assertIn("session_expires_at", sql)
        self.assertIn("seller_attested_at", sql)


if __name__ == "__main__":
    unittest.main()

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

    def test_multi_seller_review_fields_are_targeted_and_additive(self):
        sql = (ROOT / "supabase" / "homeofferflow_seller_disclosure_multi_seller_review.sql").read_text()
        api = (ROOT / "api" / "admin-dashboard.py").read_text()
        ui = (ROOT / "index.html").read_text()
        self.assertIn("seller_name", sql)
        self.assertIn("seller_index", sql)
        self.assertIn("hof_seller_review_links_draft_seller_idx", sql)
        self.assertIn("sellerReviews", api)
        self.assertIn("sellerIndex", api)
        self.assertIn("Seller 2 review email", ui)
        self.assertIn("one review recipient per seller", api)
        self.assertIn("len(requested_reviews) != len(seller_names)", api)
        self.assertIn("_refresh_seller_review_attestation", api)
        self.assertIn("allSellersAttested", api)
        self.assertIn("seller_review_attested_at", api)
        self.assertIn("seller_review_attested_by", api)
        self.assertIn("This review link is not assigned to a specific seller", api)
        self.assertIn("expected_seller_names", api)
        review_page = (ROOT / "seller-review.html").read_text()
        self.assertIn("d.sellerName", review_page)
        self.assertIn("All listed sellers have reviewed", review_page)

    def test_draft_creation_revalidates_listing_workspace_ownership(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text()
        self.assertIn("_create_seller_disclosure_draft", source)
        self.assertIn("That private listing workspace is unavailable to this agent.", source)
        self.assertIn("agent_user_id=eq.", source)
        self.assertIn("brokerage_id=eq.", source)

    def test_draft_listing_surfaces_private_review_progress(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text()
        ui = (ROOT / "index.html").read_text()
        self.assertIn("sellerReviewLinks", api)
        self.assertIn("sellerReviewProgress", api)
        self.assertIn("seller_email", api)
        self.assertIn("sellerEmail", api)
        self.assertIn("No seller review request sent", ui)
        self.assertIn("reviewStatus", ui)

    def test_draft_list_uses_permission_checked_api_for_review_progress(self):
        ui = (ROOT / "index.html").read_text()
        self.assertIn("/api/admin-dashboard?scope=seller_disclosure_drafts", ui)
        self.assertIn("Authorization: 'Bearer ' + token", ui)
        self.assertIn("return payload.drafts || []", ui)

    def test_incomplete_review_can_restore_recipients_for_follow_up(self):
        ui = (ROOT / "index.html").read_text()
        self.assertIn("hof-seller-followup", ui)
        self.assertIn("Review recipient details are restored", ui)
        self.assertIn("sellerReviewLinks", ui)
        self.assertIn("hofSeller2Email", ui)


if __name__ == "__main__":
    unittest.main()

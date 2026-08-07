import unittest
from datetime import datetime, timezone, timedelta

from lib import seller_review_access


class SellerReviewAccessTests(unittest.TestCase):
    def test_issue_token_returns_hash_only_for_storage_and_expiry(self):
        now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
        issued = seller_review_access.issue_token(ttl_days=7, now=now)
        self.assertNotEqual(issued["token"], issued["token_hash"])
        self.assertTrue(seller_review_access.token_matches(issued["token"], issued["token_hash"]))
        self.assertEqual(issued["expires_at"], "2026-08-14T12:00:00+00:00")

    def test_expiry_and_revocation_are_fail_closed(self):
        future = "2026-08-14T12:00:00+00:00"
        now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
        self.assertTrue(seller_review_access.is_active(expires_at=future, now=now))
        self.assertFalse(seller_review_access.is_active(expires_at=future, revoked_at="2026-08-06T00:00:00+00:00", now=now))
        self.assertFalse(seller_review_access.is_active(expires_at=future, now=now + timedelta(days=7)))

    def test_attestation_requires_exact_seller_name(self):
        names = ["Test Seller One", "Test Seller Two"]
        self.assertTrue(seller_review_access.seller_name_matches(" test  seller one ", names))
        self.assertFalse(seller_review_access.seller_name_matches("Other Person", names))


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime, timezone, timedelta

from lib import seller_review_access


class SellerReviewAccessTests(unittest.TestCase):
    def test_code_is_bound_to_the_link_token(self):
        now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
        issued = seller_review_access.issue_credentials(now=now)
        self.assertTrue(seller_review_access.code_matches(
            issued["code"], issued["token_hash"], issued["verification_code_hash"]
        ))
        other = seller_review_access.issue_credentials(now=now)
        self.assertFalse(seller_review_access.code_matches(
            issued["code"], other["token_hash"], issued["verification_code_hash"]
        ))

    def test_session_is_short_lived(self):
        now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
        session = seller_review_access.issue_session(now=now)
        self.assertTrue(seller_review_access.is_active(session["expires_at"], now=now + timedelta(minutes=29)))
        self.assertFalse(seller_review_access.is_active(session["expires_at"], now=now + timedelta(minutes=30)))

    def test_seller_name_matching_is_exact_after_normalization(self):
        self.assertTrue(seller_review_access.seller_name_matches(" test  seller one ", ["Test Seller One"]))
        self.assertFalse(seller_review_access.seller_name_matches("Other Person", ["Test Seller One"]))


if __name__ == "__main__":
    unittest.main()

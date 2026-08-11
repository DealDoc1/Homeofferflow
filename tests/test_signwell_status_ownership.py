from pathlib import Path
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "api" / "signwell-status.js").read_text(encoding="utf-8")


class SignWellStatusOwnershipTests(unittest.TestCase):
    def test_status_refresh_reads_only_the_verified_users_minimal_offer_record(self):
        start = SOURCE.index("async function getOfferForUser")
        end = SOURCE.index("async function getSignWellDocument", start)
        lookup = SOURCE[start:end]

        self.assertIn("`user_id=eq.${encodeURIComponent(user.id)}`", lookup)
        self.assertIn("select=id,user_id,signwell_document_id,offer_data", lookup)
        self.assertNotIn("select=*", lookup)
        self.assertNotIn("user.isAdmin", lookup)

    def test_status_refresh_write_keeps_the_verified_owner_constraint(self):
        start = SOURCE.index("async function updateOfferStatus")
        end = SOURCE.index("module.exports", start)
        update = SOURCE[start:end]

        self.assertIn("&user_id=eq.${encodeURIComponent(user.id)}", update)


if __name__ == "__main__":
    unittest.main()

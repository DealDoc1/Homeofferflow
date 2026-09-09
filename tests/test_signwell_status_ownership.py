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

    def test_standalone_refresh_is_scoped_to_the_preparing_agent(self):
        start = SOURCE.index("async function getStandaloneAgreementForUser")
        end = SOURCE.index("async function getSignWellDocument", start)
        lookup = SOURCE[start:end]
        self.assertIn("agent_user_id=eq.${encodeURIComponent(user.id)}", lookup)
        self.assertIn("select=id,agent_user_id,signwell_document_id,agreement_data", lookup)
        self.assertNotIn("select=*", lookup)

    def test_standalone_refresh_writes_only_the_verified_owner_record(self):
        start = SOURCE.index("async function updateStandaloneAgreementStatus")
        end = SOURCE.index("module.exports", start)
        update = SOURCE[start:end]
        self.assertIn("&agent_user_id=eq.${encodeURIComponent(user.id)}", update)
        self.assertIn("function safeStandaloneStatus", SOURCE)

    def test_completed_pdf_download_requires_an_owner_scoped_completed_packet(self):
        self.assertIn("async function getCompletedSignWellPdf", SOURCE)
        self.assertIn("/completed_pdf?audit_page=true&file_format=pdf", SOURCE)
        self.assertIn("body.action === 'download_completed_pdf'", SOURCE)
        self.assertIn("cleanStatusLabel(status) !== 'Buyer Signatures Complete'", SOURCE)
        self.assertIn("Cache-Control', 'private, no-store'", SOURCE)


if __name__ == "__main__":
    unittest.main()

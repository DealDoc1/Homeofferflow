import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "api" / "admin-dashboard.py"
WEBHOOK = ROOT / "api" / "signwell-webhook.py"
MIGRATION = ROOT / "supabase" / "migrations" / "20260814133553_partner_agreement_signing.sql"


class PartnerAgreementSigningTests(unittest.TestCase):
    def test_migration_tracks_a_separate_partner_agreement(self):
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("partner_agreement_status", source)
        self.assertIn("partner_agreement_signwell_document_id", source)
        self.assertIn("partner_agreement_signed_at", source)
        self.assertIn("hof_partner_leads_partner_agreement_document_id_key", source)

    def test_admin_sender_requires_paid_completed_onboarding_and_copies_support(self):
        source = ADMIN.read_text(encoding="utf-8")
        self.assertIn("async def _send_partner_agreement_for_signature", source)
        self.assertIn("PARTNER_AGREEMENT_SIGNING_ENABLED", source)
        self.assertIn("Complete Texas counsel review", source)
        self.assertIn("Complete secure partner onboarding before sending the commercial agreement.", source)
        self.assertIn('"copied_contacts": [{"name": "HomeOfferFlow Support", "email": PARTNER_AGREEMENT_COPY_EMAIL}]', source)
        self.assertIn('"with_signature_page": True', source)
        self.assertIn('"partner_agreement_status": "sent"', source)

    def test_public_placement_requires_verified_signed_partner_agreement(self):
        source = ADMIN.read_text(encoding="utf-8")
        self.assertIn('lead.get("partner_agreement_status")', source)
        self.assertIn("A completed HomeOfferFlow Partner Marketplace Agreement is required", source)

    def test_signwell_webhook_confirms_provider_completion_before_unlocking(self):
        source = WEBHOOK.read_text(encoding="utf-8")
        self.assertIn("async def _partner_agreement_completed_in_signwell", source)
        self.assertIn("https://www.signwell.com/api/v1/documents/{document_id}", source)
        self.assertIn('"partner_agreement_status": status', source)
        self.assertIn("_update_partner_agreement(document_id, event_type)", source)

    def test_agreement_renderer_makes_a_pdf_without_external_services(self):
        spec = importlib.util.spec_from_file_location("partner_agreement_admin", ADMIN)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pdf = module._partner_agreement_pdf({
            "company_name": "Example Partner LLC",
            "contact_name": "Alex Example",
            "partner_type": "inspection",
            "market_area": "Dallas County, Texas",
            "preferred_model": "monthly_placement",
        })
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 2000)


if __name__ == "__main__":
    unittest.main()

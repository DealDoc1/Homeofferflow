import importlib.util
import os
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
SPEC = importlib.util.spec_from_file_location("fsbo_auto_agreement", ROOT / "api" / "fsbo-lead.py")
fsbo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fsbo)


class PartnerAgreementAutoDispatchTests(unittest.TestCase):
    def setUp(self):
        self.lead = {
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "company_name": "North Texas Title",
            "contact_name": "Alex Example",
            "contact_email": "alex@example.com",
            "partner_type": "title",
            "market_area": "DFW",
            "preferred_model": "monthly_placement",
            "payment_status": "paid",
            "partner_agreement_status": "not_started",
        }

    def test_dispatch_sends_the_approved_pdf_once_and_copies_support(self):
        calls = []

        class Response:
            status_code = 201
            text = "[{}]"
            def json(self): return {"id": "sw_document_123"}

        class Saved:
            status_code = 200
            text = "[{}]"
            def json(self): return [{}]

        class Client:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def post(self, url, **kwargs):
                calls.append(("post", url, kwargs))
                return Response()
            def patch(self, url, **kwargs):
                calls.append(("patch", url, kwargs))
                return Saved()

        with patch.object(fsbo, "PARTNER_AGREEMENT_SIGNING_ENABLED", True), \
             patch.object(fsbo, "SIGNWELL_ENABLED", True), \
             patch.object(fsbo, "SIGNWELL_API_KEY", "test-key"), \
             patch.object(fsbo.httpx, "Client", return_value=Client()):
            result = fsbo._dispatch_partner_agreement_after_onboarding(self.lead)

        self.assertEqual(result, {"state": "sent", "document_id": "sw_document_123"})
        post = calls[0][2]["json"]
        self.assertTrue(post["files"][0]["file_base64"])
        self.assertEqual(post["copied_contacts"][0]["email"], "support@homeofferflow.com")
        self.assertEqual(post["recipients"][0]["email"], "alex@example.com")
        self.assertIn("partner_agreement_status=eq.not_started", calls[1][1])
        self.assertEqual(calls[1][2]["json"]["partner_agreement_status"], "sent")

    def test_dispatch_skips_already_sent_or_nonpaid_records(self):
        with patch.object(fsbo, "PARTNER_AGREEMENT_SIGNING_ENABLED", True), \
             patch.object(fsbo, "SIGNWELL_ENABLED", True), \
             patch.object(fsbo, "SIGNWELL_API_KEY", "test-key"), \
             patch.object(fsbo.httpx, "Client") as client:
            already_sent = dict(self.lead, partner_agreement_status="sent")
            unpaid = dict(self.lead, payment_status="pending")
            self.assertEqual(fsbo._dispatch_partner_agreement_after_onboarding(already_sent)["state"], "already_dispatched")
            self.assertEqual(fsbo._dispatch_partner_agreement_after_onboarding(unpaid)["state"], "not_paid")
        client.assert_not_called()

    def test_manual_and_automatic_delivery_render_identical_agreements(self):
        admin_spec = importlib.util.spec_from_file_location("admin_agreement", ROOT / "api" / "admin-dashboard.py")
        admin = importlib.util.module_from_spec(admin_spec)
        admin_spec.loader.exec_module(admin)
        manual = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(admin._partner_agreement_pdf(self.lead))).pages)
        automatic = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(fsbo.partner_marketplace_agreement.render(self.lead))).pages)
        self.assertEqual(manual, automatic)


if __name__ == "__main__":
    unittest.main()

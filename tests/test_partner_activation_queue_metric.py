import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
import importlib.util


class PartnerActivationQueueMetricTests(unittest.TestCase):
    def test_paid_partner_activation_queue_is_server_derived(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('paid_partner_activation_queue', source)
        self.assertIn('paidPartnerActivationQueueCount', source)
        self.assertIn('paidPartnerActivationReadinessCounts', source)
        self.assertIn('_partner_activation_readiness', source)
        self.assertIn('source_lead_id', source)

    def test_admin_dashboard_surfaces_paid_partner_queue(self):
        source = Path('index.html').read_text()
        self.assertIn('Paid Partner Activation Queue', source)
        self.assertIn('paidPartnerActivationQueueCount', source)
        self.assertIn("paid-partner-activation", source)
        self.assertIn("Email partner", source)
        self.assertIn("activation_readiness", source)
        self.assertIn("readinessLabel", source)

    def test_paid_partner_queue_prioritizes_oldest_paid_applications(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn("paid_partner_activation_queue.sort", source)
        self.assertIn("_parse_timestamp(lead.get(\"created_at\"))", source)

    def test_readiness_distinguishes_setup_agreement_and_activation(self):
        spec = importlib.util.spec_from_file_location("partner_activation_admin", Path("api/admin-dashboard.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        now = datetime.now(timezone.utc)
        self.assertEqual(module._partner_activation_readiness({}, now)["code"], "setup_access_missing")
        self.assertEqual(module._partner_activation_readiness({
            "onboarding_token_hash": "not-a-secret", "onboarding_token_expires_at": (now - timedelta(days=1)).isoformat(),
        }, now)["code"], "setup_link_expired")
        self.assertEqual(module._partner_activation_readiness({
            "onboarding_status": "complete", "partner_agreement_status": "sent"
        }, now)["code"], "awaiting_agreement")
        self.assertEqual(module._partner_activation_readiness({
            "onboarding_status": "complete", "partner_agreement_status": "signed",
            "partner_agreement_signed_at": now.isoformat(),
            "onboarding_token_expires_at": (now + timedelta(days=1)).isoformat(),
        }, now)["code"], "ready_to_activate")

    def test_unsent_agreement_reflects_its_live_signing_configuration(self):
        spec = importlib.util.spec_from_file_location("partner_activation_admin", Path("api/admin-dashboard.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.PARTNER_AGREEMENT_SIGNING_ENABLED
        try:
            module.PARTNER_AGREEMENT_SIGNING_ENABLED = False
            self.assertEqual(module._partner_activation_readiness({"onboarding_status": "complete"})["code"], "agreement_review_pending")
            module.PARTNER_AGREEMENT_SIGNING_ENABLED = True
            self.assertEqual(module._partner_activation_readiness({"onboarding_status": "complete"})["code"], "agreement_ready_to_send")
        finally:
            module.PARTNER_AGREEMENT_SIGNING_ENABLED = original


if __name__ == '__main__':
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_dashboard_txr_signing", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TxrSigningRequestPathTests(unittest.TestCase):
    def test_signing_is_opt_in_and_route_is_a_separate_action(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('TXR_SIGNING_ENABLED =', source)
        self.assertIn('if not TXR_SIGNING_ENABLED:', source)
        self.assertIn('data.get("action") == "send_txr_agreement_for_signature"', source)
        self.assertIn('scope == "standalone_agreements"', source)

    def test_dispatch_uses_the_source_specific_field_maps(self):
        cases = {
            "TXR-1501": {"signer_plan": "clients_and_associate", "compensation": {"purchase_percentage": "3"}},
            "TXR-1506": {"signer_plan": "consumers_and_associate"},
            "TXR-1507": {"signer_plan": "clients_and_associate", "compensation": {"purchase_percentage": "3"}, "service_level": "full_services", "intermediary": "authorized"},
            "TXR-1508": {"signer_plan": "associate_and_clients", "other_broker_agreement": ["no"]},
        }
        for form_code, data in cases.items():
            fields = MODULE._txr_signwell_fields(form_code, {"client_names": ["Client One"], **data}, 1)
            self.assertEqual(len(fields), 1)
            self.assertTrue(fields[0])
            self.assertTrue(all(item["page"] >= 1 for item in fields[0]))

    def test_recipient_builder_keeps_client_and_associate_roles_distinct(self):
        recipients = MODULE._txr_signwell_recipients(
            {"form_code": "TXR-1507", "client_names": ["One", "Two"], "agreement_data": {"signer_plan": "clients_and_associate"}},
            ["one@example.com", "two@example.com"],
            {"contact_email": "broker@example.com", "name": "Brokerage"},
            {"email": "associate@example.com", "name": "Associate"},
        )
        self.assertEqual([row["id"] for row in recipients], ["1", "2", "associate"])

    def test_ui_exposes_preview_and_send_only_for_draft_records(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('hof-standalone-agreement-signing-v1', html)
        self.assertIn("scope=standalone_agreements", html)
        self.assertIn("send_txr_agreement_for_signature", html)
        self.assertIn("agreement.status === 'draft'", html)
        self.assertIn("Preview only — signing QA pending", html)

    def test_standalone_scope_reports_the_signing_gate_state(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"signingEnabled": TXR_SIGNING_ENABLED', source)

    def test_shared_library_signing_does_not_require_a_brokerage_seat(self):
        signing_source = MODULE._send_txr_agreement_for_signature.__doc__ or ""
        route_source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        start = route_source.index("async def _send_txr_agreement_for_signature")
        end = route_source.index("\n\nclass handler", start)
        route = route_source[start:end]
        self.assertIn("without being assigned to a brokerage seat", signing_source)
        self.assertNotIn("_active_brokerage_member(user)", route)
        self.assertNotIn("_require_brokerage_txr_authorization", route)
        self.assertIn("select=id,brokerage_id,form_code,form_source_id", route)

    def test_workspace_starts_with_a_transaction_interview(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Start here", html)
        self.assertIn("What are you working on?", html)
        self.assertIn("data-agent-workflow-choice=\"purchase\"", html)
        self.assertIn("data-agent-workflow-choice=\"sale_listing\"", html)
        self.assertIn("data-agent-workflow-choice=\"lease_listing\"", html)
        self.assertIn("data-agent-workflow-choice=\"lease_representation\"", html)

    def test_signwell_signing_urls_are_extracted_only_from_https_recipient_urls(self):
        self.assertEqual(
            MODULE._signwell_signing_urls({
                "recipients": [
                    {"signing_url": "https://signwell.example/one"},
                    {"embedded_signing_url": "https://signwell.example/two"},
                    {"signing_url": "javascript:alert(1)"},
                    {"signing_url": "https://signwell.example/one"},
                ]
            }),
            ["https://signwell.example/one", "https://signwell.example/two"],
        )


if __name__ == "__main__":
    unittest.main()

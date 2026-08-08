from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_authenticated_txr_qa", ROOT / "scripts" / "run_authenticated_txr_qa.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuthenticatedTxrQaHelperTests(unittest.TestCase):
    def test_one_client_payload_is_restricted_and_explicit(self):
        payload = MODULE._payload("TXR-1507", 1)
        self.assertEqual(payload["action"], "create_txr_1507_draft")
        self.assertEqual(payload["formCode"], "TXR-1507")
        self.assertEqual(payload["signerPlan"], "clients_and_associate")
        self.assertTrue(payload["formUseAttested"])
        self.assertEqual(len(payload["clientNames"]), 1)
        self.assertNotIn("email", payload)
        self.assertNotIn("phone", payload)

    def test_two_client_payload_has_two_distinct_test_clients(self):
        payload = MODULE._payload("TXR-1507", 2)
        self.assertEqual(len(payload["clientNames"]), 2)
        self.assertEqual(len(set(payload["clientNames"])), 2)

    def test_all_supported_forms_have_distinct_actions_and_sources(self):
        expected = {
            "TXR-1501": "create_txr_1501_draft",
            "TXR-1506": "create_txr_1506_draft",
            "TXR-1507": "create_txr_1507_draft",
            "TXR-1508": "create_txr_1508_draft",
        }
        for form_code, action in expected.items():
            payload = MODULE._payload(form_code, 1)
            self.assertEqual(payload["action"], action)
            self.assertEqual(payload["formCode"], form_code)
            self.assertIn("formSourceId", payload)

    def test_each_form_payload_carries_its_actual_signer_plan(self):
        expected = {
            "TXR-1501": "clients_and_associate",
            "TXR-1506": "consumers_and_associate",
            "TXR-1507": "clients_and_associate",
            "TXR-1508": "associate_and_clients",
        }
        for form_code, signer_plan in expected.items():
            self.assertEqual(MODULE._payload(form_code, 1)["signerPlan"], signer_plan)

    def test_seller_disclosure_payload_is_review_only_and_uses_both_approved_sources(self):
        payload = MODULE._seller_disclosure_payload(2)
        self.assertEqual(payload["action"], "create_seller_disclosure_draft")
        self.assertEqual(payload["formCode"], "TREC-55-1")
        self.assertEqual(payload["disclosureSourceId"], MODULE.SELLER_SOURCE_IDS["TREC-55-1"])
        self.assertEqual(payload["waterSourceId"], MODULE.SELLER_SOURCE_IDS["TREC-61-0"])
        self.assertEqual(len(payload["sellerNames"]), 2)
        self.assertNotIn("signerPlan", payload)
        self.assertNotIn("send", payload)

    def test_helper_report_names_reflect_seller_subjects_without_relabeling_them_as_clients(self):
        source = (ROOT / "scripts" / "run_authenticated_txr_qa.py").read_text()
        self.assertIn('f"{form.lower()}-{client_count}-{subject_count}-qa-report.json"', source)
        self.assertIn('subject_count = "seller" if seller_disclosure else "client"', source)

    def test_helper_exposes_an_all_form_matrix_mode_without_signing(self):
        source = (ROOT / "scripts" / "run_authenticated_txr_qa.py").read_text()
        self.assertIn('("TREC-55-1", "ALL")', source)
        self.assertIn('forms = tuple(SOURCE_IDS) + ("TREC-55-1",) if args.form == "ALL" else (args.form,)', source)
        self.assertIn('"signing_sent": False', source)

    def test_helper_can_request_rendered_page_manifests_without_signing(self):
        source = (ROOT / "scripts" / "run_authenticated_txr_qa.py").read_text()
        self.assertIn("--render-pages", source)
        self.assertIn("render_manifest", source)
        self.assertIn("render_pages=args.render_pages", source)

    def test_send_mode_requires_isolated_base_url_and_explicit_client_emails(self):
        source = (ROOT / "scripts" / "run_authenticated_txr_qa.py").read_text()
        self.assertIn('parser.add_argument("--send"', source)
        self.assertIn('parser.add_argument("--client-email"', source)
        self.assertIn("Refusing to send restricted TXR QA from the production URL", source)
        self.assertIn('"action": "send_txr_agreement_for_signature"', source)

if __name__ == "__main__":
    unittest.main()

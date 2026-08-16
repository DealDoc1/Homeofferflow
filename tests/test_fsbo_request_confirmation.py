import pathlib
import importlib.util
import unittest
from unittest.mock import patch


HTML = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
API_PATH = pathlib.Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py"


class FsboRequestConfirmationTests(unittest.TestCase):
    def test_fsbo_submission_keeps_a_durable_intake_handoff(self):
        self.assertIn("downloadFsboRequestSummary", HTML)
        self.assertIn("homeofferflow-fsbo-seller-plan.txt", HTML)
        self.assertIn("Seller request saved", HTML)
        self.assertIn("confirm scope, provider involvement, availability, and final pricing", HTML)
        self.assertIn("This is an intake record, not checkout", HTML)
        self.assertIn("const fsboNextSteps", HTML)
        self.assertIn("Your next steps:", HTML)
        self.assertIn("Wait for qualified professional review before choosing a contract path.", HTML)

    def test_fsbo_submission_delivers_a_timeline_specific_readiness_plan(self):
        self.assertIn("const fsboReadinessPlans", HTML)
        self.assertIn("function fsboReadinessPlan(timeline)", HTML)
        self.assertIn("Your ready-now seller plan", HTML)
        self.assertIn("Your 30-day seller plan", HTML)
        self.assertIn("FSBO Seller Readiness Plan Delivered", HTML)
        self.assertIn("Download seller plan", HTML)

    def test_fsbo_submission_prevents_same_device_duplicate_lead_retries(self):
        self.assertIn('id="fsboSellerSubmit"', HTML)
        self.assertIn("function fsboSubmissionKey(payload)", HTML)
        self.assertIn("sessionStorage.getItem(submissionKey)", HTML)
        self.assertIn("sessionStorage.setItem(submissionKey", HTML)
        self.assertIn("Change the package selection or property details", HTML)

    def test_fsbo_intake_draft_is_preserved_until_submission(self):
        self.assertIn("hof_fsbo_intake_draft_v1", HTML)
        self.assertIn("function saveFsboDraft()", HTML)
        self.assertIn("window.restoreFsboDraft", HTML)
        self.assertIn("clearFsboDraft();", HTML)
        self.assertIn("field?.addEventListener('change', saveFsboDraft)", HTML)

    def test_seller_can_see_and_clear_the_private_device_only_draft(self):
        self.assertIn('id="fsboDraftRecovery"', HTML)
        self.assertIn("function renderFsboDraftRecoveryNotice", HTML)
        self.assertIn("Your saved seller draft was restored on this device.", HTML)
        self.assertIn("Your seller draft is saved on this device.", HTML)
        self.assertIn("It has not been submitted or shared.", HTML)
        self.assertIn("Clear this device draft", HTML)
        self.assertIn("renderFsboDraftRecoveryNotice(fsboDraftExists());", HTML)

    def test_fsbo_confirmation_keeps_a_privacy_minimized_same_device_receipt(self):
        self.assertIn("hof_fsbo_request_receipt_v1", HTML)
        self.assertIn("function saveFsboRequestReceipt(selected)", HTML)
        self.assertIn("function renderFsboRequestReceipt()", HTML)
        self.assertIn("Seller request saved on this device.", HTML)
        self.assertIn("fsboReceiptMaxAgeMs", HTML)
        self.assertIn("localStorage.removeItem(fsboReceiptStorageKey)", HTML)
        self.assertIn("FSBO Seller Request Receipt Viewed", HTML)
        self.assertIn("FSBO Seller Request Receipt Cleared", HTML)

    def test_fsbo_plan_download_is_anonymous_conversion_evidence(self):
        api = (pathlib.Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
        admin = (pathlib.Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("FSBO Seller Plan Downloaded", HTML)
        self.assertIn("fsbo_seller_plan_downloaded", api)
        self.assertIn('"sellerPlanDownloadCount"', admin)
        self.assertIn("sellerPlanDownloadCount", HTML)

    def test_seller_plan_can_be_copied_for_mobile_sharing_with_aggregate_measurement(self):
        api = (pathlib.Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
        admin = (pathlib.Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("window.copyFsboRequestSummary", HTML)
        self.assertIn("navigator.clipboard?.writeText", HTML)
        self.assertIn("Copy seller plan", HTML)
        self.assertIn("FSBO Seller Plan Copied", HTML)
        self.assertIn('"fsbo_seller_plan_copied": "copied"', api)
        self.assertIn('"sellerPlanCopiedCount"', admin)

    def test_saved_seller_request_can_offer_an_email_receipt(self):
        api = API_PATH.read_text(encoding="utf-8")
        self.assertIn("def _send_seller_plan_confirmation(payload):", api)
        self.assertIn("Best-effort transactional receipt", api)
        self.assertIn("Idempotency-Key", api)
        self.assertIn("seller_plan_email", api)
        self.assertIn("SELLER_PLAN_REPLY_TO", api)
        self.assertIn("Reply directly to this email", api)
        self.assertIn("A copy of this request was also emailed to you.", HTML)

    def test_seller_plan_receipt_escapes_seller_content_and_is_idempotent(self):
        spec = importlib.util.spec_from_file_location("fsbo_plan_receipt", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = {}

        class Response:
            status_code = 200

        class Client:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def post(self, *args, **kwargs):
                captured["args"] = args
                captured["kwargs"] = kwargs
                return Response()

        payload = {
            "seller_email": "seller@example.com",
            "property_address": "<script>bad</script>",
            "package_name": "Seller Prep Plan",
            "package_price": "$299",
            "timeline": "30_days",
        }
        with patch.object(api, "RESEND_API_KEY", "re_test"), patch.object(api.httpx, "Client", return_value=Client()):
            self.assertEqual(api._send_seller_plan_confirmation(payload), "sent")
        self.assertEqual(captured["args"][0], "https://api.resend.com/emails")
        self.assertEqual(captured["kwargs"]["json"]["to"], ["seller@example.com"])
        self.assertEqual(captured["kwargs"]["json"]["reply_to"], "support@homeofferflow.com")
        self.assertNotIn("<script>", captured["kwargs"]["json"]["html"])
        self.assertIn("not checkout", captured["kwargs"]["json"]["text"])
        self.assertIn("Reply directly to this email", captured["kwargs"]["json"]["text"])
        self.assertTrue(captured["kwargs"]["headers"]["Idempotency-Key"].startswith("fsbo-seller-plan-"))

    def test_seller_plan_receipt_does_not_attempt_delivery_without_config(self):
        spec = importlib.util.spec_from_file_location("fsbo_plan_receipt_unconfigured", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        with patch.object(api, "RESEND_API_KEY", ""):
            self.assertEqual(api._send_seller_plan_confirmation({"seller_email": "seller@example.com"}), "not_configured")

    def test_receipt_delivery_telemetry_is_aggregate_and_allowlisted(self):
        spec = importlib.util.spec_from_file_location("fsbo_plan_receipt_telemetry", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = []
        with patch.object(api, "_record_partner_checkout_event", side_effect=lambda *args: captured.append(args)):
            api._record_seller_plan_receipt_event({
                "seller_email": "seller@example.com",
                "property_address": "1438 Whitaker Road",
                "service_level": "seller_prep",
            }, "sent")
            api._record_seller_plan_receipt_event({"service_level": "seller_prep"}, "unexpected")
        self.assertEqual(len(captured), 1)
        event_type, status, _, metadata = captured[0]
        self.assertEqual(event_type, "fsbo_seller_plan_receipt_sent")
        self.assertEqual(status, "sent")
        self.assertEqual(metadata, {"surface": "seller_plan_receipt", "serviceLevel": "seller_prep"})


if __name__ == "__main__":
    unittest.main()

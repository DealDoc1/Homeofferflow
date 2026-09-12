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
        self.assertIn("confirm the scope, provider involvement, availability, and final pricing", HTML)
        self.assertIn("This is an intake record, not checkout", HTML)
        self.assertIn("const fsboNextSteps", HTML)
        self.assertIn("Your next steps:", HTML)
        self.assertIn("Use the offer comparison to identify the questions to review before choosing a contract path.", HTML)

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

    def test_clearing_a_seller_draft_resets_visible_goal_and_timeline_defaults(self):
        clear_start = HTML.index("document.getElementById('clearFsboDraft')?.addEventListener")
        clear_end = HTML.index("}, {once:true});", clear_start)
        clear_action = HTML[clear_start:clear_end]
        self.assertIn("timeline.value = 'not_sure';", clear_action)
        self.assertIn("window.renderFsboGuidedGoal?.();", clear_action)
        self.assertIn("renderFsboRequiredReadyCue();", clear_action)

    def test_fsbo_free_plan_action_stays_locked_until_the_two_required_fields_are_valid(self):
        self.assertIn('id="fsboSellerQuickSubmit" data-fsbo-submit onclick="submitFsboSellerLead(\'quick\')" disabled aria-disabled="true"', HTML)
        self.assertIn('aria-label="Save My Seller Request — enter address and email to continue"', HTML)
        self.assertIn("function fsboRequiredFieldsReady()", HTML)
        self.assertIn("emailInput?.checkValidity()", HTML)
        self.assertIn("Enter address + email to continue", HTML)
        self.assertIn("<strong>Step 1 of 2:</strong>", HTML)
        self.assertIn("<strong>Step 2 of 2:</strong>", HTML)
        self.assertIn("Clear this device draft", HTML)
        self.assertIn("renderFsboDraftRecoveryNotice(fsboDraftExists());", HTML)

    def test_fsbo_confirmation_keeps_a_privacy_minimized_same_device_receipt(self):
        self.assertIn("hof_fsbo_request_receipt_v1", HTML)
        self.assertIn("function saveFsboRequestReceipt(selected, serviceLevel)", HTML)
        self.assertIn("function renderFsboRequestReceipt()", HTML)
        self.assertIn("Seller request saved on this device.", HTML)
        self.assertIn("fsboReceiptMaxAgeMs", HTML)
        self.assertIn("localStorage.removeItem(fsboReceiptStorageKey)", HTML)
        self.assertIn("FSBO Seller Request Receipt Viewed", HTML)
        self.assertIn("FSBO Seller Request Receipt Cleared", HTML)
        self.assertIn("'FSBO Seller Request Receipt Viewed': 'fsbo_request_receipt_viewed'", HTML)
        self.assertIn("serviceLevel: fsboCampaignPackages.has(serviceLevel) ? serviceLevel : 'free_intake'", HTML)
        self.assertIn("const receiptServiceLevel = fsboCampaignPackages.has(receipt.serviceLevel) ? receipt.serviceLevel : 'free_intake';", HTML)
        self.assertIn("sellerRequestReceiptViewedCount", HTML)
        self.assertIn("Your plan is ready below; you can also start a different request.", HTML)
        self.assertNotIn("or wait for follow-up.", HTML)
        api = API_PATH.read_text(encoding="utf-8")
        admin = (pathlib.Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"fsbo_request_receipt_viewed": "viewed"', api)
        self.assertIn('"fsbo_request_receipt_cleared": "cleared"', api)
        self.assertIn('"sellerRequestReceiptViewedCount"', admin)

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

    def test_seller_plan_has_a_clean_printable_view_with_aggregate_measurement(self):
        api = (pathlib.Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
        admin = (pathlib.Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("window.printFsboRequestSummary", HTML)
        self.assertIn("Print seller plan", HTML)
        self.assertIn("A simple planning aid for your next sale decision.", HTML)
        self.assertIn("FSBO Seller Plan Printed", HTML)
        self.assertIn('"fsbo_seller_plan_printed": "printed"', api)
        self.assertIn('"sellerPlanPrintedCount"', admin)

    def test_saved_seller_plan_can_open_a_privacy_safe_support_conversation(self):
        api = API_PATH.read_text(encoding="utf-8")
        admin = (pathlib.Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("window.contactFsboSupport", HTML)
        self.assertIn("function fsboSupportButtonLabel(serviceLevel)", HTML)
        self.assertIn("Discuss your seller plan", HTML)
        self.assertIn("Ask about ${item.title}", HTML)
        self.assertIn("escapeAttr(fsboSupportButtonLabel(payload.service_level))", HTML)
        self.assertIn("FSBO Seller Support Contact Opened", HTML)
        self.assertIn("fsbo_seller_support_contact_opened", api)
        self.assertIn('"sellerSupportContactOpenedCount"', admin)
        contact_start = HTML.index("window.contactFsboSupport")
        contact_end = HTML.index("window.openFsboProviderDirectory", contact_start)
        contact = HTML[contact_start:contact_end]
        self.assertIn("mailto:support@homeofferflow.com", contact)
        self.assertNotIn("fsboPropertyAddress", contact)
        self.assertNotIn("fsboSellerEmail", contact)

    def test_saved_seller_request_can_offer_an_email_receipt(self):
        api = API_PATH.read_text(encoding="utf-8")
        self.assertIn("def _send_seller_plan_confirmation(payload):", api)
        self.assertIn("def _seller_plan_scope_note(service_level):", api)
        self.assertIn("Your free seller plan is ready to use.", api)
        self.assertIn("Best-effort transactional receipt", api)
        self.assertIn("Idempotency-Key", api)
        self.assertIn("seller_plan_email", api)
        self.assertIn("SELLER_PLAN_REPLY_TO", api)
        self.assertIn("SELLER_LEAD_ALERT_TO", api)
        self.assertIn('email_payload["bcc"]', api)
        self.assertIn("Reply directly to this email", api)
        self.assertIn("Review your selected path", api)
        self.assertIn("seller_follow_up", api)
        self.assertIn("A copy of this request was also emailed to you.", HTML)

    def test_free_seller_plan_is_immediately_usable_without_gate_like_review_copy(self):
        self.assertIn("const scopeNote = payload.service_level === 'free_intake'", HTML)
        self.assertIn("Your free seller plan is ready to use.", HTML)
        self.assertIn("If you later request paid support", HTML)
        self.assertIn("with you before any payment is requested.", HTML)
        self.assertIn("Use this plan to choose your next step: prepare, launch, explore MLS options, or organize an offer review.", HTML)
        self.assertNotIn("Watch for a HomeOfferFlow follow-up about the path that fits your goals.", HTML)
        self.assertNotIn("A qualified human review is required", HTML)

        spec = importlib.util.spec_from_file_location("fsbo_plan_scope_note", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        self.assertIn("free seller plan is ready to use", api._seller_plan_scope_note("free_intake"))
        self.assertIn("Your request is recorded", api._seller_plan_scope_note("flat_fee_mls"))
        self.assertIn("before any payment is requested", api._seller_plan_scope_note("flat_fee_mls"))

    def test_duplicate_seller_request_recovers_the_receipt_without_creating_a_second_lead(self):
        api = API_PATH.read_text(encoding="utf-8")
        duplicate_start = api.index("if existing:\n")
        payload_start = api.index("            payload = {", duplicate_start)
        duplicate_branch = api[duplicate_start:payload_start]
        self.assertIn("receipt_payload = {", api[:duplicate_start])
        self.assertIn("_send_seller_plan_confirmation(receipt_payload)", duplicate_branch)
        self.assertNotIn("_record_seller_plan_receipt_event", duplicate_branch)
        self.assertIn("must not inflate the delivery funnel", duplicate_branch)
        self.assertIn('"seller_plan_email": email_delivery', duplicate_branch)
        self.assertIn('"duplicate": True', duplicate_branch)

    def test_duplicate_seller_request_is_not_counted_as_a_new_browser_acquisition(self):
        duplicate_guard = "if (!data.duplicate) {\n        trackFsboFunnel('FSBO Seller Request Saved'"
        self.assertIn(duplicate_guard, HTML)
        self.assertIn("Your seller request is already saved.", HTML)
        self.assertIn("remains recorded for follow-up.", HTML)

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
            "service_level": "seller_prep",
            "timeline": "30_days",
        }
        with patch.object(api, "RESEND_API_KEY", "re_test"), patch.object(api.httpx, "Client", return_value=Client()):
            self.assertEqual(api._send_seller_plan_confirmation(payload), "sent")
        self.assertEqual(captured["args"][0], "https://api.resend.com/emails")
        self.assertEqual(captured["kwargs"]["json"]["to"], ["seller@example.com"])
        self.assertEqual(captured["kwargs"]["json"]["reply_to"], "support@homeofferflow.com")
        self.assertEqual(captured["kwargs"]["json"]["subject"], "Your HomeOfferFlow Seller Prep Plan next steps")
        self.assertEqual(captured["kwargs"]["json"]["bcc"], ["support@homeofferflow.com"])
        self.assertEqual(captured["kwargs"]["json"]["tags"], [
            {"name": "email_type", "value": "seller_plan_receipt"},
            {"name": "seller_package", "value": "seller_prep"},
        ])
        self.assertNotIn("<script>", captured["kwargs"]["json"]["html"])
        self.assertIn("not checkout", captured["kwargs"]["json"]["text"])
        self.assertIn("Your next steps", captured["kwargs"]["json"]["text"])
        self.assertIn("Review your selected path: https://www.homeofferflow.com/sellers?seller_package=seller_prep", captured["kwargs"]["json"]["text"])
        self.assertIn("List repairs, cleaning, staging", captured["kwargs"]["json"]["text"])
        self.assertIn("<h3>Your next steps</h3>", captured["kwargs"]["json"]["html"])
        self.assertIn('href="https://www.homeofferflow.com/sellers?seller_package=seller_prep', captured["kwargs"]["json"]["html"])
        self.assertIn("Reply directly to this email", captured["kwargs"]["json"]["text"])
        self.assertTrue(captured["kwargs"]["headers"]["Idempotency-Key"].startswith("fsbo-seller-plan-"))

    def test_seller_receipt_does_not_bcc_the_seller_to_themselves(self):
        spec = importlib.util.spec_from_file_location("fsbo_plan_receipt_bcc", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = {}

        class Response:
            status_code = 200

        class Client:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def post(self, *args, **kwargs):
                captured["payload"] = kwargs["json"]
                return Response()

        with patch.object(api, "RESEND_API_KEY", "re_test"), patch.object(api, "SELLER_LEAD_ALERT_TO", "seller@example.com"), patch.object(api.httpx, "Client", return_value=Client()):
            self.assertEqual(api._send_seller_plan_confirmation({"seller_email": "seller@example.com"}), "sent")
        self.assertNotIn("bcc", captured["payload"])

    def test_free_seller_plan_uses_a_clear_noncommercial_subject(self):
        spec = importlib.util.spec_from_file_location("fsbo_plan_receipt_subject", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = {}

        class Response:
            status_code = 200

        class Client:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def post(self, *args, **kwargs):
                captured["payload"] = kwargs["json"]
                return Response()

        with patch.object(api, "RESEND_API_KEY", "re_test"), patch.object(api.httpx, "Client", return_value=Client()):
            self.assertEqual(api._send_seller_plan_confirmation({"seller_email": "seller@example.com"}), "sent")
        self.assertEqual(captured["payload"]["subject"], "Your free HomeOfferFlow seller plan")
        self.assertIn("Continue with your seller plan: https://www.homeofferflow.com/sellers?seller_package=free_intake", captured["payload"]["text"])
        self.assertIn(">Continue with your seller plan</a>", captured["payload"]["html"])
        self.assertIn(
            "Choose the next support path that fits your goals when you are ready.",
            captured["payload"]["text"],
        )

    def test_seller_plan_receipt_steps_are_allowlisted_and_fall_back_safely(self):
        spec = importlib.util.spec_from_file_location("fsbo_plan_receipt_steps", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        self.assertEqual(
            api._seller_plan_receipt_steps({"service_level": "offer_review"})[0],
            "Keep every buyer offer and addendum together.",
        )
        self.assertEqual(
            api._seller_plan_receipt_steps({"service_level": "not-a-package"}),
            api.FSBO_RECEIPT_NEXT_STEPS["free_intake"],
        )

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

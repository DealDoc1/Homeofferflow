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
            "TXR-1905": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
            "TXR-1914": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
            "TXR-1917": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
            "TXR-1919": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
            "TXR-1948": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
            "TXR-1953": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
            "TXR-1954": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
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

    def test_lease_addenda_use_only_the_named_buyers_and_sellers(self):
        agreement = {
            "form_code": "TXR-1953",
            "client_names": ["Buyer One", "Buyer Two", "Seller One"],
            "agreement_data": {
                "buyer_names": ["Buyer One", "Buyer Two"],
                "seller_names": ["Seller One"],
            },
        }
        recipients = MODULE._txr_signwell_recipients(
            agreement,
            ["buyer1@example.com", "buyer2@example.com", "seller1@example.com"],
            {},
            {"email": "agent@example.com", "name": "Agent"},
        )
        self.assertEqual([row["id"] for row in recipients], ["1", "2", "3"])
        self.assertEqual(
            MODULE._standalone_signer_labels(agreement),
            ["Buyer 1", "Buyer 2", "Seller 1"],
        )
        self.assertNotIn("agent@example.com", [row["email"] for row in recipients])

    def test_prepared_purchase_addenda_use_only_named_buyers_and_sellers(self):
        for form_code in ("TXR-1905", "TXR-1914", "TXR-1917", "TXR-1919", "TXR-1948"):
            agreement = {
                "form_code": form_code,
                "client_names": ["Buyer One", "Seller One"],
                "agreement_data": {
                    "buyer_names": ["Buyer One"],
                    "seller_names": ["Seller One"],
                },
            }
            recipients = MODULE._txr_signwell_recipients(
                agreement,
                ["buyer@example.com", "seller@example.com"],
                {},
                {"email": "agent@example.com", "name": "Agent"},
            )
            self.assertEqual([row["id"] for row in recipients], ["1", "2"])
            self.assertEqual(MODULE._standalone_signer_labels(agreement), ["Buyer 1", "Seller 1"])
            self.assertNotIn("agent@example.com", [row["email"] for row in recipients])

    def test_source_aligned_buyer_seller_maps_are_live_signing_workflows(self):
        for form_code in ("TXR-1905", "TXR-1914", "TXR-1917", "TXR-1919", "TXR-1948"):
            self.assertIn(form_code, MODULE.TXR_SIGNING_FORM_CODES)

    def test_agent_form_roadmap_matches_the_released_review_and_send_scope(self):
        roadmap = (ROOT / "docs" / "AGENT_FORM_COVERAGE_ROADMAP.md").read_text(encoding="utf-8")
        for form_code in sorted(MODULE.TXR_SIGNING_FORM_CODES):
            with self.subTest(form_code=form_code):
                self.assertIn(form_code, roadmap)
        self.assertNotIn("These workflows do not imply a send or signature capability.", roadmap)

    def test_ui_exposes_preview_send_and_owner_refresh_actions(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('hof-standalone-agreement-signing-v1', html)
        self.assertIn("scope=standalone_agreements", html)
        self.assertIn("send_txr_agreement_for_signature", html)
        self.assertIn("agreement.status === 'draft'", html)
        self.assertIn("agreement.status === 'sent' && agreement.signwell_document_id", html)
        self.assertIn("data-refresh-signing", html)
        self.assertIn("body: JSON.stringify({ agreementId: agreement.id })", html)
        self.assertIn("agreement.status === 'signed' && agreement.signwell_document_id", html)
        self.assertIn("data-download-completed", html)
        self.assertIn("action: 'download_completed_pdf'", html)
        self.assertIn("link.download = `${agreement.form_code || 'HomeOfferFlow'}-completed.pdf`", html)
        self.assertIn("Ready to review — signature sending will appear here when available.", html)
        self.assertIn("root.hofOpenPreparedAgreement", html)
        self.assertIn("Review and send", html)

    def test_every_live_signing_form_reaches_the_review_and_send_step(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        scripts = {
            "TXR-1501": "hof-txr1501-drafts-v1",
            "TXR-1506": "hof-txr1506-drafts-v1",
            "TXR-1507": "hof-txr1507-drafts-v1",
            "TXR-1508": "hof-txr1508-drafts-v1",
            "TXR-1905": "hof-txr1905-drafts-v1",
            "TXR-1914": "hof-txr1914-drafts-v1",
            "TXR-1917": "hof-txr1917-drafts-v1",
            "TXR-1919": "hof-txr1919-drafts-v1",
            "TXR-1948": "hof-txr1948-drafts-v1",
            "TXR-1953": "hof-txr1953-drafts-v1",
            "TXR-1954": "hof-txr1954-drafts-v1",
        }
        for form_code, script_id in scripts.items():
            with self.subTest(form_code=form_code):
                start = html.index(f'id="{script_id}"')
                end = html.index("</script>", start)
                if form_code in {"TXR-1905", "TXR-1914", "TXR-1917", "TXR-1919", "TXR-1948"}:
                    self.assertIn('hof-live-addendum-signing-next-step-v1', html)
                else:
                    self.assertIn("Review and send", html[start:end])

        helper_start = html.index('id="hof-live-addendum-signing-next-step-v1"')
        helper_end = html.index("</script>", helper_start)
        helper = html[helper_start:helper_end]
        self.assertIn("Review and send", helper)
        self.assertIn("hofOpenPreparedAgreement", helper)
        self.assertIn("Prepare document for review", helper)
        self.assertIn("We’ll prepare the document for your review before you choose whether to send it for signature.", helper)
        self.assertIn("txr1914AgreementDialog", helper)
        self.assertIn("txr1917Dialog", helper)
        self.assertIn("txr1919AgreementDialog", helper)

    def test_pdf_preview_does_not_sandbox_the_browser_pdf_viewer(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        preview_scope = html[html.index('id="hof-private-form-drafts-v1"'):html.index('id="hof-seller-disclosure-draft-ui-v1"')]
        self.assertIn("frame.src = blobUrl;", preview_scope)
        self.assertNotIn("frame.setAttribute('sandbox'", preview_scope)

    def test_standalone_scope_reports_the_signing_gate_state(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"signingEnabled": TXR_SIGNING_ENABLED', source)
        self.assertIn('"signingFormCodes": sorted(TXR_SIGNING_FORM_CODES)', source)
        self.assertIn('row.pop("agreement_data", None)', source)

    def test_unavailable_signature_sending_has_a_clear_customer_next_step(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            "Signature sending is not available right now. Your document is saved for review.",
            source,
        )
        self.assertIn("signature sending is not available", html)

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
        self.assertIn("What type of transaction are you starting?", html)
        self.assertIn("data-agent-workflow-choice=\"purchase\"", html)
        self.assertIn("data-agent-workflow-choice=\"sale_listing\"", html)
        self.assertIn("data-agent-workflow-choice=\"lease_listing\"", html)
        self.assertIn("data-agent-workflow-choice=\"lease_representation\"", html)

    def test_review_save_feedback_uses_customer_facing_document_language(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        start = html.index('id="hof-private-review-save-feedback-v1"')
        end = html.index("</script>", start)
        feedback = html[start:end]
        self.assertIn("Save for review", feedback)
        self.assertIn("Saving for review…", feedback)
        self.assertIn("Saved for review", feedback)
        self.assertIn("View saved documents", feedback)
        self.assertIn("We couldn’t prepare this document. Check your entries and try again.", feedback)
        self.assertNotIn("Preparing private draft…", feedback)
        self.assertNotIn("Private draft ready", feedback)

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

    def test_provider_document_is_checked_before_a_signing_request_is_sent(self):
        expected_fields = [[
            {"api_id": "agent_initials", "recipient_id": "associate"},
            {"api_id": "client_signature", "recipient_id": "1"},
        ]]
        recipients = [{"id": "associate"}, {"id": "1"}]
        complete = {
            "fields": [[
                {"api_id": "agent_initials", "recipient_id": "associate"},
                {"api_id": "client_signature", "recipient_id": "1"},
            ]],
            "recipients": recipients,
        }
        self.assertTrue(MODULE._signwell_document_matches_signing_request(complete, expected_fields, recipients))
        complete["fields"][0][0]["recipient_id"] = "1"
        self.assertFalse(MODULE._signwell_document_matches_signing_request(complete, expected_fields, recipients))
        complete["fields"][0][0]["recipient_id"] = "associate"
        complete["fields"][0].pop(0)
        self.assertFalse(MODULE._signwell_document_matches_signing_request(complete, expected_fields, recipients))

    def test_provider_document_must_keep_the_reviewed_field_geometry(self):
        expected_fields = [[{
            "api_id": "client_signature", "recipient_id": "1", "type": "signature",
            "page": 2, "x": 360, "y": 640, "width": 80, "height": 24,
        }]]
        recipients = [{"id": "1"}]
        complete = {
            "fields": [[{
                "api_id": "client_signature", "recipient_id": "1", "type": "Signature",
                "page": 2, "x": 360, "y": 640, "width": "80.0", "height": "24.0",
            }]],
            "recipients": recipients,
        }
        self.assertTrue(MODULE._signwell_document_matches_signing_request(complete, expected_fields, recipients))
        complete["fields"][0][0]["y"] = 675
        self.assertFalse(MODULE._signwell_document_matches_signing_request(complete, expected_fields, recipients))

    def test_core_txr_signing_requests_carry_the_current_geometry_revision(self):
        self.assertEqual(
            MODULE.TXR_SIGNING_MAP_REVISIONS["TXR-1501"],
            "txr-1501-2026-09-11-execution-calibrated-v1",
        )
        self.assertEqual(
            MODULE.TXR_SIGNING_MAP_REVISIONS["TXR-1506"],
            "txr-1506-2026-09-09-final-page-calibrated-v1",
        )
        self.assertEqual(
            MODULE.TXR_SIGNING_MAP_REVISIONS["TXR-1507"],
            "txr-1507-2026-09-12-completed-packet-calibrated-v2",
        )
        self.assertEqual(
            MODULE.TXR_SIGNING_MAP_REVISIONS["TXR-1508"],
            "txr-1508-2026-09-09-acknowledgement-calibrated-v1",
        )
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"signing_map_revision": current_map_revision', source)
        self.assertIn('"signingMapRevision": TXR_SIGNING_MAP_REVISIONS.get(form_code, "source-specific-v1")', source)

    def test_saved_drafts_are_bound_to_the_layout_revision_used_for_signing(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('agreement_data["signing_map_revision"] = TXR_SIGNING_MAP_REVISIONS.get(', source)
        self.assertIn("TXR_1501_FORM_CODE,", source)
        self.assertIn("TXR_1506_FORM_CODE,", source)
        self.assertIn("TXR_1507_FORM_CODE,", source)
        self.assertIn("TXR_1508_FORM_CODE,", source)
        self.assertIn(
            "signature fields appear in the right places.",
            source,
        )

    def test_all_recalibrated_core_forms_reject_stale_signing_maps(self):
        for form_code in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            current = MODULE.TXR_SIGNING_MAP_REVISIONS[form_code]
            self.assertEqual(
                MODULE._current_txr_signing_map_revision(form_code, {"signing_map_revision": current}),
                current,
            )
            with self.assertRaisesRegex(ValueError, "signature fields appear in the right places"):
                MODULE._current_txr_signing_map_revision(form_code, {})
        self.assertEqual(
            MODULE._current_txr_signing_map_revision("TXR-1905", {}),
            "source-specific-v1",
        )

    def test_stale_core_txr_draft_offers_a_direct_current_copy_path(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("const staleMapOpeners = {", html)
        for form_code, opener in (
            ("TXR-1501", "hofOpenTxr1501Draft"),
            ("TXR-1506", "hofOpenTxr1506Draft"),
            ("TXR-1507", "hofOpenTxr1507Draft"),
            ("TXR-1508", "hofOpenTxr1508Draft"),
        ):
            self.assertIn(f"'{form_code}': root.{opener}", html)
        self.assertIn("Prepare the current copy", html)
        self.assertIn("prepareCurrentCopy();", html)


if __name__ == "__main__":
    unittest.main()

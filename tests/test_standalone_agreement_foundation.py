import importlib.util
from unittest.mock import AsyncMock, patch
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_standalone_agreements.sql").read_text()
EXPANSION_MIGRATION = (ROOT / "supabase" / "homeofferflow_expand_standalone_representation_forms.sql").read_text()
SHOWING_MIGRATION = (ROOT / "supabase" / "homeofferflow_add_txr_1508_showing_drafts.sql").read_text()
NOTICE_MIGRATION = (ROOT / "supabase" / "homeofferflow_add_txr_1506_notice_drafts.sql").read_text()
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
BACKEND = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
SPEC = importlib.util.spec_from_file_location("standalone_agreement", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_payload():
    return {
        "formCode": "TXR-1507",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "clientNames": ["Test Buyer"],
        "marketArea": "Collin and Denton Counties, Texas",
        "termStart": "2026-08-01",
        "termEnd": "2027-01-31",
        "serviceLevel": "full_services",
        "intermediary": "authorized",
        "signerPlan": "clients_and_associate",
        "formUseAttested": True,
        "compensation": {"purchasePercentage": "3"},
    }


def valid_long_payload():
    return {
        "formCode": "TXR-1501",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "clientNames": ["Test Buyer"],
        "clientAddress": "721 Broderick Lane",
        "clientCityStateZip": "Prosper, TX 75078",
        "clientPhone": "2143649890",
        "clientEmail": "buyer@example.com",
        "marketArea": "Collin and Denton Counties, Texas",
        "termStart": "2026-08-01",
        "termEnd": "2027-01-31",
        "paymentCounty": "Collin",
        "intermediary": "authorized",
        "signerPlan": "clients_and_associate",
        "formUseAttested": True,
        "compensation": {"purchasePercentage": "3"},
    }


def valid_showing_payload():
    return {
        "formCode": "TXR-1508",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "clientNames": ["Test Customer"],
        "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
        "otherBrokerAgreement": ["no"],
        "unrepresentedAcknowledgment": True,
        "signerPlan": "associate_and_clients",
        "formUseAttested": True,
    }


def valid_notice_payload():
    return {
        "formCode": "TXR-1506",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "clientNames": ["Test Consumer"],
        "consumerRole": "buyer",
        "additionalNotice": "",
        "noticeAcknowledgment": True,
        "signerPlan": "consumers_and_associate",
        "formUseAttested": True,
    }


def valid_mineral_payload():
    return {
        "formCode": "TXR-1905",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
        "buyerNames": ["Test Buyer"],
        "sellerNames": ["Test Seller"],
        "reservationChoice": "undivided_interest",
        "undividedInterest": "25",
        "surfaceRights": "waived",
        "mineralReviewAcknowledgment": True,
    }


def valid_seller_financing_payload():
    return {
        "formCode": "TXR-1914",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
        "buyerNames": ["Test Buyer"],
        "sellerNames": ["Test Seller"],
        "creditDays": "7",
        "creditDocuments": ["credit_report", "employment"],
        "noteAmount": "250000",
        "interestRate": "6.25",
        "paymentPlan": "monthly_installments",
        "installmentAmount": "1800",
        "installmentInterestStyle": "including_interest",
        "installmentBeginsAfterMonths": "1",
        "payoffAfterMonths": "180",
        "propertyTransfer": "consent_required",
        "casualtyInsurance": "required",
        "escrow": "required",
        "thirdPartyServicer": "will",
        "escrowCostPaidBy": "buyer",
        "sellerFinancingReviewAcknowledgment": True,
    }


def valid_loan_assumption_payload():
    return {
        "formCode": "TXR-1919", "formSourceId": "00000000-0000-0000-0000-000000000001",
        "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX", "buyerNames": ["Test Buyer"],
        "sellerNames": ["Test Seller"], "creditDays": "7", "creditDocuments": ["credit_report"],
        "firstLoanEnabled": True, "firstLoanLender": "Example Bank", "firstLoanBalance": "240000",
        "firstLoanPayment": "1750", "firstAssumptionFeeCap": "500", "firstInterestRateCap": "6.5",
        "secondLoanEnabled": False, "varianceAdjustment": "cash", "varianceTerminationThreshold": "2500",
        "loanAssumptionReviewAcknowledgment": True,
    }


class StandaloneAgreementFoundationTests(unittest.TestCase):
    def test_txr_library_cards_do_not_require_active_brokerage_membership(self):
        self.assertNotIn("root.hofPlatform?.brokerageMembership?.status === 'active'", HTML)

    def test_shared_source_lookup_does_not_require_a_local_brokerage_object(self):
        lookup_start = HTML.index("root.hofLoadApprovedBrokerageSource = async function")
        lookup_end = HTML.index("root.hofApprovedSourceStatusCopy", lookup_start)
        lookup = HTML[lookup_start:lookup_end]
        self.assertNotIn("brokerage()?.id", lookup)
        self.assertIn("if (!token || !formCode) return null", lookup)

    def test_relationship_workspace_describes_the_shared_mineral_draft_without_an_authorization_gate(self):
        self.assertIn("TXR-1905 · Mineral Reservation Addendum", HTML)
        self.assertIn("checks your signed-in session and the approved source revision", HTML)
        self.assertNotIn("Each tool below checks your brokerage authorization", HTML)

    def test_server_uses_the_shared_library_without_agent_authorization_gate(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text()
        create_start = backend.index("async def _create_representation_draft")
        create_end = backend.index("async def _create_txr_1507_draft", create_start)
        create = backend[create_start:create_end]
        self.assertNotIn("_active_brokerage_member", create)
        self.assertNotIn("_require_brokerage_txr_authorization", create)
        self.assertIn('"brokerage_id": source["brokerage_id"]', create)

    def test_private_standalone_records_are_separate_from_offers(self):
        self.assertIn("create table if not exists public.hof_standalone_agreements", MIGRATION)
        self.assertIn("form_code text not null check (form_code in ('TXR-1507'))", MIGRATION)
        self.assertIn("remain aggregate-only", MIGRATION)
        self.assertIn("hof_standalone_agreements_select_own", MIGRATION)
        self.assertIn("('TXR-1501', 'TXR-1507')", EXPANSION_MIGRATION)
        self.assertIn("('TXR-1501', 'TXR-1507', 'TXR-1508')", SHOWING_MIGRATION)
        self.assertIn("('TXR-1501', 'TXR-1506', 'TXR-1507', 'TXR-1508')", NOTICE_MIGRATION)
        mineral_migration = (ROOT / "supabase" / "homeofferflow_add_txr_1905_private_drafts.sql").read_text()
        self.assertIn("'TXR-1905'", mineral_migration)

    def test_valid_short_form_draft_requires_every_decision(self):
        draft = MODULE._parse_txr_1507_draft(valid_payload())
        self.assertEqual(draft["client_names"], ["Test Buyer"])
        self.assertEqual(draft["agreement_data"]["service_level"], "full_services")
        self.assertEqual(draft["agreement_data"]["intermediary"], "authorized")
        self.assertEqual(draft["agreement_data"]["signer_plan"], "clients_and_associate")

    def test_short_form_requires_an_explicit_signer_plan(self):
        payload = valid_payload()
        payload.pop("signerPlan")
        with self.assertRaisesRegex(ValueError, "Choose an authorized broker"):
            MODULE._parse_txr_1507_draft(payload)

    def test_form_cards_are_available_to_signed_in_agent_roles_without_attestation(self):
        role_guard = "['agent', 'broker', 'brokerage_admin', 'broker_admin', 'owner', 'team_lead'].includes(role)"
        self.assertGreaterEqual(HTML.count(role_guard), 4)
        self.assertNotIn('name="formUseAttested"', HTML)

    def test_showing_services_requires_its_execution_fee(self):
        payload = valid_payload()
        payload["serviceLevel"] = "showing_services"
        with self.assertRaisesRegex(ValueError, "requires the execution fee"):
            MODULE._parse_txr_1507_draft(payload)

    def test_short_form_does_not_require_agent_authority_attestation(self):
        payload = valid_payload()
        payload["formUseAttested"] = False
        self.assertEqual(MODULE._parse_txr_1507_draft(payload)["client_names"], ["Test Buyer"])

    def test_draft_rejects_invalid_term_or_unselected_compensation(self):
        payload = valid_payload()
        payload["termEnd"] = "2026-07-31"
        with self.assertRaisesRegex(ValueError, "cannot be before"):
            MODULE._parse_txr_1507_draft(payload)
        payload = valid_payload()
        payload["compensation"] = {}
        with self.assertRaisesRegex(ValueError, "at least one broker-approved"):
            MODULE._parse_txr_1507_draft(payload)

    def test_draft_does_not_accept_duplicate_clients_or_malformed_fees(self):
        payload = valid_payload()
        payload["clientNames"] = ["Test Buyer", "test buyer"]
        with self.assertRaisesRegex(ValueError, "listed only once"):
            MODULE._parse_txr_1507_draft(payload)
        payload = valid_payload()
        payload["compensation"] = {"purchaseFlatFee": "five hundred"}
        with self.assertRaisesRegex(ValueError, "dollar amount"):
            MODULE._parse_txr_1507_draft(payload)

    def test_no_more_than_two_clients_and_market_area_are_required(self):
        payload = valid_payload()
        payload["clientNames"] = ["One", "Two", "Three"]
        with self.assertRaisesRegex(ValueError, "one or two"):
            MODULE._parse_txr_1507_draft(payload)
        payload = valid_payload()
        payload["marketArea"] = ""
        with self.assertRaisesRegex(ValueError, "Market area"):
            MODULE._parse_txr_1507_draft(payload)

    def test_valid_long_form_draft_is_private_and_deliberate(self):
        draft = MODULE._parse_txr_1501_draft(valid_long_payload())
        self.assertEqual(draft["client_names"], ["Test Buyer"])
        self.assertEqual(draft["agreement_data"]["payment_county"], "Collin")
        self.assertEqual(draft["agreement_data"]["purchase_percentage"], "3")
        self.assertEqual(draft["agreement_data"]["signer_plan"], "clients_and_associate")

    def test_long_form_requires_explicit_signer_plan_without_authority_attestation(self):
        payload = valid_long_payload()
        payload.pop("signerPlan")
        with self.assertRaisesRegex(ValueError, "Choose an authorized broker"):
            MODULE._parse_txr_1501_draft(payload)
        payload = valid_long_payload()
        payload["formUseAttested"] = False
        self.assertEqual(MODULE._parse_txr_1501_draft(payload)["client_names"], ["Test Buyer"])

    def test_long_form_rejects_invalid_contact_retainer_or_protection_terms(self):
        payload = valid_long_payload()
        payload["clientEmail"] = "not-an-email"
        with self.assertRaisesRegex(ValueError, "email must be valid"):
            MODULE._parse_txr_1501_draft(payload)
        payload = valid_long_payload()
        payload["retainerAmount"] = "500"
        with self.assertRaisesRegex(ValueError, "retainer"):
            MODULE._parse_txr_1501_draft(payload)
        payload = valid_long_payload()
        payload["protectionDays"] = "0"
        with self.assertRaisesRegex(ValueError, "Protection period"):
            MODULE._parse_txr_1501_draft(payload)

    def test_valid_showing_draft_is_limited_to_unrepresented_customer_intake(self):
        draft = MODULE._parse_txr_1508_draft(valid_showing_payload())
        self.assertEqual(draft["client_names"], ["Test Customer"])
        self.assertEqual(draft["agreement_data"]["other_broker_agreement"], ["no"])
        self.assertTrue(draft["agreement_data"]["unrepresented_acknowledgment"])

    def test_showing_draft_requires_each_representation_status_and_limit_acknowledgment(self):
        payload = valid_showing_payload()
        payload["otherBrokerAgreement"] = []
        with self.assertRaisesRegex(ValueError, "representation-agreement status"):
            MODULE._parse_txr_1508_draft(payload)
        payload = valid_showing_payload()
        payload["unrepresentedAcknowledgment"] = False
        with self.assertRaisesRegex(ValueError, "no-representation"):
            MODULE._parse_txr_1508_draft(payload)

    def test_showing_draft_requires_explicit_acknowledger_without_attestation(self):
        payload = valid_showing_payload()
        payload.pop("signerPlan")
        with self.assertRaisesRegex(ValueError, "broker or associate"):
            MODULE._parse_txr_1508_draft(payload)
        payload = valid_showing_payload()
        payload["formUseAttested"] = False
        self.assertEqual(MODULE._parse_txr_1508_draft(payload)["client_names"], ["Test Customer"])

    def test_notice_draft_requires_role_and_consumer_acknowledgment(self):
        draft = MODULE._parse_txr_1506_draft(valid_notice_payload())
        self.assertEqual(draft["agreement_data"]["signer_plan"], "consumers_and_associate")
        self.assertEqual(draft["agreement_data"]["consumer_role"], "buyer")
        payload = valid_notice_payload()
        payload["noticeAcknowledgment"] = False
        with self.assertRaisesRegex(ValueError, "review and acknowledge"):
            MODULE._parse_txr_1506_draft(payload)

    def test_notice_draft_requires_explicit_signer_plan_without_attestation(self):
        payload = valid_notice_payload()
        payload.pop("signerPlan")
        with self.assertRaisesRegex(ValueError, "Choose an authorized broker"):
            MODULE._parse_txr_1506_draft(payload)
        payload = valid_notice_payload()
        payload["formUseAttested"] = False
        self.assertEqual(MODULE._parse_txr_1506_draft(payload)["client_names"], ["Test Consumer"])

    def test_mineral_draft_requires_explicit_source_choices_and_stays_private(self):
        draft = MODULE._parse_txr_1905_draft(valid_mineral_payload())
        self.assertEqual(draft["agreement_data"]["undivided_interest"], "25")
        self.assertEqual(draft["agreement_data"]["surface_rights"], "waived")
        payload = valid_mineral_payload()
        payload["undividedInterest"] = ""
        with self.assertRaisesRegex(ValueError, "undivided mineral-interest percentage"):
            MODULE._parse_txr_1905_draft(payload)
        payload = valid_mineral_payload()
        payload["mineralReviewAcknowledgment"] = False
        with self.assertRaisesRegex(ValueError, "review the mineral-reservation choices"):
            MODULE._parse_txr_1905_draft(payload)

    def test_seller_financing_draft_requires_each_conditional_source_choice(self):
        draft = MODULE._parse_txr_1914_draft(valid_seller_financing_payload())
        self.assertEqual(draft["agreement_data"]["payment"]["payoff_after_months"], "180")
        self.assertEqual(draft["agreement_data"]["escrow"]["cost_paid_by"], "buyer")
        payload = valid_seller_financing_payload()
        payload["creditDocuments"] = []
        with self.assertRaisesRegex(ValueError, "credit-documentation"):
            MODULE._parse_txr_1914_draft(payload)
        payload = valid_seller_financing_payload()
        payload["thirdPartyServicer"] = ""
        with self.assertRaisesRegex(ValueError, "third-party escrow"):
            MODULE._parse_txr_1914_draft(payload)

    def test_seller_financing_ui_is_private_and_shows_only_applicable_questions(self):
        self.assertIn("Start seller-financing draft", HTML)
        self.assertIn("create_txr_1914_draft", HTML)
        self.assertIn("TXR-1914 is temporarily unavailable in the HomeOfferFlow form library", HTML)
        self.assertIn("id=\"txr1914OnePayment\"", HTML)
        self.assertIn("id=\"txr1914Installments\"", HTML)
        self.assertIn("id=\"txr1914EscrowDetails\"", HTML)

    def test_loan_assumption_draft_is_review_only_and_requires_an_assumed_loan(self):
        draft = MODULE._parse_txr_1919_draft(valid_loan_assumption_payload())
        self.assertEqual(draft["agreement_data"]["loans"]["first"]["lender"], "Example Bank")
        payload = valid_loan_assumption_payload()
        payload["firstLoanEnabled"] = False
        with self.assertRaisesRegex(ValueError, "at least one existing loan"):
            MODULE._parse_txr_1919_draft(payload)
        self.assertIn("create_txr_1919_draft", HTML)
        self.assertIn("not a lender request or signature request", HTML)
        self.assertIn("not a loan document or signature request", HTML)

    def test_agent_ui_requires_an_approved_private_source_and_saves_draft_only(self):
        self.assertIn("Start TXR-1507 draft", HTML)
        self.assertIn("approved-form check", HTML)
        self.assertIn("hofApprovedSourceStatusCopy", HTML)
        self.assertIn("Request brokerage activation", HTML)
        self.assertGreaterEqual(HTML.count("root.hofApprovedSourceStatusCopy(error)"), 5)
        self.assertIn("Source revision", HTML)
        self.assertIn("This saves a private draft only", HTML)
        self.assertIn("create_txr_1507_draft", HTML)
        self.assertIn("HomeOfferFlow library source", HTML)
        self.assertIn("/api/admin-dashboard", HTML)
        self.assertIn("Draft saved privately. It has not been sent for signature.", HTML)
        # Browser submit events clear currentTarget after an await. Keep each
        # draft flow's button reference before the network request so a saved
        # draft is not incorrectly reported as failed.
        self.assertGreaterEqual(HTML.count("const submit = event.currentTarget.querySelector('button[type=\"submit\"]');"), 3)
        self.assertNotIn("event.currentTarget.querySelector('button[type=\"submit\"]').disabled = true", HTML)
        self.assertIn('name="serviceLevel" value="full_services" required', HTML)
        self.assertNotIn('name="serviceLevel" value="full_services" checked', HTML)
        self.assertIn("Start TXR-1501 draft", HTML)
        self.assertIn("TXR-1501 is temporarily unavailable in the HomeOfferFlow form library", HTML)
        self.assertIn("create_txr_1501_draft", HTML)
        self.assertIn("Start TXR-1508 draft", HTML)
        self.assertIn("TXR-1508 is temporarily unavailable in the HomeOfferFlow form library", HTML)
        self.assertIn("create_txr_1508_draft", HTML)
        self.assertIn("no representation, no compensation, no advice", HTML)
        self.assertIn('name="signerPlan"', HTML[HTML.index('id="hof-txr1508-drafts-v1"'):])
        self.assertIn('value="associate_and_clients"', HTML[HTML.index('id="hof-txr1508-drafts-v1"'):])
        self.assertIn('value="broker_and_clients"', HTML[HTML.index('id="hof-txr1508-drafts-v1"'):])
        self.assertNotIn('name="formUseAttested"', HTML[HTML.index('id="hof-txr1508-drafts-v1"'):])
        self.assertIn("Start TXR-1506 draft", HTML)
        self.assertIn("TXR-1506 is temporarily unavailable in the HomeOfferFlow form library", HTML)
        self.assertIn("create_txr_1506_draft", HTML)
        self.assertIn("if (submit.disabled) return;", HTML)
        self.assertIn("submit.setAttribute('aria-busy', 'true')", HTML)
        self.assertIn("submit.textContent = 'Saving draft…'", HTML)
        self.assertIn("submit.textContent = 'Save private draft'", HTML)
        self.assertGreaterEqual(HTML.count("submit.setAttribute('aria-busy', 'true')"), 3)
        self.assertGreaterEqual(HTML.count("submit.textContent = 'Saving draft…'"), 3)
        self.assertIn("Start mineral addendum draft", HTML)
        self.assertIn("create_txr_1905_draft", HTML)
        self.assertIn("TXR-1905 is temporarily unavailable in the HomeOfferFlow form library", HTML)
        self.assertIn("HomeOfferFlow saves a private review PDF", HTML)

    def test_agents_can_only_view_their_own_private_draft_summaries(self):
        self.assertIn('id="hof-private-form-drafts-v1"', HTML)
        self.assertIn(".from('hof_standalone_agreements')", HTML)
        self.assertIn(".eq('agent_user_id', user.id)", HTML)
        self.assertIn(".eq('status', 'draft')", HTML)
        self.assertIn("HomeOfferFlow does not download, send, or sign them from this list.", HTML)
        self.assertIn("Preview PDF", HTML)
        self.assertIn("preview_agreement=", HTML)
        self.assertNotIn("agreement_data", HTML[HTML.index('id="hof-private-form-drafts-v1"'):])

    def test_draft_action_reuses_an_existing_authenticated_function(self):
        self.assertFalse((ROOT / "api" / "standalone-agreement.py").exists())
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("create_txr_1507_draft", backend)
        self.assertIn("create_txr_1501_draft", backend)
        self.assertIn("create_txr_1508_draft", backend)
        self.assertIn("create_txr_1506_draft", backend)
        self.assertIn("create_txr_1905_draft", backend)
        self.assertIn("_require_brokerage_txr_authorization", backend)
        self.assertIn("txr_all_agents_authorized=is.true", backend)
        self.assertIn("txr_authorization_attested_by=not.is.null", backend)
        self.assertIn("_active_brokerage_member", backend)
        self.assertIn("_render_txr_1507_draft_preview", backend)
        self.assertIn("The approved {agreement.get('form_code') or 'TXR'} source could not be loaded.", backend)
        self.assertIn('standalone-agreement-private-draft-preview.pdf', backend)
        self.assertNotIn('TXR-1507-private-draft-preview.pdf', backend)
        self.assertIn("Cache-Control", backend)

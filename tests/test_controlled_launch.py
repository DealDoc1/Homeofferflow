import base64
from io import BytesIO
from pathlib import Path
import unittest

from pypdf import PdfReader, PdfWriter

from api import fill_pdf_20_19_production_adapter as adapter


ROOT = Path(__file__).resolve().parents[1]


def configure_local_forms():
    verified = adapter.verified
    verified.BASE_DIR = str(ROOT)
    verified.MAIN_PDF = str(ROOT / "20-19_0.pdf")
    verified.FINANCING_PDF = str(ROOT / "third_party_financing_addendum.pdf")
    verified.HOA_PDF = str(ROOT / "hoa_addendum.pdf")
    verified.SALE_PDF = str(ROOT / "sale_of_other_property_addendum.pdf")
    verified.BACKUP_PDF = str(ROOT / "backup_contract_addendum_11-9.pdf")
    verified.APPRAISAL_PDF = str(ROOT / "appraisal_addendum.pdf")
    verified.APPRAISAL_PDF_ALT = verified.APPRAISAL_PDF
    verified.NON_REALTY_PDF = str(ROOT / "non_realty_items_addendum.pdf")
    verified.NON_REALTY_PDF_ALT = verified.NON_REALTY_PDF
    verified.LEAD_PDF = str(ROOT / "lead_based_paint_56-0.pdf")
    verified.LEAD_PDF_ALT = verified.LEAD_PDF


def minimal_offer(**overrides):
    offer = {
        "buyer1": "Controlled Launch Buyer",
        "buyerEmail": "buyer@example.com",
        "seller": "Controlled Launch Seller",
        "address": "1438 Whitaker Road",
        "city": "Van Alstyne",
        "county": "Grayson",
        "zip": "75495",
        "lotNumber": "1",
        "blockNumber": "A",
        "price": "500000",
        "financing": "cash",
        "loanAmount": "0",
        "earnest": "5000",
        "optionFee": "250",
        "optionDays": "7",
        "escrowAgent": "Chicago Title DFW",
        "escrowAddress": "2770 Main Street, Frisco, TX 75033",
        "titleCompany": "Chicago Title DFW",
        "titlePayer": "buyer",
        "titleAmendment": "buyer",
        "survey": "buyerNew",
        "surveyDays": "7",
        "objectionDays": "5",
        "hoa": "no",
        "sellerDisclosure": "received",
        "sellerWaterDisclosure": "received",
        "asIs": "yes",
        "closingDate": "2026-08-21",
        "possession": "funding",
        "leases": "no",
        "saleContingency": "no",
        "backupOffer": "no",
        "appraisalAddendum": "none",
        "nonRealtyItems": "no",
        "leadBasedPaint": "no",
        "yearBuilt": "2005",
        "hasBuyerAgent": "no",
    }
    offer.update(overrides)
    return offer


def one_page_pdf_base64():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return base64.b64encode(output.getvalue()).decode()


class ControlledLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_cash_packet_uses_12_page_20_19_contract(self):
        packet = adapter.fill_and_merge_20_19(minimal_offer())
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 12)

    def test_missing_title_and_escrow_details_do_not_inject_a_provider(self):
        offer = minimal_offer(
            escrowAgent="",
            escrowAddress="",
            titleCompany="",
        )
        packet = adapter.fill_and_merge_20_19(offer)
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(packet)).pages)
        self.assertNotIn("Kate Lewis Tucker", text)
        self.assertNotIn("Forgey Law Group", text)

    def test_conventional_packet_appends_two_page_financing_addendum(self):
        packet = adapter.fill_and_merge_20_19(
            minimal_offer(financing="conventional", loanAmount="400000")
        )
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 14)

    def test_verified_percentage_contribution_packet_builds(self):
        packet = adapter.fill_and_merge_20_19(
            minimal_offer(
                hasBuyerAgent="yes",
                brokerFeeType="percent",
                brokerFeePercent="3",
            )
        )
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 12)

    def test_verified_buyer_temporary_lease_packet_builds(self):
        offer = minimal_offer(
            hasBuyerAgent="yes",
            buyer2="Controlled Launch Buyer Two",
            buyer2Email="buyer2@example.com",
            possession="temporaryLease",
            buyerTemporaryLease="yes",
            buyerTemporaryLeaseStartDate="2026-08-01",
            buyerTemporaryLeaseRentPerDay="100",
            buyerTemporaryLeaseTotalRent="1400",
            buyerTemporaryLeaseDeposit="500",
            buyerTemporaryLeaseUtilitiesPaidBySeller="Water and trash.",
            buyerTemporaryLeasePetsAllowed="One dog under 40 pounds.",
            buyerTemporaryLeaseSpecialProvisions="Tenant will maintain the yard.",
            buyerTemporaryLeaseHoldoverPerDay="250",
        )
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 14)

        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        by_id = {field["api_id"]: field for field in fields}
        self.assertEqual(by_id["buyer1_signature_buyer_temp_lease"]["page"], 14)
        self.assertEqual(by_id["buyer2_signature_buyer_temp_lease"]["page"], 14)

    def test_uploaded_disclosure_is_preserved_after_main_packet(self):
        offer = minimal_offer(
            uploadedDisclosureDocs=[{
                "name": "seller-disclosure.pdf",
                "base64": one_page_pdf_base64(),
                "signaturePlacements": [{
                    "type": "buyer1_signature",
                    "page": 1,
                    "signwellX": 120,
                    "signwellY": 700,
                }],
            }]
        )
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 13)
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        uploaded = [field for field in fields if field["api_id"].startswith("uploaded_")]
        self.assertEqual(len(uploaded), 1)
        self.assertEqual(uploaded[0]["page"], 13)

    def test_unverified_paths_fail_closed(self):
        blocked_offers = [
            minimal_offer(leases="residential"),
            minimal_offer(leases="residentialLease"),
            minimal_offer(leases="fixtureLease"),
            minimal_offer(leases="naturalResource"),
            minimal_offer(leases="naturalResourceLease"),
            minimal_offer(hydrostaticTesting="yes"),
            minimal_offer(mineralReservation="yes"),
            minimal_offer(leadBasedPaintAttached="yes"),
        ]
        for offer in blocked_offers:
            with self.subTest(offer=offer):
                with self.assertRaises(adapter.UnsupportedOfferPathError):
                    adapter.validate_supported_offer(offer)

    def test_specialized_path_message_is_clear_without_internal_release_language(self):
        with self.assertRaises(adapter.UnsupportedOfferPathError) as context:
            adapter.validate_supported_offer(minimal_offer(hydrostaticTesting="yes"))
        self.assertIn("needs a dedicated Texas form packet", str(context.exception))
        self.assertNotIn("not yet available", str(context.exception))

    def test_specialized_financing_form_sources_are_discoverable_for_packet_qa(self):
        verified = adapter.verified
        self.assertEqual(verified.normalize_financing("seller financing"), "seller_financing")
        self.assertEqual(verified.normalize_financing("loan assumption"), "loan_assumption")
        self.assertTrue((ROOT / "seller_financing_addendum_26-8.pdf").is_file())
        self.assertTrue((ROOT / "loan_assumption_addendum_41-3.pdf").is_file())

    def test_seller_financing_packet_assembly_appends_the_dedicated_addendum(self):
        offer = minimal_offer(
            financing="seller financing",
            loanAmount="400000",
            sellerFinanceCreditDays="7",
            sellerFinanceCreditDocs=["credit_report", "employment"],
            sellerFinanceNoteAmount="400000",
            sellerFinanceInterestRate="6.5",
            sellerFinancePaymentType="monthly",
            sellerFinanceMonthlyPayment="2528",
            sellerFinanceTransferConsent="required",
            sellerFinanceInsurance="required",
            sellerFinanceTaxEscrow="required",
            sellerFinanceThirdPartyEscrow="no",
            sellerFinanceEscrowPaidBy="buyer",
        )
        self.assertTrue(adapter.validate_supported_offer(offer))
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 14)
        field_ids = {field["api_id"] for field in adapter.build_signwell_fields_20_19(offer, packet)[0]}
        self.assertIn("buyer1_initials_seller_financing_p1", field_ids)
        self.assertIn("buyer1_signature_seller_financing", field_ids)

    def test_loan_assumption_packet_attaches_its_dedicated_addendum_for_qa(self):
        offer = minimal_offer(
            financing="loan assumption",
            assumptionCreditDays="7",
            assumptionFirstLender="Example Credit Union",
            assumptionFirstBalance="400000",
            assumptionFirstPayment="2800",
            assumptionFirstFeeCap="1500",
            assumptionFirstRateCap="5.75",
        )
        self.assertTrue(adapter.validate_supported_offer(offer))
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 14)
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(packet)).pages[-2:])
        self.assertIn("Example Credit Union", text)
        self.assertIn("400,000", text)
        field_ids = {field["api_id"] for field in adapter.verified.build_signwell_fields(offer, packet)[0]}
        self.assertIn("buyer1_initials_loan_assumption_p1", field_ids)
        self.assertIn("buyer1_signature_loan_assumption", field_ids)

    def test_environmental_assessment_packet_attaches_its_dedicated_addendum(self):
        offer = minimal_offer(
            environmentalAssessment="yes",
            environmentalTopics=["assessment", "wetlands"],
            environmentalDays="10",
        )
        self.assertTrue(adapter.validate_supported_offer(offer))
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 13)
        text = PdfReader(BytesIO(packet)).pages[-1].extract_text() or ""
        self.assertIn("ENVIRONMENTAL ASSESSMENT", text)
        self.assertIn("10", text)
        field_ids = {field["api_id"] for field in adapter.build_signwell_fields_20_19(offer, packet)[0]}
        self.assertIn("buyer1_environmental_assessment_addendum_signature", field_ids)

    def test_guided_special_financing_ui_avoids_third_party_questions(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="thirdPartyFinancingTerms"', page)
        self.assertIn("const isThirdPartyFinancing = ['conventional', 'fha', 'va', 'usda'].includes(financingChoice);", page)
        self.assertIn("id=\"sellerFinanceCashPortion\"", page)
        self.assertIn("id=\"assumptionCashPortion\"", page)
        self.assertIn("requireField('assumptionFirstLender', 'first-lien lender', missing);", page)
        self.assertIn("['conventional', 'usda'].includes(financing)", page)

    def test_browser_launch_guard_does_not_block_released_form_paths(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        guard = page.split("function controlledLaunchUnsupportedPaths", 1)[1].split(
            "function confirmControlledLaunchSupport", 1
        )[0]
        self.assertNotIn("buyerTemporaryLease", guard)
        self.assertNotIn("sellerFinancing", guard)
        self.assertNotIn("loanAssumption", guard)
        self.assertIn("sellerTemporaryLease", guard)


if __name__ == "__main__":
    unittest.main()

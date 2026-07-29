import base64
from io import BytesIO
from pathlib import Path
import unittest

from pypdf import PdfReader, PdfWriter

from api import fill_pdf_20_19_production_adapter as adapter


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")


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

    def test_uploaded_listing_documents_keep_agent_selected_packet_order(self):
        first = one_page_pdf_base64()
        second = one_page_pdf_base64()
        offer = minimal_offer(uploadedDisclosureDocs=[
            {"name": "seller-disclosure.pdf", "type": "seller_disclosure", "base64": first},
            {"name": "survey.pdf", "type": "survey", "base64": second},
        ])
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 14)

    def test_uploaded_listing_document_ui_supports_order_type_and_removal_before_checkout(self):
        for item in (
            "Packet attachment order",
            "moveUploadedDisclosureDoc",
            "removeUploadedDisclosureDoc",
            "setUploadedDisclosureDocType",
            "Seller disclosure",
            "These listing-side PDFs will be appended after the contract packet in this exact order",
            "base64.startsWith('JVBER')",
        ):
            self.assertIn(item, INDEX_HTML)

    def test_unverified_paths_fail_closed(self):
        blocked_offers = [
            minimal_offer(leases="residential"),
            minimal_offer(leases="residentialLease"),
            minimal_offer(leases="fixtureLease"),
            minimal_offer(leases="naturalResource"),
            minimal_offer(leases="naturalResourceLease"),
            minimal_offer(financing="seller financing"),
            minimal_offer(financing="loan assumption"),
            minimal_offer(hydrostaticTesting="yes"),
            minimal_offer(environmentalAssessment="yes"),
            minimal_offer(mineralReservation="yes"),
            minimal_offer(leadBasedPaintAttached="yes"),
        ]
        for offer in blocked_offers:
            with self.subTest(offer=offer):
                with self.assertRaises(adapter.UnsupportedOfferPathError):
                    adapter.validate_supported_offer(offer)


if __name__ == "__main__":
    unittest.main()

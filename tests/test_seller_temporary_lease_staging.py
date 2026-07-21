from io import BytesIO
from pathlib import Path
import unittest

from pypdf import PdfReader

from api import fill_pdf_20_19_staging as staging
from api import fill_pdf_20_19_production_adapter as production


ROOT = Path(__file__).resolve().parents[1]


def configure_local_forms():
    staging.BASE_DIR = str(ROOT)
    staging.MAIN_PDF = str(ROOT / "20-19_0.pdf")
    staging.FINANCING_PDF = str(ROOT / "third_party_financing_addendum.pdf")
    staging.HOA_PDF = str(ROOT / "hoa_addendum.pdf")
    staging.SALE_PDF = str(ROOT / "sale_of_other_property_addendum.pdf")
    staging.BACKUP_PDF = str(ROOT / "backup_contract_addendum_11-9.pdf")
    staging.APPRAISAL_PDF = str(ROOT / "appraisal_addendum.pdf")
    staging.APPRAISAL_PDF_ALT = staging.APPRAISAL_PDF
    staging.NON_REALTY_PDF = str(ROOT / "non_realty_items_addendum.pdf")
    staging.NON_REALTY_PDF_ALT = staging.NON_REALTY_PDF
    staging.LEAD_PDF = str(ROOT / "lead_based_paint_56-0.pdf")
    staging.LEAD_PDF_ALT = staging.LEAD_PDF


def seller_temp_offer():
    return {
        "userType": "agent",
        "hasBuyerAgent": "yes",
        "buyer1": "Seller Lease Buyer One",
        "buyer2": "Seller Lease Buyer Two",
        "buyerEmail": "buyer1@example.com",
        "buyer2Email": "buyer2@example.com",
        "buyerPhone": "2143649890",
        "buyerFax": "2145550101",
        "buyerMailAddr": "721 Broderick Lane, Prosper, TX 75078",
        "seller": "Seller Lease Seller One and Seller Lease Seller Two",
        "sellerEmail": "seller@example.com",
        "sellerPhone": "9725550134",
        "sellerFax": "9725550199",
        "sellerMailAddr": "100 Seller Lane, Van Alstyne, TX 75495",
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
        "closingDate": "2026-08-15",
        "possession": "sellerTemporaryLease",
        "sellerTemporaryLease": "yes",
        "sellerTemporaryLeaseTerminationDate": "2026-08-31",
        "sellerTemporaryLeaseRentPerDay": "125",
        "sellerTemporaryLeaseDeposit": "1000",
        "sellerTemporaryLeaseUtilitiesPaidByBuyer": "Water and trash",
        "sellerTemporaryLeasePetsAllowed": "One dog under 40 pounds",
        "sellerTemporaryLeaseSpecialProvisions": "Tenant will maintain the yard and return all keys and garage remotes when possession is surrendered.",
        "sellerTemporaryLeaseHoldoverPerDay": "300",
        "saleContingency": "no",
        "backupOffer": "no",
        "appraisalAddendum": "none",
        "nonRealtyItems": "no",
        "leadBasedPaint": "no",
        "yearBuilt": "2005",
        "agentName": "Andrew Christian",
        "agentEmail": "andrew@ondemanddfw.com",
        "agentPhone": "2143649890",
        "agentLicense": "0738821",
        "agentBrokerage": "OnDemand Realty",
        "agentBrokerLicense": "9010832",
        "teamName": "The Christian Group",
    }


class SellerTemporaryLeaseStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_staging_appends_current_two_page_15_7(self):
        packet = staging.fill_and_merge(seller_temp_offer())
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 14)
        lease_text = "\n".join(page.extract_text() or "" for page in reader.pages[12:14])
        for expected in [
            "Seller Lease Buyer One and Seller Lease Buyer Two",
            "Seller Lease Seller One and Seller Lease Seller Two",
            "August 31, 2026",
            "125",
            "1,000",
            "Water and trash",
            "One dog under 40 pounds",
            "300",
            "buyer1@example.com",
            "seller@example.com",
        ]:
            self.assertIn(expected, lease_text)

    def test_staging_signwell_fields_target_landlord_lines(self):
        offer = seller_temp_offer()
        packet = staging.fill_and_merge(offer)
        fields = staging.build_signwell_fields(offer, packet)[0]
        by_id = {field["api_id"]: field for field in fields}
        self.assertEqual(by_id["buyer1_initials_seller_temp_lease_p1"]["page"], 13)
        self.assertEqual(by_id["buyer2_initials_seller_temp_lease_p1"]["page"], 13)
        self.assertEqual(by_id["buyer1_signature_seller_temp_lease"]["page"], 14)
        self.assertEqual(by_id["buyer2_signature_seller_temp_lease"]["page"], 14)
        self.assertLess(by_id["buyer1_signature_seller_temp_lease"]["x"], 200)
        self.assertLess(by_id["buyer2_signature_seller_temp_lease"]["x"], 200)
        self.assertEqual(by_id["buyer1_signature_seller_temp_lease"]["y"], 777)
        self.assertEqual(by_id["buyer2_signature_seller_temp_lease"]["y"], 845)

    def test_seller_lease_pages_shift_following_addenda_without_overlap(self):
        offer = seller_temp_offer()
        offer.update({
            "financing": "conventional",
            "loanAmount": "400000",
            "hoa": "yes",
            "hoaName": "Test Property Owners Association",
        })
        packet = staging.fill_and_merge(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 17)
        fields = staging.build_signwell_fields(offer, packet)[0]
        by_id = {field["api_id"]: field for field in fields}
        self.assertEqual(by_id["buyer1_signature_seller_temp_lease"]["page"], 16)
        self.assertEqual(by_id["buyer1_hoa_addendum_signature"]["page"], 17)

    def test_production_still_rejects_seller_temporary_lease(self):
        for updates in [
            {"sellerTemporaryLease": "yes", "possession": "funding"},
            {"sellerTemporaryLease": "no", "possession": "sellerTemporaryLease"},
            {"sellerTemporaryLease": "no", "possession": "sellerLease"},
        ]:
            offer = seller_temp_offer()
            offer.update(updates)
            with self.subTest(updates=updates):
                with self.assertRaises(production.UnsupportedOfferPathError):
                    production.validate_supported_offer(offer)


if __name__ == "__main__":
    unittest.main()

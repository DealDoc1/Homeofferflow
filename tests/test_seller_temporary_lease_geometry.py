"""Regression guards for production seller-temporary-lease field geometry.

These checks complement page-number assertions: a field can target the right
page while still being pushed into a footer, body paragraph, or the opposite
party's signature line.  The ranges below are intentionally narrow and are
derived from the visually reviewed production placement map.
"""

import unittest
from io import BytesIO
from pathlib import Path

import pdfplumber

from lib import production_adapter
from tests.test_seller_temporary_lease_staging import seller_temp_offer

ROOT = Path(__file__).resolve().parents[1]


def _configure_production_sources():
    """Point the production adapter at checked-in QA sources for local tests."""
    verified = production_adapter.verified
    verified.BASE_DIR = str(ROOT)
    verified.MAIN_PDF = str(ROOT / "20-19_0.pdf")
    verified.FINANCING_PDF = str(ROOT / "third_party_financing_addendum.pdf")
    verified.HOA_PDF = str(ROOT / "hoa_addendum.pdf")
    verified.SALE_PDF = str(ROOT / "sale_of_other_property_addendum.pdf")
    verified.BACKUP_PDF = str(ROOT / "backup_contract_addendum_11-9.pdf")
    verified.APPRAISAL_PDF = str(ROOT / "appraisal_addendum.pdf")
    verified.NON_REALTY_PDF = str(ROOT / "non_realty_items_addendum.pdf")
    verified.BUYER_TEMP_LEASE_PDF = str(ROOT / "buyer_temporary_residential_lease.pdf")


_configure_production_sources()


class SellerTemporaryLeaseGeometryTests(unittest.TestCase):
    @staticmethod
    def _fields():
        offer = seller_temp_offer()
        offer.update(
            {
                "seller1Name": "Seller Lease Seller One",
                "seller1Email": "seller1@example.com",
                "seller2Name": "Seller Lease Seller Two",
                "seller2Email": "seller2@example.com",
            }
        )
        packet = production_adapter.fill_and_merge_20_19(offer)
        return {
            field["api_id"]: field
            for field in production_adapter.build_signwell_fields_20_19(offer, packet)[0]
        }

    def test_main_execution_signatures_stay_on_the_four_execution_rows(self):
        fields = self._fields()
        expected = {
            "buyer1_main_contract_signature": (1, 10, 115, 433),
            "buyer2_main_contract_signature": (2, 10, 115, 568),
            "seller1_main_contract_signature": (3, 10, 420, 433),
            "seller2_main_contract_signature": (4, 10, 420, 568),
        }
        for api_id, (recipient_id, page, x, y) in expected.items():
            field = fields[api_id]
            self.assertEqual(field["recipient_id"], str(recipient_id))
            self.assertEqual(field["page"], page)
            self.assertEqual((field["x"], field["y"]), (x, y))
            self.assertEqual((field["width"], field["height"]), (145, 20))

    def test_lease_execution_signatures_stay_on_landlord_and_tenant_rows(self):
        fields = self._fields()
        expected = {
            "buyer1_signature_seller_temp_lease": (1, 78, 777),
            "buyer2_signature_seller_temp_lease": (2, 78, 845),
            "seller1_signature_seller_temp_lease": (3, 440, 777),
            "seller2_signature_seller_temp_lease": (4, 440, 845),
        }
        for api_id, (recipient_id, x, y) in expected.items():
            field = fields[api_id]
            self.assertEqual(field["recipient_id"], str(recipient_id))
            self.assertEqual(field["page"], 14)
            self.assertEqual((field["x"], field["y"]), (x, y))
            self.assertEqual((field["width"], field["height"]), (145, 20))
            self.assertGreaterEqual(field["x"], 60)
            self.assertLessEqual(field["x"] + field["width"], 600)
            self.assertGreaterEqual(field["y"], 740)
            self.assertLessEqual(field["y"] + field["height"], 880)

    def test_lease_initials_stay_on_first_lease_page(self):
        fields = self._fields()
        for api_id in (
            "buyer1_initials_seller_temp_lease_p1",
            "buyer2_initials_seller_temp_lease_p1",
            "seller1_initials_seller_temp_lease_p1",
            "seller2_initials_seller_temp_lease_p1",
        ):
            field = fields[api_id]
            self.assertEqual(field["page"], 13)
            self.assertEqual(field["y"], 1004)
            self.assertEqual((field["width"], field["height"]), (24, 10))
            self.assertGreaterEqual(field["x"], 280)
            self.assertLessEqual(field["x"] + field["width"], 550)

    def test_buyer_broker_contact_values_stay_on_their_named_rows(self):
        """Page 11 must not shift the buyer-broker block up by one row."""
        offer = seller_temp_offer()
        offer.update(
            {
                "seller1Name": "Seller Lease Seller One",
                "seller1Email": "seller1@example.com",
                "seller2Name": "Seller Lease Seller Two",
                "seller2Email": "seller2@example.com",
            }
        )
        packet = production_adapter.fill_and_merge_20_19(offer)
        with pdfplumber.open(BytesIO(packet)) as document:
            words = document.pages[10].extract_words()

        def top_for(text):
            matches = [
                word["top"]
                for word in words
                if word["text"] == text and word["x0"] >= 100
            ]
            self.assertTrue(matches, f"Expected rendered value {text!r} on page 11")
            return matches[0]

        rows = {
            "OnDemand": (275, 295),
            "9010832": (320, 335),
            "Andrew": (335, 350),
            "The": (350, 365),
            "andrew@ondemanddfw.com": (365, 380),
            "2143649890": (380, 395),
        }
        for text, (minimum, maximum) in rows.items():
            top = top_for(text)
            self.assertGreaterEqual(top, minimum, text)
            self.assertLessEqual(top, maximum, text)


if __name__ == "__main__":
    unittest.main()

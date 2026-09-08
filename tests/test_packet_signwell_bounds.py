"""Production packet bounds checks for every emitted SignWell widget.

Standalone form geometry is covered in ``test_txr_signer_geometry``.  This
suite covers the assembled offer packet as well, where page offsets and
conditionally appended forms can otherwise put a valid relative field on the
wrong final page.
"""

import unittest
from io import BytesIO

from pypdf import PdfReader

from lib import production_adapter
from tests.test_controlled_launch import (
    configure_local_forms,
    fixture_lease_offer,
    minimal_offer,
    residential_lease_offer,
)


SIGNWELL_POINTS_PER_PDF_POINT = 96 / 72


def _overlap(left, right):
    if left["page"] != right["page"] or left["recipient_id"] != right["recipient_id"]:
        return False
    return not (
        left["x"] + left["width"] <= right["x"]
        or right["x"] + right["width"] <= left["x"]
        or left["y"] + left["height"] <= right["y"]
        or right["y"] + right["height"] <= left["y"]
    )


class ProductionPacketSignWellBoundsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    @staticmethod
    def _seller_temporary_lease_offer():
        return minimal_offer(
            buyer2="Second Buyer",
            buyer2Email="second@example.com",
            seller1Name="Seller One",
            seller1Email="seller1@example.com",
            seller2Name="Seller Two",
            seller2Email="seller2@example.com",
            possession="sellerTemporaryLease",
            sellerTemporaryLease="yes",
            sellerTemporaryLeaseTerminationDate="2026-08-31",
            sellerTemporaryLeaseRentPerDay="125",
            sellerTemporaryLeaseDeposit="1000",
            sellerTemporaryLeaseUtilitiesPaidByBuyer="Water and trash",
            sellerTemporaryLeasePetsAllowed="No pets",
            sellerTemporaryLeaseSpecialProvisions="Tenant will return all keys at possession.",
            sellerTemporaryLeaseHoldoverPerDay="300",
        )

    def test_every_emitted_widget_stays_on_its_assembled_page(self):
        cases = {
            "base_offer": minimal_offer(),
            "seller_temporary_lease": self._seller_temporary_lease_offer(),
            "paragraph4_residential": residential_lease_offer(),
            "paragraph4_fixture": fixture_lease_offer(),
        }
        for name, offer in cases.items():
            with self.subTest(packet=name):
                packet = production_adapter.fill_and_merge_20_19(offer)
                pages = PdfReader(BytesIO(packet)).pages
                fields = production_adapter.build_signwell_fields_20_19(offer, packet)[0]
                self.assertTrue(fields)
                self.assertEqual(len({field["api_id"] for field in fields}), len(fields))

                for field in fields:
                    self.assertIn(field["page"], range(1, len(pages) + 1), field["api_id"])
                    page = pages[field["page"] - 1]
                    page_width = float(page.mediabox.width) * SIGNWELL_POINTS_PER_PDF_POINT
                    page_height = float(page.mediabox.height) * SIGNWELL_POINTS_PER_PDF_POINT
                    self.assertGreaterEqual(field["x"], 0, field["api_id"])
                    self.assertGreaterEqual(field["y"], 0, field["api_id"])
                    self.assertGreater(field["width"], 0, field["api_id"])
                    self.assertGreater(field["height"], 0, field["api_id"])
                    self.assertLessEqual(field["x"] + field["width"], page_width, field["api_id"])
                    self.assertLessEqual(field["y"] + field["height"], page_height, field["api_id"])

                for index, field in enumerate(fields):
                    for other in fields[index + 1:]:
                        self.assertFalse(
                            _overlap(field, other),
                            f"{name} overlaps {field['api_id']} and {other['api_id']}",
                        )


if __name__ == "__main__":
    unittest.main()

"""Source-calibrated execution widgets for the supplied seller disclosures."""

import unittest

from lib.trec_seller_disclosure import build_signwell_fields


class TrecSellerDisclosureSignerGeometryTests(unittest.TestCase):
    def test_seller_and_buyer_widgets_stay_on_the_execution_rows(self):
        cases = (
            ("TREC-55-1", 4, "trec551", 749, 868, 775, 894),
            ("TREC-61-0", 2, "trec610", 782, 858, 808, 884),
        )
        data = {"seller_names": ["Seller One", "Seller Two"], "buyer_names": ["Buyer One", "Buyer Two"]}
        for form_code, page, prefix, seller_y, buyer_y, seller_bottom, buyer_bottom in cases:
            with self.subTest(form_code=form_code):
                fields = {item["api_id"]: item for item in build_signwell_fields(form_code, data)[0]}
                self.assertEqual(len(fields), 8)
                for party, row_y, row_bottom in (("seller", seller_y, seller_bottom), ("buyer", buyer_y, buyer_bottom)):
                    for index in (1, 2):
                        signature = fields[f"{prefix}_{party}{index}_signature_p{page}"]
                        date = fields[f"{prefix}_{party}{index}_date_p{page}"]
                        self.assertEqual(signature["y"], row_y)
                        self.assertEqual(date["y"], row_y)
                        self.assertEqual(signature["y"] + signature["height"], row_bottom)
                        self.assertEqual(date["y"] + date["height"], row_bottom)
                        self.assertGreater(date["x"], signature["x"])
                        self.assertEqual(signature["recipient_id"], date["recipient_id"])

    def test_listing_stage_can_send_to_sellers_before_a_buyer_is_known(self):
        fields = build_signwell_fields("TREC-55-1", {"seller_names": ["Seller One"], "buyer_names": []})[0]
        self.assertEqual([field["recipient_id"] for field in fields], ["1", "1"])
        self.assertTrue(all("seller1" in field["api_id"] for field in fields))

    def test_rejects_invalid_party_counts(self):
        with self.assertRaises(ValueError):
            build_signwell_fields("TREC-55-1", {"seller_names": [], "buyer_names": []})
        with self.assertRaises(ValueError):
            build_signwell_fields("TREC-61-0", {"seller_names": ["One"], "buyer_names": ["A", "B", "C"]})


if __name__ == "__main__":
    unittest.main()

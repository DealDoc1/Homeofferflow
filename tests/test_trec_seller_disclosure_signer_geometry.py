"""Source-calibrated execution widgets for the supplied seller disclosures."""

import unittest

from lib.trec_seller_disclosure import build_signwell_fields


class TrecSellerDisclosureSignerGeometryTests(unittest.TestCase):
    def test_seller_and_buyer_widgets_stay_on_the_execution_rows(self):
        cases = (
            ("TREC-55-1", 4, "trec551", 749, 877, 775, 903),
            ("TREC-61-0", 2, "trec610", 799, 862, 825, 888),
        )
        data = {"seller_names": ["Seller One", "Seller Two"], "buyer_names": ["Buyer One", "Buyer Two"]}
        for form_code, page, prefix, seller_y, buyer_y, seller_bottom, buyer_bottom in cases:
            with self.subTest(form_code=form_code):
                fields = {item["api_id"]: item for item in build_signwell_fields(form_code, data)[0]}
                self.assertEqual(len([f for f in fields.values() if f["type"] != "initials"]), 8)
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
                        # Source horizontal rules, independently measured.
                        rule = (208.31 if party == 'seller' else 112.46) if form_code == 'TREC-55-1' else (171.55 if party == 'seller' else 124.24)
                        bottom = 792 - row_bottom * .75
                        self.assertGreater(bottom, rule + 1)
                        self.assertLess(bottom, rule + 4)
                        if form_code == 'TREC-61-0':
                            self.assertLessEqual((date['x'] + date['width']) * .75, 301 if index == 1 else 570)
                            if party == 'seller':
                                self.assertLessEqual(792 - row_y * .75, 193)

    def test_listing_stage_can_send_to_sellers_before_a_buyer_is_known(self):
        fields = build_signwell_fields("TREC-55-1", {"seller_names": ["Seller One"], "buyer_names": []})[0]
        self.assertEqual([field["recipient_id"] for field in fields], ["1", "1"])
        self.assertTrue(all("seller1" in field["api_id"] for field in fields))

    def test_rejects_invalid_party_counts(self):
        with self.assertRaises(ValueError):
            build_signwell_fields("TREC-55-1", {"seller_names": [], "buyer_names": []})
        with self.assertRaises(ValueError):
            build_signwell_fields("TREC-61-0", {"seller_names": ["One"], "buyer_names": ["A", "B", "C"]})

    def test_appended_water_disclosure_uses_packet_page_numbers(self):
        fields = build_signwell_fields(
            "TREC-61-0", {"seller_names": ["Seller One"], "buyer_names": []}, page_offset=4
        )[0]
        self.assertEqual({field["page"] for field in fields}, {5, 6})
        self.assertTrue(all(field["api_id"].endswith("_p" + str(field["page"])) for field in fields))

    def test_rejects_an_invalid_packet_page_offset(self):
        with self.assertRaises(ValueError):
            build_signwell_fields("TREC-55-1", {"seller_names": ["Seller One"]}, page_offset=-1)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import render_txr_signwell_map_review as review


class TxrSignwellMapReviewTests(unittest.TestCase):
    def test_signwell_rect_conversion_uses_top_origin_and_letter_scale(self):
        self.assertEqual(
            review.signwell_rect_to_pdf({"x": 96, "y": 96, "width": 96, "height": 32}),
            (72.0, 696.0, 72.0, 24.0),
        )

    def test_review_map_includes_each_supported_form_and_completion_type(self):
        maps = review.review_field_sets()
        self.assertEqual(set(maps), {"TXR1501", "TXR1506", "TXR1507", "TXR1508"})
        for code, fields in maps.items():
            with self.subTest(code=code):
                self.assertTrue(fields)
                self.assertTrue({field["type"] for field in fields}.issubset(review.TYPE_COLORS))
                expected_type = "initials" if code == "TXR1508" else "signature"
                self.assertIn(expected_type, {field["type"] for field in fields})

    def test_txr1508_review_overlay_targets_the_three_acknowledgement_rows(self):
        fields = {field["api_id"]: field for field in review.review_field_sets()["TXR1508"]}
        self.assertEqual(fields["txr1508_agent_initials_p1"]["page"], 1)
        self.assertEqual(fields["txr1508_client1_initials_p1"]["y"], 716)
        self.assertEqual(fields["txr1508_client2_initials_p1"]["y"], 774)

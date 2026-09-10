import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "golden_packet_rendering",
    ROOT / "scripts" / "check_golden_packet_rendering.py",
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class GoldenRenderGeometryTests(unittest.TestCase):
    def test_coordinate_shift_fails_even_when_page_image_contract_is_unchanged(self):
        page = {"width": 612, "height": 792, "layout": "A" * 1024}
        baseline = {
            "version": 1,
            "max_width": 612,
            "scenarios": {
                "cash_single": {
                    "page_count": 1,
                    "field_ids": ["buyer_signature"],
                    "field_geometry": [{
                        "api_id": "buyer_signature", "type": "signature", "page": 1,
                        "x": 100, "y": 200, "width": 145, "height": 20,
                        "recipient_id": "1", "required": True,
                    }],
                    "pages": [page],
                }
            },
        }
        shifted = {
            **baseline,
            "scenarios": {
                "cash_single": {
                    **baseline["scenarios"]["cash_single"],
                    "field_geometry": [{
                        **baseline["scenarios"]["cash_single"]["field_geometry"][0],
                        "x": 101,
                    }],
                }
            },
        }

        matches, reason = CHECKER._cross_platform_visual_match(shifted, baseline)

        self.assertFalse(matches)
        self.assertEqual(reason, "cash_single: signing field placement changed")


if __name__ == "__main__":
    unittest.main()

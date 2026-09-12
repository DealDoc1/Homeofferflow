from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import render_txr_signwell_map_review as review


BASELINE = ROOT / "docs" / "TXR_SIGNING_MAP_BASELINE.txt"


def geometry_line(field):
    return "|".join(
        str(value)
        for value in (
            field["api_id"], field["page"], field["type"],
            field["recipient_id"], field["x"], field["y"],
            field["width"], field["height"],
        )
    )


class TxrSigningMapBaselineTests(unittest.TestCase):
    def test_every_current_map_matches_the_source_calibrated_baseline(self):
        expected = {
            line.strip()
            for line in BASELINE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }
        actual = {
            geometry_line(field)
            for fields in review.review_field_sets().values()
            for field in fields
        }
        self.assertSetEqual(actual, expected)

    def test_baseline_requires_an_explicit_source_and_provider_review(self):
        instructions = BASELINE.read_text(encoding="utf-8")
        self.assertIn("source-calibrated map review", instructions)
        self.assertIn("completed provider-PDF evidence", instructions)


if __name__ == "__main__":
    unittest.main()

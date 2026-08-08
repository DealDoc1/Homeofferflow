from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_restricted_source_preflight_tracker_reconciliation_2026_08_08.sql").read_text(
    encoding="utf-8"
)


class RestrictedSourcePreflightTrackerTests(unittest.TestCase):
    def test_tracker_keeps_four_forms_gated_after_preflight(self):
        for slug in (
            "txr-1501-long-buyer-tenant-representation",
            "txr-1506-general-information-notice",
            "txr-1507-short-buyer-tenant-representation",
            "txr-1508-unrepresented-showing",
        ):
            self.assertIn(f"'{slug}'", SQL)
        self.assertIn("completed-signature QA remain incomplete", SQL)
        self.assertIn("without enabling signing", SQL)


if __name__ == "__main__":
    unittest.main()

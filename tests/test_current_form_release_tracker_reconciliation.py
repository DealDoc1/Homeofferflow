import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECONCILIATION = (
    ROOT / "supabase" / "homeofferflow_reconcile_current_form_release_2026_09_12.sql"
).read_text(encoding="utf-8")
ADMIN_API = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")


class CurrentFormReleaseTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_does_not_label_released_form_paths_as_blocked(self):
        expected = {
            "txr-1501-long-buyer-tenant-representation": "TXR-1501",
            "txr-1506-general-information-notice": "TXR-1506",
            "txr-1507-short-buyer-tenant-representation": "TXR-1507",
            "txr-1508-unrepresented-showing": "TXR-1508",
            "seller-financing": "TXR-1914",
            "loan-assumption": "TXR-1919",
            "environmental-assessment-addendum": "TXR-1917",
            "mineral-reservation-addendum": "TXR-1905",
        }
        self.assertIn("status = 'in_progress'", RECONCILIATION)
        self.assertIn("environment = 'staging'", RECONCILIATION)
        self.assertIn("qa_status = 'partial'", RECONCILIATION)
        for slug, form_code in expected.items():
            self.assertIn(f"'{slug}'", RECONCILIATION)
            self.assertIn(f'"{form_code}"', ADMIN_API)

    def test_tracker_distinguishes_staged_code_from_provider_pdf_verification(self):
        self.assertIn("staged on main", RECONCILIATION)
        self.assertIn("completed provider-rendered packet", RECONCILIATION)
        self.assertNotIn("status = 'production'", RECONCILIATION)


if __name__ == "__main__":
    unittest.main()

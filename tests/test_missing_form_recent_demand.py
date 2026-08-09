import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_dashboard", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MissingFormRecentDemandTests(unittest.TestCase):
    def test_recent_demand_normalizes_codes_and_excludes_old_requests(self):
        recent = MODULE._missing_form_request_recent_code_counts([
            {"issue_type": "missing_addendum", "message": "Need TXR 1507", "created_at": "2099-01-02T00:00:00Z"},
            {"issue_type": "missing_addendum", "message": "Need TREC 20-8", "created_at": "2099-01-02T00:00:00Z"},
            {"issue_type": "missing_addendum", "message": "Need TXR-1507", "created_at": "2020-01-01T00:00:00Z"},
        ], days=30)
        self.assertEqual(recent, {"TREC-20-8": 1, "TXR-1507": 1})

    def test_priority_boosts_recent_demand_and_returns_ranked_safe_rows(self):
        priority = MODULE._missing_form_request_priority([
            {"issue_type": "missing_addendum", "message": "Need TXR-1501", "created_at": "2020-01-01T00:00:00Z"},
            {"issue_type": "missing_addendum", "message": "Need TXR-1501", "created_at": "2020-01-01T00:00:00Z"},
            {"issue_type": "missing_addendum", "message": "Need TREC 20-8", "created_at": "2099-01-02T00:00:00Z"},
        ], recent_days=30)
        self.assertEqual(priority[0], {"code": "TREC-20-8", "total": 1, "recent": 1, "score": 3, "rank": 1})
        self.assertEqual(priority[1], {"code": "TXR-1501", "total": 2, "recent": 0, "score": 2, "rank": 2})


if __name__ == "__main__":
    unittest.main()

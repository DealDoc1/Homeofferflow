from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_post_reset_release_tracker_reconciliation_2026_09_22.sql"
).read_text(encoding="utf-8")


class PostResetReleaseTrackerReconciliationTests(unittest.TestCase):
    def test_records_exact_verified_release_boundary(self):
        self.assertIn("prod-2026-09-22-agent-conversion-bundle", SQL)
        self.assertIn("6ba8ae7c1465bda11c499a2eb262f8b3b4320b34", SQL)
        self.assertIn("dpl_C7SiC4BRwcsuAZjjEcLbE87LB4Ro", SQL)
        self.assertIn("35707699574", SQL)
        self.assertIn("2,408-test suite", SQL)

    def test_closes_only_provider_verified_form_release_rows(self):
        for slug in (
            "txr-1501-long-buyer-tenant-representation",
            "txr-1507-short-buyer-tenant-representation",
            "seller-financing",
            "loan-assumption",
            "environmental-assessment-addendum",
            "mineral-reservation-addendum",
        ):
            self.assertIn(f"'{slug}'", SQL)

        self.assertIn("compact provider QA 4ec37d4c", SQL)
        self.assertIn("status = 'production'", SQL)
        self.assertIn("qa_status = 'passed'", SQL)

    def test_preserves_remaining_completed_provider_qa_as_partial(self):
        for slug in (
            "txr-1506-general-information-notice",
            "txr-1508-unrepresented-showing",
            "paragraph4-residential-lease",
            "paragraph4-fixture-lease",
            "hydrostatic-addendum",
        ):
            self.assertIn(f"when '{slug}'", SQL)

        self.assertIn("qa_status = 'partial'", SQL)
        self.assertIn("historical pre-correction packet remains failure evidence", SQL)
        self.assertNotIn("delete from", SQL.lower())

    def test_keeps_native_app_spend_evidence_led(self):
        self.assertIn("where slug = 'mobile-app'", SQL)
        self.assertIn("separate native iOS or Android app has not been justified or funded", SQL)
        self.assertIn("before spending on a separate native application", SQL)


if __name__ == "__main__":
    unittest.main()

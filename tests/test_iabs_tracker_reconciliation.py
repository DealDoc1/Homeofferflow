from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_iabs_tracker_reconciliation.sql").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "homeofferflow_agent_iabs_profile.sql").read_text(encoding="utf-8")


class IabsTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_marks_the_live_iabs_feature_as_optional_and_passed(self):
        self.assertIn("'agent-iabs-profile'", SQL)
        self.assertIn("'production'", SQL)
        self.assertIn("'passed'", SQL)
        self.assertIn("'automatic_attachment', false", SQL)
        self.assertIn("'buyer_signature_fields', false", SQL)
        self.assertIn("on conflict (slug) do update", SQL.lower())

    def test_tracker_entry_matches_private_profile_and_optional_append_contract(self):
        self.assertIn("document_type in ('iabs')", MIGRATION)
        self.assertIn("It is never attached automatically.", HTML)
        self.assertIn("Include my IABS?", HTML)
        self.assertIn("needsBuyerSignature: false", HTML)
        self.assertIn("needsBuyerInitials: false", HTML)


if __name__ == "__main__":
    unittest.main()

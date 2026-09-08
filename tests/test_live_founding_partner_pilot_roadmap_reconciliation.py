from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_reconcile_live_founding_partner_pilot.sql").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "migrations" / "20260907140000_reconcile_live_founding_partner_pilot.sql").read_text(encoding="utf-8")


class LiveFoundingPartnerPilotRoadmapReconciliationTests(unittest.TestCase):
    def test_records_the_live_lifecycle_without_claiming_partner_sales(self):
        for source in (SQL, MIGRATION):
            self.assertIn("where slug = 'founding-partner-pilot'", source)
            self.assertIn("status = 'in_progress'", source)
            self.assertIn("environment = 'production'", source)
            self.assertIn("qa_status = 'partial'", source)
            self.assertIn("Stripe checkout, secure onboarding, and SignWell agreement lifecycle", source)
            self.assertIn("There are no paid partner placements activated yet", source)
            self.assertIn("agreement-confirmed directory activation", source)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_ai_feedback_rls_hardening.sql").read_text(encoding="utf-8")


class AiFeedbackRlsHardeningTests(unittest.TestCase):
    def test_private_tables_are_authenticated_owner_scoped_and_minimally_granted(self):
        self.assertIn("for insert to authenticated", MIGRATION)
        self.assertIn("for select to authenticated", MIGRATION)
        self.assertIn("(select auth.uid()) = user_id", MIGRATION)
        self.assertIn("revoke all on table public.hof_ai_offer_reviews from anon, authenticated", MIGRATION)
        self.assertIn("revoke all on table public.hof_feedback from anon, authenticated", MIGRATION)
        self.assertIn("grant select, insert on table public.hof_ai_offer_reviews to authenticated", MIGRATION)
        self.assertIn("grant select, insert on table public.hof_feedback to authenticated", MIGRATION)
        self.assertNotIn("to public", MIGRATION)


if __name__ == "__main__":
    unittest.main()

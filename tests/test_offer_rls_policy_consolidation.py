import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_offer_rls_policy_consolidation.sql").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class OfferRlsPolicyConsolidationTests(unittest.TestCase):
    def test_only_duplicate_legacy_public_offer_policies_are_removed(self):
        for policy in (
            '"users can insert own offers"',
            '"hof_offers own read"',
            '"users can view own offers"',
            '"hof_offers own update"',
            '"users can update own offers"',
        ):
            self.assertIn(f"drop policy if exists {policy} on public.hof_offers", MIGRATION)
        self.assertNotIn('"Users can insert their own offers"', MIGRATION)
        self.assertNotIn('"Users can view their own offers"', MIGRATION)
        self.assertNotIn('"Users can update their own offers"', MIGRATION)

    def test_browser_offer_saves_require_an_authenticated_user(self):
        self.assertIn("const user = hofAuth.session?.user", HTML)
        self.assertIn("if (!client || !user) return null;", HTML)


if __name__ == "__main__":
    unittest.main()

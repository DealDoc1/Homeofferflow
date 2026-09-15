import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text()
MIGRATION = (ROOT / "supabase/migrations/20260915103000_canonical_agent_profile_aliases.sql").read_text()


class CanonicalAgentProfileAliasesTests(unittest.TestCase):
    def test_alias_table_is_private_and_links_to_a_canonical_profile(self):
        self.assertIn("create table if not exists public.hof_agent_profile_aliases", MIGRATION)
        self.assertIn("canonical_user_id uuid not null references public.hof_agent_profiles(user_id)", MIGRATION)
        self.assertIn("alter table public.hof_agent_profile_aliases enable row level security", MIGRATION)
        self.assertIn("revoke all on table public.hof_agent_profile_aliases from anon, authenticated", MIGRATION)
        self.assertIn("grant select on table public.hof_agent_profile_aliases to authenticated", MIGRATION)
        self.assertIn("(select auth.uid()) = login_user_id", MIGRATION)

    def test_linked_sign_in_can_read_and_update_only_its_canonical_profile(self):
        self.assertIn('policy "hof_agent_profiles linked profile read"', MIGRATION)
        self.assertIn('policy "hof_agent_profiles linked profile update"', MIGRATION)
        self.assertIn("alias.login_user_id = (select auth.uid())", MIGRATION)
        self.assertIn("alias.canonical_user_id = hof_agent_profiles.user_id", MIGRATION)
        self.assertIn("with check (exists", MIGRATION)

    def test_client_resolves_alias_before_loading_or_saving_agent_defaults(self):
        self.assertIn("root.hofResolveAgentProfileOwner", HTML)
        self.assertIn(".from('hof_agent_profile_aliases')", HTML)
        self.assertIn("profileOwnerUserId = await window.hofResolveAgentProfileOwner(client, user)", HTML)
        self.assertIn(".eq('user_id', profileOwnerUserId).maybeSingle()", HTML)
        self.assertIn(".update(payload).eq('user_id', profileOwnerUserId)", HTML)


if __name__ == "__main__":
    unittest.main()

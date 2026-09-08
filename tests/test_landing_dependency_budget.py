from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LandingDependencyBudgetTests(unittest.TestCase):
    def test_primary_landing_only_loads_the_client_runtime_it_uses(self):
        """Keep account and packet-editor libraries out of the first public render."""
        self.assertIn('<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin />', HTML)
        self.assertNotIn('<script defer src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>', HTML)
        self.assertIn("SUPABASE_BROWSER_LIBRARY_URL = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2'", HTML)
        self.assertIn('function ensureSupabaseLibrary()', HTML)
        self.assertIn('async function ensureSupabaseClient()', HTML)
        self.assertIn("if (hasSupabaseSessionHint() || hasSupabaseAuthCallback()) initSupabaseAuth();", HTML)
        self.assertIn("setAuthStatus('Connecting secure sign-in…');", HTML)
        self.assertNotIn('https://js.stripe.com/v3/', HTML)
        self.assertNotIn('cdnjs.cloudflare.com/ajax/libs/pdf-lib/', HTML)


if __name__ == "__main__":
    unittest.main()

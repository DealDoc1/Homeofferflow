import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AuthRedirectTests(unittest.TestCase):
    def test_magic_link_returns_to_the_current_deployment(self):
        self.assertIn(
            "`${window.location.origin}${window.location.pathname}`",
            HTML,
        )
        self.assertIn("emailRedirectTo: SUPABASE_REDIRECT_URL", HTML)

    def test_non_web_context_keeps_the_production_fallback(self):
        self.assertIn(
            ": 'https://www.homeofferflow.com/';",
            HTML,
        )

    def test_redirect_does_not_preserve_query_or_hash_data(self):
        redirect_start = HTML.index("const SUPABASE_REDIRECT_URL")
        redirect_end = HTML.index("const HOF_ADMIN_EMAILS", redirect_start)
        redirect_config = HTML[redirect_start:redirect_end]

        self.assertNotIn("window.location.search", redirect_config)
        self.assertNotIn("window.location.hash", redirect_config)


if __name__ == "__main__":
    unittest.main()

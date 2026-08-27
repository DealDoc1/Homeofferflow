import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class MagicLinkCanonicalRedirectTests(unittest.TestCase):
    def test_hosted_magic_links_return_to_the_canonical_app(self):
        self.assertIn("const HOF_CANONICAL_ORIGIN = 'https://www.homeofferflow.com';", HTML)
        self.assertIn("const HOF_IS_LOCAL_ORIGIN", HTML)
        self.assertIn("const HOF_IS_TXR_QA_PREVIEW", HTML)
        self.assertIn("new URLSearchParams(window.location.search).get('txr_qa') === '1'", HTML)
        self.assertIn("(HOF_IS_LOCAL_ORIGIN || HOF_IS_TXR_QA_PREVIEW)", HTML)
        self.assertIn("`${HOF_CANONICAL_ORIGIN}${window.location.pathname}`", HTML)

    def test_local_development_keeps_its_own_return_url(self):
        self.assertIn("/^(localhost|127\\.0\\.0\\.1)(?::\\d+)?$/i", HTML)
        self.assertIn("(HOF_IS_LOCAL_ORIGIN || HOF_IS_TXR_QA_PREVIEW) && ['http:', 'https:'].includes(window.location.protocol)", HTML)


if __name__ == "__main__":
    unittest.main()

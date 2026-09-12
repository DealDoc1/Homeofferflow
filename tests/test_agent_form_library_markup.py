import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "texas-agent-form-library.html").read_text(encoding="utf-8")


class AgentFormLibraryMarkupTests(unittest.TestCase):
    def test_shared_coverage_script_stays_inside_the_document(self):
        self.assertLess(
            HTML.index('id="hof-form-library-scope-copy-v1"'),
            HTML.rindex("</body>"),
        )
        self.assertNotIn("</html>\n<script", HTML)

    def test_campaign_link_uses_html_escaped_query_separators(self):
        self.assertIn(
            "?utm_source=agent_form_library&amp;utm_medium=guide&amp;utm_campaign=agent_acquisition",
            HTML,
        )

    def test_customer_copy_uses_plain_transaction_language(self):
        self.assertIn("You choose the right document", HTML)
        self.assertIn("Clear next steps", HTML)
        self.assertNotIn("A release does not silently select", HTML)
        self.assertNotIn("Released TXR relationship", HTML)

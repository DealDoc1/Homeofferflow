import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = (ROOT / "agents.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")
INVESTORS = (ROOT / "investors.html").read_text(encoding="utf-8")
BUYERS = (ROOT / "buyers.html").read_text(encoding="utf-8")
PARTNERS = (ROOT / "partners.html").read_text(encoding="utf-8")
DIRECTORY = (ROOT / "directory.html").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden_depth = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth and data.strip():
            self.text.append(data.strip())


def visible_text(html):
    parser = _VisibleText()
    parser.feed(html)
    return " ".join(parser.text)


class LowNoisePublicPageTests(unittest.TestCase):
    def test_agent_hero_starts_with_the_single_transaction_decision(self):
        hero = AGENTS.split('<section class="grid" id="transaction-start"', 1)[0]
        self.assertNotIn('class="button"', hero)
        self.assertNotIn('data-agent-cta-path=', hero)
        selector_start = AGENTS.index('<section class="grid" id="transaction-start"')
        selector_end = AGENTS.index('</section>', selector_start)
        selector = AGENTS[selector_start:selector_end]
        self.assertEqual(selector.count('data-agent-cta-path='), 4)

    def test_seller_hero_has_one_primary_action_and_one_comparison_path(self):
        hero = SELLERS.split('<section aria-labelledby="seller-question-one"', 1)[0]
        self.assertIn('>Get my free seller plan<', hero)
        self.assertIn('>Compare support paths<', hero)
        self.assertIn('Get your free seller plan immediately—no payment or commitment.', hero)
        self.assertNotIn('This is an intake—not checkout or a service order.', hero)
        self.assertEqual(hero.count('class="button"'), 1)
        self.assertEqual(hero.count('class="button secondary"'), 1)
        self.assertNotIn('Start where you are', hero)
        self.assertNotIn('No-surprises next steps', SELLERS)

    def test_seller_question_one_uses_concise_reassurance_without_repeating_legal_operations(self):
        question_start = SELLERS.index('<section aria-labelledby="seller-question-one"')
        question_end = SELLERS.index('<section id="paths">', question_start)
        question = SELLERS[question_start:question_end]
        self.assertIn('You can change direction anytime—no payment or commitment.', question)
        self.assertNotIn('no choice creates a listing, service order, or payment', question)

    def test_homepage_seller_path_does_not_use_unfinished_product_language(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('Start with your address and email.', homepage)
        self.assertNotIn('is being built as a separate seller pathway', homepage)

    def test_investor_landing_uses_saved_work_language(self):
        self.assertIn('Resume saved work or duplicate prior offer terms', INVESTORS)
        self.assertIn('saved-work recovery', INVESTORS)
        self.assertNotIn('Resume a draft or duplicate prior offer terms', INVESTORS)
        self.assertNotIn('draft recovery', INVESTORS)

    def test_public_landing_copy_uses_customer_actions_not_internal_workflow_language(self):
        pages = {
            "buyers": BUYERS,
            "sellers": SELLERS,
            "agents": AGENTS,
            "investors": INVESTORS,
            "partners": PARTNERS,
            "directory": DIRECTORY,
        }
        for page, html in pages.items():
            with self.subTest(page=page):
                self.assertNotIn("workflow", visible_text(html).lower())

    def test_homepage_acquisition_copy_uses_the_same_plain_language_standard(self):
        start = INDEX.index("<nav")
        end = INDEX.index("</footer>", start) + len("</footer>")
        homepage = visible_text(INDEX[start:end]).lower()
        self.assertNotIn("workflow", homepage)
        self.assertIn("guided texas paths", homepage)
        self.assertIn("secure signature request", homepage)


if __name__ == "__main__":
    unittest.main()

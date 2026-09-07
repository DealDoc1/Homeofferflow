import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class IntakePathClarityAuditTests(unittest.TestCase):
    def test_partner_launch_copy_does_not_make_an_unenforced_scarcity_claim(self):
        self.assertNotIn("first 10 approved partners", HTML)
        self.assertIn("Get the first 90 days for the price of one standard month.", HTML)
        self.assertIn("Each placement covers one category and market.", HTML)

    def test_shared_landing_sections_are_marked_for_path_specific_copy(self):
        for identifier in (
            'id="heroBadge"', 'id="howCta"', 'id="trustPrimary"',
            'id="howTitle"', 'id="howStepOneTitle"', 'id="homeFaqItems"',
        ):
            with self.subTest(identifier=identifier):
                self.assertIn(identifier, HTML)


if __name__ == "__main__":
    unittest.main()

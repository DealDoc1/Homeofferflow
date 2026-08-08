import unittest
from pathlib import Path


INDEX = Path(__file__).resolve().parents[1] / "index.html"


class NonRealtyUiDefaultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_nonrealty_amount_has_no_hardcoded_dollar_default(self):
        self.assertIn(
            'id="nonRealtyAmount" value="" placeholder="Leave blank if no separate amount"',
            self.source,
        )
        self.assertNotIn("id=\"nonRealtyAmount\" value=\"10\"", self.source)
        self.assertNotIn("getVal('nonRealtyAmount') || '10'", self.source)

    def test_nonrealty_review_explicitly_shows_blank_amount(self):
        self.assertIn("s.nonRealtyAmount ? fmtM(s.nonRealtyAmount) : 'No separate amount'", self.source)

    def test_selecting_nonrealty_does_not_insert_an_amount(self):
        self.assertIn("if (value === 'yes') setDefaultValue('nonRealtyAmount', '');", self.source)
        self.assertIn("setDefaultValue('nonRealtyAmount', '');", self.source)


if __name__ == "__main__":
    unittest.main()

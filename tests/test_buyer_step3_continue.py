"""Regression coverage for the buyer offer price-and-financing transition."""

from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BuyerStepThreeContinueTests(unittest.TestCase):
    def test_financing_selection_populates_required_starting_terms_before_continue(self):
        start = HTML.index("if (group === 'financing')")
        end = HTML.index("if (group === 'leases')", start)
        financing_selection = HTML[start:end]

        self.assertIn("syncFinancingFieldsFromPrice();", financing_selection)
        self.assertIn("wirePaymentCalculator();", financing_selection)
        self.assertIn("updatePaymentCalculator();", financing_selection)

    def test_non_cash_financing_defaults_cover_each_required_field(self):
        defaults_start = HTML.index("const financingDefaults = [")
        defaults_end = HTML.index("financingDefaults.forEach", defaults_start)
        defaults = HTML[defaults_start:defaults_end]

        for field in (
            "loanYears",
            "interestRateCap",
            "interestFirstYears",
            "originationCap",
            "buyerApprovalDays",
        ):
            self.assertIn(field, defaults)

        validation_start = HTML.index("if (stepId === 'step3')")
        validation_end = HTML.index("if (stepId === 'step5')", validation_start)
        validation = HTML[validation_start:validation_end]
        self.assertIn("requireField('loanAmount'", validation)
        self.assertIn("requireField('loanYears'", validation)
        self.assertIn("requireField('interestRateCap'", validation)
        self.assertIn("requireField('interestFirstYears'", validation)
        self.assertIn("requireField('originationCap'", validation)
        self.assertIn("requireField('buyerApprovalDays'", validation)


if __name__ == "__main__":
    unittest.main()

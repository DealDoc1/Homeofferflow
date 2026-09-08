import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class FinancingInterviewDefaultsTests(unittest.TestCase):
    def test_non_cash_financing_starts_with_editable_required_terms(self):
        start = INDEX.index("function calculateFinancingDefaults(forceReset = false)")
        end = INDEX.index("function wireSmartCalculations()", start)
        segment = INDEX[start:end]

        for field_id, value in (
            ("loanYears", "30"),
            ("interestRateCap", "7"),
            ("interestFirstYears", "30"),
            ("originationCap", "1"),
            ("buyerApprovalDays", "21"),
        ):
            self.assertIn(f"['{field_id}', {value}", segment)

        self.assertIn("if (field && !field._userEdited && !String(field.value || '').trim())", segment)
        self.assertIn("Starting point only — confirm the rate cap with your lender", segment)

    def test_financing_defaults_preserve_a_buyers_edited_terms(self):
        start = INDEX.index("function wireSmartCalculations()")
        end = INDEX.index("function wirePaymentCalculator()", start)
        segment = INDEX[start:end]

        for field_id in (
            "loanYears",
            "interestRateCap",
            "interestFirstYears",
            "originationCap",
            "buyerApprovalDays",
        ):
            self.assertIn(f"document.getElementById('{field_id}')", segment)
        self.assertIn("el.addEventListener('input', () => { el._userEdited = true; });", segment)


if __name__ == "__main__":
    unittest.main()

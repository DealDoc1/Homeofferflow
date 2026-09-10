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

    def test_step_three_names_the_next_interview_section(self):
        start = INDEX.index("function updateProgress()")
        end = INDEX.index("function toggleTermsFromRow", start)
        segment = INDEX[start:end]
        self.assertIn("step3: 'Review addenda →'", segment)
        self.assertIn("step7: 'Review your offer →'", segment)

    def test_financing_choice_applies_defaults_before_deferred_refresh(self):
        start = INDEX.index("function selectCard(el, group, value)")
        end = INDEX.index("if (group === 'leases')", start)
        segment = INDEX[start:end]

        immediate_defaults = segment.index("syncFinancingFieldsFromPrice();")
        deferred_refresh = segment.index("setTimeout(() =>")
        self.assertLess(immediate_defaults, deferred_refresh)


if __name__ == "__main__":
    unittest.main()

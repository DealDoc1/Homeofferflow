from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class Step3ContinueResilienceTests(unittest.TestCase):
    def test_continue_synchronizes_financing_defaults_before_validation(self):
        start = INDEX.index("async function nextStep()")
        end = INDEX.index("function prevStep()", start)
        block = INDEX[start:end]
        self.assertIn("const currentStepId = getCurrentSteps()[state.step];", block)
        self.assertIn("if (currentStepId === 'step3')", block)
        self.assertIn("syncFinancingFieldsFromPrice();", block)
        self.assertIn("updateAppraisalAddendumVisibility();", block)
        self.assertIn("try {", block)
        self.assertIn("Could not refresh Step 3 calculations:", block)
        self.assertIn("Calculation suggestions must never strand someone", block)
        self.assertLess(block.index("syncFinancingFieldsFromPrice();"), block.index("collectData();"))
        self.assertLess(block.index("syncFinancingFieldsFromPrice();"), block.index("validateCurrentStep()"))


if __name__ == "__main__":
    unittest.main()

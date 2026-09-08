from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class WizardValidationGuidanceTests(unittest.TestCase):
    def test_missing_answer_is_marked_accessibly(self):
        self.assertIn("el.dataset.validationInvalid = 'true';", INDEX)
        self.assertIn("el.setAttribute('aria-invalid', 'true');", INDEX)
        self.assertIn("delete el.dataset.validationInvalid;", INDEX)
        self.assertIn("el.removeAttribute('aria-invalid');", INDEX)

    def test_continue_guides_the_user_to_the_first_missing_answer(self):
        self.assertIn("function guideToFirstValidationAnswer(stepId)", INDEX)
        self.assertIn('[data-validation-invalid="true"]', INDEX)
        self.assertIn("invalid.scrollIntoView({ behavior: 'smooth', block: 'center' });", INDEX)
        self.assertIn("guideToFirstValidationAnswer(stepId);", INDEX)
        self.assertIn("setValidationStatus('Continue needs: '", INDEX)


if __name__ == "__main__":
    unittest.main()

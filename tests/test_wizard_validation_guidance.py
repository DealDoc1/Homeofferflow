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
        self.assertIn("setValidationStatus('To continue, add: '", INDEX)

    def test_correcting_an_answer_clears_its_stale_validation_feedback(self):
        self.assertIn('function clearValidationFeedbackFor(target)', INDEX)
        self.assertIn('clearValidationFeedbackFor(e.target);', INDEX)
        self.assertIn("delete target.dataset.validationInvalid;", INDEX)
        self.assertIn("target.removeAttribute('aria-invalid');", INDEX)
        self.assertIn("const isValidEmail = !target.matches('input[type=\"email\"]') || target.checkValidity();", INDEX)
        self.assertIn("if (hasAnswer && isValidEmail)", INDEX)
        self.assertIn("if (activeStep && !activeStep.querySelector('[data-validation-invalid=\"true\"]'))", INDEX)


if __name__ == "__main__":
    unittest.main()

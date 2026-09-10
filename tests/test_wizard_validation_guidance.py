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

    def test_step_three_explains_the_conditional_appraisal_choice_in_place(self):
        """A newly revealed financing choice must not feel like a dead Continue button."""
        self.assertIn('id="appraisalAddendumRequired" role="status" aria-live="polite" hidden', INDEX)
        self.assertIn('Choose one option to continue.', INDEX)
        self.assertIn('function setAppraisalAddendumRequired(visible)', INDEX)
        self.assertIn('const appraisalDecisionRequired = !!(', INDEX)
        self.assertIn("setAppraisalAddendumRequired(appraisalDecisionRequired);", INDEX)
        self.assertIn("if (group === 'appraisalAddendum') setAppraisalAddendumRequired(false);", INDEX)

    def test_independent_agents_are_not_blocked_by_a_missing_brokerage_name(self):
        validation_start = INDEX.index("function validateCurrentStep()")
        validation_end = INDEX.index("if (stepId === 'step2')", validation_start)
        step_one_validation = INDEX[validation_start:validation_end]

        self.assertIn("requireField('agentNameQuick'", step_one_validation)
        self.assertIn("requireField('agentLicenseQuick'", step_one_validation)
        self.assertIn("requireValidEmail('agentEmailQuick'", step_one_validation)
        self.assertIn("requireField('agentPhoneQuick'", step_one_validation)
        self.assertNotIn("requireField('agentBrokerageQuick'", step_one_validation)
        self.assertIn("Brokerage / Team Name", INDEX)
        self.assertIn("(if applicable)", INDEX)


if __name__ == "__main__":
    unittest.main()

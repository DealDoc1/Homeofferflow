import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class InterviewLabelAssociationTests(unittest.TestCase):
    def test_interview_fields_get_programmatic_label_associations(self):
        start = INDEX.index("function associateInterviewLabels()")
        end = INDEX.index("function clearValidationFeedbackFor", start)
        segment = INDEX[start:end]

        self.assertIn("#wizardOverlay .field > label:not([for])", segment)
        self.assertIn("#wizardOverlay .field .field-label-row > label:not([for])", segment)
        self.assertIn("#wizardOverlay .payment-calc-mini-field > label:not([for])", segment)
        self.assertIn("if (controls.length !== 1) return;", segment)
        self.assertIn("label.htmlFor = control.id;", segment)

    def test_label_association_runs_before_a_person_can_use_validation(self):
        self.assertIn("associateInterviewLabels();", INDEX)
        invocation = INDEX.index("associateInterviewLabels();")
        validation = INDEX.index("function validateCurrentStep()")
        self.assertLess(invocation, validation)


if __name__ == "__main__":
    unittest.main()

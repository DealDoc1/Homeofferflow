from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class Paragraph4OfferInterviewTests(unittest.TestCase):
    def test_lease_questions_stay_inside_the_offer_interview(self):
        step_start = HTML.index('<div class="wizard-step" id="step2">')
        step_end = HTML.index('<div class="wizard-step" id="step3">', step_start)
        step = HTML[step_start:step_end]
        self.assertIn('HomeOfferFlow will include the right addendum', step)
        self.assertIn('id="paragraph4LeaseFields"', step)
        self.assertIn('id="leaseResidential"', step)
        self.assertIn('id="leaseFixture"', step)
        self.assertNotIn('/texas-agent-form-library?', step)

    def test_interview_collects_and_validates_both_released_lease_paths(self):
        self.assertIn("s.leaseResidential =", HTML)
        self.assertIn("s.leaseFixture =", HTML)
        self.assertIn("function validateParagraph4LeaseInputs(data)", HTML)
        self.assertIn("if (!validateParagraph4LeaseInputs(state.data)) return;", HTML)
        self.assertIn("${atag('Residential Lease Addendum', s.leaseResidential === 'yes')}", HTML)
        self.assertIn("${atag('Fixture Lease Addendum', s.leaseFixture === 'yes')}", HTML)

    def test_review_copy_explains_seller_signing_for_included_lease_addenda(self):
        self.assertIn('id="reviewSigningExpectation"', HTML)
        self.assertIn("Sellers then sign the included ${paragraph4Forms.join(' and ')}", HTML)
        self.assertIn('Seller acceptance and any other seller-side signatures remain with the seller or listing side.', HTML)
        self.assertIn('If the terms change, update the saved transaction and generate a new package', HTML)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class Paragraph4OfferInterviewTests(unittest.TestCase):
    def test_lease_questions_stay_inside_the_offer_interview(self):
        step_start = HTML.index('<div class="wizard-step" id="step2">')
        step_end = HTML.index('<div class="wizard-step" id="step3">', step_start)
        step = HTML[step_start:step_end]
        self.assertIn('We’ll ask only the lease questions the contract needs', step)
        self.assertIn('id="paragraph4LeaseFields"', step)
        self.assertIn('id="leaseResidential"', step)
        self.assertIn('id="leaseFixture"', step)
        self.assertIn('id="leaseNaturalResource"', step)
        self.assertIn('id="leaseNRDelivered"', step)
        self.assertIn('id="naturalResourceTerminationDays"', step)
        self.assertNotIn('/texas-agent-form-library?', step)

    def test_interview_collects_and_validates_both_released_lease_paths(self):
        self.assertIn("s.leaseResidential =", HTML)
        self.assertIn("s.leaseFixture =", HTML)
        self.assertIn("s.leaseNaturalResource =", HTML)
        self.assertIn("function validateParagraph4LeaseInputs(data)", HTML)
        self.assertIn("if (!validateParagraph4LeaseInputs(state.data)) return;", HTML)
        self.assertIn("${atag('Residential Lease Addendum', s.leaseResidential === 'yes')}", HTML)
        self.assertIn("${atag('Fixture Lease Addendum', s.leaseFixture === 'yes')}", HTML)
        self.assertIn("${atag('Natural Resource Lease terms in the purchase contract', s.leaseNaturalResource === 'yes')}", HTML)

    def test_natural_resource_lease_does_not_add_an_unnecessary_seller_signature_gate(self):
        validation_start = HTML.index('function validateParagraph4LeaseInputs(data)')
        validation_end = HTML.index('function hydrostaticSigningSummary', validation_start)
        validation = HTML[validation_start:validation_end]
        self.assertIn("if (data.leaseResidential !== 'yes' && data.leaseFixture !== 'yes')", validation)
        self.assertIn("if (data.leaseNaturalResource === 'yes')", validation)
        self.assertIn("natural resource lease termination period from 1 to 999 days", validation)

    def test_review_copy_explains_seller_signing_for_included_lease_addenda(self):
        self.assertIn('id="reviewSigningExpectation"', HTML)
        self.assertIn("Sellers sign only the included ${paragraph4Forms.join(' and ')}", HTML)
        self.assertIn('Seller acceptance and any other seller-side signatures remain with the seller or listing side.', HTML)
        self.assertIn('If the terms change, update the saved transaction and generate a new package', HTML)

    def test_success_copy_explains_seller_signing_for_generated_lease_package(self):
        self.assertIn('id="successHeading"', HTML)
        self.assertIn('id="successSignatureStep"', HTML)
        self.assertIn("Buyers and sellers receive signing invitations together. Sellers sign the included ${paragraph4Forms.join(' and ')}", HTML)
        self.assertIn("? 'Packet generated'", HTML)
        self.assertIn("We’re confirming your checkout", HTML)
        self.assertIn("Your offer packet", HTML)


if __name__ == "__main__":
    unittest.main()

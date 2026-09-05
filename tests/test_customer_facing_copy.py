from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class CustomerFacingCopyTests(unittest.TestCase):
    def test_live_agent_and_seller_paths_use_finished_product_language(self):
        self.assertIn("Built for professional Texas offer workflows.", HTML)
        self.assertIn("Start with a seller request and receive the right package options.", HTML)
        self.assertNotIn("FSBO path is lead capture only for now.", HTML)
        self.assertNotIn("Built for broker-supervised workflows.", HTML)
        self.assertNotIn("without turning FSBO into checkout yet", HTML)
        self.assertNotIn("addenda currently supported by HomeOfferFlow", HTML)

    def test_lease_copy_explains_the_next_step_without_a_product_testing_message(self):
        self.assertIn("confirm the lease details and applicable addendum before generating the packet", HTML)
        self.assertNotIn("will unlock those paths after their targeted PDF testing is complete", HTML)
        self.assertNotIn("This packet includes an option that HomeOfferFlow is still testing", HTML)

    def test_upload_guidance_does_not_present_the_product_as_an_unfinished_phase(self):
        self.assertIn("confirm any signing required on an uploaded document", HTML)
        self.assertNotIn("Phase 1: upload PDF disclosures", HTML)
        self.assertNotIn("Signature placement on uploaded docs is coming next.", HTML)

    def test_agent_onboarding_uses_client_ready_language(self):
        self.assertIn("Generate your first packet", HTML)
        self.assertIn("Review buyer-side signing", HTML)
        self.assertNotIn("Generate a clean test packet", HTML)
        self.assertNotIn("Create Test Offer", HTML)
        self.assertNotIn("Create your first test offer", HTML)
        self.assertNotIn("Complete a full signing test", HTML)

    def test_signed_in_workspace_does_not_expose_internal_build_labels(self):
        self.assertIn("Loading brokerage settings...", HTML)
        self.assertIn("Loading listing tools...", HTML)
        self.assertIn("<h4>Offer Review</h4>", HTML)
        self.assertNotIn("Loading brokerage foundation...", HTML)
        self.assertNotIn("Loading seller-side foundation...", HTML)
        self.assertNotIn("AI Offer Review Foundation", HTML)
        self.assertNotIn("Future AI Checklist", HTML)

    def test_fsbo_intake_keeps_optional_partner_choices_out_of_the_initial_path(self):
        self.assertIn("What would you like help with first?", HTML)
        self.assertIn("Would local provider recommendations help?", HTML)
        self.assertIn("<details style=\"margin-top:1rem; padding-top:.9rem; border-top:1px solid rgba(255,255,255,.08);\">", HTML)

    def test_seller_landing_link_opens_the_seller_request(self):
        self.assertIn("const isSellerRequest = landingParams.get('fsbo') === '1';", HTML)
        self.assertIn("root.openFsboSellerModal?.()", HTML)

    def test_fsbo_title_company_choice_uses_the_server_supported_category(self):
        self.assertIn('name="fsboPartner" value="title"> Title company', HTML)
        self.assertNotIn('name="fsboPartner" value="title_company">', HTML)

    def test_fsbo_submission_has_its_partner_selection_helper(self):
        self.assertIn("function getFsboPartners()", HTML)
        self.assertIn("input[name=\"fsboPartner\"]:checked", HTML)

    def test_broker_workspace_does_not_describe_an_unfinished_future_build(self):
        self.assertIn("keep your team's process consistent", HTML)
        self.assertNotIn("can be added later without creating a separate login path", HTML)
        self.assertNotIn("validate the repeat-offer workflow before heavier investor tooling", HTML)
        self.assertNotIn("Broker demo note", HTML)

    def test_agent_workspace_uses_active_access_and_independent_agent_language(self):
        self.assertIn("const statusLabel = status === 'beta' ? 'Active access'", HTML)
        self.assertIn("Set your review process", HTML)
        self.assertIn("If you work with a brokerage or team, follow its process as well.", HTML)
        self.assertIn("Brokerage or Team Name <span style=\"color:var(--gray);font-weight:500;\">(optional)</span>", HTML)
        self.assertIn("Brokerage or team, if applicable", HTML)
        self.assertNotIn("Have your broker or team lead confirm", HTML)


if __name__ == "__main__":
    unittest.main()

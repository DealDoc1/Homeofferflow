from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrokerageAdminScopeTests(unittest.TestCase):
    def test_generic_form_roadmap_does_not_make_tyler_a_product_gate(self):
        roadmap = (ROOT / "docs" / "AGENT_FORM_COVERAGE_ROADMAP.md").read_text()
        self.assertIn("HomeOfferFlow's CEO or delegated product reviewer", roadmap)
        self.assertNotIn("Tyler Demando", roadmap)

    def test_release_evidence_uses_product_release_authority(self):
        evidence = (ROOT / "docs" / "RELEASE_EVIDENCE_TEMPLATE.md").read_text()
        self.assertIn("HomeOfferFlow CEO or delegated product reviewer", evidence)
        self.assertNotIn("Tyler Demando", evidence)

    def test_agent_listing_ui_does_not_expose_internal_organization_source_process(self):
        index = (ROOT / "index.html").read_text()
        self.assertNotIn("Listing Form Readiness", index)
        self.assertNotIn("Source approved", index)
        self.assertNotIn("Tyler Demando", index)

    def test_form_roadmap_matches_the_released_shared_agent_library(self):
        roadmap = (ROOT / "docs" / "AGENT_FORM_COVERAGE_ROADMAP.md").read_text()
        self.assertIn("does\nnot require a brokerage seat or a per-agent brokerage attestation", roadmap)
        self.assertIn("- signed-in agent access to the released review draft without a brokerage-seat", roadmap)
        self.assertNotIn("an explicit per-agent attestation that the user is currently authorized", roadmap)


if __name__ == "__main__":
    unittest.main()

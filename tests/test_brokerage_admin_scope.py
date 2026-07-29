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

    def test_form_ui_describes_an_organization_admin_not_ondemand_only(self):
        index = (ROOT / "index.html").read_text()
        self.assertIn("An authorized organization administrator must privately upload and attest", index)
        self.assertNotIn("Tyler Demando", index)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LegalPackageTests(unittest.TestCase):
    def test_coordinated_legal_pages_are_present_and_current(self):
        for filename in ("terms.html", "privacy.html", "disclaimer.html", "esign-consent.html"):
            content = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("July 29, 2026", content)
            self.assertIn("support@homeofferflow.com", content)

    def test_wizard_requires_explicit_current_package_acceptance(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="termsAccepted"', content)
        self.assertIn('/esign-consent.html', content)
        self.assertIn("LEGAL_POLICY_VERSION = '2026-07-29'", content)
        self.assertIn("policyVersion: LEGAL_POLICY_VERSION", content)

    def test_legal_pages_do_not_repeat_removed_public_records_claim(self):
        for filename in ("terms.html", "disclaimer.html"):
            content = (ROOT / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("public records", content)


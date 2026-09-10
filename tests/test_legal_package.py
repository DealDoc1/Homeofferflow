from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LegalPackageTests(unittest.TestCase):
    def test_live_audit_records_current_pages_and_does_not_overclaim_checkout_qa(self):
        audit = (ROOT / "docs" / "release-evidence" / "legal-policy-live-audit-2026-09-10.md").read_text(encoding="utf-8")
        for page in ("/terms.html", "/privacy.html", "/esign-consent.html", "/disclaimer.html"):
            self.assertIn(page, audit)
        self.assertIn("Version 3.0 · Last updated: July 30, 2026", audit)
        self.assertIn("2026-07-30", audit)
        self.assertIn("does **not** claim that a fresh signed-in subscription", audit)

    def test_coordinated_legal_pages_are_present_and_current(self):
        for filename in ("terms.html", "privacy.html", "disclaimer.html", "esign-consent.html"):
            content = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("July 30, 2026", content)
            self.assertIn("support@homeofferflow.com", content)

    def test_wizard_requires_explicit_current_package_acceptance(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="termsAccepted"', content)
        self.assertIn('/esign-consent.html', content)
        self.assertIn("LEGAL_POLICY_VERSION = '2026-07-30'", content)
        self.assertIn("policyVersion: LEGAL_POLICY_VERSION", content)

    def test_wizard_opening_keeps_required_acknowledgement_without_repeated_purchase_friction(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")
        start = content.index('<div class="wizard-step active" id="step0">')
        end = content.index('<div class="wizard-step" id="step05">', start)
        opening = content[start:end]
        self.assertIn("One quick acknowledgement", opening)
        self.assertIn("You can start without payment.", opening)
        self.assertIn("starting this interview does not create a charge.", opening)
        self.assertIn("TREC One to Four Family Residential Contract (Resale) No. 20-19", opening)
        self.assertIn("Electronic Communications and E-Sign Consent", opening)
        self.assertNotIn("Please review and accept the following disclaimer", opening)

    def test_legal_pages_do_not_repeat_removed_public_records_claim(self):
        for filename in ("terms.html", "disclaimer.html"):
            content = (ROOT / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("public records", content, filename)

    def test_legal_pages_use_customer_facing_limited_workflow_language(self):
        for filename in ("terms.html", "disclaimer.html"):
            content = (ROOT / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("beta", content, filename)
            self.assertNotIn("staging", content, filename)
            self.assertIn("under review", content, filename)

    def test_policy_package_contains_core_consumer_and_privacy_disclosures(self):
        privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
        esign = (ROOT / "esign-consent.html").read_text(encoding="utf-8")
        terms = (ROOT / "terms.html").read_text(encoding="utf-8")
        disclaimer = (ROOT / "disclaimer.html").read_text(encoding="utf-8")

        self.assertIn("No Sale, No Targeted Advertising", privacy)
        self.assertIn("Privacy Appeal", privacy)
        self.assertIn("Withdrawal of Consent", esign)
        self.assertIn("Hardware and Software Requirements", esign)
        self.assertIn("Source Rights", terms)
        self.assertIn("draft-only", disclaimer)
        self.assertIn("individual point-of-use attestation", terms)
        self.assertIn("active brokerage-level authorization", disclaimer)

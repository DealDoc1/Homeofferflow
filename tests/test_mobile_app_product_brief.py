from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BRIEF = (ROOT / "docs" / "MOBILE_APP_PRODUCT_BRIEF.md").read_text(encoding="utf-8")


class MobileAppProductBriefTests(unittest.TestCase):
    def test_brief_keeps_the_pwa_as_the_current_mobile_product(self):
        self.assertIn("responsive and installable as a web/PWA experience", BRIEF)
        self.assertIn("supported mobile product", BRIEF)

    def test_native_scope_is_agent_first_and_reuses_authorization(self):
        for phrase in (
            "agent-first iOS and Android companion app",
            "Reuse Supabase Auth",
            "must never contain a service-role key",
            "existing RLS-protected tables",
            "no new buyer, seller, or broker data access",
            "TXR/NAR attestation",
        ):
            self.assertIn(phrase, BRIEF)

    def test_mobile_release_requires_privacy_and_pdf_regression_gates(self):
        for phrase in (
            "notification payloads are redacted",
            "rendered-PDF golden suite",
            "completed-signature",
            "iOS and Android devices",
        ):
            self.assertIn(phrase, BRIEF)


if __name__ == "__main__":
    unittest.main()

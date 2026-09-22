import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class LegacyModalCleanupTests(unittest.TestCase):
    def test_unreachable_legacy_overlays_are_removed(self):
        for stale_marker in (
            'id="termsModal"',
            'id="agentValueModal"',
            "function openTermsModal",
            "function closeTerms",
            "function showAgentValueModal",
            "function hideAgentValueModal",
            "function continueWithHomeOfferFlow",
            "function referMyAgent",
            "function copyAgentReferralText",
            "function emailAgentReferral",
            "function useAgentInstead",
            "Thinking of using a buyer’s agent?",
            "potentially save thousands compared with",
        ):
            self.assertNotIn(stale_marker, INDEX)

    def test_current_legal_paths_remain_direct_and_accessible(self):
        self.assertIn('href="/terms.html"', INDEX)
        self.assertIn('href="/privacy.html"', INDEX)
        self.assertIn('href="/disclaimer.html"', INDEX)
        self.assertIn('href="/esign-consent.html"', INDEX)

    def test_active_subscription_consent_keeps_dialog_semantics(self):
        self.assertIn("modal.id = 'subscriptionLegalConsentModal';", INDEX)
        self.assertIn(
            'role="dialog" aria-modal="true" aria-labelledby="subscriptionLegalConsentTitle"',
            INDEX,
        )


if __name__ == "__main__":
    unittest.main()

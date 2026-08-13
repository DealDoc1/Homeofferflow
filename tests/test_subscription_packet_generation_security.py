from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
API = (ROOT / "api" / "fill-pdf.py").read_text(encoding="utf-8")


class SubscriptionPacketGenerationSecurityTests(unittest.TestCase):
    def test_browser_marks_subscribed_generation_and_sends_its_session_token(self):
        start = HTML.index("async function generateSubscribedPacket()")
        end = HTML.index("async function", start + 1)
        generation = HTML[start:end]
        self.assertIn("subscription_generation: 'true'", generation)
        self.assertIn("'Authorization': `Bearer ${hofAuth.session?.access_token || ''}`", generation)

    def test_generation_failure_recovery_uses_safe_categories_and_next_steps(self):
        start = HTML.index("function packetGenerationFailureDetails(err)")
        end = HTML.index("async function generateSubscribedPacket()", start)
        recovery = HTML[start:end]
        for category in ("session", "network", "timeout", "signature_provider", "validation", "service"):
            self.assertIn("category: '" + category + "'", recovery)
        generation_start = HTML.index("async function generateSubscribedPacket()")
        generation_end = HTML.index("function pad2", generation_start)
        generation = HTML[generation_start:generation_end]
        self.assertIn("packetGenerationFailureCategory: failure.category", generation)
        self.assertIn("errorCategory: failure.category", generation)
        self.assertIn("showPacketGenerationRecoveryNotice(failure)", generation)
        self.assertNotIn("No packet credit was used. Please try again. Error:", generation)

        self.assertIn('id="packetGenerationRecoveryNotice"', HTML)
        self.assertIn('id="packetGenerationRetryButton"', HTML)
        self.assertIn("'subscription_packet_generation_retry_clicked'", recovery)
        self.assertIn("No packet credit was used. ", recovery)
        self.assertIn("await generateSubscribedPacket();", recovery)

    def test_admin_surfaces_only_aggregate_packet_generation_failure_categories(self):
        admin = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"packetGenerationFailureCount"', admin)
        self.assertIn('"packetGenerationFailureCounts"', admin)
        self.assertIn("packet_generation_failure_categories", admin)
        self.assertIn('"unclassified"', admin)
        self.assertIn("Packet Generation Recovery", HTML)
        self.assertIn("packetGenerationFailureCounts?.signature_provider", HTML)
        self.assertIn("no offer, client, or agent details shown", HTML)

    def test_checkout_shaped_requests_fail_closed_without_stripe_or_subscription_auth(self):
        start = API.index("def do_POST(self):")
        post = API[start:]
        self.assertIn("A verified Stripe webhook or active subscription is required.", post)
        self.assertIn("is_subscription_generation", post)
        self.assertIn("self._verified_user()", post)
        self.assertIn("self._has_generation_entitlement(user_id)", post)
        self.assertGreaterEqual(post.count("Sign in again before generating a packet."), 2)
        self.assertIn("status\": \"in.(beta,active,trialing,free_admin)\"", API)
        self.assertIn("billing_month", API)
        self.assertIn("event_type\": \"eq.signed_packet\"", API)


if __name__ == "__main__":
    unittest.main()

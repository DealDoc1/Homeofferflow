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

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SubscriptionCheckoutFunnelMetricTests(unittest.TestCase):
    def test_admin_payload_counts_subscription_checkout_events(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"subscriptionCheckoutStartCount"', source)
        self.assertIn('"subscriptionCheckoutRedirectCount"', source)
        self.assertIn('"subscriptionCheckoutReturnCount"', source)
        self.assertIn('"subscriptionCheckoutFailureCount"', source)
        self.assertIn('"subscriptionCheckoutReturnRate"', source)
        self.assertIn("subscription_checkout_started", source)
        self.assertIn("subscription_checkout_returned", source)
        self.assertIn('"onDemandCheckoutStartCount"', source)
        self.assertIn('"onDemandCheckoutReturnRate"', source)
        self.assertIn('"onDemandFirstOfferStartCount"', source)
        self.assertIn('"onDemandFirstOfferStartRate"', source)
        self.assertIn("ondemand_first_offer_started", source)

    def test_admin_dashboard_surfaces_subscription_checkout_funnel(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Subscription Checkout Funnel", source)
        self.assertIn("subscriptionCheckoutStartCount", source)
        self.assertIn("subscriptionCheckoutRedirectCount", source)
        self.assertIn("subscriptionCheckoutReturnCount", source)
        self.assertIn("subscriptionCheckoutFailureCount", source)
        self.assertIn("subscriptionCheckoutReturnRate", source)
        self.assertIn("onDemandCheckoutStartCount", source)
        self.assertIn("onDemandCheckoutReturnRate", source)
        self.assertIn("onDemandFirstOfferStartCount", source)
        self.assertIn("onDemandFirstOfferStartRate", source)

    def test_ondemand_checkout_uses_the_shared_privacy_safe_funnel_events(self):
        source = (ROOT / "ondemand.html").read_text(encoding="utf-8")
        self.assertIn('recordCheckoutFunnelEvent("subscription_checkout_started")', source)
        self.assertIn('recordCheckoutFunnelEvent("subscription_checkout_returned", checkoutResult)', source)
        self.assertIn('metadata: { source: "ondemand", plan: "agent", billing: "monthly" }', source)
        self.assertIn('hof_ondemand_checkout_${eventType}_${result}_${checkoutSessionId}', source)
        self.assertIn("function markFirstOfferAttribution()", source)
        self.assertIn('sessionStorage.setItem("hof_ondemand_first_offer_attribution", "1")', source)
        self.assertIn("markFirstOfferAttribution();", source)
        self.assertNotIn("await recordFirstOfferActivation();", source)

    def test_first_offer_metric_is_delivered_from_the_destination_without_delaying_navigation(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("const ondemandFirstOfferAttributionKey = 'hof_ondemand_first_offer_attribution';", source)
        self.assertIn("function recordOndemandFirstOfferActivation()", source)
        self.assertIn("'ondemand_first_offer_started'", source)
        self.assertIn("recordOndemandFirstOfferActivation();", source)
        self.assertIn("sessionStorage.removeItem(ondemandFirstOfferAttributionKey)", source)

    def test_ondemand_success_return_offers_authenticated_workspace_handoff(self):
        source = (ROOT / "ondemand.html").read_text(encoding="utf-8")
        self.assertIn('id="workspaceButton"', source)
        self.assertIn('id="firstOfferButton"', source)
        self.assertIn('get("checkout") === "success"', source)
        self.assertIn('window.location.assign("/?pwa_action=workspace")', source)
        self.assertIn('window.location.assign("/?pwa_action=new_offer")', source)
        self.assertIn('$("firstOfferButton").style.display = checkoutComplete ? "block" : "none"', source)

    def test_cancelled_checkout_returns_to_account_with_recovery_copy(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("if (result === 'cancelled')", source)
        self.assertIn("pending.result === 'success'", source)
        self.assertIn("without completing payment.", source)
        self.assertIn("hof_subscription_checkout_cancelled", source)
        self.assertIn("Checkout was canceled.", source)

    def test_subscription_checkout_ignores_rapid_duplicate_starts(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("if (window.__hofSubscriptionCheckoutInFlight) return;", source)
        self.assertIn("window.__hofSubscriptionCheckoutInFlight = true;", source)
        self.assertGreaterEqual(source.count("window.__hofSubscriptionCheckoutInFlight = false;"), 2)

    def test_successful_checkout_reconciles_webhook_before_resuming_account(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("subscription.status === 'beta'", source)
        self.assertIn("attempt < 4", source)
        self.assertIn("setTimeout(resolve, 750)", source)
        self.assertIn("Subscription active. Your packet allowance is ready.", source)

    def test_checkout_funnel_distinguishes_redirect_failures_and_delayed_session_returns(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("subscription_checkout_redirected", source)
        self.assertIn("subscription_checkout_failed", source)
        self.assertIn("queueSubscriptionCheckoutReturn(result, plan, billing)", source)
        self.assertIn("flushSubscriptionCheckoutReturnEvent", source)
        self.assertIn("SUBSCRIPTION_CHECKOUT_RETURN_KEY", source)
        self.assertIn("SUBSCRIPTION_CHECKOUT_SOURCE_KEY", source)
        self.assertIn("subscription_reactivation", source)
        self.assertIn("subscription_card", source)
        self.assertIn("agent_activation", source)
        self.assertIn("source: subscriptionCheckoutSource(pending.source)", source)
        self.assertIn("if (logged) {", source)
        self.assertIn("sessionStorage.removeItem(SUBSCRIPTION_CHECKOUT_RETURN_KEY)", source)
        self.assertIn("sessionStorage.removeItem(SUBSCRIPTION_CHECKOUT_SOURCE_KEY)", source)


if __name__ == "__main__":
    unittest.main()

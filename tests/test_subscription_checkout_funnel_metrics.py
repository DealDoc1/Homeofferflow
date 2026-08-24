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
        self.assertIn('"subscriptionCheckoutRecoveryShownCount"', source)
        self.assertIn('"subscriptionCheckoutRecoveryStartCount"', source)
        self.assertIn('"subscriptionCheckoutReturnRate"', source)
        self.assertIn("subscription_checkout_started", source)
        self.assertIn("subscription_checkout_returned", source)
        self.assertIn('"onDemandCheckoutStartCount"', source)
        self.assertIn('"onDemandCheckoutReturnRate"', source)
        self.assertIn('"onDemandFirstOfferStartCount"', source)
        self.assertIn('"onDemandFirstOfferStartRate"', source)
        self.assertIn('"onDemandTransactionPickerOpenedCount"', source)
        self.assertIn('"onDemandTransactionPickerOpenedRate"', source)
        self.assertIn("ondemand_first_offer_started", source)
        self.assertIn("ondemand_transaction_picker_opened", source)

    def test_admin_dashboard_surfaces_subscription_checkout_funnel(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Subscription Checkout Funnel", source)
        self.assertIn("subscriptionCheckoutStartCount", source)
        self.assertIn("subscriptionCheckoutRedirectCount", source)
        self.assertIn("subscriptionCheckoutReturnCount", source)
        self.assertIn("subscriptionCheckoutFailureCount", source)
        self.assertIn("subscriptionCheckoutRecoveryShownCount", source)
        self.assertIn("subscriptionCheckoutRecoveryStartCount", source)
        self.assertIn("subscriptionCheckoutReturnRate", source)
        self.assertIn("onDemandCheckoutStartCount", source)
        self.assertIn("onDemandCheckoutReturnRate", source)
        self.assertIn("onDemandFirstOfferStartCount", source)
        self.assertIn("onDemandFirstOfferStartRate", source)
        self.assertIn("onDemandTransactionPickerOpenedCount", source)
        self.assertIn("onDemandTransactionPickerOpenedRate", source)

    def test_ondemand_checkout_uses_the_shared_privacy_safe_funnel_events(self):
        source = (ROOT / "ondemand.html").read_text(encoding="utf-8")
        self.assertIn('recordCheckoutFunnelEvent("subscription_checkout_started")', source)
        self.assertIn('recordCheckoutFunnelEvent("subscription_checkout_returned", checkoutResult)', source)
        self.assertIn('metadata: { source: "ondemand", plan: "agent", billing: "monthly", channel }', source)
        self.assertIn('hof_ondemand_checkout_${eventType}_${result}_${checkoutSessionId}', source)
        self.assertIn("function markFirstOfferAttribution()", source)
        self.assertIn('sessionStorage.setItem("hof_ondemand_first_offer_attribution", "1")', source)
        self.assertIn("markFirstOfferAttribution();", source)
        self.assertNotIn("await recordFirstOfferActivation();", source)

    def test_ondemand_cancelled_checkout_gives_an_authenticated_recovery_path(self):
        source = (ROOT / "ondemand.html").read_text(encoding="utf-8")
        self.assertIn('id="checkoutRecovery"', source)
        self.assertIn("Your enrollment is still ready.", source)
        self.assertIn("No card was saved and no charge was made.", source)
        self.assertIn('const checkoutCancelled = signedIn', source)
        self.assertIn('$("checkoutRecovery").style.display = checkoutCancelled ? "block" : "none"', source)
        self.assertIn('recordCheckoutFunnelEvent("subscription_checkout_recovery_shown", "shown")', source)

    def test_first_offer_metric_is_delivered_from_the_destination_without_delaying_navigation(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("const ondemandFirstOfferAttributionKey = 'hof_ondemand_first_offer_attribution';", source)
        self.assertIn("function recordOndemandFirstOfferActivation()", source)
        self.assertIn("'ondemand_first_offer_started'", source)
        self.assertIn("recordOndemandFirstOfferActivation();", source)
        self.assertIn("sessionStorage.removeItem(ondemandFirstOfferAttributionKey)", source)

    def test_ondemand_new_offer_returns_to_the_transaction_picker_before_a_draft(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function recordOndemandTransactionPickerOpened()", source)
        self.assertIn("'ondemand_transaction_picker_opened'", source)
        self.assertIn("async function openNewOfferShortcut(role)", source)
        self.assertIn("await window.openAccountDashboard?.({ tab: 'dashboard' });", source)
        self.assertIn("window.openAgentTransactionPicker?.();", source)

    def test_ondemand_success_return_offers_authenticated_workspace_handoff(self):
        source = (ROOT / "ondemand.html").read_text(encoding="utf-8")
        self.assertIn('id="workspaceButton"', source)
        self.assertIn('id="firstOfferButton"', source)
        self.assertIn('get("checkout") === "success"', source)
        self.assertIn('window.location.assign("/?pwa_action=workspace")', source)
        self.assertIn('window.location.assign("/?pwa_action=new_offer")', source)
        self.assertIn('$("firstOfferButton").style.display = checkoutComplete ? "block" : "none"', source)

    def test_success_return_offers_a_mobile_pwa_install_prompt_without_enrollment_noise(self):
        source = (ROOT / "ondemand.html").read_text(encoding="utf-8")
        self.assertIn('id="installHint"', source)
        self.assertIn('id="installAppButton"', source)
        self.assertIn('!checkoutComplete || !isMobileInstallCandidate()', source)
        self.assertIn('beforeinstallprompt', source)
        self.assertIn('Add to Home Screen', source)

    def test_cancelled_checkout_returns_to_account_with_recovery_copy(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("if (result === 'cancelled')", source)
        self.assertIn("pending.result === 'success'", source)
        self.assertIn("without completing payment.", source)
        self.assertIn("hof_subscription_checkout_cancelled", source)
        self.assertIn("Checkout was canceled.", source)
        self.assertIn("renderSubscriptionCheckoutRecovery()", source)
        self.assertIn("hof_subscription_checkout_cancelled_context", source)
        self.assertIn("Resume Monthly Checkout", source)
        self.assertIn("subscription_checkout_recovery_shown", source)

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
        checkout_source = (ROOT / "api" / "create-subscription-checkout" / "index.py").read_text(encoding="utf-8")
        self.assertIn("self._record_checkout_redirect(", checkout_source)
        self.assertIn('"event_type": "subscription_checkout_redirected"', checkout_source)
        self.assertIn('"Stripe subscription checkout session created."', checkout_source)
        self.assertIn("Keeping it server-side avoids losing", source)
        self.assertNotIn("await logOfferEvent(null, 'subscription_checkout_redirected'", source)
        self.assertIn("subscription_checkout_failed", source)
        self.assertIn("queueSubscriptionCheckoutReturn(result, plan, billing)", source)
        self.assertIn("flushSubscriptionCheckoutReturnEvent", source)
        self.assertIn("SUBSCRIPTION_CHECKOUT_RETURN_KEY", source)
        self.assertIn("SUBSCRIPTION_CHECKOUT_SOURCE_KEY", source)
        self.assertIn("subscription_reactivation", source)
        self.assertIn("subscription_card", source)
        self.assertIn("agent_activation", source)
        self.assertIn("subscription_cancel_recovery", source)
        self.assertIn("source: subscriptionCheckoutSource(pending.source)", source)
        self.assertIn("if (logged) {", source)
        self.assertIn("sessionStorage.removeItem(SUBSCRIPTION_CHECKOUT_RETURN_KEY)", source)
        self.assertIn("sessionStorage.removeItem(SUBSCRIPTION_CHECKOUT_SOURCE_KEY)", source)


if __name__ == "__main__":
    unittest.main()

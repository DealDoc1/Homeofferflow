from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
BUYERS = (ROOT / "buyers.html").read_text(encoding="utf-8")


class HomebuyerLandingFunnelTests(unittest.TestCase):
    def test_public_endpoint_only_accepts_allowlisted_aggregate_events_and_channels(self):
        self.assertIn("HOMEBUYER_LANDING_EVENT_TYPES", API)
        self.assertIn("HOMEBUYER_LANDING_CHANNELS", API)
        self.assertIn("def _record_homebuyer_landing_event(data):", API)
        self.assertIn('"homebuyer_landing_viewed": "viewed"', API)
        self.assertIn('"homebuyer_landing_ready_list_opened": "ready_list_opened"', API)
        self.assertIn('"homebuyer_landing_cta_selected": "selected"', API)
        self.assertIn('"homebuyer_landing_offer_started": "started"', API)
        self.assertIn('"homebuyer_checkout_cancelled": "cancelled"', API)
        self.assertIn('"homebuyer_checkout_recovery_started": "recovery_started"', API)
        self.assertIn('"pwa_buyer_offer_opened": "opened"', API)
        self.assertIn("Unsupported homebuyer landing event.", API)
        self.assertIn("Unsupported homebuyer landing channel.", API)
        self.assertIn("'homebuyer_landing_event'", API)
        self.assertIn('"surface": "homebuyer_landing"', API)

    def test_buyer_landing_records_each_stage_once_without_buyer_or_offer_details(self):
        self.assertIn("recordAggregateFunnelEvent", BUYERS)
        self.assertIn("sessionStorage.getItem(key)", BUYERS)
        self.assertIn("request_type: 'homebuyer_landing_event'", BUYERS)
        self.assertIn("homebuyer_landing_viewed", BUYERS)
        self.assertIn("homebuyer_landing_ready_list_opened", BUYERS)
        self.assertIn("homebuyer_landing_cta_selected", BUYERS)
        self.assertIn("recordAggregateFunnelEvent('homebuyer_landing_offer_started')", BUYERS)
        self.assertIn("channel: safeChannel", BUYERS)
        self.assertIn("allowedChannels.has(rawSource)", BUYERS)
        self.assertIn("keepalive: true", BUYERS)
        landing_script = BUYERS.split("<script>(() =>", 1)[1].split("</script>", 1)[0]
        self.assertNotIn("// Record the handoff before navigation", landing_script)

    def test_buyer_ctas_match_the_no_payment_before_review_flow(self):
        self.assertEqual(BUYERS.count("Build my offer — no payment to start"), 2)
        self.assertIn("The $99 one-time charge applies only when the packet is ready.", BUYERS)
        self.assertIn('"price":"99"', BUYERS)

    def test_buyer_ready_list_reduces_pre_start_uncertainty_without_collecting_details(self):
        self.assertIn('id="buyerReadyList"', BUYERS)
        self.assertIn("Bring what you know. The guided flow handles the rest.", BUYERS)
        self.assertIn("homebuyer_landing_ready_list_opened", BUYERS)
        self.assertIn("What should I have ready before starting a Texas homebuyer offer?", BUYERS)

    def test_public_buyer_cta_opens_the_guided_offer_workflow_on_a_fresh_visit(self):
        self.assertIn('href="/?buyer=1"', BUYERS)
        self.assertIn("if (params().get('buyer') === '1') setTimeout(() =>", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('buyer')", INDEX)
        self.assertIn("setAudience('homebuyer')", INDEX)
        self.assertIn("const buyerEntrySurface = buyerRouteParams.get('utm_source') === 'texas_homebuyer_offer_guide'", INDEX)
        self.assertIn("window.beginOfferFrom?.(buyerEntrySurface)", INDEX)
        self.assertIn("homebuyer_landing_offer_started", INDEX)
        self.assertIn("hof_homebuyer_landing_homebuyer_landing_offer_started_", INDEX)
        self.assertNotIn("function consumeHomebuyerLandingEntry()", INDEX)

    def test_admin_reports_aggregate_buyer_landing_conversion(self):
        for expected in (
            '"homebuyerLandingViewCount"',
            '"homebuyerLandingReadyListOpenCount"',
            '"homebuyerLandingReadyListOpenRate"',
            '"homebuyerLandingCtaCount"',
            '"homebuyerLandingCtaRate"',
            '"homebuyerLandingOfferStartedCount"',
            '"homebuyerLandingOfferStartRate"',
            '"homebuyerLandingViewCountsByChannel"',
            '"homebuyerLandingOfferStartedCountsByChannel"',
            '"homebuyerCheckoutCancelledCount"',
            '"homebuyerCheckoutRecoveryStartCount"',
            '"homebuyerCheckoutRecoveryStartRate"',
            "homebuyer_landing_view_count",
            "homebuyer_landing_cta_count",
            "homebuyer_landing_offer_started_count",
            "homebuyer_landing_view_counts_by_channel",
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("Homebuyer $99 Funnel", INDEX)
        self.assertIn("homebuyerLandingCtaRate", INDEX)
        self.assertIn("homebuyerLandingOfferStartRate", INDEX)
        self.assertIn("homebuyerCheckoutRecoveryStartRate", INDEX)
        self.assertIn("recordHomebuyerCheckoutEvent", INDEX)
        self.assertIn('"pwaBuyerOfferShortcutCount"', ADMIN)
        self.assertIn("pwaBuyerOfferShortcutCount", INDEX)

    def test_cancelled_buyer_checkout_explains_required_confirmations_before_restart(self):
        self.assertIn('id="paymentCheckoutResumeHelp"', INDEX)
        self.assertIn("confirm the one-time packet acknowledgement and receipt email below", INDEX)
        self.assertIn("Review confirmations and resume secure checkout", INDEX)
        resume_start = INDEX.index("function resumeCancelledBuyerCheckout()")
        resume_end = INDEX.index("function setRadioValue", resume_start)
        resume = INDEX[resume_start:resume_end]
        self.assertIn("First, confirm the one-time packet acknowledgement below.", resume)
        self.assertIn("Next, enter the email for your receipt and signing delivery.", resume)
        self.assertIn("Your confirmations are complete. Opening secure checkout", resume)
        self.assertIn("recordHomebuyerCheckoutEvent('homebuyer_checkout_recovery_started')", resume)


if __name__ == "__main__":
    unittest.main()

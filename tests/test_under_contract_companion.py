from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "assets" / "under-contract-companion.js").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class UnderContractCompanionTests(unittest.TestCase):
    def test_offer_workspace_exposes_the_companion_only_after_packet_generation(self):
        self.assertIn("const canTrackContract = ['generated', 'signing', 'signed'].includes(bucketForOffer(o));", INDEX)
        self.assertIn("Track accepted contract", INDEX)
        self.assertIn("window.hofUnderContract?.open", INDEX)
        self.assertIn("Contract timeline", INDEX)

    def test_companion_uses_existing_offer_data_and_no_new_address_field(self):
        self.assertIn("return offer?.property_address || data.propertyAddress || data.propAddress", SCRIPT)
        self.assertNotIn('name="propertyAddress"', SCRIPT)
        self.assertNotIn("maps.googleapis.com", SCRIPT)

    def test_private_save_is_scoped_to_the_signed_in_owner_and_offer(self):
        self.assertIn(".eq('user_id', user.id).eq('id', offer.id).select('*').single()", SCRIPT)
        self.assertIn("transactionTracking: tracking", SCRIPT)
        self.assertIn("select('offer_data').eq('user_id', user.id).eq('id', offer.id).single()", SCRIPT)
        self.assertIn("latest.data?.offer_data || data", SCRIPT)
        self.assertIn("acceptedContractConfirmed: true", SCRIPT)
        update_block = SCRIPT[SCRIPT.index("client.from('hof_offers').update({"):SCRIPT.index("if (result.error)")]
        self.assertNotIn("last_updated", update_block)
        self.assertIn("root.hofAuth?.session?.user?.id !== user.id", SCRIPT)

    def test_dates_require_signed_contract_confirmation_and_avoid_false_precision(self):
        self.assertIn("I confirm this offer was accepted", SCRIPT)
        self.assertIn("Some depend on receipt, weekends, legal holidays, or later events and are not calculated here.", SCRIPT)
        self.assertIn("5:00 p.m. local time where the property is located", SCRIPT)
        self.assertIn("Use the fully signed contract", SCRIPT)

    def test_analytics_are_private_aggregate_signals(self):
        analytics = SCRIPT[SCRIPT.index("contract_timeline_saved"):]
        self.assertIn("has_option_date", analytics)
        self.assertIn("has_closing_date", analytics)
        self.assertNotIn("effectiveDate:", analytics)
        self.assertNotIn("property:", analytics)

    def test_calendar_runtime(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests" / "under_contract_companion.runtime.cjs")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_companion_is_loaded_and_available_to_the_installed_app(self):
        self.assertIn('<script defer src="/assets/under-contract-companion.js"></script>', INDEX)
        self.assertIn("'/assets/under-contract-companion.js'", WORKER)
        self.assertIn("homeofferflow-shell-v76", WORKER)


if __name__ == "__main__":
    unittest.main()

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

    def test_private_save_uses_the_authenticated_owner_scoped_api(self):
        self.assertIn("action: 'save_agent_contract_timeline'", SCRIPT)
        self.assertIn("expectedUpdatedAt: saved.updatedAt || null", SCRIPT)
        self.assertIn("Authorization: `Bearer ${root.hofAuth?.session?.access_token || ''}`", SCRIPT)
        self.assertNotIn("getSupabaseClient", SCRIPT)
        self.assertNotIn("client.from('hof_offers')", SCRIPT)
        self.assertIn("const tracking = result.tracking", SCRIPT)
        self.assertIn("root.hofAuth?.session?.user?.id === user.id", SCRIPT)

    def test_dates_require_signed_contract_confirmation_and_avoid_false_precision(self):
        self.assertIn("I confirm this offer was accepted and the dates entered are from the fully signed contract.", SCRIPT)
        self.assertIn("Some depend on receipt, weekends, legal holidays, or later events and are not calculated here.", SCRIPT)
        self.assertIn("5:00 p.m. local time where the property is located", SCRIPT)
        self.assertIn("Use the fully signed contract", SCRIPT)

    def test_optional_transaction_milestones_are_manually_confirmed_and_bounded(self):
        self.assertIn("Other dates confirmed in the signed contract", SCRIPT)
        self.assertIn("Add up to 12 dates exactly as stated", SCRIPT)
        self.assertIn("HomeOfferFlow will not calculate these dates.", SCRIPT)
        self.assertIn("normalizeMilestones", SCRIPT)
        self.assertIn("{ rejectDuplicates: true }", SCRIPT)
        self.assertIn("Enter each confirmed date once", SCRIPT)
        self.assertIn("milestones,", SCRIPT)
        self.assertIn("Date entered by the agent from the fully signed contract or a written amendment.", SCRIPT)

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
        self.assertRegex(WORKER, r"homeofferflow-shell-v\d+")


if __name__ == "__main__":
    unittest.main()

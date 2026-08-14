from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "migrations" / "20260809221515_homeofferflow_legal_acceptance_records.sql").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ONDEMAND = (ROOT / "ondemand.html").read_text(encoding="utf-8")


class LegalAcceptanceRecordTests(unittest.TestCase):
    def test_immutable_versioned_acceptance_records_are_owner_scoped(self):
        self.assertIn("create table if not exists public.hof_legal_acceptances", MIGRATION)
        self.assertIn("unique (user_id, policy_version)", MIGRATION)
        self.assertIn("enable row level security", MIGRATION)
        self.assertIn("revoke all on table public.hof_legal_acceptances from anon", MIGRATION)
        self.assertIn("hof_legal_acceptances_select_own", MIGRATION)
        self.assertIn("hof_legal_acceptances_insert_own", MIGRATION)
        self.assertNotIn("for update", MIGRATION.lower())

    def test_offer_wizard_records_current_policy_version_without_replacing_event_metric(self):
        self.assertIn("recordCurrentLegalAcceptance", INDEX)
        self.assertIn("hof_legal_acceptances", INDEX)
        self.assertIn("legal_terms_accepted", INDEX)
        self.assertIn("policy_version: LEGAL_POLICY_VERSION", INDEX)

    def test_ondemand_checkout_records_consent_before_creating_checkout_session(self):
        start = ONDEMAND.index("async function startCheckout()")
        end = ONDEMAND.index("async function init()", start)
        checkout = ONDEMAND[start:end]
        self.assertIn("await recordLegalAcceptance()", checkout)
        self.assertIn('source: "ondemand_checkout"', ONDEMAND)
        self.assertIn("LEGAL_POLICY_VERSION", ONDEMAND)

    def test_receipt_labels_each_current_legal_acceptance_path_accurately(self):
        self.assertIn("subscription_checkout: 'Subscription enrollment'", INDEX)
        self.assertIn("ondemand_checkout: 'OnDemand enrollment'", INDEX)
        self.assertIn("offer_wizard: 'Offer workspace'", INDEX)


if __name__ == "__main__":
    unittest.main()

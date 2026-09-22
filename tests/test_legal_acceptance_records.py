from pathlib import Path
import subprocess
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

    def test_browser_acceptance_cache_is_scoped_to_the_authenticated_user(self):
        scoped_key = "hof_legal_acceptance_recorded_${LEGAL_POLICY_VERSION}_${user.id}"
        self.assertIn(scoped_key, ONDEMAND)
        self.assertEqual(INDEX.count(scoped_key), 2)
        self.assertIn("hof_legal_acceptance_${LEGAL_POLICY_VERSION}_${acceptanceUserId}", INDEX)
        self.assertNotIn("`hof_legal_acceptance_recorded_${LEGAL_POLICY_VERSION}`", ONDEMAND)
        self.assertNotIn("`hof_legal_acceptance_recorded_${LEGAL_POLICY_VERSION}`", INDEX)

    def test_ondemand_acceptance_runtime_records_each_shared_browser_identity(self):
        script = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('async function recordLegalAcceptance()');
const end = html.indexOf('async function loadConfig()', start);
if (start < 0 || end < 0) throw new Error('recordLegalAcceptance not found');
const LEGAL_POLICY_VERSION = '2026-07-30';
const state = {session: {user: {id: 'agent-1'}}};
const values = new Map();
const sessionStorage = {
  getItem(key) { return values.has(key) ? values.get(key) : null; },
  setItem(key, value) { values.set(key, value); }
};
const inserts = [];
const client = {from() { return {async insert(row) { inserts.push(row); return {error: null}; }}; }};
eval(html.slice(start, end));
(async () => {
  await recordLegalAcceptance();
  await recordLegalAcceptance();
  state.session = {user: {id: 'agent-2'}};
  await recordLegalAcceptance();
  if (inserts.length !== 2) throw new Error(`expected two user receipts, got ${inserts.length}`);
  if (inserts[0].user_id !== 'agent-1' || inserts[1].user_id !== 'agent-2') {
    throw new Error('legal acceptance receipts were not user-scoped');
  }
})().catch(error => { console.error(error); process.exit(1); });
"""
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "ondemand.html")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_receipt_labels_each_current_legal_acceptance_path_accurately(self):
        self.assertIn("subscription_checkout: 'Subscription enrollment'", INDEX)
        self.assertIn("ondemand_checkout: 'OnDemand enrollment'", INDEX)
        self.assertIn("offer_wizard: 'Offer workspace'", INDEX)


if __name__ == "__main__":
    unittest.main()

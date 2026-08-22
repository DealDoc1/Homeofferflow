from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrokerageTxrAgentAttestationTests(unittest.TestCase):
    def test_migration_adds_auditable_member_attestation_without_license_inference(self):
        sql = (ROOT / "supabase" / "homeofferflow_brokerage_txr_agent_attestation.sql").read_text(encoding="utf-8")
        for expected in (
            "txr_agent_authorized",
            "txr_agent_attested_by",
            "txr_agent_attested_at",
            "hof_brokerage_members_txr_agent_attestation_check",
            "not inferred from a license number",
            "revoke update on table public.hof_brokerage_members from anon, authenticated",
        ):
            self.assertIn(expected, sql)

    def test_shared_library_draft_does_not_require_authenticated_agent_attestation(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        start = api.index("async def _create_representation_draft")
        end = api.index("async def _create_txr_1507_draft", start)
        self.assertNotIn("_record_agent_txr_attestation", api[start:end])

    def test_each_restricted_form_ui_uses_the_shared_library_without_attestation(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("HomeOfferFlow records this attestation with my active brokerage membership.", html)

    def test_broker_dashboard_shows_attestation_status_without_buyer_details(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("txr_agent_authorized,txr_agent_attested_at", api)
        self.assertIn('"txrAgentAuthorized": member.get("txr_agent_authorized") is True', api)
        self.assertIn("TXR/NAR attestation", html)
        self.assertIn("Not yet attested", html)
        self.assertIn('"buyerDetailsIncluded": False', api)

    def test_suspension_clears_prior_agent_attestation(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        segment = api[api.index("async def _set_brokerage_member_status"):api.index("def _parse_partner_lead_update")]
        self.assertIn('"txr_agent_authorized": False', segment)
        self.assertIn('"txr_agent_attested_by": None', segment)
        self.assertIn('"txr_agent_attested_at": None', segment)


if __name__ == "__main__":
    unittest.main()

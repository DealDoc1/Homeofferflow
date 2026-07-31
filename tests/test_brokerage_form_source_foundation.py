from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_brokerage_form_sources.sql").read_text()
LISTING_EXPANSION = (ROOT / "supabase" / "homeofferflow_expand_brokerage_listing_form_sources.sql").read_text()
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SERVER_ONLY = (ROOT / "supabase" / "homeofferflow_brokerage_form_sources_server_only_select.sql").read_text(encoding="utf-8")
BROKERAGE_INDEXES = (ROOT / "supabase" / "homeofferflow_brokerage_fk_indexes.sql").read_text(encoding="utf-8")
BROKERAGE_QA = (ROOT / "docs" / "BROKERAGE_ADMIN_LIVE_QA.md").read_text(encoding="utf-8")


class BrokerageFormSourceFoundationTests(unittest.TestCase):
    def test_source_forms_are_private_and_brokerage_scoped(self):
        self.assertIn("create table if not exists public.hof_brokerage_form_sources", MIGRATION)
        self.assertIn("brokerage_id uuid not null", MIGRATION)
        self.assertIn("'brokerage-form-sources'", MIGRATION)
        self.assertIn("public, file_size_limit", MIGRATION)
        self.assertIn("false,", MIGRATION)

    def test_only_reviewed_txr_forms_are_allowed_by_the_initial_catalog(self):
        for form_code in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            self.assertIn(f"'{form_code}'", MIGRATION)
        self.assertIn("authorization_attested boolean not null default false", MIGRATION)
        self.assertIn("authorized_by_user_id", MIGRATION)
        self.assertIn("authorized_at", MIGRATION)

    def test_agents_cannot_download_source_forms_from_storage(self):
        self.assertIn("hof_brokerage_form_sources_storage_admin_manage", MIGRATION)
        self.assertIn("m.role in ('broker_admin', 'owner')", MIGRATION)
        self.assertIn("Agents never get Storage access", MIGRATION)

    def test_private_source_uploads_record_an_exact_pdf_fingerprint(self):
        fingerprint_migration = (ROOT / "supabase" / "homeofferflow_brokerage_form_source_fingerprint.sql").read_text(encoding="utf-8")
        self.assertIn("source_sha256", fingerprint_migration)
        self.assertIn("^[0-9a-f]{64}$", fingerprint_migration)
        self.assertIn("crypto.subtle.digest('SHA-256'", HTML)
        self.assertIn("source_sha256: sourceSha256", HTML)

    def test_brokerage_setup_records_txr_authorization_policy(self):
        authorization_migration = (ROOT / "supabase" / "homeofferflow_brokerage_txr_authorization.sql").read_text(encoding="utf-8")
        self.assertIn("txr_all_agents_authorized", authorization_migration)
        self.assertIn("txr_authorization_attested_by", authorization_migration)
        self.assertIn("brandTxrAuthorization", HTML)
        self.assertIn("current members of both NAR and Texas REALTORS", HTML)
        self.assertIn("Each agent still confirms their own current authorization", HTML)
        self.assertIn("brandTxrAttestation", HTML)
        self.assertIn("Check the brokerage Texas REALTORS® / NAR attestation before saving", HTML)
        self.assertIn("This is not inferred from a license number", HTML)

    def test_every_restricted_txr_workflow_requires_individual_nar_texas_realtors_attestation(self):
        """Keep the point-of-use membership/authority gate on every TXR workflow."""
        attestation = "I attest that I am a current Texas REALTORS® / NAR member"
        self.assertEqual(HTML.count(attestation), 4)
        for form_code in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            marker = f"id=\"hof-{form_code.lower().replace('-', '')}-drafts-v1\""
            self.assertIn(marker, HTML)
        dashboard = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(dashboard.count("formUseAttested"), 4)
        self.assertIn("form_use_attested_by", dashboard)
        self.assertIn("form_use_attested_at", dashboard)

    def test_brokerage_rollout_foreign_keys_have_targeted_indexes(self):
        for index_name in (
            "hof_brokerage_form_sources_authorized_by_user_id_idx",
            "hof_brokerage_invites_accepted_by_idx",
            "hof_brokerage_invites_invited_by_idx",
            "hof_brokerage_members_invited_by_idx",
            "hof_brokerage_members_user_id_idx",
            "hof_brokerages_created_by_idx",
            "hof_brokerages_txr_authorization_attested_by_idx",
        ):
            self.assertIn(f"create index if not exists {index_name}", BROKERAGE_INDEXES)
        self.assertIn("do not alter RLS", BROKERAGE_INDEXES)

    def test_broker_admin_qa_covers_positive_and_negative_txr_gate_paths(self):
        for text in (
            "Not confirmed yet",
            "all participating agents are authorized Texas REALTORS",
            "each agent must attest individually",
            "SHA-256 fingerprint",
            "No / not all",
            "completed signed PDF",
        ):
            self.assertIn(text, BROKERAGE_QA)

    def test_listing_side_sources_are_private_and_do_not_activate_workflows(self):
        for form_code in ("TXR-1101", "TXR-1102", "TXR-1406", "TXR-1418"):
            self.assertIn(f"'{form_code}'", MIGRATION)
            self.assertIn(f"'{form_code}'", LISTING_EXPANSION)
            self.assertIn(f"'{form_code}'", HTML)
        self.assertIn("does not enable form completion", LISTING_EXPANSION)
        self.assertIn("Source approval never activates a workflow", HTML)

    def test_broker_admin_can_upload_attested_private_source_but_cannot_activate_a_workflow(self):
        self.assertIn("Brokerage-approved form sources", HTML)
        self.assertIn("I am authorized to upload and approve this exact source PDF", HTML)
        self.assertIn("agents cannot download them from HomeOfferFlow", HTML)
        self.assertIn("It is not yet an active signing workflow.", HTML)
        self.assertIn("authorization_attested: true", HTML)

    def test_source_metadata_reads_are_server_only(self):
        self.assertIn("revoke select on table public.hof_brokerage_form_sources from authenticated", SERVER_ONLY)
        self.assertIn("grant insert, update, delete on table public.hof_brokerage_form_sources to authenticated", SERVER_ONLY)
        self.assertIn("scope=brokerage_form_sources", HTML)
        self.assertIn("scope=approved_brokerage_sources", HTML)
        self.assertIn("_brokerage_form_sources_payload", (ROOT / "api" / "admin-dashboard.py").read_text())
        dashboard_source = (ROOT / "api" / "admin-dashboard.py").read_text()
        self.assertIn("_json(self, 403, {\"error\": str(exc)})", dashboard_source)
        # Browser reads must use the server endpoint; only the authorized upload
        # path may still issue a direct insert into the private registry.
        self.assertNotIn(".from('hof_brokerage_form_sources')\n        .select", HTML)


if __name__ == "__main__":
    unittest.main()

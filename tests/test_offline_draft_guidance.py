from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class OfflineDraftGuidanceTests(unittest.TestCase):
    def test_wizard_explains_offline_local_draft_safety(self):
        self.assertIn('id="connectionStatus"', INDEX)
        self.assertIn('id="appConnectivityNotice"', INDEX)
        self.assertIn('Local drafts remain available', INDEX)
        self.assertIn('Offline — draft stays on this device', INDEX)
        self.assertIn('Reconnect before previewing PDFs, sending signature requests, checkout, or cloud sync.', INDEX)
        self.assertIn("window.addEventListener('offline', updateConnectionStatus)", INDEX)
        self.assertIn("window.addEventListener('online', updateConnectionStatus)", INDEX)

    def test_offline_draft_save_does_not_report_a_cloud_sync_failure(self):
        self.assertIn("hofAuth?.session && navigator.onLine !== false", INDEX)
        self.assertIn("try { saveDraftNow(); } catch (e) {}", INDEX)

    def test_signed_in_agent_draft_syncs_when_connection_returns(self):
        self.assertIn("let __hofWasOffline = navigator.onLine === false", INDEX)
        self.assertIn("Back online — syncing your saved draft…", INDEX)
        self.assertIn("const isAccountDraft = (state?.data?.userType || '') !== 'homebuyer' && hofAuth?.session && hasMeaningfulCloudDraft();", INDEX)
        self.assertIn("syncCloudDraftSave();", INDEX)

    def test_offline_shell_cache_is_versioned_for_the_new_guidance(self):
        self.assertIn("homeofferflow-shell-v39", WORKER)


if __name__ == "__main__":
    unittest.main()

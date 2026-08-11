from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class CloudDraftSaveRecoveryTests(unittest.TestCase):
    def test_cloud_save_failure_is_not_reported_as_success(self):
        start = HTML.index("async function syncCloudDraftSave()")
        end = HTML.index("function getDraftSnapshot()", start)
        saver = HTML[start:end]
        self.assertIn("if (saved)", saver)
        self.assertIn("showCloudSaveFailure()", saver)
        success_branch, failure_branch = saver.split("if (saved)", 1)[1].split("} else", 1)
        self.assertIn("Cloud Saved", success_branch)
        self.assertIn("showCloudSaveFailure()", failure_branch)

    def test_cloud_sync_failure_has_an_explicit_retry_action(self):
        start = HTML.index("function showCloudSaveFailure()")
        end = HTML.index("function getDraftSnapshot()", start)
        recovery = HTML[start:end]
        self.assertIn("Local draft saved; cloud sync needs retry.", recovery)
        self.assertIn("retryCloudDraftSave", recovery)
        self.assertIn("cloud_draft_save_retried", recovery)

    def test_cloud_saves_are_serialized_and_empty_drafts_stay_local(self):
        self.assertIn("let __hofCloudDraftSaveInFlight = false;", HTML)
        self.assertIn("let __hofCloudDraftSaveQueued = false;", HTML)
        start = HTML.index("async function syncCloudDraftSave()")
        end = HTML.index("function getDraftSnapshot()", start)
        sync = HTML[start:end]
        self.assertIn("if (__hofCloudDraftSaveInFlight)", sync)
        self.assertIn("__hofCloudDraftSaveQueued = true", sync)
        self.assertIn("if (__hofCloudDraftSaveQueued)", sync)
        saver_start = HTML.index("function saveDraftNow()")
        saver_end = HTML.index("function scheduleDraftSave()", saver_start)
        saver = HTML[saver_start:saver_end]
        self.assertIn("hasMeaningfulCloudDraft()", saver)
        self.assertIn("syncCloudDraftSave()", saver)
        self.assertNotIn("saveOfferDraftToSupabase('Draft').then", saver)

    def test_autosave_preserves_a_previously_generated_packet_state(self):
        start = HTML.index("async function saveOfferDraftToSupabase(status = 'Draft')")
        end = HTML.index("function setFeedbackStatus", start)
        saver = HTML[start:end]
        self.assertIn("const existingGeneratedAt", saver)
        self.assertIn("const hasGeneratedPacket", saver)
        self.assertIn("status === 'Draft' && hasGeneratedPacket ? 'Generated' : status", saver)
        self.assertIn("status: persistedStatus", saver)
        self.assertIn("generated_at: persistedGeneratedAt", saver)

    def test_resume_hydrates_packet_state_from_persisted_offer_columns(self):
        start = HTML.index("async function resumeOffer(id, isRetry = false)")
        end = HTML.index("async function duplicateOffer", start)
        resume = HTML[start:end]
        self.assertIn("generatedAt: offer.offer_data?.generatedAt || offer.generated_at", resume)
        self.assertIn("signwellDocumentId: offer.offer_data?.signwellDocumentId || offer.signwell_document_id", resume)
        self.assertIn("signwellStatus: offer.offer_data?.signwellStatus || offer.signwell_status", resume)


if __name__ == "__main__":
    unittest.main()

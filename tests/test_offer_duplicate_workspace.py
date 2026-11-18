from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class OfferDuplicateWorkspaceTests(unittest.TestCase):
    def test_duplicate_uses_authenticated_server_action_and_preserves_recovery(self):
        start = HTML.index("async function duplicateOffer(id)")
        end = HTML.index("\n  async function reuseOfferTerms", start)
        body = HTML[start:end]

        self.assertIn("window.hofDuplicateAgentOffer(id)", body)
        self.assertNotIn("from('hof_offers')", body)
        self.assertNotIn("getOfferById(id)", body)
        self.assertIn("loadMyOffers().catch", body)
        self.assertIn("return resumeOffer(duplicate.id)", body)
        self.assertIn("duplicate_retry_clicked", body)
        self.assertIn("return duplicateOffer(id, true, openAfterDuplicate, request)", body)

    def test_both_offer_detail_views_use_the_authenticated_api(self):
        for owner in ("root", "window"):
            start = HTML.index(f"{owner}.viewOfferDetails = async function(offerId)")
            end = HTML.index("\n  };", start)
            body = HTML[start:end]
            self.assertIn(f"{owner}.hofLoadAgentOfferDetail(offerId)", body)
            self.assertNotIn("getSupabaseClient", body)
            self.assertIn("detail.activityUnavailable", body)

    def test_resume_lookup_uses_the_authenticated_source_api(self):
        start = HTML.index("async function getOfferById(id)")
        end = HTML.index("\n  function applyOfferDataToFields", start)
        body = HTML[start:end]
        self.assertIn("window.hofLoadAgentOfferSource(id)", body)
        self.assertNotIn("getSupabaseClient", body)

    def test_repeat_use_actions_offer_one_retry_for_transient_failures(self):
        resume_start = HTML.index("async function resumeOffer(id")
        resume_end = HTML.index("\n  async function duplicateOffer", resume_start)
        duplicate_start = HTML.index("async function duplicateOffer(id")
        duplicate_end = HTML.index("\n  async function deleteOffer", duplicate_start)
        resume = HTML[resume_start:resume_end]
        duplicate = HTML[duplicate_start:duplicate_end]
        self.assertIn("isRetry = false", resume)
        self.assertIn("resume_retry_clicked", resume)
        self.assertIn("return resumeOffer(id, true)", resume)
        self.assertIn("arguments[1] === true", duplicate)
        self.assertIn("duplicate_retry_clicked", duplicate)
        self.assertIn("return duplicateOffer(id, true, openAfterDuplicate, request)", duplicate)
        self.assertIn("openAfterDuplicate", duplicate)
        self.assertIn("return resumeOffer(duplicate.id)", duplicate)

    def test_duplicate_actions_open_the_new_copy_for_immediate_editing(self):
        standard = HTML.count("false, true)\">Duplicate &amp; edit</button>")
        expired_recovery = HTML.count("false, true)\">${isExpired ? 'Duplicate &amp; edit to resend' : 'Duplicate &amp; edit'}</button>")
        self.assertGreaterEqual(standard + expired_recovery, 5)


if __name__ == "__main__":
    unittest.main()

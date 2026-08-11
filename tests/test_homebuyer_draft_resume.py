from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class HomebuyerDraftResumeTests(unittest.TestCase):
    def test_landing_ctas_resume_a_meaningful_local_draft_instead_of_resetting_it(self):
        self.assertIn("function resumableLocalOfferDraft()", HTML)
        self.assertIn("return step > 0 && hasSavedValues ? draft : null;", HTML)
        self.assertIn("if (resumableLocalOfferDraft()) {\n      resumeLocalOfferDraft();", HTML)
        self.assertIn("Resume Your Saved Offer", HTML)
        self.assertIn("Resumed Local Offer Draft", HTML)

    def test_resume_respects_draft_owner_and_never_runs_after_payment_return(self):
        start = HTML.index("function resumableLocalOfferDraft()")
        end = HTML.index("function refreshResumeOfferCtas()", start)
        helper = HTML[start:end]
        self.assertIn("window.__hofPaymentReturn", helper)
        self.assertIn("ownerUserId && ownerUserId !== currentUserId", helper)

    def test_resume_keeps_the_saved_step_while_new_offers_still_start_at_step_one(self):
        start = HTML.index("function openWizard(skipAuthGate = false, resumeDraft = false)")
        end = HTML.index("function closeWizard()", start)
        open_wizard = HTML[start:end]
        self.assertIn("if (resumeDraft)", open_wizard)
        self.assertIn("getCurrentSteps().length - 1", open_wizard)
        self.assertIn("} else {\n      state.step = 0;", open_wizard)
        self.assertIn("openWizard(true, true);", HTML)

    def test_returning_home_reveals_the_resume_choice_after_local_save(self):
        return_start = HTML.index("function returnHomeFromWizard()")
        return_end = HTML.index("function startNewOffer()", return_start)
        self.assertIn("setTimeout(refreshResumeOfferCtas, 300);", HTML[return_start:return_end])
        self.assertIn("restoreDraft();\n        refreshResumeOfferCtas();", HTML)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class PropertyFirstInterviewTests(unittest.TestCase):
    def test_new_buyer_and_account_offer_paths_start_with_property_after_their_entry_screen(self):
        self.assertIn(
            "steps: ['step0','step05','step2','step1','step3','step5','step6','step7','step8','step9','stepSuccess']",
            HTML,
        )
        self.assertIn(
            "steps: ['step0','step2','step1','step3','step5','step6','step7','step8','stepSuccess']",
            HTML,
        )
        self.assertIn(
            "names: ['Disclaimer','Have You Seen It?','Property & Leases','Parties & Contact'",
            HTML,
        )

    def test_older_local_drafts_resume_the_same_logical_screen_after_reordering(self):
        self.assertIn("const HOF_WIZARD_ORDER_VERSION = 2;", HTML)
        self.assertIn("wizardOrderVersion: HOF_WIZARD_ORDER_VERSION", HTML)
        self.assertIn("function restoredWizardStep(draft)", HTML)
        self.assertIn("if (savedStep === 2) return 3;", HTML)
        self.assertIn("if (savedStep === 3) return 2;", HTML)
        self.assertIn("if (savedStep === 1) return 2;", HTML)
        self.assertIn("if (savedStep === 2) return 1;", HTML)
        self.assertIn("const stepToRestore = restoredWizardStep(draft);", HTML)


if __name__ == "__main__":
    unittest.main()

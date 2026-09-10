"""Guard the shared guided-form presentation and representation-specific help."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
CSS = HTML.split('<style id="hof-txr1507-drafts-v1">', 1)[1].split('</style>', 1)[0]


class GuidedFormPresentationTests(unittest.TestCase):
    def test_dialog_uses_a_defined_opaque_background_and_readable_input_text(self):
        self.assertNotIn("var(--navy-dark)", CSS)
        self.assertIn("background:var(--navy,#0d1f35)", CSS)
        self.assertIn("color:var(--white,#fff)", CSS)
        self.assertIn("min-height:44px", CSS)
        self.assertIn("font:400 1rem/1.4", CSS)

    def test_long_contact_labels_and_actions_fit_small_screens(self):
        self.assertIn("repeat(2,minmax(0,1fr))", CSS)
        self.assertIn("overflow-wrap:anywhere", CSS)
        self.assertIn("min-width:0", CSS)
        self.assertIn("max-height:calc(100dvh - 2rem)", CSS)
        self.assertIn(".hof-agreement-footer { display:flex; flex-wrap:wrap", CSS)
        self.assertIn(".hof-agreement-footer > button { flex:1 1 100%; }", CSS)

    def test_native_choice_controls_do_not_receive_full_width_text_input_sizing(self):
        self.assertIn('input:not([type="checkbox"]):not([type="radio"])', CSS)
        self.assertIn('input[type="checkbox"], .hof-agreement-grid input[type="radio"]', CSS)
        self.assertIn("width:1.1rem; height:1.1rem; flex:0 0 auto", CSS)

    def test_representation_guidance_is_hidden_until_a_relevant_answer_is_known(self):
        self.assertIn('id="unrepresentedConcessionTip" style="display:none;"', HTML)
        # Called after audience changes, representation selection, and draft restore.
        self.assertEqual(HTML.count("updateUnrepresentedConcessionTip();"), 3)

    def test_restoring_other_answers_preserves_agent_details_on_the_agent_path(self):
        block = HTML.split("function restoreConditionalSections()", 1)[1].split("function clearSavedDraft", 1)[0]
        self.assertIn("const hasBuyerAgent = state.data.userType === 'agent'", block)
        self.assertIn("? 'yes' : document.querySelector", block)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for browser-helper regression checks")
    def test_representation_tip_matches_current_answer_and_path(self):
        helper = re.search(r"  function updateUnrepresentedConcessionTip\(\) \{[\s\S]*?\n  \}", HTML).group(0)
        cases = [
            ["agent", "no", "no", "none"],
            ["agent", "yes", "yes", "none"],
            ["homebuyer", "yes", "no", "none"],
            ["homebuyer", "no", "yes", "block"],
            ["homebuyer", "", "", "none"],
            ["investor", "yes", "yes", "none"],
            ["investor", "no", "no", "block"],
            ["homebuyer", "", "yes", "none"],
            ["homebuyer", "", "no", "block"],
        ]
        source = "const assert = require('node:assert/strict'); let selected; let tip; const state={data:{}}; const document={getElementById:()=>tip}; const getRadio=()=>selected;\n" + helper
        source += "\nfor (const [role,answer,saved,expected] of " + json.dumps(cases) + ") { state.data={userType:role,hasBuyerAgent:saved}; selected=answer; tip={style:{}}; updateUnrepresentedConcessionTip(); assert.equal(tip.style.display,expected); } tip=null; updateUnrepresentedConcessionTip();"
        result = subprocess.run([shutil.which("node"), "-e", source], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

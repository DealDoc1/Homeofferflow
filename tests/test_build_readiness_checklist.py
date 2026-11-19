from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "build-readiness.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "assets" / "build-readiness-checklist.js").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class BuildReadinessChecklistTests(unittest.TestCase):
    def test_seven_step_checklist_is_private_accessible_and_printable(self):
        self.assertEqual(PAGE.count("data-build-readiness-task="), 7)
        self.assertIn('aria-live="polite"', PAGE)
        self.assertIn('id="buildReadinessInstall" hidden', PAGE)
        self.assertIn("OFFLINE_PUBLIC_IMAGE_PATHS.has(requestUrl.pathname) && !requestUrl.search", WORKER)
        self.assertIn("Only checkmarks are saved in this browser on this device", PAGE)
        self.assertIn("Don’t enter client, financial, or other private information here", PAGE)
        self.assertIn("@media print", PAGE)
        self.assertIn("checklist-print-brand{display:block", PAGE)
        self.assertIn("text-decoration:none", PAGE)
        self.assertIn("(214) 364-9890 · andrew@ondemanddfw.com · homeofferflow.com/build-readiness", PAGE)
        self.assertIn(".checklist-items{grid-template-columns:1fr}", PAGE)
        self.assertIn('src="/assets/build-readiness-checklist.js"', PAGE)
        self.assertIn('<picture class="hero-picture">', PAGE)
        self.assertIn('<source media="(max-width: 640px)" srcset="/assets/build-readiness-blueprint-mobile.jpg" width="1254" height="1254">', PAGE)
        self.assertIn('src="/assets/build-readiness-blueprint-banner.jpg" width="1280" height="474"', PAGE)
        self.assertIn("'/assets/build-readiness-checklist.js'", WORKER)
        self.assertIn("hof:build-readiness-checklist:v1", SCRIPT)
        self.assertNotIn("fetch(", SCRIPT)

    def test_agent_copy_action_uses_the_same_public_blueprint_on_both_surfaces(self):
        client_path = "/build-readiness?utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=equity_to_keys"
        for filename in ("agents.html", "index.html"):
            markup = (ROOT / filename).read_text(encoding="utf-8")
            with self.subTest(page=filename):
                self.assertIn(f'data-blueprint-link href="{client_path}"', markup)
                self.assertIn("data-copy-blueprint hidden", markup)
                self.assertIn('data-blueprint-status role="status" aria-live="polite"', markup)
                self.assertIn('<label data-manual-blueprint hidden>Client link<input type="url" readonly></label>', markup)
                self.assertIn('src="/assets/agent-build-readiness-share.js"', markup)
        self.assertIn("'/assets/agent-build-readiness-share.js'", WORKER)
        self.assertIn("'/assets/agent-build-readiness-share.css'", WORKER)

    def test_browser_runtime_restores_saves_clears_and_handles_storage_failure(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests" / "build_readiness_checklist.runtime.cjs")],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

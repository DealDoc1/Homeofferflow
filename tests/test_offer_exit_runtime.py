from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OfferExitRuntimeTests(unittest.TestCase):
    def test_actual_exit_save_and_resume_code(self):
        result = subprocess.run(['node', '--test', str(ROOT / 'tests/offer_exit.runtime.cjs')],
                                cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_only_non_destructive_exit_loses_confirmation(self):
        html = (ROOT / 'index.html').read_text()
        exit_code = html.split('  function returnHomeFromWizard() {', 1)[1].split('  function startNewOffer()', 1)[0]
        self.assertNotIn('confirm(', exit_code)
        self.assertIn('scheduleDraftSave?.()', exit_code)
        new_code = html.split('  function startNewOffer() {', 1)[1].split('  function ', 1)[0]
        self.assertIn("confirm('Start a new offer? This will clear saved work on this device.')", new_code)

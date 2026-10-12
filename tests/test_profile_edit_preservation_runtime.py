from pathlib import Path
import re
import subprocess
import unittest


class ProfileEditPreservationRuntimeTests(unittest.TestCase):
    def test_actual_profile_renderer_edit_lifecycle(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('profile_edit_preservation.runtime.cjs'))],
                                capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_edit_cache_is_memory_only_and_skips_sensitive_controls(self):
        html = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
        helper = re.search(r'<script id="hof-profile-edit-draft-v1">(.*?)</script>', html, re.S).group(1)
        for forbidden in ['localStorage', 'sessionStorage', 'fetch(', 'XMLHttpRequest']:
            self.assertNotIn(forbidden, helper)
        self.assertIn("'hidden', 'password', 'file'", helper)
        self.assertIn('password|token|secret|apiKey', helper)
        self.assertIn('window.hofClearProfileEditDraft?.();', html)

from pathlib import Path
import shutil
import subprocess
import unittest


class SellerPreviewLinksTests(unittest.TestCase):
    def test_normal_and_legacy_links_keep_the_current_preview_and_clear_stale_answers(self):
        node = shutil.which('node')
        if not node: self.skipTest('Node runtime unavailable')
        result = subprocess.run([node, str(Path(__file__).with_name('seller_questionnaire_preview_links.runtime.cjs'))],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

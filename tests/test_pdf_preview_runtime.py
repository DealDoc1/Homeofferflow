from pathlib import Path
import shutil
import subprocess
import unittest


class PdfPreviewRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for browser-helper runtime tests")
    def test_production_preview_helpers(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("pdf_preview.runtime.cjs"))],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

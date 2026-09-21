"""Execute actual interview upload functions with delayed file reads."""
from pathlib import Path
import shutil
import subprocess
import unittest


class AttachmentUploadIsolationTests(unittest.TestCase):
    def test_delayed_uploads_remain_scoped_to_their_offer(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required for attachment runtime verification')
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [node, '--test', 'tests/attachment_upload_isolation.runtime.cjs'],
            cwd=root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

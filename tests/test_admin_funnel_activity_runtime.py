from pathlib import Path
import shutil
import subprocess
import unittest


class AdminFunnelActivityTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for admin rendering verification')
    def test_rendered_acquisition_activity(self):
        result = subprocess.run(
            ['node', '--test', 'tests/admin_funnel_activity.runtime.cjs'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

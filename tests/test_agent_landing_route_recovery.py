"""Run the public agent deep-link recovery behavior in an isolated browser-like VM."""

from pathlib import Path
import shutil
import subprocess
import unittest


class AgentLandingRouteRecoveryTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for route recovery runtime tests')
    def test_signed_in_and_signed_out_agent_route_recovery(self):
        runtime = Path(__file__).with_name('agent_landing_route_recovery.runtime.cjs')
        result = subprocess.run(['node', '--test', str(runtime)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

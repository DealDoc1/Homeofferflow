from pathlib import Path
import subprocess
import unittest


class AgentLandingAuthFunnelRuntimeTests(unittest.TestCase):
    def test_agent_landing_auth_funnel_runtime(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("agent_landing_auth_funnel.runtime.cjs"))],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

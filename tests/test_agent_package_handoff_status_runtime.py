from pathlib import Path
import subprocess
import unittest


class AgentPackageHandoffStatusRuntimeTests(unittest.TestCase):
    def test_runtime_feedback_tracks_real_workspace_state(self):
        runtime = Path(__file__).with_name("agent_package_handoff_status.runtime.cjs")
        result = subprocess.run(
            ["node", "--test", str(runtime)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

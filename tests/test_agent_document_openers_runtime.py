"""Execute the actual guided-form opener script, rather than match its labels."""

from pathlib import Path
import shutil
import subprocess
import unittest


class AgentDocumentOpenerRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to execute browser-script tests")
    def test_guided_form_buttons_and_loading_behavior(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("agent_document_openers.runtime.cjs"))],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

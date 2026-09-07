from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ONDEMAND = (ROOT / "ondemand.html").read_text(encoding="utf-8")


class OnDemandScriptSyntaxTests(unittest.TestCase):
    def test_inline_enrollment_script_parses_in_node(self):
        match = re.search(r"<script>\s*([\s\S]*?)</script>", ONDEMAND)
        self.assertIsNotNone(match, "The OnDemand enrollment script is missing.")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", encoding="utf-8") as script_file:
            script_file.write(match.group(1))
            script_file.flush()
            result = subprocess.run(
                ["node", "--check", script_file.name],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

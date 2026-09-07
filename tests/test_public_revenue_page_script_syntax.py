from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ACQUISITION_PAGES = (
    "index.html",
    "agents.html",
    "buyers.html",
    "sellers.html",
    "investors.html",
    "ondemand.html",
    "partners.html",
)
SCRIPT_RE = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>[\s\S]*?)</script>", re.IGNORECASE)


class PublicRevenuePageScriptSyntaxTests(unittest.TestCase):
    def test_every_inline_runtime_script_parses(self):
        for page in PUBLIC_ACQUISITION_PAGES:
            source = (ROOT / page).read_text(encoding="utf-8")
            for index, match in enumerate(SCRIPT_RE.finditer(source), start=1):
                attrs = match.group("attrs").lower()
                if "src=" in attrs or "application/ld+json" in attrs:
                    continue
                with self.subTest(page=page, script=index), tempfile.NamedTemporaryFile(
                    mode="w", suffix=".js", encoding="utf-8"
                ) as script_file:
                    script_file.write(match.group("body"))
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

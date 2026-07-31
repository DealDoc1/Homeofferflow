import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "api"


class VercelHobbyBundleTests(unittest.TestCase):
    def test_production_api_bundle_stays_within_hobby_function_limit(self):
        config = json.loads((ROOT / "vercel.json").read_text())
        ignored = set()
        for line in (ROOT / ".vercelignore").read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                ignored.add(line)

        routes = []
        for path in API_ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".js"}:
                continue
            relative = path.relative_to(ROOT).as_posix()
            if "__pycache__" in path.parts or relative in ignored:
                continue
            routes.append(relative)

        self.assertEqual(len(routes), 12, sorted(routes))
        self.assertNotIn("api/fill_pdf_20_19_staging.py", config["functions"])
        self.assertIn("api/fill-pdf.py", config["functions"])


if __name__ == "__main__":
    unittest.main()

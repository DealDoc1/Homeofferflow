import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_vercel_release_manifest.py"
spec = importlib.util.spec_from_file_location("build_vercel_release_manifest", SCRIPT)
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)


class VercelReleaseManifestTests(unittest.TestCase):
    def test_excludes_non_runtime_and_staging_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("ok", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "note.md").write_text("docs", encoding="utf-8")
            (root / "api").mkdir()
            (root / "api" / "fill_pdf_20_19_staging.py").write_text("staging", encoding="utf-8")
            (root / "api" / "fill-pdf.py").write_text("production", encoding="utf-8")
            (root / ".vercel").mkdir()
            (root / ".vercel" / "project.json").write_text("local", encoding="utf-8")
            (root / ".env.local").write_text("secret", encoding="utf-8")
            result = manifest.build_manifest(root)
            self.assertEqual(result["file_count"], 2)
            self.assertEqual([item["file"] for item in result["files"]], ["api/fill-pdf.py", "index.html"])

    def test_hashes_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("same", encoding="utf-8")
            self.assertEqual(manifest.build_manifest(root), manifest.build_manifest(root))


if __name__ == "__main__":
    unittest.main()

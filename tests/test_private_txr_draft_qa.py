import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

from scripts.run_private_txr_draft_qa import run


ROOT = Path(__file__).resolve().parents[1]


class PrivateTxrDraftQaTests(unittest.TestCase):
    def test_runner_is_local_unsigned_only(self):
        source = (ROOT / "scripts" / "run_private_txr_draft_qa.py").read_text(encoding="utf-8")
        self.assertIn("no source upload or signing will occur", source)
        self.assertNotIn("import httpx", source)
        self.assertNotIn("import requests", source)
        self.assertNotIn("create_document", source)
        self.assertNotIn("signwell.com", source)

    def test_run_requires_all_private_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "Missing private source"):
                run(Path(directory), Path(directory) / "out")

    def test_run_is_page_count_guarded_and_writes_only_local_drafts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("scripts.run_private_txr_draft_qa._renderers", return_value={
                "TXR1501": (None, lambda source, data: source, 1),
            }), patch("scripts.run_private_txr_draft_qa._data", return_value={"TXR1501": {}}):
                writer = PdfWriter()
                writer.add_blank_page(width=612, height=792)
                source = BytesIO()
                writer.write(source)
                (root / "TXR1501.pdf").write_bytes(source.getvalue())
                results = run(root, root / "out")
                self.assertEqual(results[0]["pages"], 1)
                self.assertTrue((root / "out" / "TXR1501_draft.pdf").is_file())


if __name__ == "__main__":
    unittest.main()

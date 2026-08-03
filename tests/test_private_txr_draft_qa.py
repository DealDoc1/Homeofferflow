import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_private_txr_draft_qa import run


class PrivateTxrDraftQaTests(unittest.TestCase):
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
                (root / "TXR1501.pdf").write_bytes(b"not-a-pdf")
                with self.assertRaises(Exception):
                    run(root, root / "out")


if __name__ == "__main__":
    unittest.main()


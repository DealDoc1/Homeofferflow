import pathlib
import unittest


HTML = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class FsboRequestConfirmationTests(unittest.TestCase):
    def test_fsbo_submission_keeps_a_durable_intake_handoff(self):
        self.assertIn("downloadFsboRequestSummary", HTML)
        self.assertIn("homeofferflow-fsbo-request-summary.txt", HTML)
        self.assertIn("Seller request saved", HTML)
        self.assertIn("confirm scope, provider involvement, availability, and final pricing", HTML)
        self.assertIn("This is an intake record, not checkout", HTML)


if __name__ == "__main__":
    unittest.main()

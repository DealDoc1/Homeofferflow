import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIGNWELL_ROUTES = (
    ROOT / "api" / "fill-pdf.py",
    ROOT / "api" / "fill_pdf_20_19_staging.py",
)


class SignWellLoggingHygieneTests(unittest.TestCase):
    def test_verbose_signwell_diagnostics_are_explicitly_opt_in(self):
        for route in SIGNWELL_ROUTES:
            source = route.read_text(encoding="utf-8")
            self.assertIn('SIGNWELL_DEBUG_LOGS = os.environ.get("SIGNWELL_DEBUG_LOGS", "false")', source)
            self.assertIn("def signwell_debug(label, payload, limit=3000):", source)
            self.assertNotIn('print("SIGNWELL DEBUG', source)
            self.assertNotIn('print("SIGNWELL RESPONSE BODY:', source)

    def test_failure_log_does_not_dump_signwell_response_body(self):
        for route in SIGNWELL_ROUTES:
            source = route.read_text(encoding="utf-8")
            self.assertIn('print("SignWell document request failed with status", r.status_code)', source)
            self.assertNotIn('print("SIGNWELL RESPONSE STATUS:", r.status_code)', source)


if __name__ == "__main__":
    unittest.main()

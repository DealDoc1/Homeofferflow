import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
API = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")

FORM_CODES = (
    "TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508", "TXR-1905",
    "TXR-1914", "TXR-1917", "TXR-1919", "TXR-1948", "TXR-1953",
    "TXR-1954",
)


class AgentFormSigningContractTests(unittest.TestCase):
    def test_every_shared_form_is_offered_by_the_api_signing_path(self):
        signing_set = re.search(
            r"TXR_SIGNING_FORM_CODES\s*=\s*\{(?P<body>.*?)\n\}",
            API,
            re.DOTALL,
        )
        self.assertIsNotNone(signing_set)
        for code in FORM_CODES:
            self.assertIn(code.replace("-", "_") + "_FORM_CODE", signing_set.group("body"))
        self.assertIn('data.get("action") == "send_txr_agreement_for_signature"', API)

    def test_every_shared_form_is_placed_in_the_prepared_document_queue(self):
        queue = re.search(
            r"const signingFormIds = new Set\(\[(?P<body>.*?)\]\);",
            HTML,
            re.DOTALL,
        )
        self.assertIsNotNone(queue)
        for code in FORM_CODES:
            form_id = "txr" + code.split("-")[1] + "AgreementForm"
            self.assertIn(form_id, queue.group("body"))
        self.assertIn("Review prepared documents", HTML)

    def test_every_addendum_interview_offers_the_same_immediate_review_handoff(self):
        expected = {
            "TXR-1914": "Your draft is ready. <button type=\"button\" class=\"btn-secondary\">Review and send</button>",
            "TXR-1917": "Environmental addendum ready. <button type=\"button\" class=\"btn-secondary\">Review and send</button>",
            "TXR-1919": "Loan-assumption addendum ready. <button type=\"button\" class=\"btn-secondary\">Review and send</button>",
            "TXR-1948": "Appraisal addendum ready. <button type=\"button\" class=\"btn-secondary\">Review and send</button>",
            "TXR-1953": "Lease addendum ready. <button type=\"button\" class=\"btn-secondary\">Review and send</button>",
            "TXR-1954": "Fixture-lease addendum ready. <button type=\"button\" class=\"btn-secondary\">Review and send</button>",
        }
        for form_code, handoff in expected.items():
            with self.subTest(form_code=form_code):
                self.assertIn(handoff, HTML)
        self.assertGreaterEqual(HTML.count("await root.hofOpenPreparedAgreement?.();"), 7)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest

from lib.production_adapter import UnsupportedOfferPathError, validate_supported_offer


ROOT = Path(__file__).resolve().parents[1]


class CustomerFacingPacketValidationTests(unittest.TestCase):
    def test_packet_answer_message_uses_plain_language(self):
        error = UnsupportedOfferPathError(["choose a financing type", "property address"])
        message = str(error)
        self.assertEqual(
            message,
            "Please review these offer details before continuing: choose a financing type, property address",
        )
        for internal_term in ("unsupported", "production", "staging", "path", "TREC 20-19 packet"):
            self.assertNotIn(internal_term, message.lower())

    def test_invalid_financing_does_not_expose_internal_release_language(self):
        with self.assertRaises(UnsupportedOfferPathError) as context:
            validate_supported_offer({"financing": "future_internal_value"})
        message = str(context.exception)
        self.assertIn("choose a financing type", message)
        self.assertNotIn("unsupported financing", message.lower())
        self.assertNotIn("production", message.lower())

    def test_server_and_browser_keep_internal_codes_out_of_customer_copy(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        adapter = (ROOT / "lib" / "production_adapter.py").read_text(encoding="utf-8")
        self.assertIn("action: 'review'", html)
        self.assertIn("Review offer", html)
        self.assertNotIn("not yet available in the production TREC 20-19 packet", adapter)
        self.assertNotIn("staging-only Seller Temporary Residential Lease", adapter)


if __name__ == "__main__":
    unittest.main()

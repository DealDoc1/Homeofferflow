import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


production = load_module("resend_production", ROOT / "api" / "fill-pdf.py")
staging = load_module("resend_staging", ROOT / "api" / "fill_pdf_20_19_staging.py")


class ResendDeliveryTests(unittest.TestCase):
    def test_offer_packet_idempotency_key_is_stable_and_does_not_expose_email(self):
        headers = production._resend_headers(
            "offer_packet",
            ["buyer@example.com", "support@homeofferflow.com"],
            "Your HomeOfferFlow Offer",
            "packet-sha",
        )
        same_headers = production._resend_headers(
            "offer_packet",
            ["buyer@example.com", "support@homeofferflow.com"],
            "Your HomeOfferFlow Offer",
            "packet-sha",
        )

        self.assertEqual(headers["Idempotency-Key"], same_headers["Idempotency-Key"])
        self.assertTrue(headers["Idempotency-Key"].startswith("hof/offer_packet/"))
        self.assertNotIn("buyer@example.com", headers["Idempotency-Key"])
        self.assertLessEqual(len(headers["Idempotency-Key"]), 256)

    def test_staging_and_production_use_the_same_safe_key_contract(self):
        args = ("showing_confirmation", ["buyer@example.com"], "Showing received", "content-sha")
        self.assertEqual(
            production._resend_headers(*args)["Idempotency-Key"],
            staging._resend_headers(*args)["Idempotency-Key"],
        )


if __name__ == "__main__":
    unittest.main()

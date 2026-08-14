import unittest
from unittest.mock import patch

from scripts import check_production_release as checker


class ProductionReleaseCheckTests(unittest.TestCase):
    def test_verify_accepts_verified_production_shape(self):
        health = {
            "release": "18B-controlled-launch",
            "trec_main_form": "20-19 production",
            "signwell_test_mode": False,
            **{flag: True for flag in checker.REQUIRED_TRUE_FLAGS},
        }

        def fake_get(url):
            if url.endswith("/api/fill-pdf.py"):
                return 200, "application/json", __import__("json").dumps(health).encode()
            return 200, "text/html", b"ok"

        with patch.object(checker, "_get", side_effect=fake_get):
            result = checker.verify("https://example.test", expected_release="18B-controlled-launch", expected_main_form="20-19 production")
        self.assertTrue(result["ok"])
        self.assertEqual(result["public_pages"]["/terms.html"], 200)

    def test_verify_rejects_test_mode_or_missing_asset(self):
        health = {"release": "18B-controlled-launch", "trec_main_form": "20-19 production", "signwell_test_mode": True}

        def fake_get(url):
            if url.endswith("/api/fill-pdf.py"):
                return 200, "application/json", __import__("json").dumps(health).encode()
            return 200, "text/html", b"ok"

        with patch.object(checker, "_get", side_effect=fake_get):
            result = checker.verify("https://example.test", expected_release="18B-controlled-launch", expected_main_form="20-19 production")
        self.assertFalse(result["ok"])
        self.assertIn("SignWell must be in production mode, not test mode.", result["errors"])
        self.assertTrue(any("packet_runtime_ready" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

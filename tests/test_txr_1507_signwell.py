import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("txr_1507_signwell", ROOT / "api" / "txr_1507_signwell.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def plan(two_clients=True):
    return {
        "broker_role": "associate",
        "associate": {"name": "Andrew Christian", "email": "andrew@example.com"},
        "clients": [
            {"name": "Buyer One", "email": "buyer1@example.com"},
            {"name": "Buyer Two", "email": "buyer2@example.com"},
        ] if two_clients else [{"name": "Buyer One", "email": "buyer1@example.com"}],
    }


class TXR1507SignWellTests(unittest.TestCase):
    def test_signer_role_is_explicit_and_recipients_are_distinct(self):
        recipients = MODULE.build_txr_1507_recipients(plan())
        self.assertEqual([r["id"] for r in recipients], ["1", "2", "3"])
        self.assertEqual(recipients[0]["name"], "Andrew Christian")

    def test_one_client_does_not_get_second_client_fields(self):
        fields = MODULE.build_txr_1507_signwell_fields(plan(False))
        ids = {field["api_id"] for field in fields}
        self.assertIn("txr1507_client1_signature", ids)
        self.assertNotIn("txr1507_client2_signature", ids)
        self.assertTrue(all(0 <= field["x"] <= 816 for field in fields))
        self.assertTrue(all(0 <= field["y"] <= 1056 for field in fields))

    def test_signer_plan_rejects_missing_role_or_duplicate_email(self):
        bad = plan()
        bad["broker_role"] = ""
        with self.assertRaisesRegex(MODULE.TXR1507SignerPlanError, "broker or broker associate"):
            MODULE.normalize_txr_1507_signer_plan(bad)
        bad = plan()
        bad["clients"][0]["email"] = "andrew@example.com"
        with self.assertRaisesRegex(MODULE.TXR1507SignerPlanError, "different email"):
            MODULE.normalize_txr_1507_signer_plan(bad)


if __name__ == "__main__":
    unittest.main()

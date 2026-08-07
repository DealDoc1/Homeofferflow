from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_authenticated_txr_qa", ROOT / "scripts" / "run_authenticated_txr_qa.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuthenticatedTxrQaHelperTests(unittest.TestCase):
    def test_one_client_payload_is_restricted_and_explicit(self):
        payload = MODULE._payload(1)
        self.assertEqual(payload["action"], "create_txr_1507_draft")
        self.assertEqual(payload["formCode"], "TXR-1507")
        self.assertEqual(payload["signerPlan"], "clients_and_associate")
        self.assertTrue(payload["formUseAttested"])
        self.assertEqual(len(payload["clientNames"]), 1)
        self.assertNotIn("email", payload)
        self.assertNotIn("phone", payload)

    def test_two_client_payload_has_two_distinct_test_clients(self):
        payload = MODULE._payload(2)
        self.assertEqual(len(payload["clientNames"]), 2)
        self.assertEqual(len(set(payload["clientNames"])), 2)

if __name__ == "__main__":
    unittest.main()


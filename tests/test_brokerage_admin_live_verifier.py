import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_brokerage_admin_live", ROOT / "scripts" / "verify_brokerage_admin_live.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class BrokerageAdminLiveVerifierTests(unittest.TestCase):
    def _payload(self):
        return {
            "brokerage": {"name": "OnDemand Realty", "slug": "ondemand"},
            "metrics": {"memberCount": 1, "activeMemberCount": 1, "agentSeatCount": 0, "offerCount": 0, "signedCount": 0},
            "privacy": {"buyerDetailsIncluded": False, "propertyDetailsIncluded": False, "offerTermsIncluded": False, "documentContentsIncluded": False},
            "agents": [{"name": "Agent", "role": "agent", "activity": {"offerCount": 0}}],
            "sourceReadiness": [{"formCode": "TXR-1507", "status": "not_uploaded"}],
            "pendingInvites": [],
        }

    def test_valid_privacy_limited_payload_passes(self):
        self.assertEqual(module.validate(self._payload(), "ondemand"), [])

    def test_buyer_or_source_secret_fields_fail_closed(self):
        payload = self._payload()
        payload["agents"][0]["seller"] = "must not appear"
        errors = module.validate(payload, "ondemand")
        self.assertTrue(any("private" in error or "buyer" in error for error in errors))

    def test_nested_sensitive_fields_fail_closed(self):
        payload = self._payload()
        payload["agents"][0]["activity"] = {"recent": [{"offerData": {"address": "secret"}}]}
        errors = module.validate(payload, "ondemand")
        self.assertTrue(any("buyer" in error for error in errors))

    def test_non_object_response_fails_closed(self):
        errors = module.validate([], "ondemand")
        self.assertEqual(errors, ["Brokerage response must be a JSON object."])


if __name__ == "__main__":
    unittest.main()

import importlib.util
from pathlib import Path
from unittest import mock
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "fill-pdf.py"


def load_offer_api():
    spec = importlib.util.spec_from_file_location("homeofferflow_offer_ownership_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    status_code = 200
    text = "[]"

    def json(self):
        return [{"id": "offer-123"}]


class SubscribedPacketOfferOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.api = load_offer_api()
        self.api.SUPABASE_URL = "https://example.supabase.co"
        self.api.SUPABASE_SERVICE_ROLE_KEY = "service-role-test"

    def test_verified_subscribed_generation_updates_its_existing_owned_draft(self):
        offer = {"_hofOfferId": "offer-123", "userType": "agent", "address": "1438 Whitaker Road"}
        with mock.patch.object(self.api.httpx, "patch", return_value=FakeResponse()) as patch, mock.patch.object(self.api.httpx, "post") as post:
            result = self.api.save_generated_offer_to_supabase(
                offer,
                subscription_user_id="user-456",
            )

        self.assertEqual("offer-123", result)
        patch.assert_called_once()
        post.assert_not_called()
        self.assertEqual({"id": "eq.offer-123", "user_id": "eq.user-456"}, patch.call_args.kwargs["params"])
        self.assertEqual("user-456", patch.call_args.kwargs["json"]["user_id"])

    def test_verified_subscribed_generation_falls_back_to_owned_insert_when_draft_is_missing(self):
        offer = {"userType": "agent", "address": "1438 Whitaker Road"}
        with mock.patch.object(self.api.httpx, "patch") as patch, mock.patch.object(self.api.httpx, "post", return_value=FakeResponse()) as post:
            result = self.api.save_generated_offer_to_supabase(
                offer,
                subscription_user_id="user-456",
            )

        self.assertEqual("offer-123", result)
        patch.assert_not_called()
        post.assert_called_once()
        self.assertEqual("user-456", post.call_args.kwargs["json"]["user_id"])

    def test_untrusted_checkout_keeps_the_homebuyer_insert_path(self):
        offer = {"_hofOfferId": "browser-supplied-id", "address": "1438 Whitaker Road"}
        with mock.patch.object(self.api.httpx, "patch") as patch, mock.patch.object(self.api.httpx, "post", return_value=FakeResponse()) as post:
            self.api.save_generated_offer_to_supabase(offer)

        patch.assert_not_called()
        post.assert_called_once()
        self.assertNotIn("user_id", post.call_args.kwargs["json"])


if __name__ == "__main__":
    unittest.main()

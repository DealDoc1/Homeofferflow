import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "verify_stripe_lifecycle_isolation.py"
SPEC = importlib.util.spec_from_file_location("stripe_lifecycle_isolation", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StripeLifecycleIsolationPreflightTests(unittest.TestCase):
    def test_isolated_preview_with_test_credentials_passes(self):
        env = {
            "VERCEL_ENV": "preview",
            "STRIPE_WEBHOOK_ALLOW_TEST_EVENTS": "true",
            "STRIPE_WEBHOOK_TEST_ENVIRONMENT": "preview",
            "SUPABASE_URL": "https://qa.example.supabase.co",
            "STRIPE_WEBHOOK_TEST_SUPABASE_URL": "https://qa.example.supabase.co",
            "SUPABASE_PRODUCTION_URL": "https://prod.example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-test",
            "STRIPE_SECRET_KEY": "sk_test_123",
            "STRIPE_SUBSCRIPTION_WEBHOOK_SECRET": "whsec_test_123",
        }
        with patch.dict(os.environ, env, clear=True):
            result = MODULE.check_environment("https://qa.example.supabase.co")
        self.assertTrue(result["ok"])
        self.assertTrue(all(result["checks"].values()))

    def test_preview_sharing_production_database_fails_closed(self):
        env = {
            "VERCEL_ENV": "preview",
            "STRIPE_WEBHOOK_ALLOW_TEST_EVENTS": "true",
            "STRIPE_WEBHOOK_TEST_ENVIRONMENT": "preview",
            "SUPABASE_URL": "https://prod.example.supabase.co",
            "STRIPE_WEBHOOK_TEST_SUPABASE_URL": "https://prod.example.supabase.co",
            "SUPABASE_PRODUCTION_URL": "https://prod.example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-test",
            "STRIPE_SECRET_KEY": "sk_test_123",
            "STRIPE_SUBSCRIPTION_WEBHOOK_SECRET": "whsec_test_123",
        }
        with patch.dict(os.environ, env, clear=True):
            result = MODULE.check_environment("https://qa.example.supabase.co")
        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["runtime_differs_from_production"])
        self.assertFalse(result["checks"]["expected_isolated_database"])

    def test_intentional_service_key_placeholder_fails_closed(self):
        env = {
            "VERCEL_ENV": "preview",
            "STRIPE_WEBHOOK_ALLOW_TEST_EVENTS": "true",
            "STRIPE_WEBHOOK_TEST_ENVIRONMENT": "preview",
            "SUPABASE_URL": "https://qa.example.supabase.co",
            "STRIPE_WEBHOOK_TEST_SUPABASE_URL": "https://qa.example.supabase.co",
            "SUPABASE_PRODUCTION_URL": "https://prod.example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "__QA_SERVICE_KEY_REQUIRED__",
            "STRIPE_SECRET_KEY": "sk_test_123",
            "STRIPE_SUBSCRIPTION_WEBHOOK_SECRET": "whsec_test_123",
        }
        with patch.dict(os.environ, env, clear=True):
            result = MODULE.check_environment("https://qa.example.supabase.co")
        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["service_role_key_present"])

    def test_output_contract_never_includes_urls_or_secret_values(self):
        source = PATH.read_text(encoding="utf-8")
        self.assertIn("configuration booleans only", source)
        self.assertNotIn('"runtime_url": runtime_url', source)
        self.assertNotIn('"test_url": test_url', source)
        self.assertNotIn('"production_url": production_url', source)

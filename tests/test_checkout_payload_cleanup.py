"""Cleanup uses verified terminal events, never browser intent or row age."""
import copy
import hashlib
import hmac
import importlib.util
import io
import json
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lib.checkout_payload import cleanup_expired_checkout_payload

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('checkout_cleanup_webhook', ROOT / 'api/stripe-webhook/index.py')
WEBHOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WEBHOOK)


class CheckoutPayloadCleanupTests(unittest.TestCase):
    def setUp(self):
        self.session = {'id': 'cs_expired_fixture', 'mode': 'payment', 'status': 'expired',
                        'payment_status': 'unpaid', 'after_expiration': None,
                        'metadata': {'plan': 'self', 'offer_payload_id': '11111111-1111-4111-8111-111111111111',
                                     'offer_payload_sha256': 'a' * 64}}
        self.event = {'type': 'checkout.session.expired', 'id': 'evt_expired_fixture', 'livemode': True,
                      'data': {'object': self.session}}
        self.client = Mock()
        self.client.delete.return_value = SimpleNamespace(status_code=204)

    def clean(self):
        return cleanup_expired_checkout_payload(self.event, supabase_url='https://db.example.test',
                                               service_key='fake-service', client=self.client)

    def test_scoped_delete_requires_exact_id_hash_and_matching_or_unbound_session(self):
        self.assertTrue(self.clean())
        kwargs = self.client.delete.call_args.kwargs
        self.assertEqual(kwargs['params'], {'id': 'eq.' + self.session['metadata']['offer_payload_id'],
                                          'payload_sha256': 'eq.' + 'a' * 64,
                                          'or': '(stripe_session_id.eq.cs_expired_fixture,stripe_session_id.is.null)'})
        self.assertEqual(kwargs['headers']['Prefer'], 'return=minimal')
        self.assertTrue(self.clean())  # already-removed rows also return 204

    def test_open_completed_paid_zero_total_and_subscription_sessions_are_retained(self):
        for key, value in [('status', 'open'), ('status', 'complete'), ('status', None),
                           ('payment_status', 'paid'), ('payment_status', 'no_payment_required'),
                           ('payment_status', None), ('mode', 'subscription'), ('recovered_from', 'cs_original')]:
            original = copy.deepcopy(self.session)
            with self.subTest(key=key, value=value):
                self.session[key] = value
                self.assertFalse(self.clean())
                self.client.delete.assert_not_called()
            self.session.clear(); self.session.update(original)

    def test_recovery_links_and_uncertain_recovery_configuration_are_preserved(self):
        for recovery in [{'enabled': True}, {'url': 'https://recover.example.test'},
                         {'enabled': False, 'url': 'https://recover.example.test'}, {'future': True}, 'unknown']:
            self.session['after_expiration'] = {'recovery': recovery}
            self.assertFalse(self.clean())
        self.client.delete.assert_not_called()

    def test_explicitly_disabled_recovery_can_be_cleaned(self):
        self.session['after_expiration'] = {'recovery': {'enabled': False}}
        self.assertTrue(self.clean())

    def test_completed_event_is_never_cleanup_authority_even_with_expired_fields(self):
        self.event['type'] = 'checkout.session.completed'
        self.assertFalse(self.clean())
        self.client.delete.assert_not_called()

    def test_wrong_product_missing_or_malformed_reference_is_not_deleted(self):
        for key, value in [('plan', 'seller'), ('partner_lead_id', 'partner'), ('seller_lead_id', 'seller'),
                           ('offer_payload_id', 'x,or=(id.neq.null)'), ('offer_payload_id', None),
                           ('offer_payload_sha256', ''), ('offer_payload_sha256', [])]:
            original = copy.deepcopy(self.session['metadata'])
            with self.subTest(key=key):
                self.session['metadata'][key] = value
                self.assertFalse(self.clean())
                self.client.delete.assert_not_called()
            self.session['metadata'] = original

    def test_provider_error_and_ambiguous_response_remain_retryable_and_redacted(self):
        for status in [200, 401, 403, 500]:
            self.client.delete.return_value = SimpleNamespace(status_code=status)
            with self.assertRaisesRegex(ValueError, 'Expired checkout cleanup could not be confirmed'): self.clean()
        self.client.delete.side_effect = TimeoutError('private database details')
        with self.assertRaises(ValueError) as error: self.clean()
        self.assertNotIn('private', str(error.exception))

    def request(self, *, valid=True, duplicate=False, secret='live-fixture-secret', fail=False):
        raw = json.dumps(self.event).encode()
        timestamp = str(int(time.time()))
        digest = hmac.new(secret.encode(), timestamp.encode() + b'.' + raw, hashlib.sha256).hexdigest()
        request = WEBHOOK.handler.__new__(WEBHOOK.handler)
        request.rfile = io.BytesIO(raw)
        request.headers = {'Content-Length': str(len(raw)), 'Stripe-Signature': f't={timestamp},v1={digest if valid else "invalid"}'}
        result = {}
        request._send_json = lambda code, data: result.update(code=code, data=data)
        request._log_webhook = Mock()
        request._claim_webhook_event = Mock(return_value=not duplicate)
        request._record_webhook_event = Mock()
        with patch.object(WEBHOOK, 'STRIPE_WEBHOOK_SECRET', 'live-fixture-secret'), \
             patch.object(WEBHOOK, 'STRIPE_TEST_WEBHOOK_SECRET', 'test-fixture-secret'), \
             patch.object(WEBHOOK, 'SUPABASE_URL', 'https://db.example.test'), \
             patch.object(WEBHOOK, 'SUPABASE_SERVICE_ROLE_KEY', 'fake-service'), \
             patch.object(WEBHOOK, '_test_events_allowed', return_value=False), \
             patch('lib.checkout_payload.httpx.delete', return_value=SimpleNamespace(status_code=503 if fail else 204)) as delete:
            request.do_POST()
        return request, result, delete

    def test_actual_signed_expiry_route_cleans_then_records_completion(self):
        request, result, delete = self.request()
        self.assertEqual(result['code'], 200)
        delete.assert_called_once()
        request._record_webhook_event.assert_called_once_with('evt_expired_fixture', 'processed')

    def test_invalid_signature_cannot_claim_event_or_delete(self):
        request, result, delete = self.request(valid=False)
        self.assertEqual(result['code'], 400)
        request._claim_webhook_event.assert_not_called()
        delete.assert_not_called()

    def test_test_secret_cannot_delete_live_packet(self):
        request, result, delete = self.request(secret='test-fixture-secret')
        self.assertEqual(result['code'], 400)
        delete.assert_not_called()

    def test_signed_sandbox_expiry_cannot_delete_production_packet(self):
        self.event['livemode'] = False
        request, result, delete = self.request()
        self.assertEqual(result['code'], 200)
        request._claim_webhook_event.assert_not_called()
        delete.assert_not_called()

    def test_duplicate_processed_event_skips_cleanup(self):
        request, result, delete = self.request(duplicate=True)
        self.assertTrue(result['data']['duplicate'])
        delete.assert_not_called()

    def test_cleanup_failure_records_failed_event_and_returns_retryable_response(self):
        request, result, delete = self.request(fail=True)
        self.assertEqual(result['code'], 500)
        request._record_webhook_event.assert_called_once_with('evt_expired_fixture', 'failed', 'processing_failed')

    def test_paid_packet_is_ignored_by_actual_expiration_route(self):
        self.session['payment_status'] = 'paid'
        request, result, delete = self.request()
        self.assertEqual(result['code'], 200)
        request._record_webhook_event.assert_called_once_with('evt_expired_fixture', 'ignored')
        delete.assert_not_called()

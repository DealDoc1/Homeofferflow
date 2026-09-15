"""Exercise checkout -> durable email protocol -> Resend request, offline."""
import copy
import importlib.util
import json
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lib.email_delivery import EmailDeliveryPending
from tests.test_email_delivery import Store

SPEC = importlib.util.spec_from_file_location('checkout_durable_email_api',
    Path(__file__).resolve().parents[1] / 'api/fill-pdf.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)


class CheckoutEmailDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.now = time.time()
        self.fail = None
        self.requests = []
        self.pdf_version = 0
        self.offer = {'buyer1': 'QA Buyer', 'buyerEmail': 'buyer@example.test',
                      'address': 'QA Property', 'price': '100', '_emailDeliveryKey': 'untrusted-key'}
        self.event = {'type': 'checkout.session.completed', 'data': {'object': {
            'id': 'cs_verified_test', 'customer_email': 'payer@example.test',
            'metadata': {'plan': 'self', 'offer_data': json.dumps(self.offer)}}}}
        self.record = {'id': '11111111-1111-4111-8111-111111111111', 'user_id': None}
        self.signing = Mock(return_value={'ok': True, 'enabled': True,
                                        'delivery_state': 'sent', 'document_id': 'same-signwell-document'})
        adapter = SimpleNamespace(reserve=self.store.reserve, begin_attempt=self.store.stamp,
                                  accept=self.store.accept)
        self.patches = [
            patch.object(API, 'EmailDeliveryStore', return_value=adapter),
            patch.object(API, 'hydrate_paragraph4_sources'), patch.object(API, 'validate_supported_offer'),
            patch.object(API, 'fill_and_merge', side_effect=self.render),
            patch.object(API, 'prepare_offer_signing_record', side_effect=lambda *a, **kw: copy.deepcopy(self.record)),
            patch.object(API, 'create_signwell_signature_request', self.signing),
            patch.object(API, 'ADMIN_ORDER_EMAIL', 'support@example.test'),
            patch.object(API.httpx, 'post', side_effect=self.post),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def render(self, offer):
        self.pdf_version += 1
        return b'%PDF-controlled-timestamp-' + str(self.pdf_version).encode()

    def post(self, url, *, headers, json, **kwargs):
        self.assertEqual(url, 'https://api.resend.com/emails')
        key = headers['Idempotency-Key']
        self.assertTrue(key.startswith('hof-email-v1-'))
        self.assertNotIn('cs_verified_test', key)
        self.assertNotIn('untrusted-key', key)
        self.requests.append((key, copy.deepcopy(json)))
        result = self.store.send(json, key)
        if self.fail and json['subject'].startswith(self.fail):
            raise TimeoutError('Simulated lost provider acknowledgement')
        return SimpleNamespace(status_code=201, json=lambda: result)

    def test_duplicate_checkout_never_repeats_confirmed_buyer_or_admin_email(self):
        first = API.handle_checkout(copy.deepcopy(self.event))
        second = API.handle_checkout(copy.deepcopy(self.event))
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(len(self.store.provider), 2)
        self.assertEqual(first['documentEmail']['status'], 'accepted')
        self.assertTrue(second['documentEmail']['recovered'])
        self.assertTrue(second['adminEmail']['recovered'])
        self.assertNotEqual(self.requests[0][0], self.requests[1][0])
        self.assertEqual(second['signwell']['document_id'], 'same-signwell-document')

    def test_buyer_timeout_retry_reuses_original_pdf_and_message(self):
        self.fail = 'Your HomeOfferFlow Offer'
        with self.assertRaises(EmailDeliveryPending):
            API.handle_checkout(copy.deepcopy(self.event))
        original = copy.deepcopy(self.requests[0])
        self.fail = None
        self.signing.return_value['delivery_state'] = 'signed'
        API.handle_checkout(copy.deepcopy(self.event))
        self.assertEqual(self.requests[1], original)
        self.assertEqual(len(self.store.provider), 2)  # buyer once, then admin once

    def test_admin_timeout_does_not_fail_buyer_or_resend_the_buyer_on_replay(self):
        self.fail = 'New HomeOfferFlow Order'
        first = API.handle_checkout(copy.deepcopy(self.event))
        self.assertEqual(first['documentEmail']['status'], 'accepted')
        self.assertEqual(first['adminEmail']['status'], 'unconfirmed')
        self.fail = None
        self.signing.return_value['delivery_state'] = 'signed'
        second = API.handle_checkout(copy.deepcopy(self.event))
        self.assertEqual(second['adminEmail']['status'], 'accepted')
        self.assertEqual(len(self.requests), 3)
        self.assertEqual(self.requests[1], self.requests[2])
        self.assertEqual(len(self.store.provider), 2)

    def test_failed_email_reservation_never_sends_without_tracking(self):
        self.store.reserve_fails = True
        with self.assertRaises(EmailDeliveryPending):
            API.handle_checkout(copy.deepcopy(self.event))
        self.assertEqual(self.requests, [])

    def test_invalid_checkout_identity_is_rejected_before_signing_or_email(self):
        self.event['data']['object']['id'] = ''
        with self.assertRaises(EmailDeliveryPending):
            API.handle_checkout(self.event)
        self.signing.assert_not_called()
        self.assertEqual(self.requests, [])

    def test_owned_offer_replays_are_stable_but_an_intentional_revision_is_distinct(self):
        self.record['user_id'] = 'verified-owner'
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id='verified-owner')
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id='verified-owner')
        self.assertEqual(len(self.requests), 2)
        self.offer['price'] = '200'
        self.event['data']['object']['metadata']['offer_data'] = json.dumps(self.offer)
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id='verified-owner')
        self.assertEqual(len(self.requests), 4)
        self.assertNotEqual(self.requests[0][0], self.requests[2][0])

    def test_owned_identity_cannot_be_borrowed_from_another_user(self):
        self.record['user_id'] = 'other-owner'
        with self.assertRaises(EmailDeliveryPending):
            API.handle_checkout(self.event, subscription_user_id='verified-owner')
        self.signing.assert_not_called()
        self.assertEqual(self.requests, [])

    def test_browser_internal_email_key_cannot_force_a_second_owned_email(self):
        self.record['user_id'] = 'verified-owner'
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id='verified-owner')
        self.offer['_emailDeliveryKey'] = 'try-to-force-another-send'
        self.event['data']['object']['metadata']['offer_data'] = json.dumps(self.offer)
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id='verified-owner')
        self.assertEqual(len(self.requests), 2)

    def test_buyer_and_admin_helpers_reject_missing_identity(self):
        with self.assertRaises(EmailDeliveryPending):
            API.send_email('buyer@example.test', 'Buyer', 'Property', b'%PDF', delivery_identity=None)
        with self.assertRaises(EmailDeliveryPending):
            API.send_admin_order_email({}, delivery_identity=None)
        self.assertEqual(self.requests, [])

    def test_showing_checkout_stays_on_its_separate_notification_path(self):
        self.event['data']['object']['metadata']['plan'] = 'showing-booking'
        with patch.object(API, 'send_showing_request_emails') as showing:
            API.handle_checkout(self.event)
        showing.assert_called_once()
        self.assertEqual(self.requests, [])
        self.signing.assert_not_called()

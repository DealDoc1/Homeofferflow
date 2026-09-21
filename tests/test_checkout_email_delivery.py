"""Exercise checkout -> durable email protocol -> Resend request, offline."""
import copy
import base64
import importlib.util
import json
import io
import subprocess
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lib.email_delivery import EmailDeliveryPending
from tests.test_email_delivery import Store
from tests.test_packet_generation import MemoryPacketStore
from lib.packet_generation import PacketGenerationPending

OWNER = '22222222-2222-4222-8222-222222222222'

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
        self.usage_store = MemoryPacketStore()
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
            patch.object(API, 'PacketGenerationStore', return_value=self.usage_store),
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

    def test_real_checkout_reference_preserves_unicode_and_full_size_attachment_bytes(self):
        offer = {**self.offer, 'financing': 'cash', 'earnest': '0', 'optionFee': '0', 'optionDays': '0',
                 'repairsText': 'First requirement\u2028Second requirement\u2029Final requirement 🏡',
                 'legalDescription': ('José 李\u2028Parcel notes\u2029' * 50),
                 # Synthetic bytes test transport, not PDF rendering/geometry.
                 'uploadedDisclosureDocs': [
                     {'name': 'one.pdf', 'base64': base64.b64encode(b'A' * (2 * 1024 * 1024)).decode()},
                     {'name': 'two.pdf', 'base64': base64.b64encode(b'B' * (512 * 1024)).decode()}]}
        script = r"""
const fs = require('node:fs'), vm = require('node:vm');
const offerData = JSON.parse(fs.readFileSync(0, 'utf8'));
const moduleObject = {exports: {}};
let captured, row;
const storage = require('./lib/checkout_payload');
const options = {env:{SUPABASE_URL:'https://database.example.test',SUPABASE_SERVICE_ROLE_KEY:'fake-service'},
  fetcher:async (url, request) => {
    row = {...row, ...JSON.parse(request.body)};
    return {ok:true,json:async()=>[row]};
  }};
vm.runInNewContext(fs.readFileSync('api/create-checkout.js', 'utf8'), {
  module: moduleObject, URL, console, process: {env: {STRIPE_SECRET_KEY:'mock-key'}},
  require(name) {
    if (name === '../lib/checkout_payload') return {
      saveCheckoutPayload: body => storage.saveCheckoutPayload(body, options),
      bindCheckoutPayload: (ref, id) => storage.bindCheckoutPayload(ref, id, options)
    };
    if (name !== 'stripe') throw Error('Unexpected dependency');
    return () => ({checkout:{sessions:{create:async payload => {
      captured = payload.metadata;
      return {id:'cs_verified_test',url:'https://checkout.example.test/session'};
    }}}});
  }
});
let status;
const res = {status(value){status=value;return this;},json(){return this;}};
moduleObject.exports({method:'POST', headers:{origin:'https://www.homeofferflow.com'},
  body:{email:'payer@example.test',plan:'self',offerData}}, res).then(() => {
  if (status !== 200 || !captured) throw Error('Mock checkout rejected');
  process.stdout.write(JSON.stringify({metadata:captured,row}));
}).catch(error => {console.error(error);process.exit(1);});
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps(offer), text=True,
                                capture_output=True, timeout=15,
                                cwd=Path(__file__).resolve().parents[1])
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = json.loads(result.stdout)
        self.event['data']['object'].update(metadata=captured['metadata'], mode='payment', payment_status='paid')
        from types import SimpleNamespace
        with patch.object(API, 'SUPABASE_URL', 'https://database.example.test'), \
             patch.object(API, 'SUPABASE_SERVICE_ROLE_KEY', 'fake-service'), \
             patch('lib.checkout_payload.httpx.get', return_value=SimpleNamespace(
                 status_code=200, json=lambda: [captured['row']])):
            API.handle_checkout(copy.deepcopy(self.event))
        rendered_offer = API.fill_and_merge.call_args.args[0]
        self.assertEqual(rendered_offer['repairsText'], offer['repairsText'])
        self.assertEqual(rendered_offer['legalDescription'], offer['legalDescription'])
        self.assertEqual(rendered_offer['uploadedDisclosureDocs'], offer['uploadedDisclosureDocs'])
        self.assertEqual(len(self.requests), 2)

    def test_subscription_cannot_use_another_customers_checkout_reference(self):
        self.event['data']['object']['metadata']['offer_payload_id'] = 'private-reference'
        with patch.object(API, 'load_checkout_payload') as load:
            with self.assertRaisesRegex(ValueError, 'verified payment event'):
                API.handle_checkout(self.event, subscription_user_id=OWNER)
            load.assert_not_called()
        API.fill_and_merge.assert_not_called()
        self.signing.assert_not_called()
        self.assertEqual(self.requests, [])

    def test_failed_reference_never_falls_back_to_inline_answers_or_sends(self):
        self.event['data']['object']['metadata']['offer_payload_id'] = 'private-reference'
        with patch.object(API, 'load_checkout_payload', side_effect=ValueError('unverified')):
            with self.assertRaises(ValueError): API.handle_checkout(self.event)
        API.fill_and_merge.assert_not_called()
        self.signing.assert_not_called()
        self.assertEqual(self.requests, [])

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

    def invoke(self, *, subscriber=False, authenticated=True):
        event = copy.deepcopy(self.event)
        if subscriber:
            event['data']['object']['metadata']['subscription_generation'] = 'true'
            self.record['user_id'] = OWNER
        body = json.dumps(event).encode()
        handler = object.__new__(API.handler)
        handler.headers = {'Content-Length': str(len(body))}
        if not subscriber:
            handler.headers['x-homeofferflow-checkout-signature'] = 'test-signature'
        handler.rfile = io.BytesIO(body)
        handler._json = Mock()
        handler._verified_user = Mock(return_value=OWNER if authenticated else None)
        with patch.object(API, 'verify_internal_checkout_forward_signature', return_value=authenticated):
            handler.do_POST()
        return handler._json.call_args.args

    def test_authenticated_subscriber_gets_ready_packet_and_pending_email_not_generation_failure(self):
        self.fail = 'Your HomeOfferFlow Offer'
        status, body = self.invoke(subscriber=True)
        self.assertEqual(status, 202)
        self.assertTrue(body['packetGenerated'])
        self.assertEqual(body['offerId'], self.record['id'])
        self.assertTrue(body['signwell']['ok'])
        self.assertEqual(body['documentEmail']['status'], 'unconfirmed')
        self.assertEqual(body['usage']['status'], 'recorded')
        self.assertEqual(self.usage_store.completions, 1)
        self.assertNotIn('error', body)
        self.assertNotIn('Simulated', json.dumps(body))

    def test_paid_webhook_stays_retryable_and_reuses_original_request(self):
        self.fail = 'Your HomeOfferFlow Offer'
        status, body = self.invoke()
        self.assertEqual(status, 503)
        self.assertEqual(body['code'], 'document_email_unconfirmed')
        original = copy.deepcopy(self.requests[0])
        self.fail = None
        status, body = self.invoke()
        self.assertEqual(status, 200)
        self.assertEqual(body['documentEmail']['status'], 'accepted')
        self.assertEqual(self.requests[1], original)
        self.assertEqual(len(self.store.provider), 2)

    def test_unauthenticated_caller_never_receives_partial_packet_status(self):
        for subscriber in (True, False):
            with self.subTest(subscriber=subscriber):
                status, body = self.invoke(subscriber=subscriber, authenticated=False)
                self.assertEqual(status, 401)
                self.assertNotIn('signwell', body)
        self.signing.assert_not_called()
        self.assertEqual(self.requests, [])

    def test_expired_email_keeps_review_status_without_another_send(self):
        self.fail = 'Your HomeOfferFlow Offer'
        self.invoke(subscriber=True)
        for row in self.store.rows.values():
            row['first_attempt_at'] -= 7 * 24 * 3600
        status, body = self.invoke(subscriber=True)
        self.assertEqual(status, 202)
        self.assertTrue(body['documentEmail']['needsReview'])
        self.assertEqual(len(self.requests), 1)

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
        self.record['user_id'] = OWNER
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id=OWNER)
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id=OWNER)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(self.usage_store.completions, 1)
        self.offer['price'] = '200'
        self.event['data']['object']['metadata']['offer_data'] = json.dumps(self.offer)
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id=OWNER)
        self.assertEqual(len(self.requests), 4)
        self.assertEqual(self.usage_store.completions, 2)
        self.assertNotEqual(self.requests[0][0], self.requests[2][0])

    def test_owned_identity_cannot_be_borrowed_from_another_user(self):
        self.record['user_id'] = 'other-owner'
        with self.assertRaises(PacketGenerationPending):
            API.handle_checkout(self.event, subscription_user_id=OWNER)
        self.signing.assert_not_called()
        self.assertEqual(self.requests, [])

    def test_browser_internal_email_key_cannot_force_a_second_owned_email(self):
        self.record['user_id'] = OWNER
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id=OWNER)
        self.offer['_emailDeliveryKey'] = 'try-to-force-another-send'
        self.event['data']['object']['metadata']['offer_data'] = json.dumps(self.offer)
        API.handle_checkout(copy.deepcopy(self.event), subscription_user_id=OWNER)
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

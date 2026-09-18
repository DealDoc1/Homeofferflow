"""Offline checkout/retry integration through the real purchase-offer sender."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('purchase_recovery', ROOT / 'api/fill-pdf.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = '11111111-1111-4111-8111-111111111111'
OFFER_ID = '22222222-2222-4222-8222-222222222222'


class PurchaseDeliveryRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.documents = {}, {}
        self.sends, self.creates, self.emails = 0, 0, 0
        self.failure = None
        self.offer = {'_hofOfferId': OFFER_ID, 'userType': 'agent', 'address': 'QA property',
                      'buyer1': 'QA Buyer', 'buyerEmail': 'buyer@example.com'}
        for name, value in (('SUPABASE_URL', 'https://database.example'), ('SUPABASE_SERVICE_ROLE_KEY', 'test'),
                            ('SIGNWELL_API_KEY', 'test'), ('SIGNWELL_ENABLED', True)):
            p = patch.object(API, name, value); p.start(); self.addCleanup(p.stop)
        for name, side in (('get', self.get), ('post', self.post), ('patch', self.update)):
            p = patch.object(API.httpx, name, side_effect=side); p.start(); self.addCleanup(p.stop)
        for name, value in (('hydrate_paragraph4_sources', None), ('validate_supported_offer', None),
                            ('fill_and_merge', b'%PDF-rendered'),
                            ('build_signwell_fields', [[{'api_id': 'buyer-signature', 'recipient_id': '1', 'type': 'signature', 'x': 10}]])):
            p = patch.object(API, name, return_value=value); p.start(); self.addCleanup(p.stop)

    def response(self, body, code=200):
        return SimpleNamespace(status_code=code, text=json.dumps(body), json=lambda: copy.deepcopy(body))

    def matching(self, params):
        row = self.rows.get(params['id'][3:])
        if not row: return None
        for key in ('user_id', 'signwell_document_id', 'last_updated', 'status'):
            if key not in params: continue
            condition = params[key]
            if condition == 'is.null' and row.get(key) is not None: return None
            if condition.startswith('eq.') and str(row.get(key)) != condition[3:]: return None
            if condition.startswith('in.(') and row.get(key) not in condition[4:-1].split(','): return None
        return row

    def get(self, url, *, params=None, **kwargs):
        if '/rest/v1/hof_offers' in url:
            row = self.matching(params)
            return self.response([row] if row else [])
        if url.startswith('https://www.signwell.com/'):
            document = copy.deepcopy(self.documents[url.rsplit('/', 1)[-1]])
            if self.failure == 'changed_email': document['recipients'][0]['email'] = 'wrong@example.com'
            return self.response(document)
        raise AssertionError('Unexpected read: ' + url)

    def post(self, url, *, json, **kwargs):
        if '/rest/v1/hof_offers' in url:
            if self.failure == 'save_failure': return self.response([], 503)
            if json['id'] in self.rows: return self.response([], 409)
            self.rows[json['id']] = {'user_id': None, **copy.deepcopy(json)}
            return self.response([self.rows[json['id']]], 201)
        if url.startswith('https://api.resend.com/'):
            self.emails += 1
            return self.response({'id': 'email'}, 201)
        if url.endswith('/send'):
            self.sends += 1
            document = self.documents[url.split('/')[-2]]
            row = next(row for row in self.rows.values() if row.get('signwell_document_id') == document['id'])
            self.assertEqual(row['offer_data']['_hof_signature_delivery']['phase'], 'sending')
            self.assertFalse(json['apply_signing_order'])
            self.assertNotIn('files', json)
            if self.failure == 'rejected': return self.response({}, 402)
            if self.failure == 'timeout_draft': raise TimeoutError('Unconfirmed')
            document['status'] = 'sent'
            if self.failure == 'timeout_sent': raise TimeoutError('Lost accepted response')
            return self.response(document, 201)
        if url == 'https://www.signwell.com/api/v1/documents':
            self.creates += 1
            self.assertTrue(json['draft'])
            doc_id = 'document-' + str(self.creates)
            self.documents[doc_id] = {**copy.deepcopy(json), 'id': doc_id, 'status': 'draft'}
            return self.response({'id': doc_id}, 201)
        raise AssertionError('Unexpected write: ' + url)

    def update(self, url, *, params, json, **kwargs):
        self.assertIn('/rest/v1/hof_offers', url)
        self.assertIn('user_id', params)
        self.assertIn('signwell_document_id', params)
        if self.failure == 'claim_lost' and 'offer_data' in json and '_hof_signature_delivery' in json['offer_data']:
            return self.response([])
        if self.failure == 'finish_failed' and json.get('status') == 'Sent for Signature':
            return self.response([], 503)
        row = self.matching(params)
        if not row: return self.response([])
        row.update(copy.deepcopy(json))
        return self.response([row])

    def checkout(self, owner=OWNER):
        event = {'data': {'object': {'id': 'cs_test_recovery', 'customer_email': 'buyer@example.com',
                                    'metadata': {'offer_data': json.dumps(self.offer)}}}}
        return API.handle_checkout(event, subscription_user_id=owner)

    def test_first_send_has_saved_identity_and_simultaneous_invitations(self):
        result = self.checkout()
        self.assertTrue(result['signwell']['ok'])
        self.assertEqual((self.creates, self.sends), (1, 1))
        self.assertEqual(self.rows[OFFER_ID]['user_id'], OWNER)
        self.assertEqual(self.rows[OFFER_ID]['status'], 'Sent for Signature')

    def test_rejected_request_retries_same_id_without_emailing_another_pdf(self):
        self.failure = 'rejected'
        self.assertFalse(self.checkout()['signwell']['ok'])
        self.assertEqual(self.rows[OFFER_ID]['status'], 'Generated')
        email_count = self.emails
        self.failure = None
        result = API.retry_unsent_offer_signature(OFFER_ID, OWNER)
        self.assertTrue(result['ok'])
        self.assertEqual(result['documentId'], 'document-1')
        self.assertEqual((self.creates, self.sends, self.emails), (1, 2, email_count))

    def test_timeout_after_send_is_reconciled_without_duplicate(self):
        self.failure = 'timeout_sent'
        result = self.checkout()
        self.assertTrue(result['signwell']['ok'])
        self.assertEqual((self.creates, self.sends), (1, 1))

    def test_uncertain_draft_is_saved_and_immediate_retry_cannot_resend(self):
        self.failure = 'timeout_draft'
        result = self.checkout()
        self.assertTrue(result['signwell']['deliveryUnconfirmed'])
        retry = API.retry_unsent_offer_signature(OFFER_ID, OWNER)
        self.assertFalse(retry['ok'])
        self.assertTrue(retry['deliveryUnconfirmed'])
        self.assertEqual((self.creates, self.sends), (1, 1))

    def test_guest_checkout_replay_uses_server_identity_not_browser_offer_id(self):
        first = self.checkout(owner=None)
        second = self.checkout(owner=None)
        self.assertTrue(first['signwell']['ok'])
        self.assertTrue(second['signwell']['recovered'])
        self.assertEqual(len(self.rows), 1)
        self.assertNotIn(OFFER_ID, self.rows)
        self.assertIsNone(next(iter(self.rows.values()))['user_id'])
        self.assertEqual((self.creates, self.sends), (1, 1))

    def test_failed_record_save_cannot_create_or_send_provider_document(self):
        self.failure = 'save_failure'
        with self.assertRaises(RuntimeError): self.checkout()
        self.assertEqual((self.creates, self.sends, self.emails), (0, 0, 0))

    def test_changed_provider_email_is_rejected_even_when_recipient_id_matches(self):
        self.failure = 'changed_email'
        result = self.checkout()
        self.assertFalse(result['signwell']['ok'])
        self.assertEqual((self.creates, self.sends), (1, 0))

    def test_other_account_cannot_retry_saved_offer(self):
        self.checkout()
        with self.assertRaises(PermissionError): API.retry_unsent_offer_signature(OFFER_ID, 'other-owner')
        self.assertEqual((self.creates, self.sends), (1, 1))

    def test_changed_source_manifest_cannot_send_a_saved_request(self):
        self.offer['_signing_source_hashes'] = ['source-v1']
        self.failure = 'rejected'
        self.checkout()
        self.rows[OFFER_ID]['offer_data']['_signing_source_hashes'] = ['source-v2']
        self.failure = None
        result = API.retry_unsent_offer_signature(OFFER_ID, OWNER)
        self.assertFalse(result['ok'])
        self.assertEqual((self.creates, self.sends), (1, 1))

    def test_same_owned_checkout_replay_does_not_replace_tracking(self):
        self.checkout()
        first_data = copy.deepcopy(self.rows[OFFER_ID]['offer_data'])
        result = self.checkout()
        self.assertTrue(result['signwell']['recovered'])
        self.assertEqual(self.rows[OFFER_ID]['offer_data'], first_data)
        self.assertEqual((self.creates, self.sends), (1, 1))

    def test_zero_row_claim_cannot_send_the_private_draft(self):
        self.failure = 'claim_lost'
        result = self.checkout()
        self.assertTrue(result['signwell']['deliveryUnconfirmed'])
        self.assertEqual((self.creates, self.sends), (1, 0))
        self.assertEqual(self.documents['document-1']['status'], 'draft')

    def test_final_save_failure_recovers_sent_document_without_resending(self):
        self.failure = 'finish_failed'
        result = self.checkout()
        self.assertTrue(result['signwell']['deliveryUnconfirmed'])
        self.assertEqual(self.rows[OFFER_ID]['signwell_document_id'], 'document-1')
        self.failure = None
        retry = API.retry_unsent_offer_signature(OFFER_ID, OWNER)
        self.assertTrue(retry['ok'])
        self.assertEqual((self.creates, self.sends), (1, 1))

    def test_legacy_tracked_document_is_not_recreated(self):
        self.checkout()
        self.rows[OFFER_ID]['offer_data'].pop('_hof_signature_delivery')
        with self.assertRaises(ValueError):
            API.retry_unsent_offer_signature(OFFER_ID, OWNER)
        self.assertEqual((self.creates, self.sends), (1, 1))

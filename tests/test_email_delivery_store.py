"""HTTP adapter contract tests; real database rollout remains separate."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from lib.email_delivery import EmailDeliveryPending, delivery_key, payload_fingerprint
from lib.email_delivery_store import EmailDeliveryStore


def response(rows, status=200):
    return SimpleNamespace(status_code=status, json=lambda: copy.deepcopy(rows))


class EmailDeliveryStoreTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.store = EmailDeliveryStore(supabase_url='https://database.example.test',
                                       service_key='test-only', client=self.client, clock=lambda: 1000)
        self.key = delivery_key('buyer-packet', 'cs_test_only')
        self.payload = {'to': ['qa@example.test'], 'html': 'Original body'}
        self.row = {'delivery_key': self.key, 'payload': self.payload,
                    'payload_fingerprint': payload_fingerprint(self.payload),
                    'status': 'pending', 'first_attempt_at': None, 'provider_id': None}

    def test_reservation_inserts_once_with_ignore_not_merge(self):
        self.client.get.return_value = response([])
        self.client.post.return_value = response([self.row], 201)
        saved = self.store.reserve(self.key, self.payload, self.row['payload_fingerprint'])
        self.assertEqual(saved, self.row)
        request = self.client.post.call_args.kwargs
        self.assertEqual(request['params']['on_conflict'], 'delivery_key')
        self.assertIn('resolution=ignore-duplicates', request['headers']['Prefer'])
        self.assertEqual(request['json']['payload'], self.payload)
        self.assertNotIn('first_attempt_at', request['json'])

    def test_receipt_lookup_is_exact_read_only_and_validates_key(self):
        self.client.get.return_value = response([self.row])
        self.assertEqual(self.store.read_receipt(self.key), self.row)
        self.assertEqual(self.client.get.call_args.kwargs['params']['delivery_key'], 'eq.' + self.key)
        self.client.post.assert_not_called()
        self.client.patch.assert_not_called()
        for key in ('', 'invalid', self.key + '&status=eq.accepted'):
            with self.assertRaises(ValueError):
                self.store.read_receipt(key)
        self.assertEqual(self.client.get.call_count, 1)

    def test_conflicting_initial_reservation_reads_first_saved_body(self):
        self.client.get.side_effect = [response([]), response([self.row])]
        self.client.post.return_value = response([], 201)
        changed = {'to': ['other@example.test'], 'html': 'Later template'}
        result = self.store.reserve(self.key, changed, payload_fingerprint(changed))
        self.assertEqual(result['payload'], self.payload)
        self.client.patch.assert_not_called()

    def test_existing_accepted_record_requires_no_write_or_body(self):
        accepted = {**self.row, 'status': 'accepted', 'provider_id': 'email-1', 'payload': None}
        self.client.get.return_value = response([accepted])
        self.assertEqual(self.store.reserve(self.key, {}, 'ignored'), accepted)
        self.client.post.assert_not_called()
        self.client.patch.assert_not_called()

    def test_no_row_after_insert_never_claims_success(self):
        self.client.get.return_value = response([])
        self.client.post.return_value = response([], 201)
        with self.assertRaises(EmailDeliveryPending):
            self.store.reserve(self.key, self.payload, self.row['payload_fingerprint'])

    def test_attempt_timestamp_is_conditionally_set_once(self):
        stamped = {**self.row, 'first_attempt_at': 1000}
        self.client.patch.return_value = response([stamped])
        self.assertEqual(self.store.begin_attempt(self.row), stamped)
        request = self.client.patch.call_args.kwargs
        self.assertEqual(request['params']['first_attempt_at'], 'is.null')
        self.assertEqual(request['params']['status'], 'eq.pending')
        self.assertEqual(request['params']['payload_fingerprint'], 'eq.' + self.row['payload_fingerprint'])
        self.assertEqual(request['json'], {'first_attempt_at': 1000})
        self.store.begin_attempt(stamped)
        self.assertEqual(self.client.patch.call_count, 1)

    def test_stamp_race_returns_already_accepted_record(self):
        accepted = {**self.row, 'status': 'accepted', 'provider_id': 'email-1',
                    'payload': None, 'first_attempt_at': 900}
        self.client.patch.return_value = response([])
        self.client.get.return_value = response([accepted])
        self.assertEqual(self.store.begin_attempt(self.row), accepted)

    def test_acceptance_clears_body_and_is_scoped_to_key_fingerprint_and_attempt(self):
        stamped = {**self.row, 'first_attempt_at': 1000}
        accepted = {**stamped, 'status': 'accepted', 'provider_id': 'email-1', 'payload': None}
        self.client.patch.return_value = response([accepted])
        self.assertTrue(self.store.accept(stamped, 'email-1'))
        request = self.client.patch.call_args.kwargs
        self.assertEqual(request['params']['delivery_key'], 'eq.' + self.key)
        self.assertEqual(request['params']['first_attempt_at'], 'eq.1000')
        self.assertEqual(request['json'], {'status': 'accepted', 'provider_id': 'email-1', 'payload': None})

    def test_zero_row_acceptance_checks_same_provider_id_not_any_status(self):
        self.client.patch.return_value = response([])
        for provider_id, expected in [('email-1', True), ('different-email', False)]:
            self.client.get.return_value = response([{**self.row, 'status': 'accepted',
                                                     'provider_id': provider_id, 'payload': None}])
            self.assertIs(self.store.accept({**self.row, 'first_attempt_at': 1000}, 'email-1'), expected)

    def test_database_error_or_ambiguous_multiple_rows_are_not_success(self):
        for result in (response([], 500), response({}), response([self.row, self.row])):
            self.client.get.return_value = result
            with self.assertRaises(EmailDeliveryPending):
                self.store.reserve(self.key, self.payload, self.row['payload_fingerprint'])
        self.client.post.assert_not_called()

    def test_configuration_cannot_fall_back_to_browser_or_unauthenticated_access(self):
        with self.assertRaises(EmailDeliveryPending):
            EmailDeliveryStore(supabase_url='https://database.example.test', service_key='')
        self.client.get.return_value = response([self.row])
        self.store.reserve(self.key, self.payload, self.row['payload_fingerprint'])
        request = self.client.get.call_args.kwargs
        self.assertEqual(request['headers']['Authorization'], 'Bearer test-only')
        self.assertEqual(request['headers']['apikey'], 'test-only')

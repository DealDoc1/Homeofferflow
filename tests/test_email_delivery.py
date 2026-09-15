"""Offline fault injection for the durable email protocol; no live sends."""
import copy
from concurrent.futures import ThreadPoolExecutor
import threading
import unittest

from lib.email_delivery import (
    EmailDeliveryNeedsReview, EmailDeliveryPending, SAFE_RETRY_SECONDS,
    deliver_email_once, delivery_key, receipt_payload,
)


class Store:
    def __init__(self):
        self.key = delivery_key('buyer-packet', 'cs_controlled_test_only')
        self.payload = {'from': 'offers@example.test', 'to': ['buyer@example.test'],
                        'subject': 'Your offer', 'html': '<p>Review your offer.</p>',
                        'attachments': [{'filename': 'offer.pdf', 'content': 'private-fixture'}]}
        self.rows = {}
        self.provider = {}
        self.provider_calls = []
        self.now = 1000
        self.lock = threading.Lock()
        self.reserve_fails = False
        self.stamp_fails = False
        self.accept_fails = False
        self.accept_false = False
        self.provider_times_out = False
        self.provider_response = 'normal'

    def reserve(self, key, payload, fingerprint):
        if self.reserve_fails:
            raise TimeoutError('private database details')
        with self.lock:
            self.rows.setdefault(key, {'delivery_key': key, 'payload': copy.deepcopy(payload),
                                      'payload_fingerprint': fingerprint, 'status': 'pending',
                                      'first_attempt_at': None, 'provider_id': None})
            return copy.deepcopy(self.rows[key])

    def stamp(self, row):
        if self.stamp_fails:
            raise TimeoutError('private database details')
        with self.lock:
            saved = self.rows[row['delivery_key']]
            if saved['first_attempt_at'] is None:
                saved['first_attempt_at'] = self.now
            return copy.deepcopy(saved)

    def send(self, payload, key):
        with self.lock:
            assert self.rows[key]['first_attempt_at'] is not None
            self.provider_calls.append((key, copy.deepcopy(payload)))
            if key in self.provider:
                assert self.provider[key]['payload'] == payload, 'Provider rejects a changed body'
            else:
                self.provider[key] = {'id': 'email-' + str(len(self.provider) + 1),
                                      'payload': copy.deepcopy(payload)}
            result = {'id': self.provider[key]['id']}
        if self.provider_times_out:
            raise TimeoutError('private provider response')
        return result if self.provider_response == 'normal' else self.provider_response

    def accept(self, row, provider_id):
        if self.accept_fails:
            raise TimeoutError('private database details')
        if self.accept_false:
            return False
        with self.lock:
            saved = self.rows[row['delivery_key']]
            if saved['status'] == 'accepted':
                return saved['provider_id'] == provider_id
            saved.update(status='accepted', provider_id=provider_id, payload=None)
            return True

    def run(self):
        return deliver_email_once(key=self.key, payload=self.payload, reserve=self.reserve,
                                  begin_attempt=self.stamp, send=self.send, accept=self.accept,
                                  clock=lambda: self.now)


class EmailDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_first_send_saves_acceptance_without_claiming_inbox_delivery(self):
        original = copy.deepcopy(self.store.payload)
        result = self.store.run()
        self.assertEqual(result, {'id': 'email-1', 'status': 'accepted', 'recovered': False})
        self.assertEqual(self.store.payload, original)
        self.assertIsNone(self.store.rows[self.store.key]['payload'])

    def test_confirmed_acceptance_prevents_replay_even_after_provider_key_expires(self):
        self.store.run()
        self.store.now += 7 * 24 * 3600
        result = self.store.run()
        self.assertTrue(result['recovered'])
        self.assertEqual(len(self.store.provider_calls), 1)

    def test_timeout_retry_uses_original_attachment_template_status_and_recipients(self):
        original = copy.deepcopy(self.store.payload)
        self.store.provider_times_out = True
        with self.assertRaises(EmailDeliveryPending):
            self.store.run()
        self.store.provider_times_out = False
        self.store.payload.update(to=['changed@example.test'], html='<p>New signing status</p>',
                                  attachments=[{'filename': 'offer.pdf', 'content': 'new-pdf-timestamp'}])
        self.store.run()
        self.assertEqual(len(self.store.provider), 1)
        tagged = receipt_payload(self.store.key, original)
        self.assertEqual([body for _, body in self.store.provider_calls], [tagged, tagged])

    def test_uncertain_final_write_replays_same_provider_key(self):
        for failure in ('accept_fails', 'accept_false'):
            with self.subTest(failure=failure):
                self.store = Store()
                setattr(self.store, failure, True)
                with self.assertRaises(EmailDeliveryPending):
                    self.store.run()
                setattr(self.store, failure, False)
                self.store.run()
                self.assertEqual(len(self.store.provider), 1)
                self.assertEqual(len(self.store.provider_calls), 2)

    def test_failed_persistence_never_falls_back_to_untracked_send(self):
        for failure in ('reserve_fails', 'stamp_fails'):
            with self.subTest(failure=failure):
                self.store = Store()
                setattr(self.store, failure, True)
                with self.assertRaises(EmailDeliveryPending) as caught:
                    self.store.run()
                self.assertNotIn('private', str(caught.exception))
                self.assertEqual(self.store.provider_calls, [])

    def test_old_uncertain_attempt_is_not_sent_with_expired_provider_protection(self):
        self.store.provider_times_out = True
        with self.assertRaises(EmailDeliveryPending):
            self.store.run()
        self.store.provider_times_out = False
        self.store.now += SAFE_RETRY_SECONDS
        with self.assertRaises(EmailDeliveryNeedsReview):
            self.store.run()
        self.assertEqual(len(self.store.provider_calls), 1)

    def test_repeated_attempts_do_not_reset_first_attempt_clock(self):
        self.store.provider_times_out = True
        for advance in (0, 100, 200):
            self.store.now += advance
            with self.assertRaises(EmailDeliveryPending):
                self.store.run()
        self.assertEqual(self.store.rows[self.store.key]['first_attempt_at'], 1000)

    def test_never_attempted_record_can_start_later_without_false_expiration(self):
        self.store.stamp_fails = True
        with self.assertRaises(EmailDeliveryPending):
            self.store.run()
        self.store.now += 7 * 24 * 3600
        self.store.stamp_fails = False
        self.assertEqual(self.store.run()['status'], 'accepted')

    def test_parallel_callbacks_share_one_immutable_provider_request(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: self.store.run(), range(20)))
        self.assertEqual({result['id'] for result in results}, {'email-1'})
        self.assertEqual(len(self.store.provider), 1)

    def test_changed_or_missing_stored_body_cannot_be_sent(self):
        self.store.stamp_fails = True
        with self.assertRaises(EmailDeliveryPending):
            self.store.run()
        self.store.stamp_fails = False
        self.store.rows[self.store.key]['payload']['to'] = ['unreviewed@example.test']
        with self.assertRaises(EmailDeliveryPending):
            self.store.run()
        self.assertEqual(self.store.provider_calls, [])

    def test_malformed_acceptance_never_becomes_sent_status(self):
        for response in (None, {}, {'id': ''}, {'id': 1}):
            with self.subTest(response=response):
                self.store = Store()
                self.store.provider_response = response
                with self.assertRaises(EmailDeliveryPending):
                    self.store.run()
                self.assertEqual(self.store.rows[self.store.key]['status'], 'pending')

    def test_invalid_attempt_timestamps_are_not_treated_as_safe(self):
        for timestamp in (True, 'nan', 'inf', 'bad', 2000):
            with self.subTest(timestamp=timestamp):
                self.store = Store()
                self.store.stamp_fails = True
                with self.assertRaises(EmailDeliveryPending):
                    self.store.run()
                self.store.stamp_fails = False
                self.store.rows[self.store.key]['first_attempt_at'] = timestamp
                with self.assertRaises(EmailDeliveryPending):
                    self.store.run()
                self.assertEqual(self.store.provider_calls, [])

    def test_keys_are_stable_scoped_and_do_not_expose_raw_identity(self):
        first = delivery_key('buyer-packet', 'cs_test_secret')
        self.assertEqual(first, delivery_key('buyer-packet', 'cs_test_secret'))
        self.assertNotEqual(first, delivery_key('admin-alert', 'cs_test_secret'))
        self.assertNotEqual(first, delivery_key('buyer-packet', 'cs_other_order'))
        self.assertNotIn('cs_test_secret', first)
        self.assertLess(len(first), 256)

    def test_missing_trusted_identity_and_nonfinite_payload_fail_before_storage(self):
        for identity in ('', None):
            with self.assertRaises(ValueError):
                delivery_key('buyer-packet', identity)
        self.store.payload['invalid'] = float('nan')
        with self.assertRaises(ValueError):
            self.store.run()
        self.assertEqual(self.store.rows, {})

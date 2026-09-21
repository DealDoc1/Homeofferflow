"""Offline provider-receipt recovery; never contacts Resend or sends mail."""
import copy
import io
import json
import time
import unittest
from unittest.mock import Mock, patch

from lib.email_delivery import (EmailDeliveryPending, EmailDeliveryNeedsReview,
    payload_fingerprint, receipt_payload, reconcile_verified_email_event)
from tests.test_email_delivery import Store
from tests import test_resend_delivery_webhook as webhook_tests

MODULE = webhook_tests.MODULE


class EmailReceiptRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.provider_times_out = True
        with self.assertRaises(EmailDeliveryPending):
            self.store.run()
        body = self.store.provider[self.store.key]['payload']
        self.event = {'type': 'email.delivered', 'data': {
            'email_id': 'email-1', 'from': body['from'], 'to': body['to'],
            'tags': {tag['name']: tag['value'] for tag in body['tags']}}}

    def recover(self, event=None):
        return reconcile_verified_email_event(event or self.event,
            read=lambda key: copy.deepcopy(self.store.rows.get(key)), accept=self.store.accept)

    def test_late_receipt_recovers_timed_out_send_without_provider_replay(self):
        self.store.now += 7 * 24 * 3600
        with self.assertRaises(EmailDeliveryNeedsReview):
            self.store.run()
        self.assertTrue(self.recover())
        self.assertEqual(self.store.run()['status'], 'accepted')
        self.assertEqual(len(self.store.provider_calls), 1)
        self.assertIsNone(self.store.rows[self.store.key]['payload'])

    def test_repeated_or_out_of_order_receipts_preserve_provider_identity(self):
        self.assertTrue(self.recover())
        self.event['type'] = 'email.sent'
        self.assertTrue(self.recover())
        self.event['data']['email_id'] = 'another-email'
        self.assertFalse(self.recover())
        self.assertEqual(self.store.rows[self.store.key]['provider_id'], 'email-1')

    def test_bounce_confirms_acceptance_not_delivery_and_does_not_resend(self):
        self.event['type'] = 'email.bounced'
        self.assertTrue(self.recover())
        self.assertEqual(self.store.run()['status'], 'accepted')
        self.assertEqual(len(self.store.provider_calls), 1)

    def test_wrong_tags_sender_recipients_or_provider_id_cannot_accept(self):
        changes = [('tags', {}), ('tags', {'hof_delivery': self.store.key, 'hof_payload': '0' * 64}),
                   ('from', 'someone@example.test'), ('to', ['other@example.test']),
                   ('email_id', ''), ('email_id', '../another')]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                event = copy.deepcopy(self.event)
                event['data'][field] = value
                self.assertFalse(self.recover(event))
                self.assertEqual(self.store.rows[self.store.key]['status'], 'pending')

    def test_unknown_inbound_and_legacy_events_do_not_even_lookup(self):
        read = Mock()
        for event in ({'type': 'email.received', 'data': self.event['data']},
                      {'type': 'email.sent', 'data': {'email_id': 'legacy'}}):
            self.assertFalse(reconcile_verified_email_event(event, read=read, accept=Mock()))
        read.assert_not_called()

    def test_missing_unattempted_and_corrupted_records_are_untouched(self):
        row = copy.deepcopy(self.store.rows[self.store.key])
        for invalid in (None, {**row, 'first_attempt_at': None},
                        {**row, 'payload_fingerprint': '0' * 64}):
            accept = Mock()
            self.assertFalse(reconcile_verified_email_event(self.event, read=lambda key: invalid, accept=accept))
            accept.assert_not_called()

    def test_digest_binds_attachment_content_even_if_database_hash_is_recomputed(self):
        row = self.store.rows[self.store.key]
        row['payload']['attachments'][0]['content'] = 'different-pdf'
        row['payload_fingerprint'] = payload_fingerprint(row['payload'])
        self.assertFalse(self.recover())

    def test_database_write_failure_can_be_retried_without_sending(self):
        self.store.accept_false = True
        with self.assertRaises(EmailDeliveryPending):
            self.recover()
        self.store.accept_false = False
        self.assertTrue(self.recover())
        self.assertEqual(len(self.store.provider_calls), 1)

    def test_existing_campaign_tags_are_preserved_and_reserved_tags_rejected(self):
        for tags in ([], [{'name': 'email_type', 'value': 'buyer_packet'}]):
            source = {**self.store.payload, 'tags': tags}
            body = receipt_payload(self.store.key, source)
            self.assertEqual(body['tags'][:-2], tags)
            row = {**self.store.rows[self.store.key], 'payload': body,
                   'payload_fingerprint': payload_fingerprint(body)}
            event = copy.deepcopy(self.event)
            event['data']['tags'] = {tag['name']: tag['value'] for tag in body['tags']}
            accept = Mock(return_value=True)
            self.assertTrue(reconcile_verified_email_event(event, read=lambda key: row, accept=accept))
        for tags in ({}, [{'name': 'hof_delivery', 'value': 'override'}], [None], [{}] * 74):
            with self.assertRaises(ValueError):
                receipt_payload(self.store.key, {**self.store.payload, 'tags': tags})


class ReceiptWebhookBoundaryTests(unittest.TestCase):
    def run_webhook(self, event, *, valid=True, reconcile_effect=None, claimed=True):
        body = json.dumps(event).encode()
        timestamp = str(int(time.time()))
        signature = webhook_tests.ResendDeliveryWebhookTests()._signature(body, timestamp=timestamp)
        handler = object.__new__(MODULE.handler)
        handler.headers = {'Content-Length': str(len(body)), 'svix-id': 'msg_1',
            'svix-timestamp': timestamp, 'svix-signature': signature if valid else 'v1,invalid'}
        handler.rfile = io.BytesIO(body)
        handler._log_resend_webhook = Mock()
        with patch.object(MODULE, 'RESEND_WEBHOOK_SECRET', 'whsec_c2lnbmluZy1rZXk'), \
             patch.object(MODULE, '_reconcile_resend_receipt', side_effect=reconcile_effect) as reconcile, \
             patch.object(MODULE, '_claim_resend_webhook_event', return_value=claimed) as claim, \
             patch.object(MODULE, '_send') as send:
            handler._handle_resend_webhook()
        return send.call_args.args[1], reconcile, claim

    def test_invalid_signature_never_reconciles_or_claims(self):
        status, reconcile, claim = self.run_webhook({'type': 'email.sent'}, valid=False)
        self.assertEqual(status, 400)
        reconcile.assert_not_called()
        claim.assert_not_called()

    def test_reconciliation_failure_does_not_claim_event_and_returns_retryable_error(self):
        status, reconcile, claim = self.run_webhook({'type': 'email.sent'},
            reconcile_effect=EmailDeliveryPending('unavailable'))
        self.assertEqual(status, 500)
        reconcile.assert_called_once()
        claim.assert_not_called()

    def test_duplicate_telemetry_still_runs_receipt_reconciliation(self):
        status, reconcile, claim = self.run_webhook({'type': 'email.sent'}, claimed=False)
        self.assertEqual(status, 200)
        reconcile.assert_called_once()
        claim.assert_called_once()

    def test_verified_route_recovers_real_coordinator_timeout_and_checkout_replay(self):
        store = Store()
        store.provider_times_out = True
        with self.assertRaises(EmailDeliveryPending):
            store.run()
        body = store.provider[store.key]['payload']
        event = {'type': 'email.delivered', 'data': {'email_id': 'email-1',
            'from': body['from'], 'to': body['to'],
            'tags': {tag['name']: tag['value'] for tag in body['tags']}}}
        original_reconcile = MODULE._reconcile_resend_receipt
        with patch.object(MODULE, 'EmailDeliveryStore') as factory:
            factory.return_value.read_receipt.side_effect = lambda key: copy.deepcopy(store.rows.get(key))
            factory.return_value.accept.side_effect = store.accept
            status, _, _ = self.run_webhook(event, reconcile_effect=original_reconcile)
        self.assertEqual(status, 200)
        store.now += 7 * 24 * 3600
        self.assertEqual(store.run()['status'], 'accepted')
        self.assertEqual(len(store.provider_calls), 1)

    def test_wrapper_uses_private_store_without_leaking_receipt_tags_to_telemetry(self):
        with patch.object(MODULE, 'EmailDeliveryStore') as factory:
            self.assertFalse(MODULE._reconcile_resend_receipt({'type': 'email.sent', 'data': {}}))
            factory.assert_not_called()
        store = Store()
        event = {'type': 'email.sent', 'data': {'tags': {'hof_delivery': store.key, 'hof_payload': 'a' * 64}}}
        with patch.object(MODULE, 'EmailDeliveryStore') as factory, \
             patch.object(MODULE, 'reconcile_verified_email_event', return_value=True) as reconcile:
            self.assertTrue(MODULE._reconcile_resend_receipt(event))
            self.assertEqual(reconcile.call_args.kwargs['read'], factory.return_value.read_receipt)
        self.assertEqual(MODULE._resend_event_row(event, 'msg_1')['tags'], {})


if __name__ == '__main__':
    unittest.main()

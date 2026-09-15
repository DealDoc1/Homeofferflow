import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from lib.email_delivery import EmailDeliveryPending, payload_fingerprint, receipt_payload
from lib.email_receipt_lookup import inspect_email_receipt
from scripts import reconcile_email_receipt as cli
from tests.test_email_delivery import Store


class EmailReceiptLookupTests(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.provider_id = '11111111-1111-4111-8111-111111111111'
        body = receipt_payload(self.store.key, self.store.payload)
        self.row = self.store.reserve(self.store.key, body, payload_fingerprint(body))
        self.row = self.store.stamp(self.row)
        self.result = {'object': 'email', 'id': self.provider_id, 'last_event': 'delivered',
                       'from': body['from'], 'to': body['to'], 'tags': body['tags']}
        self.retrieve = Mock(side_effect=lambda _: copy.deepcopy(self.result))
        self.accept = Mock(side_effect=self.store.accept)

    def run_lookup(self, apply=False):
        return inspect_email_receipt(key=self.store.key, provider_id=self.provider_id,
            read=lambda key: copy.deepcopy(self.store.rows.get(key)), accept=self.accept,
            retrieve=self.retrieve, apply=apply)

    def test_read_only_default_matches_without_mutation_or_sending(self):
        self.assertEqual(self.run_lookup()['status'], 'matched')
        self.accept.assert_not_called()
        self.assertEqual(self.store.rows[self.store.key]['status'], 'pending')
        self.assertEqual(self.store.provider_calls, [])

    def test_apply_uses_conditional_acceptance_then_requires_no_provider_request_on_replay(self):
        self.assertTrue(self.run_lookup(True)['updated'])
        self.assertIsNone(self.store.rows[self.store.key]['payload'])
        self.assertEqual(self.run_lookup(True)['status'], 'already_accepted')
        self.retrieve.assert_called_once_with(self.provider_id)
        self.accept.assert_called_once()

    def test_rejected_mail_is_attention_not_delivered_and_never_sent_again(self):
        for outcome in ('bounced', 'suppressed', 'complained'):
            self.result['last_event'] = outcome
            result = self.run_lookup()
            self.assertTrue(result['needsAttention'])
            self.assertEqual(result['providerStatus'], outcome)
        self.assertEqual(self.store.provider_calls, [])

    def test_legacy_untagged_or_conflicting_tagged_messages_are_not_auto_confirmed(self):
        for tags in ([], None, self.result['tags'] + [self.result['tags'][0]],
                     [{'name': 'hof_delivery', 'value': 'different-request'}]):
            self.result['tags'] = tags
            self.assertEqual(self.run_lookup(True)['status'], 'unmatched')
        self.accept.assert_not_called()

    def test_wrong_recipient_or_content_digest_is_not_a_match(self):
        self.result['to'] = ['wrong@example.test']
        self.assertEqual(self.run_lookup(True)['status'], 'unmatched')
        self.result['to'] = self.store.payload['to']
        self.result['tags'][1]['value'] = '0' * 64
        self.assertEqual(self.run_lookup(True)['status'], 'unmatched')
        self.accept.assert_not_called()

    def test_unknown_scheduled_and_failed_statuses_do_not_claim_acceptance(self):
        for status in ('scheduled', 'failed', None, 'future_status'):
            self.result['last_event'] = status
            self.assertEqual(self.run_lookup(True)['status'], 'unconfirmed')
        self.accept.assert_not_called()

    def test_unknown_delivery_does_not_query_provider(self):
        self.store.rows.clear()
        self.assertEqual(self.run_lookup(True)['status'], 'not_found')
        self.retrieve.assert_not_called()

    def test_mismatched_provider_response_and_database_failure_do_not_report_success(self):
        self.result['id'] = 'another-id'
        with self.assertRaises(EmailDeliveryPending):
            self.run_lookup(True)
        self.accept.assert_not_called()
        self.result['id'] = self.provider_id
        self.store.accept_false = True
        with self.assertRaises(EmailDeliveryPending):
            self.run_lookup(True)

    def test_invalid_provider_id_is_rejected_before_io(self):
        for provider_id in ('../emails', self.provider_id + '?token=value', '', None):
            with self.assertRaises(ValueError):
                inspect_email_receipt(key=self.store.key, provider_id=provider_id,
                    read=Mock(), accept=self.accept, retrieve=self.retrieve)
        self.retrieve.assert_not_called()

    def test_cli_is_read_only_by_default_and_never_prints_provider_content(self):
        client = Mock()
        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = {**self.result, 'html': 'PRIVATE BODY'}
        store = Mock()
        store.read_receipt.return_value = self.row
        output = io.StringIO()
        with patch.dict(cli.os.environ, {'RESEND_API_KEY': 'secret-test-only'}), \
             patch.object(cli.httpx, 'Client') as factory, \
             patch.object(cli, 'EmailDeliveryStore', return_value=store), redirect_stdout(output):
            factory.return_value.__enter__.return_value = client
            code = cli.main(['--delivery-key', self.store.key, '--provider-id', self.provider_id])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())['status'], 'matched')
        self.assertNotIn('PRIVATE', output.getvalue())
        self.assertNotIn('secret-test-only', output.getvalue())
        self.assertEqual(client.get.call_args.args[0], 'https://api.resend.com/emails/' + self.provider_id)
        store.accept.assert_not_called()
        client.post.assert_not_called()

    def test_cli_exception_output_is_sanitized(self):
        output = io.StringIO()
        with patch.dict(cli.os.environ, {'RESEND_API_KEY': 'secret-test-only'}), \
             patch.object(cli, 'EmailDeliveryStore', side_effect=RuntimeError('PRIVATE TOKEN')), redirect_stdout(output):
            code = cli.main(['--delivery-key', self.store.key, '--provider-id', self.provider_id])
        self.assertEqual(code, 1)
        self.assertNotIn('PRIVATE', output.getvalue())
        self.assertFalse(json.loads(output.getvalue())['updated'])


if __name__ == '__main__':
    unittest.main()

"""Verified webhook-to-update tests, with a stateful offline HTTP adapter."""
import asyncio
import hashlib
import hmac
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('webhook_lifecycle_runtime', ROOT / 'api/signwell-webhook.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WebhookLifecycleRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.rows = {
            'hof_offers': {'status': 'Generated', 'signwell_status': None},
            'hof_standalone_agreements': {'status': 'draft', 'signwell_status': None},
            'hof_seller_disclosure_drafts': {'status': 'draft', 'signwell_status': None},
        }
        self.requests = []
        self.responses = []
        self.client = AsyncMock()
        self.client.patch.side_effect = self.database_patch
        self.client.post.return_value = SimpleNamespace(status_code=201)
        self.patches = [
            patch.object(MODULE, 'SUPABASE_URL', 'https://database.example'),
            patch.object(MODULE, 'SUPABASE_SERVICE_ROLE_KEY', 'test-only'),
            patch.object(MODULE, 'SIGNWELL_WEBHOOK_ID', 'test-webhook'),
            patch.object(MODULE, '_update_partner_agreement', AsyncMock()),
            patch.object(MODULE, '_json', lambda handler, code, body: self.responses.append((code, body))),
            patch.object(MODULE.httpx, 'AsyncClient'),
        ]
        for item in self.patches:
            result = item.start()
            self.addCleanup(item.stop)
        result.return_value.__aenter__.return_value = self.client

    async def database_patch(self, url, *, json, **kwargs):
        self.requests.append((url, json))
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        self.assertEqual(query['signwell_document_id'], ['eq.tracked-doc'])
        table = parsed.path.rsplit('/', 1)[-1]
        row = self.rows[table]
        guard = query['status'][0]
        self.assertTrue(guard.startswith('not.in.('))
        excluded = [value.strip('"') for value in guard[len('not.in.('):-1].split(',')]
        if row['status'] in excluded:
            return SimpleNamespace(status_code=200)
        if 'or' in query:
            expression = query['or'][0]
            self.assertTrue(expression.startswith('(signwell_status.is.null,signwell_status.not.in.('))
            values = expression.split('not.in.(', 1)[1][:-2]
            progressed = [value.strip('"') for value in values.split(',')]
            if row['signwell_status'] in progressed:
                return SimpleNamespace(status_code=200)
        row.update(json)
        return SimpleNamespace(status_code=200)

    def event(self, event_type, recipients=None, valid=True):
        signature = hmac.new(b'test-webhook', f'{event_type}@123'.encode(), hashlib.sha256).hexdigest()
        payload = {'event': {'type': event_type, 'time': 123, 'hash': signature if valid else 'invalid'},
                   'data': {'id': 'tracked-doc'}, 'recipients': recipients or []}
        body = json.dumps(payload).encode()
        handler = MODULE.handler.__new__(MODULE.handler)
        handler.headers = {'Content-Length': str(len(body)), 'content-length': str(len(body))}
        handler.rfile = io.BytesIO(body)
        handler.do_POST()
        self.assertEqual(self.responses[-1][0], 200)

    def test_created_event_never_marks_any_packet_sent(self):
        self.event('document_created')
        self.assertEqual(self.requests, [])
        self.assertEqual(self.rows['hof_standalone_agreements']['status'], 'draft')
        self.assertEqual(self.rows['hof_seller_disclosure_drafts']['status'], 'draft')
        self.assertEqual(MODULE._status_for({'event': 'document_created'}), ('Generated', 'Draft - not sent'))

    def test_one_signer_event_never_marks_whole_packet_signed(self):
        for recipients in ([{'status': 'signed'}], [{'status': 'completed'}, {}],
                           [{'status': 'completed', 'role': 'cc'}], []):
            self.event('document_signed', recipients)
            for row in self.rows.values():
                self.assertEqual(row['signwell_status'], 'Partially Signed')
                self.assertNotIn('signed_at', row)
            self.assertEqual(self.rows['hof_standalone_agreements']['status'], 'sent')

    def test_completed_event_marks_all_packet_types_signed_and_replays_do_not_reset_timestamp(self):
        self.event('document_completed')
        before = {table: dict(row) for table, row in self.rows.items()}
        for row in self.rows.values():
            self.assertEqual(row['signwell_status'], 'Buyer Signatures Complete')
            self.assertIn('signed_at', row)
        for event in ('document_completed', 'document_sent', 'document_viewed', 'document_signed', 'document_created'):
            self.event(event)
        self.assertEqual(self.rows, before)

    def test_delayed_sent_or_viewed_event_does_not_regress_partial_progress(self):
        self.event('document_in_progress')
        before = {table: dict(row) for table, row in self.rows.items()}
        self.event('document_sent')
        self.event('document_viewed')
        self.assertEqual(self.rows, before)

    def test_delayed_sent_event_does_not_undo_viewed_status(self):
        self.event('document_viewed')
        self.event('document_sent')
        self.assertTrue(all(row['signwell_status'] == 'Viewed' for row in self.rows.values()))

    def test_void_requests_stay_void_when_older_progress_notifications_arrive(self):
        self.event('document_canceled')
        before = {table: dict(row) for table, row in self.rows.items()}
        for event in ('document_created', 'document_sent', 'document_viewed', 'document_signed'):
            self.event(event)
        self.assertEqual(self.rows, before)

    def test_unknown_and_unsigned_events_never_guess_success(self):
        for event in ('document_unsigned', 'document_not_completed', 'future_event', 'template_completed'):
            self.event(event, [{'status': 'completed'}])
            self.assertEqual(self.responses[-1][1]['reason'], 'unsupported_lifecycle_event')
        self.assertEqual(self.requests, [])

    def test_unverified_notification_never_updates_records(self):
        self.event('document_completed', valid=False)
        self.assertEqual(self.requests, [])
        self.assertEqual(self.responses[-1][1]['reason'], 'invalid_webhook_signature')

    def test_recipient_telemetry_does_not_count_unsigned_or_truthy_strings_as_signed(self):
        total, signed, viewed = MODULE._recipient_stats({'recipients': [
            {'status': 'unsigned'}, {'status': 'not completed'}, {'signed': 'false'},
            {'status': 'signed'}, {'completed': True},
        ]})
        self.assertEqual((total, signed, viewed), (5, 2, 0))


if __name__ == '__main__':
    unittest.main()

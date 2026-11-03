import copy
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lib.offer_printing import unsigned_offer_copy

OWNER = '22222222-2222-4222-8222-222222222222'
OFFER = '11111111-1111-4111-8111-111111111111'


class OfferPrintingTests(unittest.TestCase):
    def setUp(self):
        self.record = {'id': OFFER, 'user_id': OWNER, 'status': 'Generated', 'offer_data': {
            'address': 'Fictional QA property', 'price': '125000',
            '_signing_source_hashes': {'main': 'a' * 64},
            '_signing_render_revisions': {'main': 'v1'}, 'signwell': {'private': 'not print authority'}}}
        self.load = Mock(return_value=self.record)
        self.render = Mock(return_value=b'%PDF-fictional-unsigned-copy')

    def call(self, **kwargs):
        return unsigned_offer_copy(kwargs.get('offer_id', OFFER), kwargs.get('user_id', OWNER), load=self.load, render=self.render)

    def test_uses_owned_server_snapshot_without_mutating_it(self):
        original = copy.deepcopy(self.record)
        def render(answers, record):
            self.assertNotIn('signwell', answers)
            self.assertEqual(answers['price'], '125000')
            answers['local_render_only'] = True
            record['status'] = 'Not persisted'
            return b'%PDF-fictional-unsigned-copy'
        self.render.side_effect = render
        self.assertTrue(self.call().startswith(b'%PDF-'))
        self.assertEqual(self.record, original)
        self.load.assert_called_once_with(OFFER, OWNER)

    def test_forged_or_missing_ownership_never_renders(self):
        for row in (None, {}, {**self.record, 'user_id': 'other'}, {**self.record, 'id': 'other'}):
            self.load.return_value = row
            with self.assertRaises(PermissionError): self.call()
        self.render.assert_not_called()

    def test_invalid_ids_never_read_private_data(self):
        for values in ({'offer_id': '../other'}, {'user_id': None}):
            with self.assertRaises(ValueError): self.call(**values)
        self.load.assert_not_called()

    def test_unprepared_draft_cannot_be_printed_as_a_packet(self):
        for status in ('Draft', 'Generating', 'Generation Failed'):
            self.record['status'] = status
            with self.assertRaises(ValueError): self.call()
        self.render.assert_not_called()

    def test_unsigned_copy_remains_available_during_and_after_signing(self):
        for status in ('Generated', 'Awaiting Signature', 'Signed', 'Expired'):
            self.record['status'] = status
            self.assertTrue(self.call().startswith(b'%PDF-'))

    def test_changed_source_or_renderer_cannot_silently_replace_prior_packet(self):
        for field in ('_signing_source_hashes', '_signing_render_revisions'):
            def changed(answers, record):
                answers[field] = {'main': 'different'}
                return b'%PDF-new-source'
            self.render.side_effect = changed
            with self.assertRaisesRegex(ValueError, 'version has changed'): self.call()

    def test_malformed_pdf_is_not_downloaded(self):
        self.render.return_value = b'not a PDF'
        with self.assertRaises(RuntimeError): self.call()


class OfferPrintApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('offer_print_api', Path(__file__).resolve().parents[1] / 'api/fill-pdf.py')
        cls.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.api)

    def request(self, user=OWNER, error=None, extra=None):
        api = self.api
        body = json.dumps({'action': 'print_offer_pdf', 'offerId': OFFER, **(extra or {})}).encode()
        fake = SimpleNamespace(headers={'Content-Length': str(len(body))}, rfile=io.BytesIO(body), wfile=io.BytesIO(),
            send_response=Mock(), send_header=Mock(), end_headers=Mock(), _verified_user=Mock(return_value=user), _json=Mock())
        with patch.object(api, 'print_owned_offer', return_value=b'%PDF-fixture', side_effect=error) as printing, \
             patch.object(api, 'render_subscribed_packet', side_effect=AssertionError('No packet usage')), \
             patch.object(api, 'create_signwell_signature_request', side_effect=AssertionError('No signing request')), \
             patch.object(api, 'send_email', side_effect=AssertionError('No email')):
            api.handler.do_POST(fake)
            return fake, printing

    def test_id_only_dispatch_no_allowance_or_delivery(self):
        fake, printing = self.request(extra={'offerData': {'price': 'forged'}, 'pdfBase64': 'forged',
            'type': 'checkout.session.completed', 'data': {'object': {'metadata': {'subscription_generation': 'true'}}}})
        printing.assert_called_once_with(OFFER, OWNER)
        fake.send_response.assert_called_once_with(200)
        self.assertEqual(fake.wfile.getvalue(), b'%PDF-fixture')
        self.assertIn(('Cache-Control', 'private, no-store'), [c.args for c in fake.send_header.call_args_list])

    def test_signed_out_never_reads_offer(self):
        fake, printing = self.request(user=None)
        self.assertEqual(fake._json.call_args.args[0], 401)
        printing.assert_not_called()

    def test_cross_account_refusal_and_private_failure_details_are_safe(self):
        for error, status in ((PermissionError('private'), 404), (ValueError('Version changed'), 409), (RuntimeError('secret provider response'), 503)):
            fake, _ = self.request(error=error)
            self.assertEqual(fake._json.call_args.args[0], status)
            self.assertNotIn('secret provider', str(fake._json.call_args))

    def test_database_read_is_owner_scoped_and_has_no_write_or_provider_call(self):
        api = self.api
        row = {'id': OFFER, 'user_id': OWNER, 'status': 'Generated', 'offer_data': {'address': 'Fictional QA property'}}
        with patch.object(api, 'SUPABASE_URL', 'https://fictional.example'), \
             patch.object(api, 'SUPABASE_SERVICE_ROLE_KEY', 'fictional'), \
             patch.object(api.httpx, 'get', return_value=SimpleNamespace(status_code=200,json=lambda:[row])) as read, \
             patch.object(api.httpx, 'post', side_effect=AssertionError('No outbound send or usage reservation')), \
             patch.object(api.httpx, 'patch', side_effect=AssertionError('No transaction changes')), \
             patch.object(api, 'hydrate_paragraph4_sources'), patch.object(api, 'validate_supported_offer'), \
             patch.object(api, 'fill_and_merge', return_value=b'%PDF-fixture'):
            self.assertEqual(api.print_owned_offer(OFFER, OWNER), b'%PDF-fixture')
        self.assertEqual(read.call_args.kwargs['params']['user_id'], 'eq.' + OWNER)
        self.assertEqual(read.call_args.kwargs['params']['id'], 'eq.' + OFFER)


if __name__ == '__main__': unittest.main()

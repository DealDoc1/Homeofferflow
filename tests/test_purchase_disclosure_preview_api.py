"""Real HTTP handler dispatch with fictional auth/store; never sends a packet."""
import base64
import importlib.util
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tests.test_purchase_disclosure_execution import USER, OFFER, DRAFT, REVISION

SPEC = importlib.util.spec_from_file_location('purchase_disclosure_preview_admin',
    Path(__file__).resolve().parents[1] / 'api/admin-dashboard.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)


class PurchaseDisclosurePreviewApiTests(unittest.TestCase):
    def setUp(self):
        self.data = {'action': 'preview_purchase_disclosure_execution', 'offerId': OFFER, 'draftId': DRAFT}
        self.plan = SimpleNamespace(pdf=b'%PDF-fictional-preview', binding={'id': DRAFT, 'revision': REVISION},
            recipients=[{'id': '1', 'name': 'QA Buyer', 'email': 'buyer@example.test'},
                        {'id': '3', 'name': 'QA Seller', 'email': 'seller@example.test'}])

    def request(self, data=None, user=None, error=None):
        body = json.dumps(self.data if data is None else data).encode()
        fake = SimpleNamespace(path='/api/admin-dashboard', headers={'authorization': 'Bearer fictional', 'Content-Length': str(len(body))}, rfile=BytesIO(body))
        with patch.object(API, 'SUPABASE_URL', 'https://private.example'), \
             patch.object(API, 'SUPABASE_SERVICE_ROLE_KEY', 'fictional'), \
             patch.object(API, '_verified_user', AsyncMock(return_value=user)), \
             patch.object(API, '_is_platform_admin', AsyncMock(side_effect=AssertionError('No admin or brokerage seat gate'))), \
             patch.object(API, '_json') as respond, \
             patch('lib.purchase_disclosure_store.PurchaseDisclosureStore') as store:
            store.return_value.prepare.return_value = self.plan
            store.return_value.prepare.side_effect = error
            API.handler.do_POST(fake)
            return respond.call_args.args[1:], store

    def test_authenticated_owner_preview_uses_server_records_not_browser_content(self):
        (code, result), store = self.request(user={'id': USER})
        self.assertEqual(code, 200)
        store.return_value.prepare.assert_called_once_with(user_id=USER, offer_id=OFFER, draft_id=DRAFT)
        self.assertTrue(result['previewOnly'])
        self.assertFalse(result['signatureRequestCreated'])
        self.assertEqual(base64.b64decode(result['pdfBase64']), self.plan.pdf)
        self.assertEqual([r['role'] for r in result['recipients']], ['Buyer', 'Seller'])
        self.assertNotIn('service_key', result)
        self.assertNotIn('fields', result)

    def test_signed_out_request_never_accesses_private_store(self):
        (code, _), store = self.request()
        self.assertEqual(code, 401); store.assert_not_called()

    def test_browser_cannot_supply_pdf_or_recipient_override(self):
        for extra in ({'pdfBase64': 'forged'}, {'recipients': []}, {'fieldPlan': []}):
            with self.subTest(extra=extra):
                (code, _), store = self.request({**self.data, **extra}, user={'id': USER})
                self.assertEqual(code, 400); store.assert_not_called()

    def test_cross_account_refusal_remains_forbidden_not_a_generated_preview(self):
        (code, result), _ = self.request(user={'id': USER}, error=PermissionError('Private disclosure unavailable.'))
        self.assertEqual(code, 403)
        self.assertNotIn('pdfBase64', result)

    def test_private_preview_response_is_not_cacheable(self):
        fake = SimpleNamespace(send_response=Mock(), send_header=Mock(), end_headers=Mock(), wfile=BytesIO())
        API._json(fake, 200, {'ok': True})
        self.assertIn(('Cache-Control', 'no-store'), [call.args for call in fake.send_header.call_args_list])


if __name__ == '__main__': unittest.main()

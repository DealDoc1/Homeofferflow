"""Actual HTTP adapter with fictional responses; no hosted requests or writes."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from lib.purchase_disclosure_store import PurchaseDisclosureStore
from lib.purchase_disclosure_execution import DisclosureNotReady
from tests.test_purchase_disclosure_execution import fixture, USER, OFFER, DRAFT, OTHER


class PurchaseDisclosureStoreTests(TestCase):
    def setUp(self):
        self.record, self.draft, self.links = fixture(water=True)
        self.calls = []
        self.mutation = None
        self.client = Mock()
        self.client.get.side_effect = self.get
        self.store = PurchaseDisclosureStore(supabase_url='https://private.example', service_key='fictional-test-key', client=self.client)

    def get(self, url, *, headers, timeout, params=None):
        self.calls.append((url, deepcopy(params)))
        self.assertEqual(headers['Authorization'], 'Bearer fictional-test-key')
        if '/storage/v1/object/' in url:
            return SimpleNamespace(status_code=200, content=b'%PDF-fictional-private-source')
        table = url.split('/')[-1]
        rows = {'hof_offers': [self.record], 'hof_seller_disclosure_drafts': [self.draft],
                'hof_seller_disclosure_review_links': self.links}.get(table)
        if table == 'hof_brokerage_form_sources':
            rows = [{'id': params['id'][3:], 'form_code': params['form_code'][3:], 'status': 'approved',
                'authorization_attested': True, 'source_revision': '05-04-2026',
                'storage_bucket': 'private-forms', 'storage_path': params['form_code'][3:] + '.pdf'}]
        if self.mutation: rows = self.mutation(table, deepcopy(rows))
        return SimpleNamespace(status_code=200, json=lambda: deepcopy(rows))

    def prepare(self):
        return self.store.prepare(user_id=USER, offer_id=OFFER, draft_id=DRAFT)

    def test_loads_exact_owned_records_current_reviews_and_approved_private_sources(self):
        with patch('lib.purchase_disclosure_store.prepare_execution', return_value='server-plan') as compose:
            self.assertEqual(self.prepare(), 'server-plan')
        args, kwargs = compose.call_args
        self.assertEqual(args, (self.record, self.draft, self.links))
        self.assertEqual(kwargs, {'user_id': USER, 'source_pdf': b'%PDF-fictional-private-source', 'water_pdf': b'%PDF-fictional-private-source'})
        offer_query, draft_query, link_query = [params for _, params in self.calls[:3]]
        self.assertEqual(offer_query['id'], 'eq.' + OFFER)
        self.assertEqual(offer_query['user_id'], 'eq.' + USER)
        self.assertEqual(draft_query['id'], 'eq.' + DRAFT)
        self.assertEqual(draft_query['agent_user_id'], 'eq.' + USER)
        self.assertEqual(link_query['agent_user_id'], 'eq.' + USER)
        self.assertEqual(link_query['draft_id'], 'eq.' + DRAFT)
        self.assertEqual(link_query['revoked_at'], 'is.null')
        self.assertNotIn('token_hash', link_query['select'])
        self.assertTrue(all('/storage/v1/object/private-forms/' in url for url, params in self.calls if params is None))
        self.client.post.assert_not_called(); self.client.patch.assert_not_called(); self.client.delete.assert_not_called()

    def test_wrong_offer_or_disclosure_readback_is_rejected_before_sources(self):
        for table, field in [('hof_offers', 'user_id'), ('hof_offers', 'id'),
                             ('hof_seller_disclosure_drafts', 'agent_user_id'), ('hof_seller_disclosure_drafts', 'id')]:
            self.calls.clear()
            self.mutation = lambda name, rows: [{**rows[0], field: OTHER}] if name == table else rows
            with self.subTest(table=table, field=field), self.assertRaises(PermissionError): self.prepare()
            self.assertFalse(any('/storage/' in url for url, _ in self.calls))

    def test_unfinished_or_bound_disclosure_never_loads_private_sources(self):
        for change in ({'seller_review_attested': False}, {'status': 'signed'}, {'signature_offer_id': OTHER}, {'signature_packet_id': OTHER}):
            self.calls.clear()
            self.mutation = lambda name, rows: [{**rows[0], **change}] if name == 'hof_seller_disclosure_drafts' else rows
            with self.subTest(change=change), self.assertRaises(DisclosureNotReady): self.prepare()
            self.assertFalse(any('/storage/' in url for url, _ in self.calls))

    def test_source_revision_authorization_and_identity_are_read_back_not_assumed(self):
        for change in ({'status': 'revoked'}, {'authorization_attested': False}, {'id': OFFER},
                       {'source_revision': 'old'}, {'form_code': 'TXR-1101'}, {'storage_path': ''}):
            self.calls.clear()
            self.mutation = lambda name, rows: [{**rows[0], **change}] if name == 'hof_brokerage_form_sources' else rows
            with self.subTest(change=change), self.assertRaises(DisclosureNotReady): self.prepare()
            self.assertFalse(any('/storage/' in url for url, _ in self.calls))

    def test_invalid_ids_fail_before_any_request(self):
        with self.assertRaises(ValueError): self.store.prepare(user_id=USER, offer_id='bad', draft_id=DRAFT)
        self.client.get.assert_not_called()

    def test_transport_failure_is_not_a_missing_optional_disclosure_claim(self):
        self.client.get.return_value = SimpleNamespace(status_code=503)
        self.client.get.side_effect = None
        with self.assertRaises(RuntimeError): self.prepare()

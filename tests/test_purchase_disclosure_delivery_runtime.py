"""Complete owned generation/delivery/retry path using fictional services."""
from copy import deepcopy
import base64
from io import BytesIO
import unittest
from unittest.mock import patch
from pypdf import PdfReader

from lib.purchase_disclosure_execution import DisclosureNotReady, prepare_execution
from lib.purchase_disclosure_packet import RECIPE_KEY
from lib.packet_generation import PacketGenerationPending
from tests.test_purchase_disclosure_execution import fixture, blank_pdf, USER, OFFER
from tests import test_purchase_offer_delivery_recovery as recovery

API = recovery.API


class PurchaseDisclosureDeliveryRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.h = recovery.PurchaseDeliveryRecoveryTests(methodName='runTest')
        self.h.setUp(); self.addCleanup(self.h.doCleanups)
        record, draft, links = fixture()
        self.h.offer.update(record['offer_data'])
        with patch('lib.trec_seller_disclosure.validate_source_bytes'):
            self.plan = prepare_execution(record, draft, links, user_id=USER, source_pdf=blank_pdf(4))
        self.h.offer.update(purchaseSellerDisclosureId=draft['id'],
            purchaseSellerDisclosureRevision=draft['review_content_revision'],
            purchaseSellerDisclosureFingerprint=self.plan.content_fingerprint)
        API.fill_and_merge.return_value = blank_pdf(12)
        p = patch('lib.purchase_disclosure_store.PurchaseDisclosureStore')
        self.store = p.start(); self.addCleanup(p.stop)
        self.store.return_value.prepare.return_value = self.plan

    def test_current_disclosure_is_composed_and_bound_before_parallel_send(self):
        result = self.h.checkout()
        self.assertTrue(result['signwell']['ok'])
        self.assertEqual(result['pendingDocuments'], [])
        self.assertEqual((self.h.creates,self.h.sends,self.h.usage.completions), (1,1,1))
        saved = self.h.rows[OFFER]
        self.assertEqual(saved['offer_data']['_hof_signature_delivery']['seller_disclosure'], self.plan.binding)
        self.assertEqual(saved['offer_data'][RECIPE_KEY]['binding'], self.plan.binding)
        doc = next(iter(self.h.documents.values()))
        self.assertEqual([(r['id'],r['email']) for r in doc['recipients']],
            [('1','buyer-one@example.com'),('3','seller-1@example.com')])
        self.assertFalse(doc['apply_signing_order'])
        self.assertEqual(len(PdfReader(BytesIO(base64.b64decode(doc['files'][0]['file_base64']))).pages), 16)
        self.assertEqual({f['page'] for f in doc['fields'][0] if f['api_id'].startswith('purchase_disclosure_')}, {16})
        self.assertEqual(doc['metadata']['debug_payload'], 'bundle_v20_purchase_disclosure')

    def test_rejected_send_retries_same_document_binding_without_new_allowance_or_email(self):
        self.h.failure = 'rejected'
        self.assertFalse(self.h.checkout()['signwell']['ok'])
        before = self.h.emails
        self.h.failure = None
        result = API.retry_unsent_offer_signature(OFFER, USER)
        self.assertTrue(result['ok'])
        self.assertEqual((self.h.creates,self.h.sends,self.h.emails,self.h.usage.completions), (1,2,before,1))
        self.assertTrue(self.store.return_value.prepare.call_args.kwargs['for_retry'])
        self.assertEqual(self.h.rows[OFFER]['offer_data']['_hof_signature_delivery']['seller_disclosure'], self.plan.binding)

    def test_lost_send_response_reconciles_existing_document_without_resend(self):
        self.h.failure = 'timeout_sent'
        self.assertTrue(self.h.checkout()['signwell']['ok'])
        self.h.failure = None
        self.assertTrue(API.retry_unsent_offer_signature(OFFER, USER)['ok'])
        self.assertEqual((self.h.creates,self.h.sends,self.h.usage.completions), (1,1,1))

    def test_unfinished_optional_disclosure_does_not_stop_ready_purchase(self):
        self.store.return_value.prepare.side_effect = DisclosureNotReady('Seller review pending')
        result = self.h.checkout()
        self.assertTrue(result['signwell']['ok'])
        self.assertEqual(len(result['pendingDocuments']), 1)
        self.assertFalse(self.h.rows[OFFER]['offer_data'][RECIPE_KEY]['included'])
        doc = next(iter(self.h.documents.values()))
        self.assertEqual([r['id'] for r in doc['recipients']], ['1'])
        self.assertIn("Seller's disclosure is not included", doc['message'])
        self.assertNotIn('seller_disclosure', self.h.rows[OFFER]['offer_data']['_hof_signature_delivery'])

    def test_pending_retry_cannot_add_a_disclosure_that_becomes_ready_later(self):
        self.store.return_value.prepare.side_effect = DisclosureNotReady('Pending')
        self.h.failure = 'rejected'; self.h.checkout()
        self.store.return_value.prepare.reset_mock(); self.store.return_value.prepare.side_effect = None
        self.h.failure = None
        self.assertTrue(API.retry_unsent_offer_signature(OFFER, USER)['ok'])
        self.store.return_value.prepare.assert_not_called()
        self.assertEqual(len(next(iter(self.h.documents.values()))['recipients']), 1)

    def test_stale_preview_is_explicitly_pending_not_replaced_with_new_answers(self):
        self.h.offer['purchaseSellerDisclosureFingerprint'] = 'stale'
        result = self.h.checkout()
        self.assertTrue(result['signwell']['ok'])
        self.assertEqual(len(result['pendingDocuments']), 1)
        self.assertFalse(self.h.rows[OFFER]['offer_data'][RECIPE_KEY]['included'])

    def test_unconfirmed_binding_checkpoint_cannot_send(self):
        self.h.failure = 'claim_lost'
        result = self.h.checkout()
        self.assertFalse(result['signwell']['ok'])
        self.assertEqual((self.h.creates,self.h.sends), (1,0))

    def test_browser_cannot_forge_the_server_inclusion_recipe(self):
        self.h.offer[RECIPE_KEY] = {'included': True,'binding':{'id':'forged'}}
        self.assertTrue(self.h.checkout()['signwell']['ok'])
        self.assertEqual(self.h.rows[OFFER]['offer_data'][RECIPE_KEY]['binding'], self.plan.binding)

    def test_addendum_signer_conflict_is_refused_before_provider_creation(self):
        with patch.object(API, 'hydrostatic_execution_parties', return_value=[
            {'id':'3','name':'Another Seller','email':'other@example.com'}]):
            result = self.h.checkout()
        self.assertFalse(result['signwell']['ok'])
        self.assertEqual((self.h.creates,self.h.sends), (0,0))

    def test_later_generation_uses_my_offers_retry_not_another_request(self):
        self.h.checkout()
        with self.assertRaises(PacketGenerationPending): self.h.checkout()
        self.assertEqual((self.h.creates,self.h.sends,self.h.usage.completions), (1,1,1))

    def test_changed_retry_binding_cannot_create_or_send_again(self):
        self.h.failure = 'rejected'; self.h.checkout(); self.h.failure = None
        self.store.return_value.prepare.return_value = deepcopy(self.plan)
        self.store.return_value.prepare.return_value.binding['fingerprint'] = 'changed'
        with self.assertRaises(ValueError): API.retry_unsent_offer_signature(OFFER, USER)
        self.assertEqual((self.h.creates,self.h.sends), (1,1))

    def test_download_then_send_reuses_the_same_packet_allowance(self):
        pdf, record, usage, prepared = API.render_subscribed_purchase_disclosure(self.h.offer, USER)
        self.assertEqual(len(PdfReader(BytesIO(pdf)).pages), 16)
        self.assertEqual((self.h.creates,self.h.sends,self.h.usage.completions), (0,0,1))
        self.assertTrue(self.h.checkout()['signwell']['ok'])
        self.assertEqual((self.h.creates,self.h.sends,self.h.usage.completions), (1,1,1))

    def test_duplicate_uploaded_disclosure_keeps_existing_attachment_and_does_not_add_second(self):
        self.h.offer['uploadedDisclosureDocs'] = [{'type':'seller_disclosure','name':'existing.pdf'}]
        self.assertTrue(self.h.checkout()['signwell']['ok'])
        self.store.return_value.prepare.assert_not_called()
        self.assertFalse(self.h.rows[OFFER]['offer_data'][RECIPE_KEY]['included'])


if __name__ == '__main__': unittest.main()

"""Purchase + environmental review integration, with no external service calls."""
import copy
import hashlib
from io import BytesIO
from itertools import product
import unittest
from unittest.mock import patch

import pdfplumber
from pypdf import PdfReader
from lib import production_adapter as adapter, txr_1917
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_bytes, one_page_pdf_base64
from tests.test_paragraph4_source_hydration import load_offer_api, FakeResponse


def environmental_offer(**changes):
    data = dict(environmentalAssessment='yes', environmentalReviewTypes=['environmental', 'wetlands'],
        environmentalTerminationDays='15', seller1Name='Seller One', seller1Email='seller@example.test',
        _paragraph4_source_pdf_bytes={'TXR-1917': one_page_pdf_bytes()})
    data.update(changes)
    return minimal_offer(**data)


class EnvironmentalPacketTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()
        self.hash = hashlib.sha256(one_page_pdf_bytes()).hexdigest()
        for key in ('ENVIRONMENTAL_SOURCE_SHA256', 'MINERAL_SOURCE_SHA256'):
            guard = patch.object(adapter, key, self.hash)
            guard.start()
            self.addCleanup(guard.stop)

    def test_packet_matrix_reuses_source_address_and_correct_signer_columns(self):
        for buyers, sellers in product((1, 2), repeat=2):
            with self.subTest(buyers=buyers, sellers=sellers):
                offer = environmental_offer(
                    **({'buyer2':'Buyer Two', 'buyer2Email':'two@example.test'} if buyers == 2 else {}),
                    **({'seller2Name':'Seller Two', 'seller2Email':'seller2@example.test'} if sellers == 2 else {}))
                packet = adapter.fill_and_merge_20_19(offer)
                reader = PdfReader(BytesIO(packet))
                self.assertEqual(len(reader.pages), 13)
                self.assertIn(offer['address'], reader.pages[-1].extract_text())
                self.assertIn('15', reader.pages[-1].extract_text())
                self.assertNotIn('Seller One', reader.pages[-1].extract_text())
                fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
                env = [f for f in fields if f['api_id'].startswith('txr1917')]
                self.assertEqual({f['page'] for f in env}, {13})
                self.assertEqual(len(env), buyers + sellers)
                self.assertEqual({f['recipient_id'] for f in env}, {'1', '3'} | ({'2'} if buyers == 2 else set()) | ({'4'} if sellers == 2 else set()))
                self.assertFalse(any(f['recipient_id'] in ('3', '4') and f['page'] <= 12 for f in fields))
                self.assertIn(self.hash, offer['_signing_source_hashes'])
                self.assertEqual(offer['_signing_render_revisions']['TXR-1917'], txr_1917.RENDER_REVISION)

    def test_contract_checkbox_uses_environmental_row_not_hydrostatic_row(self):
        for selected in ('yes', 'no'):
            with pdfplumber.open(BytesIO(adapter.fill_and_merge_20_19(environmental_offer(environmentalAssessment=selected)))) as pdf:
                marks = [c for c in pdf.pages[8].chars if c['text'] == 'X' and 61 <= c['x0'] <= 74 and 324 <= c['top'] <= 338]
                self.assertEqual(len(marks), int(selected == 'yes'))
                for mark in marks:
                    self.assertLessEqual(mark['bottom'], 338)
                self.assertFalse(any(c['text'] == 'X' and 61 <= c['x0'] <= 74 and 311 <= c['top'] <= 323 for c in pdf.pages[8].chars))

    def test_all_addenda_and_upload_offsets_remain_stable(self):
        offer = environmental_offer(mineralReservation='yes', mineralReservationChoice='all', mineralSurfaceRights='waived',
            hydrostaticTesting='yes', hydrostaticRiskAllocation='seller', leaseResidential='yes', leases='yes',
            residentialLeaseStatus='assignment', residentialLeaseDelivery='received',
            uploadedDisclosureDocs=[{'name':'QA.pdf', 'base64':one_page_pdf_base64(),
                'signaturePlacements':[{'type':'buyer1_signature', 'page':1, 'signwellX':50, 'signwellY':50}]}])
        offer['_paragraph4_source_pdf_bytes'].update({'TXR-1905':one_page_pdf_bytes(), 'TXR-1953':one_page_pdf_bytes()})
        packet = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 17)
        for prefix, page in [('txr1953', 13), ('trec48_1', 14), ('txr1905', 15), ('txr1917', 16), ('uploaded_', 17)]:
            self.assertEqual({f['page'] for f in fields if f['api_id'].startswith(prefix)}, {page})
        self.assertEqual(len(fields), len({f['api_id'] for f in fields}))
        other = copy.deepcopy(offer)
        other['environmentalAssessment'] = 'no'
        previous = adapter.build_signwell_fields_20_19(other, adapter.fill_and_merge_20_19(other))[0]
        self.assertEqual([f for f in fields if not f['api_id'].startswith(('txr1917', 'uploaded_'))],
                         [f for f in previous if not f['api_id'].startswith('uploaded_')])

    def test_invalid_terms_signers_and_sources_fail_before_render(self):
        changes = [{'environmentalReviewTypes':v} for v in ([], 'wetlands', ['other'], [{}])]
        changes += [{'environmentalTerminationDays':v} for v in ('', '0', '-1', '1.5', '1000', 'NaN', '1e2')]
        changes += [{'seller1Email':'bad'}, {'seller1Email':'BUYER@example.com'}, {'buyer2':'Missing email'},
                    {'_paragraph4_source_pdf_bytes':{}}, {'_paragraph4_source_pdf_bytes':{'TXR-1917':one_page_pdf_bytes()+b'changed'}}]
        for change in changes:
            with self.subTest(change=change), patch.object(adapter.verified, 'fill_and_merge') as render:
                with self.assertRaises(adapter.UnsupportedOfferPathError):
                    adapter.fill_and_merge_20_19(environmental_offer(**change))
                render.assert_not_called()

    def test_legacy_alias_and_deselection_with_stale_terms(self):
        offer = environmental_offer(environmentalAssessment='no', environmentalAddendum=True,
            paragraph4Seller1Name='Old Seller', paragraph4Seller1Email='old@example.test')
        self.assertEqual(adapter.environmental_execution_parties(offer)[0]['email'], 'seller@example.test')
        self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages), 13)
        offer.update(environmentalAddendum='no', environmentalReviewTypes=['old'], environmentalTerminationDays='bad', seller1Email='')
        offer.pop('_paragraph4_source_pdf_bytes')
        self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages), 12)
        self.assertNotIn('TXR-1917', offer['_signing_render_revisions'])

    def test_one_file_simultaneous_signing_payload_and_private_source_fetch(self):
        api = load_offer_api()
        api.SUPABASE_URL, api.SUPABASE_SERVICE_ROLE_KEY = 'https://example.supabase.co', 'fixture'
        offer = environmental_offer()
        offer.pop('_paragraph4_source_pdf_bytes')
        with patch.object(api.httpx, 'get', side_effect=[
            FakeResponse(200, payload=[{'source_revision':'12-05-2011', 'storage_bucket':'private', 'storage_path':'TXR1917.pdf'}]),
            FakeResponse(200, content=one_page_pdf_bytes())]) as get:
            api.hydrate_paragraph4_sources(offer)
        self.assertEqual(get.call_args_list[0].kwargs['params']['form_code'], 'eq.TXR-1917')
        self.assertNotIn('brokerage_id', get.call_args_list[0].kwargs['params'])
        api.SIGNWELL_ENABLED, api.SIGNWELL_API_KEY = True, 'fixture'
        packet = adapter.fill_and_merge_20_19(offer)
        with patch.object(api, 'deliver_offer_document', return_value={
            'document_id':'fixture', 'document':{'status':'sent'}, 'state':'sent', 'message':'sent', 'recovered':False}) as deliver:
            self.assertTrue(api.create_signwell_signature_request(offer, packet)['ok'])
        payload = deliver.call_args.args[1]
        self.assertFalse(payload['apply_signing_order'])
        self.assertEqual(len(payload['files']), 1)
        self.assertEqual([r['id'] for r in payload['recipients']], ['1', '3'])
        self.assertIn('environmental-assessment addendum', payload['message'])

    def test_continuation_signer_ids_and_page_offsets_are_not_lost(self):
        offer = environmental_offer(address='LongStreet' * 50, seller2Name='Two', seller2Email='two@example.test')
        packet = adapter.fill_and_merge_20_19(offer)
        fields = [f for f in adapter.build_signwell_fields_20_19(offer, packet)[0] if f['api_id'].startswith('txr1917')]
        self.assertEqual({f['page'] for f in fields}, {13, 14})
        self.assertEqual({f['recipient_id'] for f in fields if f['page'] == 14}, {'1', '3', '4'})
        text = PdfReader(BytesIO(packet)).pages[-1].extract_text().replace('\n', '')
        self.assertIn(offer['address'], text)


class EnvironmentalSourceBoundsTests(unittest.TestCase):
    def data(self, **changes):
        return {'property_address':'100 Example Street, Frisco, TX 75034', 'termination_days':'999',
                'review_types':['environmental','species','wetlands'], 'buyer_names':['Buyer One','Buyer Two'],
                'seller_names':['Seller One','Seller Two'], **changes}

    def test_signature_rectangles_fit_each_source_rule(self):
        for buyers, sellers in product((1, 2), repeat=2):
            data = self.data(buyer_names=['B']*buyers, seller_names=['S']*sellers)
            for field in txr_1917.build_signwell_fields_txr1917(data)[0]:
                left, right = (54, 288) if '_buyer' in field['api_id'] else (324, 558)
                rule = 602.88 if '2_signature' in field['api_id'] else 532.38
                self.assertGreaterEqual(field['x']*.75, left)
                self.assertLessEqual((field['x']+field['width'])*.75, right)
                gap = rule - (field['y']+field['height'])*.75
                self.assertGreaterEqual(gap, 0)
                self.assertLessEqual(gap, 2)

    def test_all_review_checkbox_combinations_and_answer_blanks_fit(self):
        choices = ['environmental','species','wetlands']
        bounds = {'environmental':(58,68.7,242.64,254.64), 'species':(58,68.7,280.32,292.32), 'wetlands':(58,68.7,345.9,357.9)}
        for flags in product((False, True), repeat=3):
            selected = [k for k, flag in zip(choices,flags) if flag]
            raw = txr_1917.render_txr_1917(one_page_pdf_bytes(), self.data(review_types=selected, _for_signing=True))
            with pdfplumber.open(BytesIO(raw)) as pdf:
                marks = [c for c in pdf.pages[0].chars if c['text'] == 'X' and c['x0'] < 70]
                self.assertEqual(len(marks), len(selected))
                for key in selected:
                    left,right,top,bottom = bounds[key]
                    self.assertEqual(sum(left<=c['x0']<c['x1']<=right and top<=c['top']<c['bottom']<=bottom for c in marks),1)
                for c in pdf.pages[0].chars:
                    if c in marks or c['text']==' ': continue
                    self.assertGreaterEqual(c['size'],7)
                    self.assertTrue((39.78<=c['x0']<c['x1']<=576 and 172<=c['top']<c['bottom']<=190.38)
                                    or (90.3<=c['x0']<c['x1']<=120.66 and 403<=c['top']<c['bottom']<=417.42),c)

    def test_long_answers_are_lossless_and_review_signing_have_same_continuations(self):
        data = self.data(property_address='LongAddress' * 45, buyer_names=['BuyerName' * 25], seller_names=['SellerName' * 25, 'SecondSeller' * 25])
        review = PdfReader(BytesIO(txr_1917.render_txr_1917(one_page_pdf_bytes(), data)))
        signed = PdfReader(BytesIO(txr_1917.render_txr_1917(one_page_pdf_bytes(), {**data, '_for_signing':True})))
        self.assertEqual(len(review.pages), len(signed.pages))
        self.assertGreater(len(review.pages), 1)
        text = ''.join(p.extract_text().replace('\n', '') for p in signed.pages[1:])
        for value in [data['property_address'], *data['buyer_names'], *data['seller_names']]:
            self.assertIn(value, text)
        fields = txr_1917.build_signwell_fields_txr1917(data)[0]
        self.assertEqual({f['recipient_id'] for f in fields if f['page']>1}, {'1','2','3'})


if __name__ == '__main__':
    unittest.main()

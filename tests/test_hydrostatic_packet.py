"""Combined purchase-packet checks using real local PDF sources; no provider calls."""
import base64
import copy
from io import BytesIO
import json
from pathlib import Path
import unittest

from pypdf import PdfReader
import pdfplumber
from lib import production_adapter as adapter
from lib.trec_48_1 import SOURCE_SHA256, RENDER_REVISION
from lib.trec_48_1 import RISK_FIELDS
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64, one_page_pdf_bytes
from tests.test_seller_temporary_lease_production_signwell import load_offer_api


def hydrostatic_offer(**overrides):
    return minimal_offer(**{'address':'123 Example Lane','city':'Frisco','zip':'75034',
        'hydrostaticTesting':'yes','hydrostaticRiskAllocation':'buyer_capped',
        'hydrostaticBuyerLiabilityLimit':'2500','seller1Name':'Seller One',
        'seller1Email':'seller1@example.test', **overrides})


class HydrostaticPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_appends_one_editable_form_and_binds_source_identity(self):
        offer=hydrostatic_offer()
        packet=adapter.fill_and_merge_20_19(offer)
        reader=PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages),13)
        self.assertIn('AUTHORIZING HYDROSTATIC TESTING',reader.pages[12].extract_text())
        self.assertIn(SOURCE_SHA256,offer['_signing_source_hashes'])
        self.assertEqual(offer['_signing_render_revisions']['TREC-48-1'],RENDER_REVISION)
        fields=reader.get_fields()
        self.assertEqual(fields['hof_trec48_1.Street Address and City']['/V'],'123 Example Lane, Frisco')
        self.assertEqual(fields['hof_trec48_1.exceed']['/V'],'2,500.00')
        self.assertTrue(any(ref.get_object().get('/Parent') for ref in reader.pages[-1]['/Annots']))
        for risk, name in RISK_FIELDS.items():
            self.assertEqual(fields['hof_trec48_1.' + name]['/V'], '/On' if risk == 'buyer_capped' else '/Off')
        for reference in reader.pages[-1]['/Annots']:
            widget = reference.get_object()
            if widget.get('/FT') == '/Sig':
                continue
            self.assertTrue(widget['/AP']['/N'])
            canonical = fields['hof_trec48_1.' + widget['/T']]
            self.assertEqual(widget.get('/V'), canonical.get('/V'))

    def test_contract_checkbox_is_inside_the_hydrostatic_box_only_when_included(self):
        for selected in ('yes', 'no'):
            packet = adapter.fill_and_merge_20_19(hydrostatic_offer(hydrostaticTesting=selected))
            with pdfplumber.open(BytesIO(packet)) as pdf:
                marks = [char for char in pdf.pages[8].chars if char['text'] == 'X'
                         and 61 <= char['x0'] <= 72 and 311 <= char['top'] <= 325]
                self.assertEqual(len(marks), 1 if selected == 'yes' else 0)
                if marks:
                    self.assertLessEqual(marks[0]['x1'], 72)
                    self.assertLessEqual(marks[0]['bottom'], 325)

    def test_temporary_lease_and_hydrostatic_share_sellers_without_shifting_lease_fields(self):
        offer = hydrostatic_offer(possession='sellerTemporaryLease', sellerTemporaryLease='yes',
             buyer2='Buyer Two', buyer2Email='buyer2@example.test', seller2Name='Seller Two', seller2Email='seller2@example.test',
             sellerTemporaryLeaseTerminationDate='2026-10-01', sellerTemporaryLeaseRentPerDay='125',
             sellerTemporaryLeaseDeposit='1000', sellerTemporaryLeaseHoldoverPerDay='300')
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 15)
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        hydro = [field for field in fields if field['api_id'].startswith('trec48_1_')]
        self.assertEqual({field['page'] for field in hydro}, {15})
        self.assertEqual({field['recipient_id'] for field in hydro}, {'1','2','3','4'})
        seller_lease = [field for field in fields if field['recipient_id'] in ('3','4') and field not in hydro]
        self.assertTrue(seller_lease)
        base_offer = {**offer, 'hydrostaticTesting':'no'}
        base_fields = adapter.build_signwell_fields_20_19(base_offer, adapter.fill_and_merge_20_19(base_offer))[0]
        self.assertEqual(seller_lease, [field for field in base_fields if field['recipient_id'] in ('3','4')])
        self.assertEqual({field['page'] for field in seller_lease}, {10,13,14})

    def test_four_party_matrix_uses_correct_absolute_page_and_ids(self):
        for buyers in (1,2):
            for sellers in (1,2):
                offer=hydrostatic_offer(**({'buyer2':'Buyer Two','buyer2Email':'buyer2@example.test'} if buyers==2 else {}),
                    **({'seller2Name':'Seller Two','seller2Email':'seller2@example.test'} if sellers==2 else {}))
                packet=adapter.fill_and_merge_20_19(offer)
                fields=adapter.build_signwell_fields_20_19(offer,packet)[0]
                hydro=[f for f in fields if f['api_id'].startswith('trec48_1_')]
                self.assertEqual(len(hydro),buyers+sellers)
                self.assertEqual({f['page'] for f in hydro},{13})
                self.assertEqual({f['recipient_id'] for f in hydro},{'1','3'} | ({'2'} if buyers==2 else set()) | ({'4'} if sellers==2 else set()))
                self.assertFalse(any(f['recipient_id'] in ('3','4') and f['page'] <=12 for f in fields))

    def test_hydrostatic_sits_after_leases_before_uploads_without_shifting_their_fields(self):
        offer=hydrostatic_offer(leases='yes',leaseResidential='yes',residentialLeaseStatus='assignment',
            residentialLeaseDelivery='received',_paragraph4_source_pdf_bytes={'TXR-1953':one_page_pdf_bytes()},
            uploadedDisclosureDocs=[{'name':'QA disclosure.pdf','base64':one_page_pdf_base64(),
               'signaturePlacements':[{'type':'buyer1_signature','page':1,'signwellX':40,'signwellY':50}]}])
        packet=adapter.fill_and_merge_20_19(offer)
        reader=PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages),15)
        self.assertIn('HYDROSTATIC',reader.pages[13].extract_text())
        fields=adapter.build_signwell_fields_20_19(offer,packet)[0]
        self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('txr1953')},{13})
        self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('trec48_1')},{14})
        self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('uploaded_')},{15})

    def test_missing_invalid_or_conflicting_signers_fail_before_render(self):
        for changes in ({'seller1Email':''}, {'seller1Email':'invalid'},
                        {'seller1Email':'buyer@example.com'},
                        {'buyer2':'Name without email'},
                        {'seller1Name':'','seller1Email':'','seller':'','seller2Name':'Two','seller2Email':'two@example.test'},
                        {'sellerTemporaryLease':'yes','possession':'sellerTemporaryLease',
                         'leases':'yes','leaseResidential':'yes',
                         'paragraph4Seller1Name':'Different Seller','paragraph4Seller1Email':'different@example.test'}):
            with self.subTest(changes=changes), self.assertRaises(adapter.UnsupportedOfferPathError):
                adapter.validate_supported_offer(hydrostatic_offer(**changes))

    def test_deselected_lease_signers_never_override_the_current_hydrostatic_sellers(self):
        offer = hydrostatic_offer(paragraph4Seller1Name='Stale Seller', paragraph4Seller1Email='old@example.test')
        self.assertEqual(adapter.hydrostatic_execution_parties(offer)[0]['email'], 'seller1@example.test')

    def test_unknown_risk_and_missing_cap_cannot_render(self):
        for changes in ({'hydrostaticRiskAllocation':''},{'hydrostaticBuyerLiabilityLimit':''}):
            with self.assertRaises(adapter.UnsupportedOfferPathError):
                adapter.fill_and_merge_20_19(hydrostatic_offer(**changes))

    def test_combined_signing_payload_has_one_file_and_simultaneous_seller_invitations(self):
        api=load_offer_api()
        api.SIGNWELL_ENABLED=True
        api.SIGNWELL_API_KEY='local-fixture'
        offer=hydrostatic_offer(buyer2='Buyer Two',buyer2Email='buyer2@example.test',
                               seller2Name='Seller Two',seller2Email='seller2@example.test')
        packet=adapter.fill_and_merge_20_19(offer)
        captured={}
        def delivery(record,payload,offer,**kwargs):
            captured.update(copy.deepcopy(payload))
            return {'document_id':'fixture','document':{'id':'fixture','status':'sent'},
                    'state':'sent','message':'sent','recovered':False}
        api.deliver_offer_document=delivery
        result=api.create_signwell_signature_request(offer,packet)
        self.assertTrue(result['ok'])
        self.assertFalse(captured['apply_signing_order'])
        self.assertEqual(len(captured['files']),1)
        self.assertEqual(base64.b64decode(captured['files'][0]['file_base64']),packet)
        self.assertEqual([r['id'] for r in captured['recipients']],['1','2','3','4'])
        self.assertIn('hydrostatic-testing authorization',captured['message'])
        self.assertNotIn('seller-side changes are handled separately',captured['message'])
        self.assertEqual(result['mode'],'bundle_v15_hydrostatic_multisigner')

    def test_source_is_explicitly_included_without_enabling_deployments(self):
        config=json.loads((Path(__file__).resolve().parents[1]/'vercel.json').read_text())
        self.assertIn('hydrostatic_testing_48-1.pdf',config['functions']['api/fill-pdf.py']['includeFiles'])
        self.assertIs(config['git']['deploymentEnabled'],False)


if __name__ == '__main__':
    unittest.main()

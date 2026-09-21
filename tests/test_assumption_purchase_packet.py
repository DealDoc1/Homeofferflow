"""Loan-assumption packet foundation; synthetic data and mocked providers only."""
from decimal import Decimal
import copy
import hashlib
from io import BytesIO
from itertools import product
import unittest
from unittest.mock import patch

import pdfplumber
from pypdf import PdfReader
from lib import production_adapter as adapter
from lib.loan_assumption import parse_terms, money, display_money
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_bytes, one_page_pdf_base64
from tests.test_txr_1919_renderer import blank_pdf
from tests.test_paragraph4_source_hydration import load_offer_api, FakeResponse


SOURCE = blank_pdf()


def assumption_offer(**changes):
    offer = minimal_offer(financing='assumption', price='500000.55', loanAmount='1', downPayment='1',
        seller1Name='QA Seller', seller1Email='seller@example.test',
        assumptionCreditDays='7', assumptionCreditDocuments=['credit_report','other'], assumptionCreditOther='QA document',
        assumptionFirstEnabled=True, assumptionFirstLender='QA First Lender', assumptionFirstBalance='240000.12',
        assumptionFirstPayment='1750.25', assumptionFirstFeeCap='500.25', assumptionFirstRateCap='6.125',
        assumptionSecondEnabled=True, assumptionSecondLender='QA Second Lender', assumptionSecondBalance='30000.23',
        assumptionSecondPayment='300.50', assumptionSecondFeeCap='100', assumptionSecondRateCap='8',
        assumptionVarianceAdjustment='cash', assumptionVarianceThreshold='2500.75',
        _paragraph4_source_pdf_bytes={'TXR-1919':SOURCE})
    offer.update(changes)
    return offer


class AssumptionPacketTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()
        guard = patch.object(adapter, 'ASSUMPTION_SOURCE_SHA256', hashlib.sha256(SOURCE).hexdigest())
        guard.start()
        self.addCleanup(guard.stop)

    def test_exact_balances_replace_stale_amounts_before_persistence(self):
        offer = assumption_offer(financing='loan assumption')
        adapter.validate_supported_offer(offer)
        self.assertEqual(offer['financing'], 'assumption')
        self.assertEqual(offer['loanAmount'], '270000.35')
        self.assertEqual(offer['downPayment'], '230000.20')
        self.assertEqual(Decimal(offer['loanAmount']) + Decimal(offer['downPayment']), Decimal(offer['price']))
        normalized = copy.deepcopy(offer)
        adapter.validate_supported_offer(offer)
        self.assertEqual(offer, normalized)

    def test_main_contract_cents_and_two_assumption_checkboxes(self):
        offer = assumption_offer()
        raw = adapter.fill_and_merge_20_19(offer)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            self.assertEqual(len(pdf.pages),14)
            page = pdf.pages[0]
            for expected, top, bottom in [('230,000.20',465,476), ('270,000.35',514,525), ('500,000.55',526,538)]:
                values = ''.join(c['text'] for c in page.chars if 457<=c['x0']<556 and top<=c['top']<bottom)
                self.assertEqual(values.strip(), expected)
            for number, bounds in [(0,(74.42,85.94,512.79,525.75)), (8,(61.10,72.74,193.54,206.50))]:
                left,right,top,bottom=bounds
                marks=[c for c in pdf.pages[number].chars if c['text']=='X' and left<=c['x0']<right and top<=c['top']<bottom]
                self.assertEqual(len(marks),1)
                self.assertLessEqual(marks[0]['x1'],right)
                self.assertLessEqual(marks[0]['bottom'],bottom)
            self.assertFalse(any(c['text']=='X' and 313<c['x0']<326 and 498<c['top']<512 for c in page.chars))
            self.assertFalse(any(c['text']=='X' and 61<c['x0']<74 and 119<c['top']<132 for c in pdf.pages[8].chars))
        self.assertIn('240,000.12', PdfReader(BytesIO(raw)).pages[12].extract_text())
        self.assertNotIn('THIRD PARTY FINANCING ADDENDUM', '\n'.join(p.extract_text() for p in PdfReader(BytesIO(raw)).pages))

    def test_party_matrix_keeps_buyers_and_sellers_on_the_correct_pages(self):
        for buyers,sellers in product((1,2),repeat=2):
            offer=assumption_offer(**({'buyer2':'QA Buyer Two','buyer2Email':'two@example.test'} if buyers==2 else {}),
                **({'seller2Name':'QA Seller Two','seller2Email':'seller2@example.test'} if sellers==2 else {}))
            raw=adapter.fill_and_merge_20_19(offer)
            fields=adapter.build_signwell_fields_20_19(offer,raw)[0]
            assumption=[f for f in fields if f['api_id'].startswith('txr1919')]
            self.assertEqual(len(assumption),2*(buyers+sellers))
            self.assertEqual({f['page'] for f in assumption if f['type']=='signature'},{14})
            self.assertEqual({f['page'] for f in assumption if f['type']=='initials'},{13})
            self.assertEqual({f['recipient_id'] for f in assumption},{'1','3'}|({'2'} if buyers==2 else set())|({'4'} if sellers==2 else set()))
            self.assertFalse(any(f['recipient_id'] in ('3','4') and f['page']<=12 for f in fields))
            self.assertEqual(offer['_signing_render_revisions']['TXR-1919'],adapter.ASSUMPTION_RENDER_REVISION)

    def test_all_prior_addenda_and_uploads_keep_correct_page_offsets(self):
        offer=assumption_offer(environmentalAssessment='yes',environmentalReviewTypes=['wetlands'],environmentalTerminationDays='15',
            mineralReservation='yes',mineralReservationChoice='all',mineralSurfaceRights='waived',
            hydrostaticTesting='yes',hydrostaticRiskAllocation='seller',leases='yes',leaseResidential='yes',
            residentialLeaseStatus='assignment',residentialLeaseDelivery='received',
            uploadedDisclosureDocs=[{'name':'QA.pdf','base64':one_page_pdf_base64(),
                'signaturePlacements':[{'type':'buyer1_signature','page':1,'signwellX':50,'signwellY':50}]}])
        blank=one_page_pdf_bytes()
        offer['_paragraph4_source_pdf_bytes'].update({'TXR-1905':blank,'TXR-1917':blank,'TXR-1953':blank})
        with patch.object(adapter,'MINERAL_SOURCE_SHA256',hashlib.sha256(blank).hexdigest()),patch.object(adapter,'ENVIRONMENTAL_SOURCE_SHA256',hashlib.sha256(blank).hexdigest()):
            raw=adapter.fill_and_merge_20_19(offer)
            fields=adapter.build_signwell_fields_20_19(offer,raw)[0]
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages),19)
        for prefix,pages in [('txr1953',{13}),('trec48_1',{14}),('txr1905',{15}),('txr1917',{16}),('txr1919',{17,18}),('uploaded_',{19})]:
            self.assertEqual({f['page'] for f in fields if f['api_id'].startswith(prefix)},pages)
        self.assertEqual(len(fields),len({f['api_id'] for f in fields}))

    def test_first_or_second_loan_only_ignores_hidden_answers(self):
        for enabled in ('First','Second'):
            disabled='Second' if enabled=='First' else 'First'
            offer=assumption_offer(**{'assumption'+disabled+'Enabled':False,'assumption'+disabled+'Balance':'bad',
                'assumption'+disabled+'RateCap':'bad','assumptionCreditDocuments':['credit_report'],'assumptionCreditOther':'stale'})
            data,total,_=parse_terms(offer)
            self.assertEqual(total,Decimal(offer['assumption'+enabled+'Balance']))
            self.assertEqual(data['loans'][disabled.lower()],{'enabled':False})
            self.assertEqual(data['credit_other'],'')
            adapter.fill_and_merge_20_19(offer)

    def test_invalid_terms_or_signers_fail_before_render(self):
        cases=[{'assumptionCreditDays':v} for v in ('','0','1e2','1000','1.5')]
        cases += [{'assumptionCreditDocuments':v} for v in ([],['invalid'],[{}],'credit_report')]
        cases += [{'assumptionFirstBalance':v} for v in ('','NaN','1e3','-1','1.001','2,50','0')]
        cases += [{'assumptionFirstRateCap':v} for v in ('','100.1','1e2','1.12345')]
        cases += [{'assumptionCreditOther':''},{'assumptionFirstEnabled':False,'assumptionSecondEnabled':False},
                  {'assumptionVarianceAdjustment':''},{'assumptionVarianceThreshold':''},{'price':'1'},
                  {'seller1Email':'bad'},{'buyer2':'Missing email'}]
        for changes in cases:
            with self.subTest(changes=changes),patch.object(adapter.verified,'fill_and_merge') as render:
                with self.assertRaises(adapter.UnsupportedOfferPathError):adapter.fill_and_merge_20_19(assumption_offer(**changes))
                render.assert_not_called()

    def test_source_hash_must_match_before_core_rendering(self):
        for source in (None,b'wrong',SOURCE+b'changed'):
            offer=assumption_offer(_paragraph4_source_pdf_bytes={'TXR-1919':source})
            with patch.object(adapter.verified,'fill_and_merge') as render:
                with self.assertRaises(adapter.UnsupportedOfferPathError):adapter.fill_and_merge_20_19(offer)
                render.assert_not_called()

    def test_cash_and_conventional_do_not_inherit_assumption_answers(self):
        for financing,count in [('cash',12),('conventional',14)]:
            offer=assumption_offer(financing=financing,loanAssumption='no',loanAmount='400000',_paragraph4_source_pdf_bytes={})
            raw=adapter.fill_and_merge_20_19(offer)
            self.assertEqual(len(PdfReader(BytesIO(raw)).pages),count)
            self.assertNotIn('TXR-1919',offer['_signing_render_revisions'])
            self.assertFalse(any(f['api_id'].startswith('txr1919') for f in adapter.build_signwell_fields_20_19(offer,raw)[0]))
        with self.assertRaises(adapter.UnsupportedOfferPathError):adapter.validate_supported_offer(assumption_offer(financing='cash',loanAssumption='yes'))

    def test_private_source_hydration_and_simultaneous_one_file_request(self):
        api=load_offer_api();api.SUPABASE_URL='https://example.supabase.co';api.SUPABASE_SERVICE_ROLE_KEY='fixture'
        offer=assumption_offer();offer.pop('_paragraph4_source_pdf_bytes')
        with patch.object(api.httpx,'get',side_effect=[FakeResponse(200,payload=[{'source_revision':'11-07-2022','storage_bucket':'private','storage_path':'TXR1919.pdf'}]),FakeResponse(200,content=SOURCE)]) as get:
            api.hydrate_paragraph4_sources(offer)
        self.assertEqual(get.call_args_list[0].kwargs['params']['form_code'],'eq.TXR-1919')
        self.assertNotIn('brokerage_id',get.call_args_list[0].kwargs['params'])
        raw=adapter.fill_and_merge_20_19(offer)
        api.SIGNWELL_ENABLED=True;api.SIGNWELL_API_KEY='fixture'
        with patch.object(api,'deliver_offer_document',return_value={'document_id':'fixture','document':{'status':'sent'},'state':'sent','message':'sent','recovered':False}) as deliver:
            self.assertTrue(api.create_signwell_signature_request(offer,raw)['ok'])
        payload=deliver.call_args.args[1]
        self.assertFalse(payload['apply_signing_order']);self.assertEqual(len(payload['files']),1)
        self.assertEqual([r['id'] for r in payload['recipients']],['1','3'])
        self.assertIn('does not obtain lender consent',payload['message'])

    def test_overflow_continuation_is_counted_and_assigned_to_all_signers(self):
        offer=assumption_offer(assumptionFirstLender='LongLender'*45,
            seller2Name='QA Second Seller',seller2Email='seller2@example.test')
        raw=adapter.fill_and_merge_20_19(offer)
        fields=[f for f in adapter.build_signwell_fields_20_19(offer,raw)[0] if f['api_id'].startswith('txr1919')]
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages),15)
        self.assertEqual({f['recipient_id'] for f in fields if f['page']==15},{'1','3','4'})
        self.assertIn(offer['assumptionFirstLender'],PdfReader(BytesIO(raw)).pages[-1].extract_text().replace('\n',''))

    def test_decimal_math_accepts_zero_caps_and_preserves_cents(self):
        offer=assumption_offer(assumptionFirstFeeCap='0',assumptionFirstRateCap='0',assumptionVarianceThreshold='0')
        terms,_,_=parse_terms(offer)
        self.assertEqual(terms['loan_terms']['first_fee_cap'],'0')
        self.assertEqual(terms['loan_terms']['first_rate_cap'],'0')
        self.assertEqual(display_money(money('1,234.50','amount')),'1,234.50')


if __name__=='__main__':unittest.main()

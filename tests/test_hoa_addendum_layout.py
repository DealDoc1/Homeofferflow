"""HOA source bounds, material choices, continuations and packet delivery."""
from io import BytesIO
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import pdfplumber
from pypdf import PdfReader
from lib import hoa_addendum_layout as layout, production_adapter as adapter
from lib.pdf_text import text_width
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64
from tests.test_seller_temporary_lease_production_signwell import load_offer_api


def sample(**overrides):
    return minimal_offer(**{'hoa':'yes', 'hoaName':'José 李 Community Association',
        'hoaPhone':'972-555-0100', 'hoaSubdivisionInfo':'seller', 'hoaDays':'7',
        'hoaReserves':'12345.67', 'hoaTitleCost':'buyer',
        'buyer2':'Second Buyer', 'buyer2Email':'second@example.com', **overrides})


class HoaLayoutTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()

    def test_all_delivery_and_resale_choices_mark_only_the_selected_source_cells(self):
        for delivery, updated in [('seller',''),('buyer',''),('received','yes'),('received','no'),('notRequired','')]:
            offer = sample(hoaSubdivisionInfo=delivery, hoaUpdatedResaleCertificate=updated)
            original = copy.deepcopy(offer)
            answers = layout.answer_layout(offer)
            expected = [delivery, 'cost_buyer'] + (['updated_' + updated] if delivery == 'received' else [])
            self.assertEqual(answers.checks, expected)
            self.assertEqual(offer, original)
            raw = adapter.fill_and_merge_20_19(offer)
            with pdfplumber.open(BytesIO(raw)) as pdf:
                marks = [c for c in pdf.pages[12].chars if c['text'] == 'X' and c['size'] == 6]
                self.assertEqual(len(marks), len(expected))
                for char, key in zip(marks, expected):
                    x, y = layout.CHECK_CENTERS[key]
                    self.assertLess(abs((char['x0'] + char['x1'])/2 - x), 1)
                    self.assertLess(abs((char['top'] + char['bottom'])/2 - (792-y)), 2)
            self.assertEqual(offer['_signing_render_revisions']['TREC-36-11'], layout.RENDER_REVISION)

    def test_text_is_readable_and_within_measured_blanks(self):
        answers = layout.answer_layout(sample())
        self.assertFalse(answers.overflow)
        for x,y,text,size in answers.pages[1]:
            blank = next(v for v in layout.TEXT_BLANKS.values() if v[:2] == (x,y))
            self.assertGreaterEqual(size, 7)
            self.assertLessEqual(text_width(text, 'Helvetica', size), blank[2])
        self.assertIn('12,345.67', [e[2] for e in answers.pages[1]])

    def test_received_requires_an_explicit_resale_choice_but_other_paths_ignore_stale_answers(self):
        for value in ('', None, 'maybe'):
            with self.assertRaisesRegex(ValueError, 'updated HOA resale certificate'):
                adapter.fill_and_merge_20_19(sample(hoaSubdivisionInfo='received', hoaUpdatedResaleCertificate=value))
        answers = layout.answer_layout(sample(hoaSubdivisionInfo='notRequired', hoaUpdatedResaleCertificate='yes', hoaDays='999'))
        self.assertFalse(any(key.startswith('updated_') for key in answers.checks))
        self.assertNotIn('999', [e[2] for e in answers.pages[1]])
        layout.validate_hoa_answers(sample(hoa='no', hoaSubdivisionInfo='received'))

    def test_signatures_are_above_buyer_rules_without_unprinted_dates(self):
        source = PdfReader(adapter.verified.HOA_PDF)
        self.assertIsNone(source.get_fields())
        self.assertFalse(source.pages[0].get('/Annots'))
        for buyers in (1,2):
            offer = sample(buyer2Email='second@example.com' if buyers == 2 else '')
            raw = adapter.fill_and_merge_20_19(offer)
            fields = [f for f in adapter.build_signwell_fields_20_19(offer,raw)[0] if 'hoa' in f['api_id']]
            self.assertEqual(len(fields),buyers)
            for index, field in enumerate(fields):
                self.assertEqual(field['type'],'signature')
                self.assertEqual(field['recipient_id'],str(index+1))
                self.assertEqual(field['page'],13)
                self.assertEqual(tuple(field[k] for k in ('x','y','width','height')),layout.BUYER_SIGNATURE_BOXES[index])
                self.assertLess((field['y']+field['height'])*.75, (644.6384,699.59825)[index])
                self.assertGreaterEqual(field['x']*.75,43.07989)
                self.assertLessEqual((field['x']+field['width'])*.75,281.87929)

    def test_long_answers_are_lossless_and_following_pages_stay_aligned(self):
        for buyers in (1,2):
            offer=sample(address='A'*400, hoaName='José 李 <b>HOA</b> & '+'B'*900,
                buyer2Email='second@example.com' if buyers==2 else '',
                saleContingency='yes',salePropertyAddress='1 Sale St',saleContingencyDate='2026-10-01',
                saleWaiverDays='3',saleAdditionalEarnest='1000',
                uploadedDisclosureDocs=[{'name':'Attachment.pdf','base64':one_page_pdf_base64()}])
            answers=layout.answer_layout(offer)
            count=len(PdfReader(BytesIO(answers.continuation())).pages)
            raw=adapter.fill_and_merge_20_19(offer)
            reader=PdfReader(BytesIO(raw))
            continuation=''.join(p.extract_text() for p in reader.pages[13:13+count])
            self.assertIn('A'*400,''.join(continuation.split()))
            self.assertIn('B'*900,''.join(continuation.split()))
            self.assertIn('<b>HOA</b>',continuation)
            fields=adapter.build_signwell_fields_20_19(offer,raw)[0]
            self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
            sale=next(f for f in fields if f['api_id']=='buyer1_sale_other_property_addendum_signature')
            self.assertEqual(sale['page'],14+count)
            for page in range(14,14+count):
                initials=[f for f in fields if f['page']==page and f['api_id'].startswith('hoa_continuation_')]
                self.assertEqual({f['recipient_id'] for f in initials},{str(i+1) for i in range(buyers)})
            self.assertFalse(any(f['page']==len(reader.pages) for f in fields))

    def test_missing_selected_source_is_not_silently_omitted(self):
        with patch.object(adapter.verified,'HOA_PDF','/nonexistent/hoa.pdf'):
            with self.assertRaisesRegex(ValueError,'HOA addendum source'):
                adapter.fill_and_merge_20_19(sample())

    def test_offline_real_packet_requests_preserve_parallel_buyers(self):
        api=load_offer_api()
        for buyers in (1,2):
            for long in (False,True):
                offer=sample(userType='agent',address='A'*400 if long else '100 Example Street',
                    buyer2Email='second@example.com' if buyers==2 else '')
                raw=adapter.fill_and_merge_20_19(offer)
                captured={}
                def deliver(record,payload,answers,**options):
                    captured.update(payload)
                    return {'document_id':'offline-hoa','document':{'id':'offline-hoa','status':'sent'},
                            'state':'sent','message':'Signature request sent.','recovered':False}
                with patch.object(api,'SIGNWELL_ENABLED',True),patch.object(api,'SIGNWELL_API_KEY','offline-only'), \
                     patch.object(api,'deliver_offer_document',side_effect=deliver) as delivery:
                    self.assertTrue(api.create_signwell_signature_request(offer,raw)['ok'])
                delivery.assert_called_once()
                self.assertFalse(captured['apply_signing_order'])
                self.assertEqual(captured['fields'],adapter.build_signwell_fields_20_19(offer,raw))
                self.assertEqual({r['id'] for r in captured['recipients']},{str(i+1) for i in range(buyers)})


if __name__=='__main__':
    unittest.main()

"""TREC 10-6 answer bounds and assembled-packet signature regressions."""
from io import BytesIO
import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
import pdfplumber
from pypdf import PdfReader, PdfWriter
from lib import sale_contingency_layout as layout, production_adapter as adapter
from lib.pdf_text import text_width
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64
from tests.test_seller_temporary_lease_production_signwell import load_offer_api


def sample(**overrides):
    return minimal_offer(**{'saleContingency':'yes','salePropertyAddr':'100 José 李 Street, Frisco TX 75033',
        'saleContingencyDate':'2026-09-30','saleWaiverDays':'3','saleAdditionalEarnest':'12345.67',
        'buyer2':'Second Buyer','buyer2Email':'second@example.com',**overrides})


class SaleContingencyLayoutTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()

    def test_source_structure_and_complete_answers_fit_measured_blanks(self):
        reader=PdfReader(adapter.verified.SALE_PDF)
        self.assertEqual(len(reader.pages),1)
        self.assertIsNone(reader.get_fields())
        self.assertFalse(reader.pages[0].get('/Annots'))
        offer=sample(); original=copy.deepcopy(offer);answers=layout.answer_layout(offer)
        self.assertEqual(offer,original);self.assertFalse(answers.overflow)
        for x,y,text,size in answers.pages[1]:
            blank=next(b for b in layout.TEXT_BLANKS.values() if b[:2]==(x,y))
            self.assertGreaterEqual(size,7)
            self.assertLessEqual(text_width(text,'Helvetica',size),blank[2])
        values=[entry[2] for entry in answers.pages[1]]
        for expected in ('September 30','26','3','12,345.67',offer['salePropertyAddr']):
            self.assertIn(expected,values)
        raw=adapter.fill_and_merge_20_19(offer)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            page=pdf.pages[12]
            self.assertIn('12,345.67',page.extract_text())
            for x,y,text,size in answers.pages[1]:
                # The actual PDF overlay must use the same start/baseline as
                # the measured model, including Unicode font substitution.
                self.assertTrue(any(abs(c['x0']-x)<.1 and c['text']==text[0] for c in page.chars))
        self.assertEqual(offer['_signing_render_revisions']['TREC-10-6'],layout.RENDER_REVISION)
        self.assertIn(hashlib.sha256(Path(adapter.verified.SALE_PDF).read_bytes()).hexdigest(),offer['_signing_source_hashes'])

    def test_all_legacy_address_aliases_and_numeric_zero_are_preserved(self):
        for alias in ('salePropertyAddr','salePropertyAddress','buyerSalePropertyAddress'):
            offer=sample(salePropertyAddr='',saleAdditionalEarnest=0)
            offer[alias]='X'
            raw=adapter.fill_and_merge_20_19(offer)
            with pdfplumber.open(BytesIO(raw)) as pdf:
                page=pdf.pages[12]
                self.assertTrue(any(c['text']=='0' and abs(c['x0']-506)<.1 for c in page.chars))
                self.assertTrue(any(c['text']=='X' and abs(c['x0']-67)<.1 and c['size']==9 for c in page.chars))
        values=[e[2] for e in layout.answer_layout(sample(saleAdditionalEarnest='')).pages[1]]
        self.assertNotIn('0',values)

    def test_invalid_dates_cannot_be_stamped_as_malformed_deadlines(self):
        for value in ('2026-02-30','not a date','1999-12-31','2100-01-01'):
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'sale contingency'):
                adapter.fill_and_merge_20_19(sample(saleContingencyDate=value))
        self.assertEqual(layout.date_parts('2028-02-29'),('February 29','28'))
        self.assertEqual(layout.date_parts(''),('',''))

    def test_signatures_fit_buyer_rules_without_extra_dates_or_sellers(self):
        for buyers in (1,2):
            offer=sample(buyer2Email='second@example.com' if buyers==2 else '')
            raw=adapter.fill_and_merge_20_19(offer)
            fields=[f for f in adapter.build_signwell_fields_20_19(offer,raw)[0] if 'sale_other_property' in f['api_id']]
            self.assertEqual(len(fields),buyers)
            for i,f in enumerate(fields):
                self.assertEqual(f['type'],'signature');self.assertEqual(f['recipient_id'],str(i+1))
                self.assertEqual(f['page'],13)
                self.assertEqual(tuple(f[k] for k in ('x','y','width','height')),layout.BUYER_SIGNATURE_BOXES[i])
                self.assertLess((f['y']+f['height'])*.75,(540.6,601.32)[i])
                self.assertGreaterEqual(f['x']*.75,55.44)
                self.assertLessEqual((f['x']+f['width'])*.75,298.44)

    def test_multi_page_continuation_keeps_all_text_initials_and_later_offsets(self):
        for buyers in (1,2):
            offer=sample(salePropertyAddr='José 李 <b>Old</b> & '+'Z'*5000,
                buyer2Email='second@example.com' if buyers==2 else '',
                backupOffer='yes',backupAdditionalEarnest='500',backupAdditionalOptionFee='100',
                backupAdditionalDays='3',firstContractDate='2026-06-01',backupTerminationDate='2026-10-01',
                uploadedDisclosureDocs=[{'name':'Attachment.pdf','base64':one_page_pdf_base64()}])
            count=len(PdfReader(BytesIO(layout.answer_layout(offer).continuation())).pages)
            self.assertGreater(count,1)
            raw=adapter.fill_and_merge_20_19(offer);reader=PdfReader(BytesIO(raw))
            text=''.join(p.extract_text() for p in reader.pages[13:13+count])
            self.assertEqual(text.count('Z'),5000);self.assertIn('<b>Old</b>',text)
            fields=adapter.build_signwell_fields_20_19(offer,raw)[0]
            self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
            for page in range(14,14+count):
                initials=[f for f in fields if f['page']==page and f['api_id'].startswith('sale_continuation_')]
                self.assertEqual({f['recipient_id'] for f in initials},{str(i+1) for i in range(buyers)})
                self.assertTrue(all(f['type']=='initials' and f['required'] for f in initials))
            backup=next(f for f in fields if f['api_id']=='buyer1_backup_addendum_signature')
            self.assertEqual(backup['page'],15+count)
            self.assertFalse(any(f['page']==len(reader.pages) for f in fields))

    def test_missing_source_and_continuation_cannot_silently_change_the_packet(self):
        with patch.object(adapter.verified,'SALE_PDF','/nonexistent/sale.pdf'):
            with self.assertRaisesRegex(ValueError,'sale-of-other-property addendum source'):
                adapter.fill_and_merge_20_19(sample())
        writer=PdfWriter()
        for _ in range(13):writer.add_blank_page(612,792)
        out=BytesIO();writer.write(out)
        with self.assertRaisesRegex(ValueError,'sale contingency continuation'):
            adapter.build_signwell_fields_20_19(sample(salePropertyAddr='Z'*5000),out.getvalue())

    def test_deselection_removes_addendum_continuation_and_signature_fields(self):
        offer=sample(saleContingency='no',salePropertyAddr='Z'*5000,saleContingencyDate='invalid')
        raw=adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages),12)
        self.assertFalse(any('sale_' in f['api_id'] for f in adapter.build_signwell_fields_20_19(offer,raw)[0]))
        self.assertNotIn('TREC-10-6',offer['_signing_render_revisions'])

    def test_real_request_payloads_preserve_parallel_buyers_with_short_or_long_answers(self):
        api=load_offer_api()
        for buyers in (1,2):
            for long in (False,True):
                offer=sample(userType='agent',salePropertyAddr='Z'*5000 if long else '100 Example Street',
                    buyer2Email='second@example.com' if buyers==2 else '')
                raw=adapter.fill_and_merge_20_19(offer);captured={}
                def deliver(record,payload,answers,**options):
                    captured.update(payload)
                    return {'document_id':'offline-sale','document':{'id':'offline-sale','status':'sent'},
                            'state':'sent','message':'Signature request sent.','recovered':False}
                with patch.object(api,'SIGNWELL_ENABLED',True),patch.object(api,'SIGNWELL_API_KEY','offline-only'), \
                     patch.object(api,'deliver_offer_document',side_effect=deliver) as delivery:
                    self.assertTrue(api.create_signwell_signature_request(offer,raw)['ok'])
                delivery.assert_called_once();self.assertFalse(captured['apply_signing_order'])
                self.assertEqual(captured['fields'],adapter.build_signwell_fields_20_19(offer,raw))
                self.assertEqual({r['id'] for r in captured['recipients']},{str(i+1) for i in range(buyers)})
                self.assertEqual(len(captured['files']),1)


if __name__=='__main__':unittest.main()

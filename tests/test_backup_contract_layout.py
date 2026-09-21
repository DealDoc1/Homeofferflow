"""Backup-contract source bounds and complete production request regressions."""
import copy
import hashlib
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch
import pdfplumber
from pypdf import PdfReader, PdfWriter
from lib import backup_contract_layout as layout, production_adapter as adapter
from lib.pdf_text import text_width
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64
from tests.test_seller_temporary_lease_production_signwell import load_offer_api


def sample(**overrides):
    return minimal_offer(**{'backupOffer':'yes', 'address':'100 José 李 Street',
        'bkupFirstContractDate':'2026-09-01', 'bkupTerminateDate':'2026-09-30',
        'closingDate':'2026-10-15', 'bkupAdditionalEarnest':'12345.67',
        'bkupAdditionalOption':'123.45', 'bkupAdditionalDays':'3',
        'buyer2':'Second Buyer', 'buyer2Email':'second@example.com', **overrides})


class BackupContractLayoutTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()

    def test_source_and_answers_fit_measured_blanks(self):
        reader=PdfReader(adapter.verified.BACKUP_PDF)
        self.assertEqual(len(reader.pages),2); self.assertIsNone(reader.get_fields())
        self.assertTrue(all(not p.get('/Annots') for p in reader.pages))
        offer=sample(); original=copy.deepcopy(offer); answers=layout.answer_layout(offer)
        self.assertEqual(offer,original); self.assertFalse(answers.overflow)
        for entries in answers.pages.values():
            for x,y,text,size in entries:
                blank=next(b for b in layout.TEXT_BLANKS.values() if b[:2]==(x,y))
                self.assertGreaterEqual(size,7)
                self.assertLessEqual(text_width(text,'Helvetica',size),blank[2])
        raw=adapter.fill_and_merge_20_19(offer)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            for index,entries in answers.pages.items():
                page=pdf.pages[11+index]
                for x,y,text,size in entries:
                    self.assertTrue(any(abs(c['x0']-x)<.1 and c['text']==text[0] for c in page.chars))
        # The source's text underscores interleave with answers in a spatial
        # extraction. Content-order extraction retains the actual answer runs.
        text=PdfReader(BytesIO(raw)).pages[12].extract_text()
        for value in ('12,345.67','123.45','September 1','September 30'):
            self.assertIn(value,text)
        self.assertEqual(offer['_signing_render_revisions']['TREC-11-9'],layout.RENDER_REVISION)
        self.assertIn(hashlib.sha256(Path(adapter.verified.BACKUP_PDF).read_bytes()).hexdigest(),offer['_signing_source_hashes'])

    def test_aliases_zero_values_and_literal_text_are_preserved(self):
        defaults={'first':'2026-09-01','termination':'2026-09-30','earnest':0,'option':0,'days':'X'}
        expected={'first':'September 1','termination':'September 30','earnest':'0','option':'0','days':'X'}
        for key,aliases in layout.ALIASES.items():
            for alias in aliases:
                offer=sample(**{a:'' for a in aliases}); offer[alias]=defaults[key]
                values=[e[2] for e in layout.answer_layout(offer).pages[1]]
                self.assertIn(expected[key],values,(key,alias))
        offer=sample(bkupAdditionalEarnest=0,bkupAdditionalOption=0,bkupAdditionalDays='X')
        raw=adapter.fill_and_merge_20_19(offer)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            chars=pdf.pages[12].chars
            for x in (344,88):
                self.assertTrue(any(c['text']=='0' and abs(c['x0']-x)<.1 for c in chars))
            self.assertTrue(any(c['text']=='X' and abs(c['x0']-278)<.1 and abs(c['size']-9)<.01 for c in chars))
        values=[e[2] for e in layout.answer_layout(sample(bkupAdditionalEarnest='',bkupAdditionalOption='')).pages[1]]
        self.assertNotIn('0',values)

    def test_bad_dates_rejected_without_replacing_blank_drafts(self):
        for key in ('bkupFirstContractDate','bkupTerminateDate'):
            for value in ('invalid','2026-02-30','1999-12-31','2100-01-01'):
                with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'backup contract'):
                    adapter.fill_and_merge_20_19(sample(**{key:value}))
        self.assertEqual(layout.date_parts(''),('',''))
        self.assertEqual(layout.date_parts('2028-02-29'),('February 29','28'))

    def test_initials_and_signatures_fit_the_actual_buyer_rules(self):
        for buyers in (1,2):
            offer=sample(buyer2Email='second@example.com' if buyers==2 else '')
            raw=adapter.fill_and_merge_20_19(offer)
            fields=[f for f in adapter.build_signwell_fields_20_19(offer,raw)[0] if 'backup' in f['api_id']]
            self.assertEqual(len(fields),buyers*2)
            for f in fields:
                index=int(f['recipient_id'])-1
                boxes=layout.BUYER_INITIAL_BOXES if f['type']=='initials' else layout.BUYER_SIGNATURE_BOXES
                self.assertEqual(tuple(f[k] for k in ('x','y','width','height')),boxes[index])
                if f['type']=='initials':
                    self.assertEqual(f['page'],13)
                    self.assertGreaterEqual(f['x']*.75,205.08)
                    self.assertLessEqual((f['x']+f['width'])*.75,271.2)
                    self.assertLess((f['y']+f['height'])*.75,776.88)
                    self.assertGreater(f['y']*.75,755.04)
                else:
                    self.assertEqual(f['type'],'signature'); self.assertEqual(f['page'],14)
                    self.assertGreaterEqual(f['x']*.75,65.88)
                    self.assertLessEqual((f['x']+f['width'])*.75,303.36)
                    self.assertLess((f['y']+f['height'])*.75,(176.04,250.92)[index])

    def test_continuation_keeps_long_answers_and_moves_following_repair_pages(self):
        for buyers in (1,2):
            offer=sample(address='José 李 <b>Property</b> & '+'Z'*400,
                buyer2Email='second@example.com' if buyers==2 else '',asIs='repairs',repairsText='R'*5000,
                uploadedDisclosureDocs=[{'name':'Attachment.pdf','base64':one_page_pdf_base64()}])
            continuation=layout.answer_layout(offer).continuation()
            count=len(PdfReader(BytesIO(continuation)).pages); self.assertGreater(count,0)
            raw=adapter.fill_and_merge_20_19(offer); reader=PdfReader(BytesIO(raw))
            text=''.join(p.extract_text() for p in reader.pages[14:14+count])
            self.assertIn('<b>Property</b>',text)
            self.assertGreaterEqual(text.count('Z'),400)
            self.assertEqual(layout.answer_layout(offer).overflow['Property'],
                f"{offer['address']}, {offer['city']}, TX {offer['zip']}")
            fields=adapter.build_signwell_fields_20_19(offer,raw)[0]
            self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
            for page in range(15,15+count):
                initials=[f for f in fields if f['page']==page and f['api_id'].startswith('backup_continuation_')]
                self.assertEqual({f['recipient_id'] for f in initials},{str(i+1) for i in range(buyers)})
                self.assertTrue(all(f['type']=='initials' and f['required'] for f in initials))
            repair=[f for f in fields if f['api_id'].startswith('repair_continuation_')]
            self.assertTrue(repair)
            self.assertEqual(min(f['page'] for f in repair),15+count)
            self.assertFalse(any(f['page']==len(reader.pages) for f in fields))

    def test_missing_selected_source_or_pages_fail_explicitly(self):
        with patch.object(adapter.verified,'BACKUP_PDF','/nonexistent/backup.pdf'):
            with self.assertRaisesRegex(ValueError,'backup contract addendum source'):
                adapter.fill_and_merge_20_19(sample())
        for pages,offer,message in ((13,sample(),'backup contract addendum'),
                (14,sample(address='Z'*400),'backup contract continuation')):
            writer=PdfWriter()
            for _ in range(pages):writer.add_blank_page(612,792)
            out=BytesIO();writer.write(out)
            with self.assertRaisesRegex(ValueError,message):
                adapter.build_signwell_fields_20_19(offer,out.getvalue())

    def test_deselected_backup_ignores_stale_answers_and_has_no_fields(self):
        offer=sample(backupOffer='no',bkupFirstContractDate='invalid')
        raw=adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages),12)
        self.assertFalse(any('backup' in f['api_id'] for f in adapter.build_signwell_fields_20_19(offer,raw)[0]))
        self.assertNotIn('TREC-11-9',offer['_signing_render_revisions'])

    def test_offline_production_requests_keep_parallel_invitations(self):
        api=load_offer_api()
        for buyers in (1,2):
            for long in (False,True):
                offer=sample(userType='agent',address='Z'*400 if long else '100 Example Street',
                    buyer2Email='second@example.com' if buyers==2 else '')
                raw=adapter.fill_and_merge_20_19(offer); captured={}
                def deliver(record,payload,answers,**options):
                    captured.update(payload)
                    return {'document_id':'offline-backup','document':{'id':'offline-backup','status':'sent'},
                            'state':'sent','message':'Signature request sent.','recovered':False}
                with patch.object(api,'SIGNWELL_ENABLED',True),patch.object(api,'SIGNWELL_API_KEY','offline-only'), \
                     patch.object(api,'deliver_offer_document',side_effect=deliver) as delivery:
                    self.assertTrue(api.create_signwell_signature_request(offer,raw)['ok'])
                delivery.assert_called_once(); self.assertFalse(captured['apply_signing_order'])
                self.assertEqual(captured['fields'],adapter.build_signwell_fields_20_19(offer,raw))
                self.assertEqual({r['id'] for r in captured['recipients']},{str(i+1) for i in range(buyers)})
                self.assertEqual(len(captured['files']),1)


if __name__=='__main__':unittest.main()

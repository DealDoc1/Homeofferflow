"""TREC 40-11 loan-path, source geometry and assembled-packet regressions."""
import copy
import hashlib
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch
import pdfplumber
from pypdf import PdfReader, PdfWriter
from lib import financing_addendum_layout as layout, production_adapter as adapter
from lib.pdf_text import text_width
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64
from tests.test_seller_temporary_lease_production_signwell import load_offer_api


def sample(**overrides):
    return minimal_offer(**{'financing':'conventional','address':'100 José 李 Street',
        'loanAmount':'412345.67','loanYears':'30','interestRateCap':'7.125',
        'interestFirstYears':'5','originationCap':'1.25','buyerApprovalDays':'21',
        'buyer2':'Second Buyer','buyer2Email':'second@example.com',**overrides})


class FinancingAddendumLayoutTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()

    def test_source_and_each_loan_path_keep_readable_bounded_answers(self):
        source=PdfReader(adapter.verified.FINANCING_PDF)
        self.assertEqual(len(source.pages),2); self.assertIsNone(source.get_fields())
        self.assertTrue(all(not p.get('/Annots') for p in source.pages))
        for kind in layout.LOAN_BLANKS:
            offer=sample(financing=kind); original=copy.deepcopy(offer)
            answers=layout.answer_layout(offer,kind)
            self.assertEqual(offer,original); self.assertFalse(answers.overflow)
            blanks=list(layout.TEXT_BLANKS.values())+list(layout.LOAN_BLANKS[kind])
            for entries in answers.pages.values():
                for x,y,text,size in entries:
                    blank=next(b for b in blanks if b[:2]==(x,y))
                    self.assertGreaterEqual(size,7)
                    self.assertLessEqual(text_width(text,'Helvetica',size),blank[2])
            raw=adapter.fill_and_merge_20_19(offer); reader=PdfReader(BytesIO(raw))
            text=reader.pages[12].extract_text()
            for value in ('412,345.67','7.125','1.25'):
                self.assertIn(value,text)
            self.assertEqual('203(b)' in text,kind=='fha')
            self.assertEqual('500,000' in reader.pages[13].extract_text(),kind in ('fha','va'))
            self.assertEqual(offer['_signing_render_revisions']['TREC-40-11'],layout.RENDER_REVISION)
            self.assertIn(hashlib.sha256(Path(adapter.verified.FINANCING_PDF).read_bytes()).hexdigest(),offer['_signing_source_hashes'])

    def test_only_active_source_boxes_are_marked_for_each_loan_and_approval_choice(self):
        for kind in layout.LOAN_BLANKS:
            for approval in ('yes','no'):
                offer=sample(financing=kind,buyerApproval=approval)
                answers=layout.answer_layout(offer,kind)
                expected={kind,'approval_'+approval}
                if kind=='conventional':expected.add('first_mortgage')
                self.assertEqual(set(answers.checks),expected)
                raw=adapter.fill_and_merge_20_19(offer)
                with pdfplumber.open(BytesIO(raw)) as pdf:
                    for page in (1,2):
                        marks=[c for c in pdf.pages[11+page].chars if c['text']=='X' and abs(c['size']-6)<.01]
                        wanted=[layout.CHECK_CENTERS[key] for key in expected if layout.CHECK_CENTERS[key][0]==page]
                        self.assertEqual(len(marks),len(wanted))
                        for _,x,y in wanted:
                            self.assertTrue(any(abs(c['x0']-(x-2))<.1 for c in marks))
                days=[e for e in answers.pages[2] if e[:2]==layout.TEXT_BLANKS['approval_days'][:2]]
                self.assertEqual(bool(days),approval=='yes')

    def test_zero_values_aliases_and_existing_legacy_defaults(self):
        aliases={'loanYears':'loanTermYears','interestRateCap':'loanInterestCap',
                 'originationCap':'loanOriginationCap','buyerApprovalDays':'financingApprovalDays',
                 'fhaSection':'fhaProgram'}
        offer=sample(financing='fha',fhaSection='SPECIAL')
        expected=layout.answer_layout(offer,'fha').pages
        for key,alias in aliases.items():
            changed=copy.deepcopy(offer); changed[alias]=changed.pop(key)
            self.assertEqual(layout.answer_layout(changed,'fha').pages,expected)
        zero=sample(interestRateCap=0,originationCap=0,buyerApprovalDays=0,appraisedValue=0)
        answers=layout.answer_layout(zero,'fha')
        self.assertIn('0',[e[2] for e in answers.pages[1]])
        self.assertEqual([e[2] for e in answers.pages[2] if e[:2] in
            (layout.TEXT_BLANKS['approval_days'][:2],layout.TEXT_BLANKS['appraised_value'][:2])],['0','0'])
        defaults=layout.answer_layout(minimal_offer(financing='fha'),'fha')
        for value in ('30','7','1','203(b)'):
            self.assertIn(value,[e[2] for e in defaults.pages[1]])
        self.assertIn('21',[e[2] for e in defaults.pages[2]])
        raw=adapter.fill_and_merge_20_19(sample(financing='third party'))
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages),14)

    def test_buyer_initials_and_signatures_stay_above_their_own_rules(self):
        for buyers in (1,2):
            offer=sample(buyer2Email='second@example.com' if buyers==2 else '')
            raw=adapter.fill_and_merge_20_19(offer)
            fields=[f for f in adapter.build_signwell_fields_20_19(offer,raw)[0] if 'financing' in f['api_id']]
            self.assertEqual(len(fields),buyers*2)
            for f in fields:
                index=int(f['recipient_id'])-1
                if f['type']=='initials':
                    box=layout.BUYER_INITIAL_BOXES[index]; low,high=((205.08,228.24),(237.24,264.24))[index]
                    self.assertEqual(f['page'],13); rule=769.68
                    self.assertGreater(f['y']*.75,752)
                else:
                    self.assertEqual(f['type'],'signature')
                    box=layout.BUYER_SIGNATURE_BOXES[index]; low,high=55.68,298.56
                    self.assertEqual(f['page'],14); rule=(625.44,676.8)[index]
                self.assertEqual(tuple(f[k] for k in ('x','y','width','height')),box)
                self.assertGreaterEqual(f['x']*.75,low)
                self.assertLessEqual((f['x']+f['width'])*.75,high)
                self.assertLess((f['y']+f['height'])*.75,rule)

    def test_multi_page_answers_preserve_literal_text_and_shift_following_forms(self):
        for buyers in (1,2):
            offer=sample(financing='fha',fhaSection='José 李 <b>Section</b> & '+'Z'*5000,
                buyer2Email='second@example.com' if buyers==2 else '',backupOffer='yes',
                uploadedDisclosureDocs=[{'name':'Attachment.pdf','base64':one_page_pdf_base64()}])
            answers=layout.answer_layout(offer,'fha')
            count=len(PdfReader(BytesIO(answers.continuation())).pages); self.assertGreater(count,1)
            raw=adapter.fill_and_merge_20_19(offer); reader=PdfReader(BytesIO(raw))
            text=''.join(p.extract_text() for p in reader.pages[14:14+count])
            self.assertEqual(text.count('Z'),5000); self.assertIn('<b>Section</b>',text)
            fields=adapter.build_signwell_fields_20_19(offer,raw)[0]
            self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
            for page in range(15,15+count):
                initials=[f for f in fields if f['page']==page and f['api_id'].startswith('financing_continuation_')]
                self.assertEqual({f['recipient_id'] for f in initials},{str(i+1) for i in range(buyers)})
                self.assertTrue(all(f['type']=='initials' and f['required'] for f in initials))
            backup=next(f for f in fields if f['api_id']=='buyer1_backup_addendum_signature')
            self.assertEqual(backup['page'],16+count)
            self.assertFalse(any(f['page']==len(reader.pages) for f in fields))

    def test_missing_selected_source_and_required_pages_fail_explicitly(self):
        with patch.object(adapter.verified,'FINANCING_PDF','/nonexistent/financing.pdf'):
            with self.assertRaisesRegex(ValueError,'financing addendum source'):
                adapter.fill_and_merge_20_19(sample())
        for pages,offer,message in ((13,sample(),'financing addendum'),
                (14,sample(address='Z'*400),'financing continuation')):
            writer=PdfWriter()
            for _ in range(pages):writer.add_blank_page(612,792)
            out=BytesIO(); writer.write(out)
            with self.assertRaisesRegex(ValueError,message):
                adapter.build_signwell_fields_20_19(offer,out.getvalue())

    def test_cash_ignores_stale_loan_terms_and_other_products_are_not_fabricated(self):
        offer=sample(financing='cash',fhaSection='Z'*5000)
        raw=adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages),12)
        self.assertFalse(any('financing' in f['api_id'] for f in adapter.build_signwell_fields_20_19(offer,raw)[0]))
        self.assertNotIn('TREC-40-11',offer['_signing_render_revisions'])
        for kind in ('reverse','texas_veterans','other'):
            with self.assertRaisesRegex(ValueError,'supported loan type'):
                layout.answer_layout(sample(),kind)

    def test_real_offline_requests_cover_all_loan_types_and_parallel_buyers(self):
        api=load_offer_api()
        for kind in layout.LOAN_BLANKS:
            for buyers in (1,2):
                for long in (False,True):
                    offer=sample(userType='agent',financing=kind,address='Z'*400 if long else '100 Example Street',
                        buyer2Email='second@example.com' if buyers==2 else '')
                    raw=adapter.fill_and_merge_20_19(offer); captured={}
                    def deliver(record,payload,answers,**options):
                        captured.update(payload)
                        return {'document_id':'offline-financing','document':{'id':'offline-financing','status':'sent'},
                                'state':'sent','message':'Signature request sent.','recovered':False}
                    with patch.object(api,'SIGNWELL_ENABLED',True),patch.object(api,'SIGNWELL_API_KEY','offline-only'), \
                         patch.object(api,'deliver_offer_document',side_effect=deliver) as delivery:
                        self.assertTrue(api.create_signwell_signature_request(offer,raw)['ok'])
                    delivery.assert_called_once(); self.assertFalse(captured['apply_signing_order'])
                    self.assertEqual(captured['fields'],adapter.build_signwell_fields_20_19(offer,raw))
                    self.assertEqual({r['id'] for r in captured['recipients']},{str(i+1) for i in range(buyers)})
                    self.assertEqual(len(captured['files']),1)


if __name__=='__main__':unittest.main()

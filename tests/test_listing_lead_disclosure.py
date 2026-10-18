from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path
import unittest

from pypdf import PdfReader
import pdfplumber

from lib import listing_lead_disclosure as lead
from lib.txr_1101 import validate_answers
from lib.listing_packet import PreparedDocument, assemble_listing_packet
from tests.test_listing_packet import pdf, signing_fields
from tests.test_txr_1101 import sample_answers


ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'lead_based_paint_56-0.pdf').read_bytes()


class ListingLeadTests(unittest.TestCase):
    def prepare(self,**changes):
        return lead.prepare_listing_lead(SOURCE,validate_answers(sample_answers(addenda=['C'],**changes)))

    def test_exact_static_source_and_strict_nested_answer_contract(self):
        self.assertEqual(hashlib.sha256(SOURCE).hexdigest(),lead.SOURCE_SHA256)
        self.assertEqual(lead.validate_answers(),{'knowledge':'unanswered','records':'unanswered','knowledge_details':'','records_details':''})
        for bad in ([],{'seller_names':['untrusted']},{'knowledge':True},{'records':'has_records'}, {'records_details':'x'*4001}):
            with self.subTest(bad=repr(bad)[:60]),self.assertRaises(ValueError):lead.validate_answers(bad)
        original={'knowledge':'known','knowledge_details':'QA supplied fact','records':'none'}
        before=deepcopy(original);lead.validate_answers(original);self.assertEqual(original,before)
        with self.assertRaises(ValueError):lead.prepare_listing_lead(b'%PDF-wrong-source',sample_answers())

    def test_unanswered_seller_choices_have_exact_one_groups_and_conditional_explanations(self):
        result=self.prepare()
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),2)
        self.assertEqual(len(result.checkbox_groups),2);self.assertEqual(len(result.conditional_rules),2)
        checkboxes=[field for field in result.fields[0] if field['type']=='checkbox']
        self.assertEqual(len(checkboxes),4)
        self.assertTrue(all(field['recipient_id']=='1' and field['required'] is False and 'value' not in field for field in checkboxes))
        for group in result.checkbox_groups:
            self.assertEqual((group['validation'],group['required'],group['exact_value']),('exact',True,1))
        texts=[field for field in result.fields[0] if field['type']=='text']
        self.assertEqual(len(texts),2)
        self.assertTrue(all(field['page']==2 and field['required'] is False and field['fixed_width'] and field['height']<=74 for field in texts))
        self.assertTrue(all(rule['action_type']=='require' for rule in result.conditional_rules))

    def test_explicit_no_knowledge_and_no_records_need_no_answer_controls_or_extra_page(self):
        result=self.prepare(lead_disclosure={'knowledge':'none','records':'none'})
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),1)
        self.assertEqual(result.checkbox_groups,[]);self.assertEqual(result.conditional_rules,[])
        self.assertEqual({field['type'] for field in result.fields[0]},{'signature','date'})
        with pdfplumber.open(BytesIO(result.pdf)) as reader:
            marks=[c for c in reader.pages[0].chars if c['text']=='X' and 65<=c['x0']<=75 and 400<=c['y0']<=540]
        self.assertEqual(len(marks),2)
        self.assertTrue(any(499<=mark['y0']<=504 for mark in marks))
        self.assertTrue(any(444<=mark['y0']<=449 for mark in marks))

    def test_known_facts_are_rendered_only_in_the_corresponding_seller_blanks(self):
        result=self.prepare(lead_disclosure={'knowledge':'known','knowledge_details':'QA known painted trim',
                                            'records':'provided','records_details':'QA inspection report'})
        text=' '.join(PdfReader(BytesIO(result.pdf)).pages[0].extract_text().split())
        self.assertIn('QA known painted trim',text);self.assertIn('QA inspection report',text)
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),1)
        self.assertEqual(result.checkbox_groups,[])

    def test_inactive_old_explanations_are_not_printed_as_current_seller_facts(self):
        result=self.prepare(lead_disclosure={'knowledge':'none','knowledge_details':'Old QA claim',
                                             'records':'none','records_details':'Old QA report'})
        text=PdfReader(BytesIO(result.pdf)).pages[0].extract_text()
        self.assertNotIn('Old QA',text)

    def test_explicit_positive_without_details_collects_explanation_without_inventing_one(self):
        result=self.prepare(lead_disclosure={'knowledge':'known','records':'none'})
        texts=[f for f in result.fields[0] if f['type']=='text']
        self.assertEqual(len(texts),1);self.assertTrue(texts[0]['required'])
        self.assertNotIn('value',texts[0]);self.assertEqual(result.conditional_rules,[])

    def test_single_seller_broker_plan_never_requests_a_second_seller_or_any_buyer(self):
        result=self.prepare(client_names=['QA José 李 Seller'],signer_plan='clients_and_broker')
        self.assertEqual({f['recipient_id'] for f in result.fields[0]},{'1','broker'})
        self.assertFalse(any('buyer' in f['api_id'] for f in result.fields[0]))
        self.assertTrue(all(f['x']>=325*4/3 for f in result.fields[0] if f['type']=='signature'))
        dates=[f for f in result.fields[0] if f['type']=='date']
        self.assertTrue(all(f['lock_sign_date'] and f['width']==80 and f['height']==18 for f in dates))

    def test_long_unicode_details_are_lossless_static_continuations(self):
        value='QA Büro 李 '+('Seller-provided lead condition '*95)
        result=self.prepare(lead_disclosure={'knowledge':'known','knowledge_details':value,'records':'none'})
        reader=PdfReader(BytesIO(result.pdf));self.assertGreater(len(reader.pages),1)
        combined=''.join(''.join(page.extract_text().split()) for page in reader.pages)
        self.assertIn(''.join(value.split()),combined)
        self.assertTrue(any(f['page']>1 and f['type']=='initials' for f in result.fields[0]))
        self.assertFalse(any(f['type']=='text' for f in result.fields[0]))

    def test_packet_composer_offsets_every_field_and_namespaces_controls_together(self):
        answers=validate_answers(sample_answers(addenda=['C']))
        result=lead.prepare_listing_lead(SOURCE,answers)
        component=PreparedDocument('C',result.pdf,result.fields,{'1':'1','2':'2','associate':'associate'},
                                   result.content_fingerprint,result.checkbox_groups,result.conditional_rules)
        packet=assemble_listing_packet(answers,pdf('Fictional listing',11),signing_fields(),documents=[component])
        self.assertEqual(packet.manifest['included'][-1]['start_page'],12)
        self.assertEqual(packet.manifest['page_count'],13)
        self.assertEqual(len(packet.conditional_rules),2)
        ids={f['api_id'] for f in packet.fields[0]}
        self.assertTrue(all(set(group['checkbox_ids'])<=ids for group in packet.checkbox_groups))
        self.assertTrue(all(rule['target_id'] in ids and set(rule['action_field_ids'])<=ids for rule in packet.conditional_rules))
        self.assertTrue(all(field['page'] in (12,13) for field in packet.fields[0][1:]))

    def test_preparation_fingerprint_is_stable_and_changes_with_explicit_facts(self):
        self.assertEqual(self.prepare().content_fingerprint,self.prepare().content_fingerprint)
        self.assertNotEqual(self.prepare().content_fingerprint,self.prepare(lead_disclosure={'knowledge':'none','records':'none'}).content_fingerprint)


if __name__=='__main__':unittest.main()

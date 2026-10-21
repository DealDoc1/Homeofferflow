from copy import deepcopy
import hashlib
from io import BytesIO
import os
from pathlib import Path
import unittest

import pdfplumber
from pypdf import PdfReader

from lib import lease_disclosures as rental
from lib.listing_packet import PreparedDocument, assemble_lease_listing_packet
from tests.test_listing_packet import pdf,signing_fields
from tests.test_txr_1102 import sample


FILES = {'TXR-2008':'TXR-2008-2003-10-14.pdf','TXR-2015':'TXR-2015-2025-09-01.pdf'}
IDENTITY = {'client_names':['QA José 李 Landlord','QA Zoë Landlord'],
            'property_address':'100 Fictional Rental Lane, QA City, TX 75000',
            'signer_plan':'clients_and_associate'}


class RentalAnswerTests(unittest.TestCase):
    def test_missing_facts_stay_unanswered_and_no_tenant_receipts_are_accepted(self):
        self.assertEqual(rental.validate_answers('TXR-2015'),
                         {'floodplain':'unanswered','flooding_last_five_years':'unanswered'})
        self.assertEqual(rental.validate_answers('TXR-2008'),
                         {'knowledge':'unanswered','records':'unanswered','knowledge_details':'','records_details':''})
        for code in FILES:
            for bad in ([],{'tenant_received':True},{'recipient_id':'tenant'},{'source_sha256':'injected'}):
                with self.subTest(code=code,bad=bad),self.assertRaises(ValueError):rental.validate_answers(code,bad)
        for bad in (None,[],'TREC-56-0','TXR-1406'):
            with self.subTest(form=bad),self.assertRaises(ValueError):rental.validate_answers(bad)

    def test_strict_explicit_choices_and_bounded_details_do_not_mutate_input(self):
        for code,choices in [('TXR-2008',rental.LEAD_CHOICES),('TXR-2015',rental.FLOOD_CHOICES)]:
            for key,options in choices.items():
                for value in options:
                    self.assertEqual(rental.validate_answers(code,{key:value})[key],value)
                for value in (True,0,None,[],{},'yes','no'):
                    with self.subTest(key=key,value=value),self.assertRaises(ValueError):rental.validate_answers(code,{key:value})
        original={'knowledge':'known','knowledge_details':'QA painted trim','records':'none','records_details':'Stale report'}
        before=deepcopy(original);result=rental.validate_answers('TXR-2008',original)
        self.assertEqual(original,before);self.assertEqual(result['records_details'],'')
        for value in ('x'*4001,True,{},None):
            with self.subTest(details=value if not isinstance(value,str) else 'overflow'),self.assertRaises(ValueError):
                rental.validate_answers('TXR-2008',{'knowledge_details':value})

    def test_no_alternate_source_or_injected_recipient_can_enter_the_adapter(self):
        for code in FILES:
            with self.assertRaises(ValueError):rental.prepare_lease_disclosure(code,b'%PDF-fake',IDENTITY)
        for change in ({'client_names':[]},{'client_names':['A','B','C']},{'client_names':['']},
                       {'client_names':['x'*301]},{'property_address':''},{'property_address':'x'*401},
                       {'signer_plan':'tenant_only'}):
            with self.subTest(change=change),self.assertRaises(ValueError):rental._identity({**IDENTITY,**change})


@unittest.skipUnless(os.environ.get('HOF_LEASE_DISCLOSURE_SOURCES'),'Private official rental PDFs are opt-in.')
class RentalSourceTests(unittest.TestCase):
    def source(self,code):return (Path(os.environ['HOF_LEASE_DISCLOSURE_SOURCES'])/FILES[code]).read_bytes()
    def prepare(self,code,answers=None,**changes):
        return rental.prepare_lease_disclosure(code,self.source(code),{**IDENTITY,**changes},answers)

    def test_exact_sources_original_legal_text_preserved_supplier_imprint_only_removed(self):
        for code in FILES:
            original=self.source(code);before=hashlib.sha256(original).hexdigest()
            self.assertEqual(before,rental.SOURCES[code]['sha256'])
            result=self.prepare(code)
            text=PdfReader(BytesIO(result.pdf)).pages[0].extract_text()
            self.assertIn(rental.SOURCES[code]['revision'],text)
            self.assertNotIn('Andrew Christian',text);self.assertNotIn('12225 Greenville',text)
            self.assertIn('Tenant',text)
            if code=='TXR-2015':self.assertIn('NOT AUTHORIZED',text)
            self.assertEqual(hashlib.sha256(original).hexdigest(),before)
            with self.assertRaises(ValueError):
                rental.prepare_lease_disclosure(code,original+b'\nchanged',IDENTITY)

    def test_unanswered_flood_choices_are_landlord_owned_exact_one_without_agent_or_tenant_fields(self):
        result=self.prepare('TXR-2015')
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),1)
        self.assertEqual({f['recipient_id'] for f in result.fields[0]},{'1','2'})
        self.assertEqual(len(result.checkbox_groups),2);self.assertEqual(result.conditional_rules,[])
        self.assertEqual(len([f for f in result.fields[0] if f['type']=='checkbox']),4)
        for group in result.checkbox_groups:
            self.assertEqual((group['recipient_id'],group['validation'],group['required'],group['exact_value']),('1','exact',True,1))
        self.assertTrue(all('value' not in f for f in result.fields[0]))
        self.assertTrue(result.remaining_actions)

    def test_flood_explicit_branches_stamp_only_the_selected_source_boxes(self):
        for first in ('aware','not_aware'):
            for second in ('aware','not_aware'):
                result=self.prepare('TXR-2015',{'floodplain':first,'flooding_last_five_years':second})
                self.assertEqual(result.checkbox_groups,[])
                with pdfplumber.open(BytesIO(result.pdf)) as doc:
                    marks=[c for c in doc.pages[0].chars if c['text']=='X' and 98<=c['x0']<145]
                self.assertEqual(len(marks),2)
                self.assertAlmostEqual(marks[0]['x0'],101 if first=='aware' else 135,places=1)
                self.assertAlmostEqual(marks[1]['x0'],101.2 if second=='aware' else 135.2,places=1)

    def test_unanswered_lead_collects_landlord_details_but_never_checks_tenant_receipt(self):
        result=self.prepare('TXR-2008')
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),2)
        self.assertEqual(len(result.checkbox_groups),2);self.assertEqual(len(result.conditional_rules),2)
        controls=[f for f in result.fields[0] if f['type']=='checkbox']
        self.assertEqual(len(controls),4)
        self.assertTrue(all(f['recipient_id']=='1' and not f['required'] for f in controls))
        self.assertTrue(all(f['x']==53.1*4/3 for f in controls))
        self.assertFalse(any('tenant' in f['api_id'] for f in result.fields[0]))
        texts=[f for f in result.fields[0] if f['type']=='text']
        self.assertEqual(len(texts),2)
        self.assertTrue(all(f['page']==2 and not f['required'] and f['height']==18 and 'value' not in f for f in texts))
        self.assertEqual({f['recipient_id'] for f in result.fields[0]},{'1','2','associate'})

    def test_explicit_negative_single_landlord_broker_has_no_extra_party_or_answer_page(self):
        for code,answers in [('TXR-2008',{'knowledge':'none','records':'none'}),
                             ('TXR-2015',{'floodplain':'not_aware','flooding_last_five_years':'not_aware'})]:
            result=self.prepare(code,answers,client_names=['QA Landlord'],signer_plan='clients_and_broker')
            self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),1)
            self.assertEqual(result.checkbox_groups,[]);self.assertEqual(result.conditional_rules,[])
            self.assertEqual({f['recipient_id'] for f in result.fields[0]}, {'1','broker'} if code=='TXR-2008' else {'1'})
            self.assertEqual({f['type'] for f in result.fields[0]},{'signature','date'})
            dates=[f for f in result.fields[0] if f['type']=='date']
            self.assertTrue(all(f['date_format']=='MM/DD/YYYY' and f['lock_sign_date'] and f['height']==18 and f['width']==72 for f in dates))

    def test_explicit_positive_details_remain_lossless_with_unicode_and_overflow(self):
        detail='QA Büro 李 - '+('Landlord-provided painted trim details. '*70)
        address='100 QA Straße 李 '+('Fictional rental property description '*10)
        result=self.prepare('TXR-2008',{'knowledge':'known','knowledge_details':detail,
                                     'records':'provided','records_details':'QA landlord-supplied report'},property_address=address)
        reader=PdfReader(BytesIO(result.pdf));self.assertGreater(len(reader.pages),1)
        text=''.join(''.join(p.extract_text().split()) for p in reader.pages)
        self.assertIn(''.join(detail.split()),text);self.assertIn(''.join(address.split()),text)
        self.assertIn('QAlandlord-suppliedreport',text)
        self.assertFalse(any(f['type']=='text' for f in result.fields[0]))
        flood=self.prepare('TXR-2015',property_address=address,client_names=['QA Landlord'])
        self.assertGreater(len(PdfReader(BytesIO(flood.pdf)).pages),1)
        self.assertEqual({f['recipient_id'] for f in flood.fields[0]},{'1'})
        self.assertTrue(all(f['recipient_id']=='1' for f in flood.fields[0] if f['type']=='initials'))

    def test_positive_without_details_requires_an_explanation_without_prefilling_a_fact(self):
        result=self.prepare('TXR-2008',{'knowledge':'known','records':'none'})
        text=[f for f in result.fields[0] if f['type']=='text']
        self.assertEqual(len(text),1);self.assertTrue(text[0]['required']);self.assertNotIn('value',text[0])
        self.assertEqual(result.conditional_rules,[])

    def test_all_field_bounds_ids_and_continuation_roles_are_valid(self):
        for code in FILES:
            for count in (1,2):
                for plan in ('clients_and_associate','clients_and_broker'):
                    result=self.prepare(code,client_names=IDENTITY['client_names'][:count],signer_plan=plan)
                    fields=result.fields[0];ids={f['api_id'] for f in fields};pages=len(PdfReader(BytesIO(result.pdf)).pages)
                    self.assertEqual(len(ids),len(fields))
                    for f in fields:
                        self.assertTrue(1<=f['page']<=pages)
                        self.assertTrue(0<=f['x']<f['x']+f['width']<=816)
                        self.assertTrue(0<=f['y']<f['y']+f['height']<=1056)
                        if f['page']==1:self.assertLessEqual(f['x']+f['width'],288*4/3)
                    for g in result.checkbox_groups:self.assertTrue(set(g['checkbox_ids'])<=ids)
                    for rule in result.conditional_rules:
                        self.assertIn(rule['target_id'],ids);self.assertTrue(set(rule['action_field_ids'])<=ids)

    def test_signature_and_date_rectangles_never_cover_original_printed_text(self):
        for code in FILES:
            result=self.prepare(code)
            with pdfplumber.open(BytesIO(self.source(code))) as doc:
                chars=[c for c in doc.pages[0].chars if c['text'].strip()]
            for f in result.fields[0]:
                if f['page']!=1 or f['type'] not in {'signature','date'}:continue
                left=f['x']*.75;right=(f['x']+f['width'])*.75
                top=792-f['y']*.75;bottom=top-f['height']*.75
                overlapping=[c['text'] for c in chars if min(right,c['x1'])-max(left,c['x0'])>.2
                             and min(top,c['y1'])-max(bottom,c['y0'])>.2]
                self.assertEqual(overlapping,[],(code,f['api_id'],overlapping))

    def test_package_offsets_and_namespaces_both_forms_without_adding_tenants(self):
        answers=sample(addenda=['B','C']);documents=[]
        for code,slot in [('TXR-2015','B'),('TXR-2008','C')]:
            result=self.prepare(code)
            documents.append(PreparedDocument(slot,result.pdf,result.fields,
                {'1':'1','2':'2','associate':'associate'},result.content_fingerprint,
                result.checkbox_groups,result.conditional_rules))
        packet=assemble_lease_listing_packet(answers,pdf('Fictional lease listing',11),signing_fields(),documents=documents)
        self.assertEqual([(r['code'],r['start_page'],r['end_page']) for r in packet.manifest['included']],
                         [('TXR-1102',1,11),('B',12,12),('C',13,14)])
        self.assertEqual(packet.manifest['pending'],[])
        self.assertEqual(len(packet.checkbox_groups),4);self.assertEqual(len(packet.conditional_rules),2)
        self.assertEqual({f['recipient_id'] for f in packet.fields[0]},{'1','2','associate'})
        ids={f['api_id'] for f in packet.fields[0]}
        for g in packet.checkbox_groups:self.assertTrue(set(g['checkbox_ids'])<=ids)
        self.assertEqual({f['page'] for f in packet.fields[0] if f['api_id'].startswith('listing_B_')},{12})
        self.assertEqual({f['page'] for f in packet.fields[0] if f['api_id'].startswith('listing_C_')},{13,14})

    def test_fingerprint_is_stable_but_binds_source_answers_property_and_parties(self):
        for code in FILES:
            baseline=self.prepare(code).content_fingerprint
            self.assertEqual(baseline,self.prepare(code).content_fingerprint)
            self.assertNotEqual(baseline,self.prepare(code,client_names=['QA Other Landlord']).content_fingerprint)
            self.assertNotEqual(baseline,self.prepare(code,property_address='200 QA Changed Property').content_fingerprint)
            changed={'knowledge':'none'} if code=='TXR-2008' else {'floodplain':'aware'}
            self.assertNotEqual(baseline,self.prepare(code,changed).content_fingerprint)


if __name__=='__main__':unittest.main()

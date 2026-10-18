"""Actual PDF composition and signing offsets, never a provider invitation."""
from copy import deepcopy
from io import BytesIO
import os
from pathlib import Path
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject
from reportlab.pdfgen.canvas import Canvas

from lib import listing_packet as packet
from lib import txr_1101
from tests.test_txr_1101 import sample_answers, BROKER, ASSOCIATE


def pdf(text='Fictional related document',pages=1):
    stream=BytesIO();canvas=Canvas(stream,pagesize=(612,792))
    for page in range(pages):
        canvas.drawString(36,740,text+' '+str(page+1));canvas.showPage()
    canvas.save();return stream.getvalue()


def signing_fields(recipient='1',**changes):
    return [[{'api_id':'seller_signature','type':'signature','recipient_id':recipient,
              'page':1,'x':72,'y':800,'width':200,'height':26,'required':True,**changes}]]


def component(code,**changes):
    return packet.PreparedDocument(**{'code':code,'pdf':pdf('Fictional '+code),
        'fields':signing_fields(),'recipient_map':{'1':'1'},'content_fingerprint':'a'*64,**changes})


class ListingPacketTests(unittest.TestCase):
    def build(self,answers=None,documents=(),**changes):
        return packet.assemble_listing_packet(answers or sample_answers(),
            changes.pop('listing_pdf',pdf('Fictional listing',10)),
            changes.pop('listing_fields',signing_fields()),documents=documents,**changes)

    def test_missing_seller_disclosure_does_not_stop_the_actual_listing_pdf(self):
        result=self.build()
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),10)
        self.assertEqual(result.manifest['page_count'],10)
        self.assertEqual([row['code'] for row in result.manifest['included']],['TXR-1101'])
        self.assertEqual([row['code'] for row in result.manifest['pending']],['A','B'])
        self.assertTrue(result.manifest['has_pending_documents'])
        self.assertEqual(result.fields,signing_fields())

    def test_actual_pdf_order_and_signer_offsets_follow_source_order_not_arrival(self):
        answers=sample_answers(addenda=['P','C','B'])
        docs=[component('P',pdf=pdf('Fictional water',2)),component('B',pdf=pdf('Fictional disclosure',4)),component('C')]
        result=self.build(answers,docs)
        reader=PdfReader(BytesIO(result.pdf))
        self.assertEqual(len(reader.pages),17)
        self.assertIn('Fictional disclosure 1',reader.pages[10].extract_text())
        self.assertIn('Fictional C 1',reader.pages[14].extract_text())
        self.assertIn('Fictional water 1',reader.pages[15].extract_text())
        self.assertEqual([(row['code'],row['start_page'],row['end_page']) for row in result.manifest['included']],
                         [('TXR-1101',1,10),('B',11,14),('C',15,15),('P',16,17)])
        self.assertEqual([field['page'] for field in result.fields[0]],[1,11,15,16])
        self.assertEqual([field['api_id'] for field in result.fields[0]],
            ['seller_signature','listing_B_seller_signature','listing_C_seller_signature','listing_P_seller_signature'])
        self.assertFalse(result.manifest['has_pending_documents'])

    def test_local_recipient_ids_are_explicitly_remapped_and_inputs_are_not_mutated(self):
        answers=sample_answers(addenda=['B']);before=deepcopy(answers)
        fields=signing_fields('local_seller_2');field_before=deepcopy(fields)
        result=self.build(answers,[component('B',fields=fields,recipient_map={'local_seller_2':'2'})])
        self.assertEqual(result.fields[0][-1]['recipient_id'],'2')
        self.assertEqual(answers,before);self.assertEqual(fields,field_before)
        result.manifest['included'][0]['label']='changed'
        self.assertEqual(self.build(answers).manifest['included'][0]['label'],'Sale listing agreement')

    def test_pre1978_and_hoa_answers_produce_pending_requirements_not_fake_attachments(self):
        result=self.build(sample_answers(addenda=[],built_before_1978='yes',request_hoa_information='yes',other_documents='QA custom notice'))
        self.assertEqual([row['code'] for row in result.manifest['pending']],['C','G'])
        self.assertEqual(result.manifest['other_documents'],'QA custom notice')
        self.assertEqual(len(result.manifest['included']),1)

    def test_unselected_duplicate_or_unbound_documents_cannot_be_added(self):
        for docs in ([component('C')],[component('B'),component('B')],
                     [component('B',content_fingerprint='unconfirmed')],['client-controlled-pdf']):
            with self.subTest(docs=repr(docs)[:80]),self.assertRaises(ValueError):self.build(documents=docs)

    def test_unknown_signers_cannot_silently_become_the_agent_or_a_seller(self):
        for mapping in ({},{'1':'buyer1'},{'1':'broker'},{'1':1}):
            with self.subTest(mapping=mapping),self.assertRaises(ValueError):
                self.build(documents=[component('B',recipient_map=mapping)])
        result=self.build(sample_answers(addenda=['B'],signer_plan='clients_and_broker'),
                          [component('B',recipient_map={'1':'broker'})])
        self.assertEqual(result.fields[0][-1]['recipient_id'],'broker')

    def test_invalid_or_duplicate_fields_and_multiple_groups_fail_before_composition(self):
        for fields in (signing_fields(page=2),signing_fields(page=True),signing_fields(x=-1),
                       signing_fields(width=900),signing_fields(height=0),signing_fields(y=float('nan')),
                       signing_fields(api_id='bad id'),[signing_fields()[0]*2],[[],[]]):
            with self.subTest(fields=fields),self.assertRaises(ValueError):
                self.build(documents=[component('B',fields=fields)])

    def test_unreadable_encrypted_and_rotated_supplied_documents_are_not_silently_omitted(self):
        encrypted=PdfWriter();encrypted.add_blank_page(612,792);encrypted.encrypt('fictional-password')
        stream=BytesIO();encrypted.write(stream)
        rotated=PdfWriter();rotated.add_blank_page(612,792);rotated.pages[0][NameObject('/Rotate')]=NumberObject(90)
        second=BytesIO();rotated.write(second)
        for content in (b'not a PDF',b'%PDF-broken',stream.getvalue(),second.getvalue()):
            with self.subTest(content=content[:16]),self.assertRaises(ValueError):
                self.build(documents=[component('B',pdf=content)])

    def test_unsigned_interactive_form_fields_are_namespaced_and_retained(self):
        # Both PDFs deliberately use the same canonical field name.
        def interactive():
            stream=BytesIO();canvas=Canvas(stream,pagesize=(612,792))
            canvas.acroForm.textfield(name='property',value='QA property',x=100,y=650,width=200,height=20)
            canvas.showPage();canvas.save();return stream.getvalue()
        result=self.build(sample_answers(addenda=['B']),[component('B',pdf=interactive(),fields=[],recipient_map={})],
                          listing_pdf=interactive())
        reader=PdfReader(BytesIO(result.pdf));fields=reader.get_fields()
        self.assertEqual(fields['hof_listing_primary.property']['/V'],'QA property')
        self.assertEqual(fields['hof_listing_B.property']['/V'],'QA property')
        self.assertEqual(len(reader.pages[1]['/Annots']),1)

    def test_rotated_information_only_pages_do_not_get_unnecessary_signing_restrictions(self):
        writer=PdfWriter();writer.add_blank_page(612,792)
        writer.pages[0][NameObject('/Rotate')]=NumberObject(90)
        stream=BytesIO();writer.write(stream)
        result=self.build(documents=[component('A',pdf=stream.getvalue(),fields=[],recipient_map={})])
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),11)
        self.assertEqual(PdfReader(BytesIO(result.pdf)).pages[-1].get('/Rotate'),90)

    def test_selected_document_size_limit_is_combined_not_only_per_file(self):
        from unittest.mock import patch
        with patch.object(packet,'MAX_INPUT_BYTES',len(pdf('Fictional listing',10))+500):
            with self.assertRaises(ValueError):self.build(documents=[component('A')])

    def test_retry_identity_ignores_volatile_pdf_metadata_but_binds_changed_component_content(self):
        first=self.build(documents=[component('B')])
        changed_pdf=PdfWriter();changed_pdf.append(PdfReader(BytesIO(pdf('Same logical renderer data'))))
        changed_pdf.add_metadata({'/CreationDate':'D:20261018000000Z'})
        stream=BytesIO();changed_pdf.write(stream)
        same=self.build(documents=[component('B',pdf=stream.getvalue())])
        self.assertEqual(first.content_fingerprint,same.content_fingerprint)
        changed=self.build(documents=[component('B',content_fingerprint='b'*64)])
        self.assertNotEqual(first.content_fingerprint,changed.content_fingerprint)
        self.assertNotEqual(first.content_fingerprint,self.build().content_fingerprint)

    def controlled_component(self,**changes):
        fields=signing_fields()[0]+[
            {**signing_fields()[0][0],'api_id':key,'type':kind,'required':False}
            for key,kind in [('yes','checkbox'),('no','checkbox'),('explanation','text')]]
        return component('B',fields=[fields],checkbox_groups=[{
            'group_name':'choice','recipient_id':'1','checkbox_ids':['yes','no'],
            'validation':'exact','required':True,'exact_value':1}],conditional_rules=[{
            'target_id':'yes','action_type':'require','action_field_ids':['explanation'],
            'conditions':[{'condition_type':'all_of','status':'completed','field_api_ids':['yes']}]}],**changes)

    def test_completion_controls_reject_dangling_and_cross_signer_references(self):
        original=self.controlled_component()
        variants=[]
        for key,value in [('checkbox_ids',['yes','missing']),('checkbox_ids',['yes','seller_signature']),
                          ('recipient_id','2'),('exact_value',True),('required','true')]:
            changed=deepcopy(original);changed.checkbox_groups[0][key]=value;variants.append(changed)
        for key,value in [('target_id','missing'),('action_field_ids',['missing']),
                          ('action_field_ids',['yes']),('conditions',[])]:
            changed=deepcopy(original);changed.conditional_rules[0][key]=value;variants.append(changed)
        changed=deepcopy(original);changed.fields[0][-1]['recipient_id']='2'
        changed.recipient_map['2']='2';variants.append(changed)
        changed=deepcopy(original);changed.conditional_rules[0]['conditions'][0]['field_api_ids']=['missing']
        variants.append(changed)
        for item in variants:
            with self.subTest(item=item),self.assertRaises(ValueError):self.build(documents=[item])

    def test_completion_controls_are_namespaced_immutable_and_bound_to_packet_identity(self):
        document=self.controlled_component();before=deepcopy(document)
        first=self.build(documents=[document])
        self.assertEqual(document,before)
        self.assertEqual(first.checkbox_groups[0]['checkbox_ids'],['listing_B_yes','listing_B_no'])
        self.assertEqual(first.conditional_rules[0]['target_id'],'listing_B_yes')
        self.assertEqual(first.conditional_rules[0]['action_field_ids'],['listing_B_explanation'])
        changed=deepcopy(document);changed.checkbox_groups[0]['exact_value']=2
        self.assertNotEqual(first.content_fingerprint,self.build(documents=[changed]).content_fingerprint)
        changed=deepcopy(document);changed.conditional_rules[0]['conditions'][0]['status']='not_completed'
        self.assertNotEqual(first.content_fingerprint,self.build(documents=[changed]).content_fingerprint)
        changed=deepcopy(document);changed.conditional_rules.extend(deepcopy(changed.conditional_rules)*10)
        with self.assertRaises(ValueError):self.build(documents=[changed])

    @unittest.skipUnless(os.environ.get('HOF_TXR1101_SOURCE'),'Exact private source opt-in')
    def test_real_listing_continuations_and_single_unicode_seller_keep_their_signing_pages(self):
        source=Path(os.environ['HOF_TXR1101_SOURCE']).read_bytes()
        for names in (['QA José 李 Seller'],['QA Seller One','QA Seller Two']):
            with self.subTest(names=names):
                answers=sample_answers(client_names=names,addenda=['B'],special_provisions='QA Büro 李 '*240)
                primary=txr_1101.render_txr_1101(source,answers,BROKER,ASSOCIATE)
                count=len(PdfReader(BytesIO(primary)).pages)
                fields=txr_1101.build_signwell_fields_txr1101(answers,client_count=len(names),page_count=count)
                result=packet.assemble_listing_packet(answers,primary,fields,documents=[component('B')])
                self.assertGreater(count,10)
                self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),count+1)
                self.assertEqual(result.fields[0][:len(fields[0])],fields[0])
                self.assertEqual(result.fields[0][-1]['page'],count+1)
                self.assertEqual(result.manifest['included'][-1]['start_page'],count+1)


if __name__=='__main__':unittest.main()

"""One fixed fictional lead-disclosure test, using the existing QA sender.

Only test recipient IDs/page offsets differ from the listing adapter. No
customer data, private source download, credential or caller settings enter
this builder. Its draft must pass actual provider readback before invitations.
"""
import base64
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re

from pypdf import PdfReader, PdfWriter
from lib.listing_lead_disclosure import prepare_listing_lead, SOURCE_SHA256, REVISION
from lib.purchase_signing_qa import QA_RECIPIENTS, QA_OPERATOR_EMAILS

QA_REVISION='listing-lead-56-0-provider-2026-10-17-v1'
QA_SCENARIO='listing-lead-disclosure-provider-placement'
REVIEWED_SOURCE_COMMIT='fcbf606c19662af45793eb662df6329f44ee43ab'
RENDER_REVISION=REVISION
DOCUMENT_PREFIX='QA ONLY - listing lead disclosure - '
QA_TITLE='Listing lead disclosure completion and placement'
QA_DESCRIPTION='Fixed fictional Seller choices, conditional details, one/two Sellers, broker/associate and Unicode continuation.'
TEST_LABEL='listing lead disclosure'
VERIFY_DRAFT=True
LAYOUT_SHA256='30f9711e64bff16ecbb44fb7031ed8e6f845afb0bf149629e84a13c65992e8e1'


def cases():
    base={'property_address':'100 QA ONLY Example Lane, Example City, TX 75001',
          'client_names':['QA Seller One','QA Seller Two'],'signer_plan':'clients_and_associate'}
    return (
        ('unconfirmed_single',{**base,'client_names':['QA Seller One'],'signer_plan':'clients_and_broker'}),
        ('unconfirmed_two',deepcopy(base)),
        ('none_two',{**base,'lead_disclosure':{'knowledge':'none','records':'none'}}),
        ('known_unicode',{**base,'client_names':['QA José 李 Seller','QA Zoë Seller'],
            'lead_disclosure':{'knowledge':'known','records':'provided',
                'knowledge_details':'QA Büro 李 Seller reports painted trim. '*65,
                'records_details':'QA ONLY report dated October 1, 2026.'}}),
    )


def completion_controls():
    groups=[];rules=[]
    for name in ('unconfirmed_single','unconfirmed_two'):
        for key in ('knowledge','records'):
            positive=f'{name}_lead_{key}_positive'
            groups.append({'group_name':f'{name}_lead_{key}','recipient_id':'qa_a',
                'checkbox_ids':[positive,f'{name}_lead_{key}_negative'],
                'validation':'exact','required':True,'exact_value':1})
            rules.append({'target_id':positive,'action_type':'require',
                'action_field_ids':[f'{name}_lead_{key}_explanation'],
                'conditions':[{'condition_type':'all_of','status':'completed',
                    'field_api_ids':[positive],'position':1}]})
    return groups,rules


def layout_fingerprint(fields,cases):
    groups,rules=completion_controls()
    return hashlib.sha256(json.dumps({'source':SOURCE_SHA256,'render_revision':RENDER_REVISION,
        'fields':fields,'groups':groups,'rules':rules,'cases':cases},
        sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def build_packet():
    source=(Path(__file__).resolve().parents[1]/'lead_based_paint_56-0.pdf').read_bytes()
    writer=PdfWriter();fields=[];manifest=[];actual_groups=[];actual_rules=[]
    for name,data in cases():
        document=prepare_listing_lead(source,data);reader=PdfReader(BytesIO(document.pdf))
        offset=len(writer.pages)
        for page in reader.pages:writer.add_page(page)
        ids={item['api_id']:name+'_'+item['api_id'] for item in document.fields[0]}
        def recipient(value):return 'qa_b' if value=='2' else 'qa_a'
        fields.extend({**item,'api_id':ids[item['api_id']],'page':item['page']+offset,
            'recipient_id':recipient(item['recipient_id'])} for item in document.fields[0])
        for original in document.checkbox_groups:
            actual_groups.append({**original,'group_name':name+'_'+original['group_name'],
                'recipient_id':recipient(original['recipient_id']),
                'checkbox_ids':[ids[value] for value in original['checkbox_ids']]})
        for original in document.conditional_rules:
            actual_rules.append({**original,'target_id':ids[original['target_id']],
                'action_field_ids':[ids[value] for value in original['action_field_ids']],
                'conditions':[{**condition,'field_api_ids':[ids[value] for value in condition['field_api_ids']]}
                    for condition in original['conditions']]})
        manifest.append({'case':name,'source_pages':list(range(1,len(reader.pages)+1)),
            'output_pages':list(range(offset+1,len(writer.pages)+1)),
            'content_sha256':[hashlib.sha256(page.get_contents().get_data()).hexdigest() for page in reader.pages],
            'field_count':len(document.fields[0]),'signer_plan':data['signer_plan']})
    if (actual_groups,actual_rules)!=completion_controls():
        raise ValueError('The QA completion controls changed; review the specimen before sending.')
    if len(writer.pages)!=7 or len(fields)!=42 or len({field['api_id'] for field in fields})!=42:
        raise ValueError('The QA packet shape changed; review the specimen before sending.')
    writer.add_metadata({'/Title':'QA ONLY - listing lead disclosure',
        '/Subject':'Fictional nonbinding Seller disclosure completion and placement test'})
    output=BytesIO();writer.write(output)
    return output.getvalue(),[fields],manifest


def build_payload(packet,fields,release_sha):
    if release_sha!=REVIEWED_SOURCE_COMMIT or not re.fullmatch(r'[0-9a-f]{40}',release_sha):
        raise ValueError('Use the exact reviewed listing lead source revision.')
    reader=PdfReader(BytesIO(packet))
    if len(reader.pages)!=7:raise ValueError('Use the complete reviewed QA packet.')
    manifest=[{'case':name,'source_pages':list(range(1,pages+1)),
        'output_pages':list(range(start,start+pages)),'field_count':count,'signer_plan':data['signer_plan']}
        for (name,data),start,pages,count in zip(cases(),(1,3,5,6),(2,2,1,2),(12,15,6,9))]
    for item in manifest:
        item['content_sha256']=[hashlib.sha256(reader.pages[number-1].get_contents().get_data()).hexdigest()
            for number in item['output_pages']]
    if not LAYOUT_SHA256 or layout_fingerprint(fields,manifest)!=LAYOUT_SHA256:
        raise ValueError('The listing lead specimen does not match the visually reviewed layout.')
    groups,rules=completion_controls()
    return {'test_mode':True,'draft':True,'apply_signing_order':False,'reminders':False,
        'with_signature_page':False,'name':DOCUMENT_PREFIX+release_sha[:12],
        'subject':'TEST ONLY: listing lead disclosure choices and placement',
        'message':'Fictional nonbinding test, not a client document. In the first case choose known hazards and no reports; in the second choose no actual knowledge and reports provided. Supply QA-only explanations when required. Both test recipients may sign independently.',
        'recipients':[dict(item) for item in QA_RECIPIENTS],
        'files':[{'name':'QA_ONLY_listing_lead_disclosure.pdf','file_base64':base64.b64encode(packet).decode('ascii')}],
        'fields':fields,'checkbox_groups':groups,'conditional_rules':rules,
        'metadata':{'qa_kind':'listing-lead-disclosure','qa_revision':QA_REVISION,
            'release_sha':release_sha,'layout_sha256':LAYOUT_SHA256}}

"""Seller-side TREC 56-0 preparation for a listing, not Buyer acknowledgement.

The bundled static source has identical extracted text to TREC's current
05-04-2026 fillable download. Only explicit Seller answers are stamped. Unknown
answers are collected from Seller 1 in SignWell with exact-one groups; both
named Sellers certify their own information. Buyer rights, receipts and Buyer
or Buyer's Broker signatures are never populated in this listing workflow.
"""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from lib.pdf_text import draw_text, paragraph_markup
from lib.txr_addenda_layout import inline, clean
from lib.txr1501_answers import render_continuation, continuation_fields, INITIAL_X


SOURCE_SHA256='eb8bdfb943cafbe8402e6b44fe44d73eb66d6acd6a99f31f73498f938fd76e6c'
OFFICIAL_FILLABLE_SHA256='515bda0aa4b834e55b0fe894378e8ce200c9c3547c81fcb11bf1019107dbf868'
REVISION='listing-lead-disclosure-56-0-2026-05-04-v1'
MAX_DETAIL=4000
LIVE_DETAIL_LIMIT=200


def validate_answers(data=None):
    if data is None:data={}
    if not isinstance(data,dict) or set(data)-{'knowledge','knowledge_details','records','records_details'}:
        raise ValueError('Check the lead-based paint disclosure details.')
    result={}
    for key,options in (('knowledge',('known','none','unanswered')),('records',('provided','none','unanswered'))):
        value=data.get(key,'unanswered')
        if value not in options:raise ValueError('Choose an explicit Seller lead disclosure response.')
        result[key]=value
        details=data.get(key+'_details','')
        if not isinstance(details,str) or len(details)>MAX_DETAIL:
            raise ValueError('Keep each lead disclosure explanation within 4,000 characters.')
        result[key+'_details']=clean(details)
    return result


@dataclass(frozen=True)
class LeadDocument:
    pdf: bytes
    fields: list
    checkbox_groups: list
    conditional_rules: list
    content_fingerprint: str


def prepare_listing_lead(source, listing):
    """Use already validated listing identity; never accept alternate signers."""
    if not isinstance(source,bytes) or hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:
        raise ValueError('The lead disclosure source differs from the reviewed TREC 56-0 copy.')
    reader=PdfReader(BytesIO(source))
    if len(reader.pages)!=1 or reader.get_fields() or tuple(map(float,reader.pages[0].mediabox))!=(0.,0.,612.,792.):
        raise ValueError('Use the reviewed one-page static TREC 56-0 source.')
    names=listing.get('client_names')
    if not isinstance(names,list) or not 1<=len(names)<=2 or any(not isinstance(n,str) or not clean(n) for n in names):
        raise ValueError('Identify one or two Sellers for the lead disclosure.')
    if listing.get('signer_plan') not in {'clients_and_associate','clients_and_broker'}:
        raise ValueError('Choose the listing professional who will sign.')
    address=listing.get('property_address')
    if not isinstance(address,str) or not clean(address) or len(address)>400:
        raise ValueError('Identify the property for the lead disclosure.')
    answers=validate_answers(listing.get('lead_disclosure'))
    role='associate' if listing['signer_plan']=='clients_and_associate' else 'broker'
    fields=[];groups=[];rules=[];overflow={};live=[]
    overlay=BytesIO();canvas=Canvas(overlay,pagesize=(612,792))
    def put(value,blanks,label):
        entries=inline(value,blanks)
        if entries is None:
            overflow[label]=clean(value);entries=inline('See attached details',blanks[-1:])
        for x,y,text,size in entries or []:draw_text(canvas,text,x,y,size)
    def field(key,kind,page,x,y,width,height,recipient='1',required=True,**extra):
        item={'api_id':'lead_'+key,'type':kind,'page':page,'x':x*4/3,'y':(792-y-height)*4/3,
              'width':width*4/3,'height':height*4/3,'recipient_id':recipient,'required':required,**extra}
        if kind=='date':item.update(date_format='MM/DD/YYYY',lock_sign_date=True)
        fields.append(item);return item['api_id']
    put(address,[(205,679,370)],'Property')
    for key,on_y,off_y,description_blanks in (
        ('knowledge',521,499,[(528,522,48),(92,510,485)]),
        ('records',476,444,[(371,467,206),(92,455,485)])):
        choice=answers[key];positive='known' if key=='knowledge' else 'provided'
        positive_id='lead_'+key+'_positive'
        if choice=='unanswered':
            first=field(key+'_positive','checkbox',1,65,on_y,11,11,required=False)
            second=field(key+'_negative','checkbox',1,65,off_y,11,10,required=False)
            groups.append({'group_name':'lead_'+key,'recipient_id':'1','checkbox_ids':[first,second],
                           'validation':'exact','required':True,'exact_value':1})
        else:
            draw_text(canvas,'X',67,(on_y if choice==positive else off_y)+2,8)
        details=answers[key+'_details']
        if choice!='none' and details:
            put(details,description_blanks,'Known lead paint or hazards' if key=='knowledge' else 'Reports provided to purchaser')
        elif choice!='none':
            live.append((key,choice=='unanswered',positive_id))
            put('See lead disclosure details',description_blanks,'Lead disclosure details reference')
    # Only Seller and the listing professional execution rules. No Buyer fields.
    for label,recipient,x,y,width in [('seller1','1',325,200,190),
                                     *(([('seller2','2',325,156,190)]) if len(names)==2 else []),
                                     (role,role,325,112,190)]:
        field(label+'_signature','signature',1,x,y,width,20,recipient)
        field(label+'_date','date',1,518,y,60,13.5,recipient)
    canvas.showPage();canvas.save()
    writer=PdfWriter();writer.append(reader,import_outline=False)
    writer.pages[0].merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
    if overflow:
        continuation=render_continuation(listing,overflow,title='Lead-Based Paint - Entered Details',
            party_label='Seller',description='Seller-provided information referenced in the attached TREC 56-0.')
        writer.append(PdfReader(BytesIO(continuation)),import_outline=False)
    if live:
        page_number=len(writer.pages)+1
        output=BytesIO();canvas=Canvas(output,pagesize=(612,792))
        canvas.setFont('Helvetica-Bold',14);canvas.drawString(48,748,'Lead Disclosure Details')
        canvas.setFont('Helvetica',9);canvas.drawString(48,730,'Complete only the explanations that apply to the Seller disclosures on TREC 56-0.')
        paragraph=Paragraph(paragraph_markup('Property: '+address),ParagraphStyle('lead_property',fontName='Helvetica',fontSize=9,leading=12))
        _,height=paragraph.wrap(504,130);paragraph.drawOn(canvas,48,710-height)
        for key,conditional,positive_id in live:
            y=475 if key=='knowledge' else 305
            canvas.setFont('Helvetica-Bold',11)
            canvas.drawString(48,y+78,'Known lead-based paint or hazards' if key=='knowledge' else 'Records and reports provided to purchaser')
            canvas.setFont('Helvetica',9);canvas.drawString(48,y+63,f'Briefly explain (up to {LIVE_DETAIL_LIMIT} characters). Supply supporting reports separately.')
            canvas.setLineWidth(.5);canvas.rect(48,y,504,55)
            text_id=field(key+'_explanation','text',page_number,48,y,504,55,required=not conditional,
                label=f'Brief Seller explanation (up to {LIVE_DETAIL_LIMIT} characters)',fixed_width=True,validation='custom',
                validation_regex=rf'^[\s\S]{{1,{LIVE_DETAIL_LIMIT}}}$',validation_regex_error_message=f'Use up to {LIVE_DETAIL_LIMIT} characters; provide longer details and reports separately.')
            if conditional:
                rules.append({'target_id':positive_id,'action_type':'require','action_field_ids':[text_id],
                    'conditions':[{'condition_type':'all_of','status':'completed','field_api_ids':[positive_id],'position':1}]})
        labels=[('Seller 1','1')]+([('Seller 2','2')] if len(names)==2 else [])+[(role.title(),'professional')]
        canvas.setFont('Helvetica',8)
        for label,key in labels:
            x=INITIAL_X[key];canvas.drawString(x-62,70,label+' initials');canvas.line(x,68,x+50,68)
        canvas.drawString(48,40,'TREC 56-0 - Seller completion details')
        canvas.showPage();canvas.save();writer.append(PdfReader(BytesIO(output.getvalue())),import_outline=False)
    fields.extend(continuation_fields(listing,len(names),len(writer.pages),source_pages=1,prefix='lead'))
    output=BytesIO();writer.write(output)
    fingerprint=hashlib.sha256(json.dumps({'source':SOURCE_SHA256,'revision':REVISION,'answers':answers,
        'property':address,'sellers':names,'role':role,'fields':fields,'groups':groups,'rules':rules},
        sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    return LeadDocument(output.getvalue(),[fields],groups,rules,fingerprint)

"""Exact-source landlord preparation of TXR-2008 and TXR-2015.

This pure adapter never selects tenants, acknowledges tenant receipt, resolves
private sources or sends documents. The caller owns source access, saved facts
and package delivery. Tenant execution remains separate from landlord listing
preparation. Unanswered landlord facts are completed by Landlord 1 in SignWell.
"""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from lib.pdf_text import draw_text, paragraph_markup
from lib.txr_addenda_layout import clean, inline
from lib.txr_1101 import _remove_member_footer


SOURCES = {
    'TXR-2008': {'sha256':'c6aaeefec282b09d5981a76326c1fd4e2a317ee6b4618184c16cf14b3e57372b',
                 'revision':'10-14-03','render_revision':'lease-lead-2008-2003-10-14-v1'},
    'TXR-2015': {'sha256':'8a2439f6c191063a3abfe500d7a523e9fe9bb0265b03f663990e424ccedd3581',
                 'revision':'09-01-25','render_revision':'rental-flood-2015-2025-09-01-v1'},
}
MAX_DETAIL = 4000
LIVE_DETAIL_LIMIT = 200
LIVE_LINE_HEIGHT = 13.5
INITIAL_X = {'1':110,'2':286,'professional':462}
FLOOD_CHOICES = {'floodplain':('aware','not_aware','unanswered'),
                 'flooding_last_five_years':('aware','not_aware','unanswered')}
LEAD_CHOICES = {'knowledge':('known','none','unanswered'),
                'records':('provided','none','unanswered')}


def validate_answers(form_code, answers=None):
    if not isinstance(form_code,str) or form_code not in SOURCES:
        raise ValueError('Choose the rental disclosure to prepare.')
    if answers is None: answers = {}
    choices = LEAD_CHOICES if form_code == 'TXR-2008' else FLOOD_CHOICES
    details = {'knowledge_details','records_details'} if form_code == 'TXR-2008' else set()
    if not isinstance(answers, dict) or set(answers)-set(choices)-details:
        raise ValueError('Check the landlord disclosure answers.')
    result = {}
    for key, options in choices.items():
        value = answers.get(key,'unanswered')
        if value not in options:
            raise ValueError('Choose an explicit landlord disclosure answer.')
        result[key] = value
    for key in sorted(details):
        value = answers.get(key,'')
        if not isinstance(value,str) or len(value)>MAX_DETAIL:
            raise ValueError('Keep each landlord explanation within 4,000 characters.')
        # Stale details must not contradict a later explicit negative answer.
        result[key] = clean(value) if result[key.removesuffix('_details')]!='none' else ''
    return result


@dataclass(frozen=True)
class LeaseDisclosure:
    pdf: bytes
    fields: list
    checkbox_groups: list
    conditional_rules: list
    content_fingerprint: str
    form_code: str
    render_revision: str
    remaining_actions: tuple


def _identity(listing):
    if not isinstance(listing,dict):
        raise ValueError('Identify the landlord and rental property.')
    names = listing.get('client_names')
    address = listing.get('property_address')
    plan = listing.get('signer_plan')
    if (not isinstance(names,list) or len(names) not in (1,2)
            or any(not isinstance(name,str) or not clean(name) or len(name)>300 for name in names)):
        raise ValueError('Identify one or two landlords for the rental disclosure.')
    if not isinstance(address,str) or not clean(address) or len(address)>400:
        raise ValueError('Identify the rental property.')
    if plan not in {'clients_and_associate','clients_and_broker'}:
        raise ValueError('Choose the listing professional who will sign.')
    return {'client_names':[clean(name) for name in names], 'property_address':clean(address), 'signer_plan':plan}


def _continuation(overflow, title, parties):
    out = BytesIO()
    document = SimpleDocTemplate(out,pagesize=(612,792),leftMargin=48,rightMargin=48,
                                 topMargin=106,bottomMargin=112)
    style = ParagraphStyle('lease_disclosure_details',fontName='Helvetica',fontSize=10,
                           leading=14,spaceAfter=12,splitLongWords=True,allowWidows=0,allowOrphans=0)
    label = ParagraphStyle('lease_disclosure_label',parent=style,keepWithNext=True)
    story = []
    for heading,text in overflow.items():
        if story: story.append(Spacer(1,6))
        story.extend([Paragraph(paragraph_markup(heading),label),Paragraph(paragraph_markup(text),style)])
    def frame(canvas, doc):
        canvas.setFont('Helvetica-Bold',13);canvas.drawString(48,749,title)
        canvas.setFont('Helvetica',9);canvas.drawString(48,730,'Landlord-provided information referenced in the attached rental disclosure.')
        canvas.setFont('Helvetica',8)
        for name,_,key in parties:
            x = INITIAL_X[key];canvas.drawString(x-62,70,name+' initials');canvas.line(x,68,x+50,68)
        canvas.drawString(48,40,title);canvas.drawRightString(564,40,'Continuation page '+str(doc.page))
    document.build(story,onFirstPage=frame,onLaterPages=frame)
    return out.getvalue()


def prepare_lease_disclosure(form_code, source, listing, answers=None):
    """Prepare landlord-side fields only; preserve all original tenant blanks."""
    data = validate_answers(form_code,answers)
    identity = _identity(listing)
    spec = SOURCES[form_code]
    if not isinstance(source,bytes) or hashlib.sha256(source).hexdigest()!=spec['sha256']:
        raise ValueError('The rental disclosure source differs from the reviewed official copy.')
    reader = PdfReader(BytesIO(source),strict=True)
    if (reader.is_encrypted or len(reader.pages)!=1 or reader.get_fields()
            or tuple(map(float,reader.pages[0].mediabox))!=(0.,0.,612.,792.)
            or any(a.get_object().get('/Subtype')=='/Widget' for a in reader.pages[0].get('/Annots',[]))):
        raise ValueError('Use the reviewed one-page rental disclosure source.')
    writer = PdfWriter();writer.append(reader,import_outline=False)
    _remove_member_footer(writer)
    prefix = 'lease'+form_code.removeprefix('TXR-')+'_'
    role = 'associate' if identity['signer_plan']=='clients_and_associate' else 'broker'
    parties = [('Landlord 1','1','1')]
    if len(identity['client_names'])==2: parties.append(('Landlord 2','2','2'))
    if form_code=='TXR-2008': parties.append((role.title(),role,'professional'))
    fields=[];groups=[];rules=[];overflow={};live=[]
    out=BytesIO();canvas=Canvas(out,pagesize=(612,792))
    def put(value, blanks, label):
        entries=inline(value,blanks)
        if entries is None:
            overflow[label]=clean(value);entries=inline('See attached details',blanks[-1:])
        for x,y,text,size in entries or []: draw_text(canvas,text,x,y,size)
    def field(key, kind, page, x, y, width, height, recipient='1', required=True, **extra):
        item={'api_id':prefix+key,'type':kind,'page':page,'x':x*4/3,'y':(792-y-height)*4/3,
              'width':width*4/3,'height':height*4/3,'recipient_id':recipient,'required':required,**extra}
        if kind=='date': item.update(date_format='MM/DD/YYYY',lock_sign_date=True)
        fields.append(item);return item['api_id']
    put(identity['property_address'],[(423,667 if form_code=='TXR-2008' else 663,153),
                                    (36,655 if form_code=='TXR-2008' else 651,540)],'Rental property')
    if form_code=='TXR-2015':
        choices=[('floodplain',99,133,563),('flooding_last_five_years',99.2,133.2,464)]
        for key,x1,x2,y in choices:
            if data[key]=='unanswered':
                ids=[field(key+'_'+value,'checkbox',1,x,y,10,11,required=False)
                     for x,value in [(x1,'aware'),(x2,'not_aware')]]
                groups.append({'group_name':prefix+key,'recipient_id':'1','checkbox_ids':ids,
                               'validation':'exact','required':True,'exact_value':1})
            else: draw_text(canvas,'X',(x1 if data[key]=='aware' else x2)+2,y+2,8)
        signature_rows=[('1',242)]+([('2',203.5)] if len(parties)==2 else [])
        signature_width,date_x=145,198
    else:
        for key,on_y,off_y,blanks in [
            ('knowledge',531,493,[(90,520,486),(90,507.5,480)]),
            ('records',457.4,419.4,[(433,446,143),(90,433.5,480)])]:
            positive='known' if key=='knowledge' else 'provided'
            positive_id=prefix+key+'_positive'
            if data[key]=='unanswered':
                ids=[field(key+'_'+which,'checkbox',1,53.1,y,11,11,required=False)
                     for which,y in [('positive',on_y),('negative',off_y)]]
                groups.append({'group_name':prefix+key,'recipient_id':'1','checkbox_ids':ids,
                               'validation':'exact','required':True,'exact_value':1})
            else: draw_text(canvas,'X',55.1,(on_y if data[key]==positive else off_y)+2,8)
            if data[key]!='none':
                if data[key+'_details']:
                    put(data[key+'_details'],blanks,'Known lead-based paint or hazards' if key=='knowledge' else 'Lead records and reports')
                else:
                    put('See attached landlord details',blanks,'Landlord details reference')
                    live.append((key,data[key]=='unanswered',positive_id))
        signature_rows=[('1',170)]+([('2',141)] if len(identity['client_names'])==2 else [])+[(role,113)]
        signature_width,date_x=180,234
    for recipient,y in signature_rows:
        # TXR-2008's lower rows have only 28pt between lines, including the
        # previous row's printed label. A 20pt field overlaps that label.
        height=13.5 if form_code=='TXR-2008' and recipient!='1' else 20
        field(recipient+'_signature','signature',1,36,y,signature_width,height,recipient)
        field(recipient+'_date','date',1,date_x,y,54,13.5,recipient)
    canvas.showPage();canvas.save()
    writer.pages[0].merge_page(PdfReader(BytesIO(out.getvalue())).pages[0])
    title = 'Rental Lead Disclosure - Entered Details' if form_code=='TXR-2008' else 'Rental Flood Disclosure - Entered Details'
    if overflow:
        writer.append(PdfReader(BytesIO(_continuation(overflow,title,parties))),import_outline=False)
    if live:
        page=len(writer.pages)+1;out=BytesIO();canvas=Canvas(out,pagesize=(612,792))
        canvas.setFont('Helvetica-Bold',14);canvas.drawString(48,748,'Rental Lead Disclosure Details')
        canvas.setFont('Helvetica',9);canvas.drawString(48,730,'Complete the explanations that apply to the landlord answers on TXR-2008.')
        property_text=Paragraph(paragraph_markup('Property: '+identity['property_address']),
            ParagraphStyle('rental_lead_property',fontName='Helvetica',fontSize=9,leading=12))
        _,height=property_text.wrap(504,120);property_text.drawOn(canvas,48,710-height)
        for key,conditional,positive_id in live:
            top=530 if key=='knowledge' else 350
            canvas.setFont('Helvetica-Bold',11)
            canvas.drawString(48,top+25,'Known lead-based paint or hazards' if key=='knowledge' else 'Lead records and reports')
            canvas.setFont('Helvetica',9);canvas.drawString(48,top+10,'Use one paragraph, up to 200 characters. Provide supporting reports separately.')
            canvas.setLineWidth(.5);canvas.rect(48,top-95,504,95)
            text_id=field(key+'_explanation','text',page,48,top-LIVE_LINE_HEIGHT,504,LIVE_LINE_HEIGHT,
                required=not conditional,label='Brief landlord explanation (up to 200 characters)',fixed_width=True,
                validation='custom',validation_regex=rf'^[^\r\n]{{1,{LIVE_DETAIL_LIMIT}}}$',
                validation_regex_error_message='Use one paragraph up to 200 characters; provide longer details separately.')
            if conditional:
                rules.append({'target_id':positive_id,'action_type':'require','action_field_ids':[text_id],
                    'conditions':[{'condition_type':'all_of','status':'completed','field_api_ids':[positive_id],'position':1}]})
        canvas.setFont('Helvetica',8)
        for name,_,key in parties:
            x=INITIAL_X[key];canvas.drawString(x-62,70,name+' initials');canvas.line(x,68,x+50,68)
        canvas.drawString(48,40,'TXR-2008 - Landlord completion details')
        canvas.showPage();canvas.save();writer.append(PdfReader(BytesIO(out.getvalue())),import_outline=False)
    for page in range(2,len(writer.pages)+1):
        for _,recipient,key in parties:
            field(f'page{page}_{recipient}_initials','initials',page,INITIAL_X[key],70,50,16,recipient)
    fingerprint=hashlib.sha256(json.dumps({'source':spec['sha256'],'revision':spec['render_revision'],
        'identity':identity,'answers':data,'fields':fields,'groups':groups,'rules':rules},
        sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    output=BytesIO();writer.write(output)
    return LeaseDisclosure(output.getvalue(),[fields],groups,rules,fingerprint,form_code,spec['render_revision'],
        ('Tenant receipt and signature remain to be completed.',))

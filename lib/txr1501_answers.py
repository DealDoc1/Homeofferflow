"""Lossless placement of entered long-form answers, without changing terms."""
from io import BytesIO
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from lib.pdf_text import paragraph_markup
from lib.txr_addenda_layout import inline, clean

TITLE = 'TXR-1501 - Answer Continuation'
INITIAL_X = {'1':110, '2':286, 'professional':462}


def answer_layout(data, brokerage, associate):
    pages={n:[] for n in range(1,7)}
    overflow={}
    def put(page,value,label,blanks,size=8):
        entries=inline(value,blanks,size)
        if entries is None:
            overflow[label]=clean(value)
            entries=inline('See exhibit',blanks[:1],7)
            if entries is None:entries=inline('Exhibit',blanks[:1],7)
            if entries is None:raise ValueError('Answer reference does not fit its form blank')
        pages[page].extend(entries)
    clients=data.get('client_names') or []
    broker=brokerage.get('legal_name') or brokerage.get('name') or brokerage.get('dba_name') or ''
    agent=associate.get('name') or associate.get('agent_name') or ''
    put(1,', '.join(clients),'Paragraph 1 - Clients',[(110,615,464),(110,602,464)])
    put(1,broker,'Paragraph 1 - Broker',[(110,533,464),(110,520,464)])
    for key,x,y,width in [('client_address',129,589,445),('client_city_state_zip',161,577,413),
                          ('client_phone',120,564,202),('client_email',116,552,206)]:
        put(1,data.get(key),'Paragraph 1 - '+key.replace('_',' '),[(x,y,width)])
    for key,x,y,width in [('address',126,508,448),('city_state_zip',158,495,416),
                          ('phone',117,482,205),('email',113,470,209)]:
        put(1,brokerage.get(key),'Paragraph 1 - broker '+key.replace('_',' '),[(x,y,width)])
    put(1,data.get('market_area'),'Paragraph 3C - Market Area',[(146,312,428),(83,299,490),(83,287,485)])
    put(1,data.get('term_start'),'Paragraph 4 - Start date',[(236,171,86)])
    put(1,data.get('term_end'),'Paragraph 4 - End date',[(460,171,69)])
    for key,x,y,width in [('purchase_percentage',176,476,38),('purchase_flat_fee',405,476,97),
                          ('lease_one_month_percentage',157,457,57),('lease_total_rents_percentage',350,457,44),
                          ('lease_flat_fee',282,445,76)]:
        put(2,(data.get('compensation') or {}).get(key),'Paragraph 7A - '+key.replace('_',' '),[(x,y,width)])
    put(2,data.get('retainer_amount'),'Paragraph 7B - Retainer',[(142,412,63)])
    put(3,data.get('protection_days'),'Paragraph 7F - Protection days',[(110,486,63)])
    put(3,data.get('payment_county'),'Paragraph 7H - Payment county',[(381,311,112)])
    for label,value,x,y,width in [
        ('Broker printed name',broker,36,400,197),
        ('Broker license',brokerage.get('license_number'),240,400,46),
        ('Associate printed name',agent,36,309,197),
        ('Associate license',associate.get('license_number'),240,309,46),
        ('Client 1 printed name',clients[0] if clients else '',324,400,250),
        ('Client 2 printed name',clients[1] if len(clients)>1 else '',324,309,250)]:
        put(6,value,'Execution - '+label,[(x,y,width)],size=7)
    if overflow:
        put(5,'Answer continuation (attached)','Continuation reference',[(86,278,200)])
    return pages,overflow


def render_continuation(data, overflow, *, title=TITLE, party_label='Client',
                        description='Continuation of the entered answers referenced in the attached agreement.'):
    if not overflow:return None
    output=BytesIO()
    detail=ParagraphStyle('txr1501_detail',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=12,
                          splitLongWords=True,allowWidows=0,allowOrphans=0)
    label_style=ParagraphStyle('representation_answer_label',parent=detail,keepWithNext=True)
    document=SimpleDocTemplate(output,pagesize=(612,792),leftMargin=48,rightMargin=48,
                               topMargin=106,bottomMargin=112)
    story=[]
    for label,value in overflow.items():
        # A trailing spacer can spill onto a blank page and accidentally add
        # initials for a page with no answers. Space only between entries.
        if story:story.append(Spacer(1,6))
        story.extend([Paragraph(paragraph_markup(label),label_style),
                      Paragraph(paragraph_markup(value),detail)])
    role='Associate' if data.get('signer_plan')=='clients_and_associate' else 'Broker'
    labels=[(party_label+' 1','1')]
    if len(data.get('client_names') or [])>1:labels.append((party_label+' 2','2'))
    labels.append((role,'professional'))
    def frame(canvas,doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold',13);canvas.drawString(48,749,title)
        canvas.setFont('Helvetica',9)
        canvas.drawString(48,730,description)
        for label,key in labels:
            x=INITIAL_X[key]
            canvas.setFont('Helvetica',7 if party_label=='Customer' else 8)
            canvas.drawString(x-62,70,label+' initials')
            canvas.line(x,68,x+50,68)
        canvas.drawString(48,40,title)
        canvas.drawRightString(564,40,'Continuation page '+str(doc.page))
        canvas.restoreState()
    document.build(story,onFirstPage=frame,onLaterPages=frame)
    return output.getvalue()


def continuation_fields(data, client_count, page_count, *, source_pages=6, prefix='txr1501'):
    if not isinstance(page_count,int) or isinstance(page_count,bool) or page_count<source_pages:
        raise ValueError('The completed representation packet must contain all its source pages')
    role='associate' if data.get('signer_plan')=='clients_and_associate' else 'broker'
    recipients=[('1','1'),(role,'professional')]
    if client_count==2:recipients.insert(1,('2','2'))
    return [{'api_id':f'{prefix}_continuation_{page-source_pages}_{recipient}_initials',
             'type':'initials','page':page,'recipient_id':recipient,'required':True,
             'x':INITIAL_X[key]*4/3,'y':706*4/3,'width':50*4/3,'height':16*4/3}
            for page in range(source_pages+1,page_count+1) for recipient,key in recipients]

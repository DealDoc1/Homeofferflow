"""Three local fictional placement proofs. Does not accept provider credentials."""
import argparse
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1102 import render_txr_1102, build_signwell_fields_txr1102, answer_layout
from lib.pdf_text import draw_text
from tests.test_txr_1102 import sample, with_preferences, BROKER, ASSOCIATE


def cases():
    return {
        'ordinary':with_preferences(make_ready='landlord_pays',make_ready_limit='250',make_ready_service_fee='25'),
        'single-broker':sample(client_names=['QA Sole Landlord'],fee_scope='broker_only',cobroker_basis='',cobroker_amount='',
            fee_basis='other',fee_amount='',fee_other='Fictional negotiated flat fee: 1500',
            renewal_basis='other',renewal_amount='',renewal_other='No renewal fee in this fictional specimen',
            sale_fee_basis='other',sale_fee_amount='',sale_fee_other='No sale fee in this fictional specimen',
            mls_filing='none',internet_display='not_applicable',hoa='no',keybox='no',intermediary='not_authorized',
            signer_plan='clients_and_broker',addenda=['A','C'],built_before_1978='unanswered'),
        'unicode-continuation':with_preferences(client_names=['QA Élodie 李','QA Landlord Two'],
            client_address='Fictional Résidence 李 '*10,property_address='123 Fictional Büro 李 Road, '+('North QA District '*8)+'Dallas, TX 75201',
            fee_basis='total_percentage',fee_amount='2.5',cobroker_basis='flat',cobroker_amount='100',
            renewal_basis='other',renewal_amount='',renewal_other='Fictional renewal instruction Büro 李 '*20,
            sale_fee_basis='other',sale_fee_amount='',sale_fee_other='Fictional sale compensation Büro 李 '*20,
            mls_filing='delayed',mls_delay_days='5',mls_delay_purpose='Fictional preparation instruction Büro 李 '*15,
            internet_display='hide_address',make_ready='broker_reimbursed',make_ready_limit='1000',
            make_ready_service_fee='Fictional negotiated service arrangement Büro 李 '*20,
            special_provisions='Fictional continuation QA only. Büro 李 '*80,
            rent_due='other',rent_due_other='Fictional agreed rent timing Büro 李 '*8,
            initial_late_basis='percentage',initial_late_amount='7.5',animals='not_permitted',animal_restrictions='',
            animal_deposit='',animal_monthly_rent='',animal_one_time_fee='',yard='named_contractor',
            yard_contractor='Fictional contractor Büro 李 '*12,pool='other',pool_other='Fictional pool arrangement Büro 李 '*20,
            tenant_replacement_amount='999999.99',landlord_replacement_amount='25',
            lease_special_provisions='Fictional lease-preference continuation Büro 李 '*35,
            other_documents='Fictional related notice Büro 李 '*25)}


def prepare(source,output):
    raw=source.read_bytes();output.mkdir(parents=True,exist_ok=True);report=[]
    for name,answers in cases().items():
        rendered=render_txr_1102(raw,answers,BROKER,ASSOCIATE)
        reader=PdfReader(BytesIO(rendered));fields=build_signwell_fields_txr1102(answers,
            client_count=len(answers['client_names']),page_count=len(reader.pages))[0]
        guide=BytesIO();canvas=Canvas(guide,pagesize=(612,792))
        for n in range(1,len(reader.pages)+1):
            canvas.saveState();canvas.setFillAlpha(.08);canvas.setFillColorRGB(.8,0,0)
            canvas.translate(306,396);canvas.rotate(38);canvas.setFont('Helvetica-Bold',31)
            canvas.drawCentredString(0,0,'FICTIONAL QA - NOT FOR USE');canvas.restoreState()
            for field in (f for f in fields if f['page']==n):
                x=field['x']*.75;y=792-(field['y']+field['height'])*.75
                canvas.setStrokeColorRGB(.15,.35,.8);canvas.setLineWidth(.4)
                canvas.rect(x,y,field['width']*.75,field['height']*.75)
                text='10/20/2026' if field['type']=='date' else 'QA' if field['type']=='initials' else 'QA '+field['recipient_id']+' signature'
                draw_text(canvas,text,x+2,y+4,7)
            canvas.showPage()
        canvas.save();overlay=PdfReader(BytesIO(guide.getvalue()));writer=PdfWriter()
        for i,page in enumerate(reader.pages):writer.add_page(page);writer.pages[i].merge_page(overlay.pages[i])
        writer.add_metadata({'/Title':'FICTIONAL QA ONLY - TXR-1102 '+name})
        target=output/('QA_ONLY_TXR1102_'+name+'.pdf')
        with target.open('wb') as stream:writer.write(stream)
        _,overflow=answer_layout(answers,BROKER,ASSOCIATE)
        report.append({'case':name,'pages':len(reader.pages),'fields':len(fields),'continuationAnswers':len(overflow),
            'sourcePages':11,'nothingSent':True,'output':str(target)})
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();prepare(args.source,args.output)

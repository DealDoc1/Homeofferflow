"""Six private fictional rental-disclosure placement proofs; never sends."""
import argparse
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.lease_disclosures import prepare_lease_disclosure
from lib.pdf_text import draw_text


FILES={'TXR-2008':'TXR-2008-2003-10-14.pdf','TXR-2015':'TXR-2015-2025-09-01.pdf'}


def cases():
    common={'client_names':['QA José 李 Landlord','QA Zoë Landlord'],
            'property_address':'100 Fictional Rental Lane, QA City, TX 75000',
            'signer_plan':'clients_and_associate'}
    return {
        'ordinary':(common,{},{}),
        'single-negative':({**common,'client_names':['QA Sole Landlord'],'signer_plan':'clients_and_broker'},
            {'knowledge':'none','records':'none'},
            {'floodplain':'not_aware','flooding_last_five_years':'not_aware'}),
        'unicode-continuation':({**common,'property_address':'100 QA Straße 李 '+('Fictional rental property description '*10)},
            {'knowledge':'known','knowledge_details':'QA Büro 李 - '+('Fictional landlord-provided trim details. '*70),
             'records':'provided','records_details':'Fictional landlord-supplied report'},
            {'floodplain':'aware','flooding_last_five_years':'not_aware'}),
    }


def prepare(sources,output):
    output.mkdir(parents=True,exist_ok=True);reports=[]
    for code,filename in FILES.items():
        source=(sources/filename).read_bytes()
        for case,(identity,lead,flood) in cases().items():
            result=prepare_lease_disclosure(code,source,identity,lead if code=='TXR-2008' else flood)
            reader=PdfReader(BytesIO(result.pdf));guide=BytesIO();canvas=Canvas(guide,pagesize=(612,792))
            for page in range(1,len(reader.pages)+1):
                canvas.saveState();canvas.setFillAlpha(.06);canvas.setFillColorRGB(.8,0,0)
                canvas.translate(306,396);canvas.rotate(38);canvas.setFont('Helvetica-Bold',29)
                canvas.drawCentredString(0,0,'FICTIONAL QA - NOT FOR USE');canvas.restoreState()
                for field in (f for f in result.fields[0] if f['page']==page):
                    x=field['x']*.75;y=792-(field['y']+field['height'])*.75
                    canvas.setStrokeColorRGB(.15,.35,.8);canvas.setLineWidth(.4)
                    canvas.rect(x,y,field['width']*.75,field['height']*.75)
                    text=('10/20/2026' if field['type']=='date' else 'QA' if field['type']=='initials'
                          else 'X' if field['type']=='checkbox' else 'Fictional brief landlord explanation' if field['type']=='text'
                          else 'QA '+field['recipient_id']+' signature')
                    draw_text(canvas,text,x+2,y+3,7)
                canvas.showPage()
            canvas.save();overlay=PdfReader(BytesIO(guide.getvalue()));writer=PdfWriter()
            for index,page in enumerate(reader.pages):
                writer.add_page(page);writer.pages[index].merge_page(overlay.pages[index])
            writer.add_metadata({'/Title':'FICTIONAL QA ONLY - '+code+' '+case})
            target=output/('QA_ONLY_'+code+'_'+case+'.pdf')
            with target.open('wb') as stream:writer.write(stream)
            reports.append({'code':code,'case':case,'pages':len(reader.pages),'fields':len(result.fields[0]),
                'checkboxGroups':len(result.checkbox_groups),'conditionalRules':len(result.conditional_rules),
                'providerSends':0,'output':str(target)})
    print(json.dumps(reports,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--sources',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();prepare(args.sources,args.output)

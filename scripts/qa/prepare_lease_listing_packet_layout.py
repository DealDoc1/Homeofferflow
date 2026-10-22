"""Three fictional combined-PDF proofs; never a provider request or real IABS."""
import argparse
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.listing_packet import PreparedDocument,assemble_lease_listing_packet
from lib.pdf_text import draw_text
from lib.txr_1102 import render_txr_1102,build_signwell_fields_txr1102
from scripts.qa.prepare_txr1102_layout import cases
from tests.test_txr_1102 import BROKER,ASSOCIATE


def fictional_iabs():
    stream=BytesIO();canvas=Canvas(stream,pagesize=(612,792))
    canvas.setFont('Helvetica-Bold',18);canvas.drawString(36,742,'FICTIONAL IABS PLACEHOLDER')
    canvas.setFont('Helvetica',11)
    for y,text in [(710,'COMPOSITOR QA ONLY - NOT AN OFFICIAL FORM'),
                   (684,'This page represents an account-owned saved PDF for page-order testing.'),
                   (660,'It contains no recipient, signature, acknowledgement or disclosure answers.'),
                   (636,'Real production assembly uses the agent\'s verified private saved IABS.'),
                   (612,'Rental flood and lease lead documents are pending, not represented by this page.')]:
        canvas.drawString(36,y,text)
    canvas.showPage();canvas.save();return stream.getvalue()


def prepare(source,output):
    import hashlib
    raw=source.read_bytes();output.mkdir(parents=True,exist_ok=True);reports=[]
    iabs=fictional_iabs()
    for name,answers in cases().items():
        answers={**answers,'_for_signing':True}
        listing=render_txr_1102(raw,answers,BROKER,ASSOCIATE)
        primary_pages=len(PdfReader(BytesIO(listing)).pages)
        fields=build_signwell_fields_txr1102(answers,client_count=len(answers['client_names']),page_count=primary_pages)
        packet=assemble_lease_listing_packet(answers,listing,fields,documents=[
            PreparedDocument('A',iabs,[],{},hashlib.sha256(iabs).hexdigest())])
        reader=PdfReader(BytesIO(packet.pdf));guide=BytesIO();canvas=Canvas(guide,pagesize=(612,792))
        for page_number in range(1,len(reader.pages)+1):
            canvas.saveState();canvas.setFillAlpha(.08);canvas.setFillColorRGB(.8,0,0)
            canvas.translate(306,396);canvas.rotate(38);canvas.setFont('Helvetica-Bold',31)
            canvas.drawCentredString(0,0,'FICTIONAL QA - NOT FOR USE');canvas.restoreState()
            for field in (f for f in packet.fields[0] if f['page']==page_number):
                x=field['x']*.75;y=792-(field['y']+field['height'])*.75
                canvas.setStrokeColorRGB(.15,.35,.8);canvas.setLineWidth(.4)
                canvas.rect(x,y,field['width']*.75,field['height']*.75)
                label='10/20/2026' if field['type']=='date' else 'QA' if field['type']=='initials' else 'QA '+field['recipient_id']+' signature'
                draw_text(canvas,label,x+2,y+4,7)
            canvas.showPage()
        canvas.save();overlay=PdfReader(BytesIO(guide.getvalue()));writer=PdfWriter()
        for index,page in enumerate(reader.pages):writer.add_page(page);writer.pages[index].merge_page(overlay.pages[index])
        writer.add_metadata({'/Title':'FICTIONAL QA ONLY - combined lease listing '+name})
        target=output/('QA_ONLY_lease_listing_packet_'+name+'.pdf')
        with target.open('wb') as stream:writer.write(stream)
        reports.append({'case':name,'primaryPages':primary_pages,'totalPages':len(reader.pages),
                        'fields':len(packet.fields[0]),'manifest':packet.manifest,'output':str(target),'providerSends':0})
    print(json.dumps(reports,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();prepare(args.source,args.output)

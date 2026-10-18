#!/usr/bin/env python3
"""Render eight fictional TXR-1101 geometry cases using a private source.

Local only: no API calls, credentials, uploads, invitations or customer data.
Blue signing rectangles are geometry guides, NOT a completed-provider test.
Never commit the source or resulting filled forms to Git.
"""
import argparse
from io import BytesIO
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
import pypdfium2

from lib.pdf_text import draw_text, text_width
from lib.txr_1101 import render_txr_1101, build_signwell_fields_txr1101
from tests.test_txr_1101 import qa_cases, BROKER, ASSOCIATE


VISUAL_PAGES = {
    'standard-two':list(range(1,11)), 'flat-one':[2,10], 'broker-two':[5,9,10],
    'delayed-two':[3,6], 'offmls-one':[3,6,9], 'extra-fee-two':[2,3,6,7,8],
    'unicode-two':[1,7,10], 'overflow-one':[1,2,8,10],
}


def placement_guide(packet,fields):
    source=PdfReader(BytesIO(packet)); overlay=BytesIO()
    canvas=Canvas(overlay,pagesize=(612,792))
    for page in range(1,len(source.pages)+1):
        for f in fields:
            if f['page']!=page:continue
            x,width,height=f['x']*.75,f['width']*.75,f['height']*.75
            y=792-f['y']*.75-height
            canvas.setStrokeColorRGB(.1,.35,.8)
            canvas.setLineWidth(.45);canvas.rect(x,y,width,height)
            text=('QA signature' if f['type']=='signature' else
                  '10/17/2026' if f['type']=='date' else 'QA')
            size=10 if f['type']=='date' else 9 if f['type']=='signature' else 7
            if text_width(text,'Helvetica',size)>width-2:
                raise ValueError('QA guide value does not fit the signing field')
            canvas.setFillColorRGB(.1,.35,.8)
            draw_text(canvas,text,x+1,y+2,size)
        canvas.setFillColorRGB(.5,.15,.15)
        draw_text(canvas,'TEST ONLY - PLACEMENT GUIDE - NOT SIGNED',36,25,8)
        canvas.showPage()
    canvas.save()
    guide=PdfReader(BytesIO(overlay.getvalue())); writer=PdfWriter()
    for i,p in enumerate(source.pages):
        writer.add_page(p);writer.pages[i].merge_page(guide.pages[i])
    output=BytesIO();writer.write(output);return output.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    source=args.source.read_bytes()
    pdf_dir=args.output_dir/'output'/'pdf';image_dir=args.output_dir/'tmp'/'pdfs'
    pdf_dir.mkdir(parents=True,exist_ok=True);image_dir.mkdir(parents=True,exist_ok=True)
    results=[]
    for case,data in qa_cases().items():
        packet=render_txr_1101(source,data,BROKER,ASSOCIATE)
        page_count=len(PdfReader(BytesIO(packet)).pages)
        fields=build_signwell_fields_txr1101(data,client_count=len(data['client_names']),page_count=page_count)[0]
        output=placement_guide(packet,fields)
        pdf_path=pdf_dir/f'txr1101-{case}-placement-QA.pdf';pdf_path.write_bytes(output)
        images=[];document=pypdfium2.PdfDocument(output)
        pages=VISUAL_PAGES[case]+list(range(11,page_count+1))
        for number in pages:
            path=image_dir/f'{case}-p{number}.png'
            document[number-1].render(scale=1.5).to_pil().save(path)
            images.append(str(path))
        results.append({'case':case,'pages':page_count,'fields':len(fields),
                        'pdf':str(pdf_path),'visual_pages':pages,'images':images,
                        'completed_provider_verified':False})
    manifest=args.output_dir/'manifest.json'
    manifest.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'cases':len(results),'manifest':str(manifest),
                      'page_counts':{r['case']:r['pages'] for r in results}},indent=2))


if __name__=='__main__':main()

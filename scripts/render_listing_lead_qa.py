#!/usr/bin/env python3
"""Create a compact, fictional seller-side lead-disclosure placement set."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pypdfium2
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from lib import listing_lead_disclosure as lead
from lib.txr_1101 import validate_answers
from lib.pdf_text import paragraph_markup
from tests.test_txr_1101 import sample_answers
from scripts.render_txr1101_placement_qa import placement_guide


def guide(result):
    simple=[f for f in result.fields[0] if f['type'] in {'signature','initials','date'}]
    base=PdfReader(BytesIO(placement_guide(result.pdf,simple)))
    stream=BytesIO();canvas=Canvas(stream,pagesize=(612,792))
    for number in range(1,len(base.pages)+1):
        for f in result.fields[0]:
            if f['page']!=number or f['type'] not in {'checkbox','text'}:continue
            x,w,h=f['x']*.75,f['width']*.75,f['height']*.75;y=792-f['y']*.75-h
            canvas.setStrokeColorRGB(.1,.35,.8);canvas.setLineWidth(.5);canvas.rect(x,y,w,h)
            if f['type']=='text':
                paragraph=Paragraph(paragraph_markup('李'*lead.LIVE_DETAIL_LIMIT),ParagraphStyle('qa_text',fontName='Helvetica',fontSize=9.75,leading=12,splitLongWords=True))
                _,height=paragraph.wrap(w-4,h-4)
                if height>h-4:raise ValueError('Maximum-length QA text does not fit its completion box.')
                paragraph.drawOn(canvas,x+2,y+h-2-height)
        canvas.showPage()
    canvas.save();overlay=PdfReader(BytesIO(stream.getvalue()));writer=PdfWriter()
    for index,page in enumerate(base.pages):
        writer.add_page(page);writer.pages[index].merge_page(overlay.pages[index])
    output=BytesIO();writer.write(output);return output.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();pdf_dir=args.output_dir/'output'/'pdf';images=args.output_dir/'tmp'/'pdfs'
    pdf_dir.mkdir(parents=True,exist_ok=True);images.mkdir(parents=True,exist_ok=True)
    source=(Path(__file__).resolve().parents[1]/'lead_based_paint_56-0.pdf').read_bytes()
    cases={'unconfirmed-single':sample_answers(client_names=['QA José 李 Seller']),
        'none-two':sample_answers(lead_disclosure={'knowledge':'none','records':'none'}),
        'known-two':sample_answers(lead_disclosure={'knowledge':'known','knowledge_details':'QA Seller reports painted window trim.',
                                                  'records':'provided','records_details':'QA report dated October 1, 2026.'}),
        'unicode-continuation':sample_answers(lead_disclosure={'knowledge':'known','knowledge_details':'QA Büro 李 '+('Seller-provided QA condition '*90),
                                                             'records':'none'})}
    manifest=[]
    for name,answers in cases.items():
        result=lead.prepare_listing_lead(source,validate_answers(answers));document=guide(result)
        output=pdf_dir/f'listing-lead-{name}.pdf';output.write_bytes(document);rendered=pypdfium2.PdfDocument(document)
        files=[]
        for index in range(len(rendered)):
            image=images/f'{name}-p{index+1}.png';rendered[index].render(scale=1.5).to_pil().save(image);files.append(str(image))
        manifest.append({'case':name,'pdf':str(output),'images':files,'pages':len(rendered),'fields':result.fields,
            'checkbox_groups':result.checkbox_groups,'conditional_rules':result.conditional_rules,'revision':lead.REVISION,
            'source_sha256':lead.SOURCE_SHA256,'completed_provider_verified':False})
    output=args.output_dir/'manifest.json';output.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':str(output),'pages':{row['case']:row['pages'] for row in manifest}},indent=2))


if __name__=='__main__':main()

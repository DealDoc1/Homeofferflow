"""Render the fixed provider specimen locally. Never calls a provider."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import pypdfium2
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from lib.pdf_text import paragraph_markup
from lib.listing_lead_disclosure import LIVE_DETAIL_LIMIT
from lib import listing_lead_signing_qa as qa


def guide(packet,fields):
    reader=PdfReader(BytesIO(packet));overlay=BytesIO();canvas=Canvas(overlay,pagesize=(612,792))
    for number in range(1,len(reader.pages)+1):
        for field in fields[0]:
            if field['page']!=number:continue
            x,w,h=field['x']*.75,field['width']*.75,field['height']*.75
            y=792-field['y']*.75-h
            canvas.setStrokeColorRGB(.1,.35,.8);canvas.setLineWidth(.5);canvas.rect(x,y,w,h)
            if field['type']=='text':
                text=Paragraph(paragraph_markup('李'*LIVE_DETAIL_LIMIT),ParagraphStyle('qa_sample',fontName='Helvetica',fontSize=9.75,leading=12,splitLongWords=True))
                _,height=text.wrap(w-4,h-4)
                if height>h-4:raise ValueError('The reviewed explanation does not fit its field.')
                text.drawOn(canvas,x+2,y+h-2-height)
            elif field['type']!='checkbox':
                canvas.setFillColorRGB(.1,.35,.8);canvas.setFont('Helvetica',8)
                label={'signature':'QA signature','initials':'QA','date':'10/17/2026'}[field['type']]
                canvas.drawString(x+1,y+2,label)
        canvas.setFillColorRGB(.65,.1,.1);canvas.setFont('Helvetica',7)
        canvas.drawString(36,14,'TEST ONLY - PLACEMENT GUIDE - NOT SIGNED');canvas.showPage()
    canvas.save();pages=PdfReader(BytesIO(overlay.getvalue()));writer=PdfWriter()
    for index,page in enumerate(reader.pages):
        writer.add_page(page);writer.pages[index].merge_page(pages.pages[index])
    output=BytesIO();writer.write(output);return output.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();output=args.output_dir/'output'/'pdf';images=args.output_dir/'tmp'/'pdfs'
    output.mkdir(parents=True,exist_ok=True);images.mkdir(parents=True,exist_ok=True)
    packet,fields,cases=qa.build_packet()
    qa.build_payload(packet,fields,qa.REVIEWED_SOURCE_COMMIT)
    (output/'unsigned-listing-lead-provider-qa.pdf').write_bytes(packet)
    document=guide(packet,fields)
    rendered=pypdfium2.PdfDocument(document)
    for index in range(len(rendered)):
        rendered[index].render(scale=1.5).to_pil().save(images/f'listing-lead-provider-p{index+1}.png')
    groups,rules=qa.completion_controls()
    manifest={'qa_revision':qa.QA_REVISION,'reviewed_source_commit':qa.REVIEWED_SOURCE_COMMIT,
        'layout_sha256':qa.layout_fingerprint(fields,cases),'cases':cases,'fields':fields,
        'checkbox_groups':groups,'conditional_rules':rules,'completed_provider_verified':False}
    (args.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'pages':len(rendered),'fields':len(fields[0]),'layout_sha256':manifest['layout_sha256']}))


if __name__=='__main__':main()

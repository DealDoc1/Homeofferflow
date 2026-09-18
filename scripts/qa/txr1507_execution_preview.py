"""Private local geometry previews using fake names; never sends or signs."""
import argparse
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_1507 import render_txr_1507, build_signwell_fields_txr1507
from scripts.render_txr_signwell_map_review import signwell_rect_to_pdf, txr1507_value_overlay_data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    for role in ('associate','broker'):
        data,brokerage,associate=txr1507_value_overlay_data()
        data['signer_plan']='clients_and_'+role
        if role=='broker':
            data.update(service_level='showing_services',showing_fee='150',intermediary='not_authorized')
        reader=PdfReader(BytesIO(render_txr_1507(args.source.read_bytes(),data,brokerage,associate)))
        fields=build_signwell_fields_txr1507(data,client_count=2)[0]
        writer=PdfWriter()
        for n,page in enumerate(reader.pages,1):
            packet=BytesIO();c=Canvas(packet,pagesize=(612,792))
            c.setFont('Helvetica-Bold',8);c.setFillColorRGB(.6,0,0)
            c.drawString(36,778,'LOCAL GEOMETRY PREVIEW - SYNTHETIC MARKS - NOT SIGNED')
            for field in fields:
                if field['page']!=n:continue
                x,y,w,h=signwell_rect_to_pdf(field)
                c.setStrokeColorRGB(.1,.4,.7);c.setLineWidth(.4);c.rect(x,y,w,h)
                c.setFillColorRGB(0,0,0)
                c.setFont('Helvetica-Oblique' if field['type']=='signature' else 'Helvetica',10)
                value='09/18/2026' if field['type']=='date' else 'QA' if field['type']=='initials' else 'Review Signer '+field['recipient_id']
                c.drawString(x+1,y+3,value)
            c.save();writer.add_page(page);writer.pages[-1].merge_page(PdfReader(BytesIO(packet.getvalue())).pages[0])
        target=args.output/f'txr1507-{role}-candidate.pdf'
        with target.open('wb') as stream:writer.write(stream)
        print(target)


if __name__=='__main__':main()

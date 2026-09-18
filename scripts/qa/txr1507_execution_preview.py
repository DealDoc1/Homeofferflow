"""Private local geometry previews using fake names; never sends or signs."""
import argparse
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_1507 import render_txr_1507, build_signwell_fields_txr1507
from lib.txr_1501 import render_txr_1501, build_signwell_fields_txr1501
from scripts.render_txr_signwell_map_review import signwell_rect_to_pdf, txr1507_value_overlay_data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--form',choices=('1507','1501'),default='1507')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    for role in ('associate','broker'):
        data,brokerage,associate=txr1507_value_overlay_data()
        data['signer_plan']='clients_and_'+role
        if args.form=='1501':
            # Populate every supported long-form area; empty short-form
            # fixtures cannot reveal misplaced contact/retainer/county values.
            data.update(client_address='100 QA Street',client_city_state_zip='Frisco, TX 75034',
                        client_phone='2145550100',client_email='client@example.test',
                        retainer_amount='400',retainer_treatment='apply' if role=='associate' else 'not_apply',
                        protection_days='30',payment_county='Collin')
            data['compensation']=({'purchase_percentage':'3','lease_one_month_percentage':'100'}
                if role=='associate' else {'purchase_flat_fee':'5000','lease_total_rents_percentage':'3.5','lease_flat_fee':'2500'})
            brokerage.update(address='200 QA Avenue',city_state_zip='Frisco, TX 75034',
                             phone='2145550101',email='broker@example.test')
        if role=='broker':
            data.update(service_level='showing_services',showing_fee='150',intermediary='not_authorized')
        render,build=(render_txr_1501,build_signwell_fields_txr1501) if args.form=='1501' else (render_txr_1507,build_signwell_fields_txr1507)
        reader=PdfReader(BytesIO(render(args.source.read_bytes(),data,brokerage,associate)))
        fields=build(data,client_count=2)[0]
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
        target=args.output/f'txr{args.form}-{role}-candidate.pdf'
        with target.open('wb') as stream:writer.write(stream)
        print(target)


if __name__=='__main__':main()

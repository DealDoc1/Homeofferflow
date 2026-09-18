"""Private, synthetic showing-form previews; no network, sends or signatures."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_1508 import render_txr_1508, build_signwell_fields_txr1508
from lib.txr_source_imprint import SOURCE_IMPRINTS
from scripts.render_txr_signwell_map_review import signwell_rect_to_pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_IMPRINTS['TXR-1508'][0]:
        raise ValueError('Use the reviewed 02-25-26 TXR-1508 blank source')
    args.output.mkdir(parents=True, exist_ok=True)
    for role in ('associate', 'broker'):
        for long in (False, True):
            names = ['José Review Customer', 'Ana Review Customer'][:2 if role == 'associate' else 1]
            data = {'client_names': names, 'property_address': '100 Example Property Road, Frisco, TX 75034',
                    'signer_plan': role + '_and_clients',
                    'other_broker_agreement': ['yes', 'no'][:len(names)]}
            broker = {'name': 'Review Brokerage', 'license_number': '0000000'}
            agent = {'agent_name': 'Review Associate', 'license_number': '0000000'}
            if long:
                data['property_address'] = '100 Example Property ' + 'Building and address details ' * 13
                data['client_names'] = [(name + ' FamilyName ' * 13).strip() for name in names]
                broker['name'] = 'Review Brokerage ' + 'Regional Office ' * 10
                agent['agent_name'] = 'Review Associate ' + 'Professional Name ' * 8
            reader = PdfReader(BytesIO(render_txr_1508(source, data, broker, agent)))
            fields = build_signwell_fields_txr1508(data, client_count=len(names), page_count=len(reader.pages))[0]
            writer = PdfWriter()
            for number, page in enumerate(reader.pages, 1):
                packet = BytesIO()
                canvas = Canvas(packet, pagesize=(612, 792))
                canvas.setFont('Helvetica-Bold', 8)
                canvas.setFillColorRGB(.6, 0, 0)
                canvas.drawString(36, 778, 'LOCAL GEOMETRY PREVIEW - FIELD OUTLINES ONLY - NOT SIGNED')
                for field in fields:
                    if field['page'] != number:
                        continue
                    x, y, width, height = signwell_rect_to_pdf(field)
                    canvas.setStrokeColorRGB(.1, .4, .7)
                    canvas.setLineWidth(.4)
                    canvas.rect(x, y, width, height)
                canvas.save()
                writer.add_page(page)
                writer.pages[-1].merge_page(PdfReader(BytesIO(packet.getvalue())).pages[0])
            target = args.output / f'txr1508-{role}-{"long" if long else "standard"}.pdf'
            with target.open('wb') as stream:
                writer.write(stream)
            print(f'{target}: {len(reader.pages)} pages, {len(fields)} acknowledgement fields')
    assert args.source.read_bytes() == source, 'Source changed during read-only QA'


if __name__ == '__main__':
    main()

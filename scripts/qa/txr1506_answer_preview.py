"""Private synthetic notice previews, with no network or signing activity."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_1506 import render_txr_1506, build_signwell_fields_txr1506
from lib.txr_source_imprint import SOURCE_IMPRINTS
from scripts.render_txr_signwell_map_review import signwell_rect_to_pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_IMPRINTS['TXR-1506'][0]:
        raise ValueError('Use the reviewed 06-15-26 TXR-1506 blank source')
    args.output.mkdir(parents=True, exist_ok=True)
    for role in ('associate', 'broker'):
        for long in (False, True):
            names = ['José Review Consumer', 'Ana Review Consumer'][:2 if role == 'associate' else 1]
            data = {'client_names': names, 'signer_plan': 'consumers_and_' + role,
                    'additional_notice': 'Ask the broker about the property before signing. ' * 4,
                    '_for_signing': True}
            broker = {'name': 'Review Brokerage'}
            if long:
                data['client_names'] = [(name + ' FamilyName ' * 13).strip() for name in names]
                data['additional_notice'] = ('Please review the property information and raise any questions. ' * 15).strip()
                broker['name'] = 'Review Brokerage ' + 'Regional Office ' * 10
            reader = PdfReader(BytesIO(render_txr_1506(source, data, broker)))
            fields = build_signwell_fields_txr1506(data, client_count=len(names), page_count=len(reader.pages))[0]
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
            target = args.output / f'txr1506-{role}-{"long" if long else "standard"}.pdf'
            with target.open('wb') as stream:
                writer.write(stream)
            print(f'{target}: {len(reader.pages)} pages, {len(fields)} fields')
    assert args.source.read_bytes() == source, 'Source changed during read-only QA'


if __name__ == '__main__':
    main()

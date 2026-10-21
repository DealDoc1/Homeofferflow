"""Offline fixed lease specimen. No credentials, network access or sends."""
import argparse
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib import lease_listing_signing_qa as qa
from lib.pdf_text import draw_text


def prepare(primary, rental_sources, output):
    sources = {'TXR-1102': primary.read_bytes(),
        'TXR-2008': (rental_sources / 'TXR-2008-2003-10-14.pdf').read_bytes(),
        'TXR-2015': (rental_sources / 'TXR-2015-2025-09-01.pdf').read_bytes()}
    packet, fields, cases = qa.build_packet(sources)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'QA_ONLY_ordinary_lease_unsigned.pdf').write_bytes(packet)
    guide = BytesIO()
    canvas = Canvas(guide, pagesize=(612, 792))
    reader = PdfReader(BytesIO(packet))
    for page in range(1, len(reader.pages) + 1):
        canvas.saveState(); canvas.setFillAlpha(.08); canvas.setFillColorRGB(.8, 0, 0)
        canvas.translate(306, 396); canvas.rotate(38); canvas.setFont('Helvetica-Bold', 30)
        canvas.drawCentredString(0, 0, 'FICTIONAL QA - NOT FOR USE'); canvas.restoreState()
        for field in (f for f in fields[0] if f['page'] == page):
            x, y = field['x'] * .75, 792 - (field['y'] + field['height']) * .75
            canvas.setStrokeColorRGB(.15, .35, .8); canvas.setLineWidth(.4)
            canvas.rect(x, y, field['width'] * .75, field['height'] * .75)
            text = ('10/20/2026' if field['type'] == 'date' else 'QA' if field['type'] == 'initials'
                    else 'X' if field['type'] == 'checkbox' else 'Fictional QA explanation'
                    if field['type'] == 'text' else 'QA ' + field['recipient_id'] + ' signature')
            draw_text(canvas, text, x + 2, y + 3, 7)
        canvas.showPage()
    canvas.save()
    overlay = PdfReader(BytesIO(guide.getvalue())); writer = PdfWriter()
    for index, page in enumerate(reader.pages):
        writer.add_page(page); writer.pages[index].merge_page(overlay.pages[index])
    with (output / 'QA_ONLY_ordinary_lease_field_guide.pdf').open('wb') as stream:
        writer.write(stream)
    groups, rules = qa.completion_controls()
    report = {'layout_sha256': qa.layout_fingerprint(packet, fields), 'cases': cases,
        'fields': fields, 'checkbox_groups': groups, 'conditional_rules': rules,
        'provider_sends': 0, 'status': 'offline specimen; not provider-completed QA'}
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('layout_sha256', 'cases', 'provider_sends', 'status')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--primary', type=Path, required=True)
    parser.add_argument('--rental-sources', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.primary, args.rental_sources, args.output)

"""Local actual-source composition/placement proof; never contacts a service."""
import argparse
from contextlib import redirect_stdout
from io import BytesIO, StringIO
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
import pypdfium2 as pdfium
from reportlab.pdfgen.canvas import Canvas

from lib import production_adapter as adapter
from lib.purchase_disclosure_execution import append_execution, prepare_execution
from tests.test_controlled_launch import configure_local_forms, minimal_offer
from tests.test_purchase_disclosure_execution import USER, fixture


def prepare(source_dir, output_dir):
    main = (source_dir / 'seller_disclosure_notice_55-1.pdf').read_bytes()
    water = (source_dir / 'seller_water_disclosure_61-0.pdf').read_bytes()
    configure_local_forms()
    output_dir.mkdir(parents=True, exist_ok=True)
    for label, options in [('ordinary', {}),
                           ('four-parties-water-unicode', {'buyers': 2, 'sellers': 2, 'water': True, 'long': True})]:
        record, draft, links = fixture(**options)
        plan = prepare_execution(record, draft, links, user_id=USER, source_pdf=main,
            water_pdf=water if options.get('water') else None)
        with redirect_stdout(StringIO()):
            purchase = adapter.fill_and_merge_20_19(minimal_offer(**record['offer_data']))
        packet, fields = append_execution(purchase, plan)
        prefix = len(PdfReader(BytesIO(purchase)).pages)
        before, after = pdfium.PdfDocument(plan.pdf), pdfium.PdfDocument(packet)
        # Preserve every actual disclosure/continuation page through composition.
        for index in range(len(before)):
            assert before[index].render(scale=1).to_pil().tobytes() == after[prefix + index].render(scale=1).to_pil().tobytes()
        marked = PdfWriter()
        for number, page in enumerate(PdfReader(BytesIO(packet)).pages, 1):
            on_page = [field for field in fields if field['page'] == number]
            if on_page:
                overlay = BytesIO(); canvas = Canvas(overlay, pagesize=(612, 792))
                for field in on_page:
                    x, y = field['x'] * .75, 792 - (field['y'] + field['height']) * .75
                    canvas.setStrokeColorRGB(.8, .05, .1); canvas.setFillColorRGB(.8, .05, .1)
                    canvas.rect(x, y, field['width'] * .75, field['height'] * .75)
                    canvas.setFont('Helvetica', 6)
                    canvas.drawString(x + 2, y + 2, f"QA ROLE {field['recipient_id']} {field['type']}")
                canvas.save(); page.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
            marked.add_page(page)
        marked.add_metadata({'/Title': 'FICTIONAL LOCAL QA - NOT SIGNED OR SENT'})
        path = output_dir / f'{label}-placement.pdf'
        with path.open('wb') as stream: marked.write(stream)
        rendered = pdfium.PdfDocument(path)
        pages = {prefix + 4, *(prefix + page for page in plan.continuation_pages)}
        if options.get('water'): pages.add(prefix + 6)
        for number in sorted(pages):
            rendered[number - 1].render(scale=1.3).to_pil().save(output_dir / f'{label}-page-{number}.png')
        summary = {'pages': len(rendered), 'fields': len(fields), 'prefixPages': prefix,
            'roles': [row['id'] for row in plan.recipients], 'allAppendedPixelsIdentical': True,
            'renderRevision': plan.binding['render_revision'], 'providerSent': False}
        (output_dir / f'{label}-summary.json').write_text(json.dumps(summary, indent=2))
        print(label, summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.source_dir, args.output_dir)

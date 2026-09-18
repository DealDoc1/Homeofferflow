"""Render offline appraisal packet specimens with clearly labelled field boxes."""
import argparse
from io import BytesIO
from pathlib import Path
import subprocess

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms
from tests.test_purchase_appraisal_layout import offer_sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_dir', type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure_local_forms()
    for choice, long in [('waiver', False), ('partialWaiver', False), ('additionalRight', True)]:
        offer = offer_sample(appraisalAddendum=choice, appraisalMinimum='475000',
            address='A' * 400 if long else '100 José 李 Street',
            hoa='yes', hoaDelivery='seller', hoaDeliveryDays='7', hoaName='Example HOA')
        packet = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(packet))
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        selected = sorted({f['page'] for f in fields if 'appraisal' in f['api_id']
                           or long and 'hoa_addendum' in f['api_id']})
        writer = PdfWriter()
        writer.append(reader, pages=[page - 1 for page in selected])
        for index, number in enumerate(selected):
            overlay = BytesIO()
            canvas = Canvas(overlay, pagesize=(612, 792))
            canvas.setFillColorRGB(0.1, 0.25, 0.8)
            canvas.setFont('Helvetica', 8)
            canvas.drawString(40, 780, f'LOCAL QA ONLY - packet page {number} - boxes are NOT signatures')
            for field in fields:
                if field['page'] != number:
                    continue
                x, y = field['x'] * .75, 792 - (field['y'] + field['height']) * .75
                width, height = field['width'] * .75, field['height'] * .75
                canvas.setStrokeColorRGB(0.1, 0.25, 0.8)
                canvas.rect(x, y, width, height)
                canvas.setFont('Helvetica', min(8, height * .65))
                canvas.drawString(x + 2, y + 3, f"Buyer {field['recipient_id']} {field['type']}")
            canvas.showPage()
            canvas.save()
            writer.pages[index].merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
        path = args.output_dir / (choice + '.pdf')
        with path.open('wb') as stream:
            writer.write(stream)
        subprocess.run(['pdftoppm', '-scale-to', '1300', '-png', str(path), str(path.with_suffix(''))], check=True)
        print(f'{choice}: reviewed packet pages {selected}; no provider or email activity')


if __name__ == '__main__':
    main()

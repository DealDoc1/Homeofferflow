"""Three synthetic changed-page specimens; never sends or alters a real PDF."""
import argparse
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms
from tests.test_purchase_contract_source_alignment import contact_offer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure_local_forms()
    cases = {
        "single": {},
        "two": {"buyer2": "QA Buyer Two", "buyer2Email": "second@example.com"},
        "unicode": {"agentName": "Élodie Hernández " * 65,
                    "agentBrokerage": "Élodie Hernández Residential Realty Group",
                    "agentEmail": "long" * 70 + "@example.com",
                    "buyer2": "QA Buyer Two", "buyer2Email": "second@example.com"},
    }
    for name, values in cases.items():
        offer = contact_offer(**values)
        packet = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        reader, writer = PdfReader(BytesIO(packet)), PdfWriter()
        for page_number in [8, 10, 11, *range(13, len(reader.pages) + 1)]:
            page = reader.pages[page_number - 1]
            overlay = BytesIO()
            canvas = Canvas(overlay, pagesize=(612, 792))
            canvas.setFont("Helvetica", 7)
            canvas.setFillColorRGB(.12, .32, .7)
            canvas.drawString(40, 781, "SOFTWARE QA ONLY - synthetic field boxes, not completed SignWell signatures")
            for field in fields:
                if field["page"] != page_number:
                    continue
                x, top, width, height = (field[k] * .75 for k in ("x", "y", "width", "height"))
                y = 792 - top - height
                canvas.setStrokeColorRGB(.12, .32, .7)
                canvas.rect(x, y, width, height, fill=0, stroke=1)
                canvas.setFont("Helvetica-Oblique", 7)
                value = "QA Signature" if field["type"] == "signature" else "10/11/2026" if field["type"] == "date" else "QA"
                canvas.drawString(x + 1, y + 1, value)
            canvas.save()
            page.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
            writer.add_page(page)
        output = args.output_dir / f"{name}.pdf"
        with output.open("wb") as stream:
            writer.write(stream)
        print(f"{name}: {len(reader.pages)} packet pages; {len(writer.pages)} changed pages; {len(fields)} signing fields")


if __name__ == "__main__":
    main()

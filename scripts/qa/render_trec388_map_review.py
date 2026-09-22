"""Render the TREC 38-8 Buyer signature/date rectangles for local visual QA."""

import argparse
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen.canvas import Canvas

from lib.trec_38_8 import build_signwell_fields_trec388, render_trec_38_8


SCALE = 72 / 96
COLORS = {
    "signature": Color(0.79, 0.18, 0.18),
    "date": Color(0.10, 0.55, 0.28),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = {
        "property_address": "QA ONLY - 1438 Whitaker Road, Van Alstyne, TX",
        "buyer_names": ["QA Buyer One", "QA Buyer Two"],
        "seller_names": ["QA Seller One", "QA Seller Two"],
        "termination_reasons": ["option_period", "other"],
        "other_termination_basis": "QA ONLY - Paragraph 22 and attached addendum.",
    }
    rendered = render_trec_38_8(args.source.read_bytes(), data)
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(612, 792))
    for field in build_signwell_fields_trec388(data)[0]:
        x = field["x"] * SCALE
        width = field["width"] * SCALE
        height = field["height"] * SCALE
        y = 792 - ((field["y"] + field["height"]) * SCALE)
        canvas.setStrokeColor(COLORS[field["type"]])
        canvas.setFillColor(COLORS[field["type"]])
        canvas.setLineWidth(1.35)
        canvas.rect(x, y, width, height, fill=0, stroke=1)
        canvas.setFont("Helvetica-Bold", 5)
        canvas.drawString(x + 1.5, y + height + 2, f"Buyer {field['recipient_id']} {field['type']}")
    canvas.save()
    packet.seek(0)
    writer = PdfWriter()
    writer.add_page(PdfReader(BytesIO(rendered)).pages[0])
    writer.pages[0].merge_page(PdfReader(packet).pages[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as target:
        writer.write(target)


if __name__ == "__main__":
    main()

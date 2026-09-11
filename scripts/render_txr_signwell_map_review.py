#!/usr/bin/env python3
"""Render review copies of TXR sources with their SignWell widgets overlaid.

This utility is deliberately local-only: it reads privately supplied source
PDFs and produces local review PDFs.  It never uploads a source, creates a
draft, or sends a signing request.  The coloured outlines are in SignWell's
96-DPI, top-origin coordinate system, converted onto the source's PDF page so
that a reviewer can see precisely where initials, signatures, and dates will
land before a new source revision is released.

Example:

    python scripts/render_txr_signwell_map_review.py \
      /path/to/private/forms /private/tmp/txr-map-review

The source directory must contain each supported TXR source PDF. Generated
output stays outside the repository by default.
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import sys

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.txr_1501 import build_signwell_fields_txr1501
from lib.txr_1506 import build_signwell_fields_txr1506
from lib.txr_1507 import build_signwell_fields_txr1507, render_txr_1507
from lib.txr_1508 import build_signwell_fields_txr1508
from lib.txr_1905 import build_signwell_fields_txr1905
from lib.txr_1914 import build_signwell_fields_txr1914
from lib.txr_1917 import build_signwell_fields_txr1917
from lib.txr_1919 import build_signwell_fields_txr1919
from lib.txr_1948 import build_signwell_fields_txr1948
from lib.txr_1953 import build_signwell_fields_txr1953
from lib.txr_1954 import build_signwell_fields_txr1954


PDF_WIDTH = 612
PDF_HEIGHT = 792
SIGNWELL_TO_PDF = 72 / 96
TYPE_COLORS = {
    "signature": Color(0.79, 0.18, 0.18),
    "initials": Color(0.08, 0.36, 0.78),
    "date": Color(0.10, 0.55, 0.28),
}


def signwell_rect_to_pdf(field: dict) -> tuple[float, float, float, float]:
    """Convert one SignWell rectangle to PDF coordinates on US Letter."""
    width = field["width"] * SIGNWELL_TO_PDF
    height = field["height"] * SIGNWELL_TO_PDF
    x = field["x"] * SIGNWELL_TO_PDF
    y = PDF_HEIGHT - ((field["y"] + field["height"]) * SIGNWELL_TO_PDF)
    return x, y, width, height


def _sample_data() -> dict[str, dict]:
    return {
        "TXR1501": {
            "client_names": ["Review Client One", "Review Client Two"],
            "signer_plan": "clients_and_associate",
        },
        "TXR1506": {"signer_plan": "consumers_and_associate"},
        "TXR1507": {
            "client_names": ["Review Client One", "Review Client Two"],
            "signer_plan": "clients_and_associate",
        },
        "TXR1508": {"signer_plan": "associate_and_clients"},
        **{
            code: {
                "buyer_names": ["Review Buyer One", "Review Buyer Two"],
                "seller_names": ["Review Seller One", "Review Seller Two"],
            }
            for code in ("TXR1905", "TXR1914", "TXR1917", "TXR1919", "TXR1948", "TXR1953", "TXR1954")
        },
    }


def txr1507_value_overlay_data() -> tuple[dict, dict, dict]:
    """Return non-production values for a complete short-form QA render.

    The ordinary map review intentionally leaves source values blank so it can
    review every supported form the same way.  TXR-1507 additionally draws
    decision X marks into its source before SignWell adds signatures.  This
    sample lets a reviewer see both layers together, without creating a draft
    or exposing a real transaction.
    """
    return (
        {
            "client_names": ["Review Client One", "Review Client Two"],
            "market_area": "Review market area, Texas",
            "term_start": "2026-01-01",
            "term_end": "2026-12-31",
            "service_level": "full_services",
            "showing_fee": "",
            "compensation": {
                "purchase_percentage": "3",
                "purchase_flat_fee": "",
                "lease_one_month_percentage": "",
                "lease_total_rents_percentage": "",
                "lease_flat_fee": "",
            },
            "intermediary": "authorized",
            "signer_plan": "clients_and_associate",
        },
        {"legal_name": "Review Brokerage", "license_number": "0000000"},
        {"name": "Review Associate", "license_number": "0000000"},
    )


def review_field_sets() -> dict[str, list[dict]]:
    """Return the complete two-client signer map for each reviewable source."""
    data = _sample_data()
    return {
        "TXR1501": build_signwell_fields_txr1501(data["TXR1501"], client_count=2)[0],
        "TXR1506": build_signwell_fields_txr1506(data["TXR1506"], client_count=2)[0],
        "TXR1507": build_signwell_fields_txr1507(data["TXR1507"], client_count=2)[0],
        "TXR1508": build_signwell_fields_txr1508(data["TXR1508"], client_count=2)[0],
        "TXR1905": build_signwell_fields_txr1905(data["TXR1905"])[0],
        "TXR1914": build_signwell_fields_txr1914(data["TXR1914"])[0],
        "TXR1917": build_signwell_fields_txr1917(data["TXR1917"])[0],
        "TXR1919": build_signwell_fields_txr1919(data["TXR1919"])[0],
        "TXR1948": build_signwell_fields_txr1948(data["TXR1948"])[0],
        "TXR1953": build_signwell_fields_txr1953(data["TXR1953"])[0],
        "TXR1954": build_signwell_fields_txr1954(data["TXR1954"])[0],
    }


def _overlay(page_number: int, fields: list[dict]) -> bytes:
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PDF_WIDTH, PDF_HEIGHT))
    for field in fields:
        if field["page"] != page_number:
            continue
        x, y, width, height = signwell_rect_to_pdf(field)
        color = TYPE_COLORS[field["type"]]
        canvas.setStrokeColor(color)
        canvas.setFillColor(color)
        canvas.setLineWidth(1.35)
        canvas.rect(x, y, width, height, fill=0, stroke=1)
        canvas.setFont("Helvetica-Bold", 4.8)
        canvas.drawString(x + 1.4, y + height + 1.4, field["type"][0].upper())
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_review(source_path: Path, output_path: Path, fields: list[dict], *, include_txr1507_values: bool = False) -> None:
    source_bytes = source_path.read_bytes()
    if include_txr1507_values:
        data, brokerage, associate = txr1507_value_overlay_data()
        source_bytes = render_txr_1507(source_bytes, data, brokerage, associate)
    source = PdfReader(BytesIO(source_bytes))
    writer = PdfWriter()
    for index, source_page in enumerate(source.pages, start=1):
        writer.add_page(source_page)
        page_fields = [field for field in fields if field["page"] == index]
        if page_fields:
            overlay = PdfReader(BytesIO(_overlay(index, page_fields)))
            writer.pages[-1].merge_page(overlay.pages[0])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as target:
        writer.write(target)


def run(source_dir: Path, output_dir: Path, *, include_txr1507_values: bool = False) -> list[Path]:
    outputs = []
    for code, fields in review_field_sets().items():
        source = source_dir / f"{code}.pdf"
        if not source.is_file():
            raise FileNotFoundError(f"Missing approved private source: {source}")
        output = output_dir / f"{code}_signwell_map_review.pdf"
        render_review(
            source,
            output,
            fields,
            include_txr1507_values=include_txr1507_values and code == "TXR1507",
        )
        outputs.append(output)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--include-txr1507-values",
        action="store_true",
        help="Add non-production TXR-1507 values and X marks beneath the signing-field outlines.",
    )
    args = parser.parse_args()
    print("Rendering local SignWell map-review copies; no documents will be sent.")
    for output in run(
        args.source_dir,
        args.output_dir,
        include_txr1507_values=args.include_txr1507_values,
    ):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

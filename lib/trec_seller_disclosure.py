"""QA-only field map for supplied TREC-55-1 and TREC-61-0 PDFs.

The source PDFs are non-fillable. This module records source-specific points and
can render an unsigned local preview for visual QA. It deliberately has no
SignWell integration and refuses production activation until the map is marked
verified.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
TREC_55_1_PAGE_COUNT = 4
TREC_61_0_PAGE_COUNT = 2
TREC_55_1_SOURCE_SHA256 = "65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a"
TREC_61_0_SOURCE_SHA256 = "91056ab6520af8cbef319986e03490f1bf6947817c3d3f563348f80f957f871f"

# Coordinates are PDF points with origin at bottom-left. These are initial
# source-specific anchors from the supplied 05-04-2026 PDFs. They are not
# production-approved until the rendered preview is reviewed page by page.
TREC_55_1_MAP = {
    "property_address": {"page": 1, "x": 185, "y": 674, "width": 390},
    "seller_occupancy_yes": {"page": 1, "x": 76, "y": 604},
    "seller_occupancy_no": {"page": 1, "x": 102, "y": 604},
    "seller_occupancy_duration": {"page": 1, "x": 492, "y": 596, "width": 100},
    "item_responses_page_1": {"page": 1, "y_start": 570, "row_height": 18},
    "repair_awareness_yes": {"page": 1, "x": 133, "y": 103},
    "repair_awareness_no": {"page": 1, "x": 167, "y": 103},
    "smoke_detectors_yes": {"page": 2, "x": 219, "y": 728},
    "smoke_detectors_no": {"page": 2, "x": 248, "y": 728},
    "smoke_detectors_unknown": {"page": 2, "x": 283, "y": 728},
    "condition_responses_page_2": {"page": 2, "y_start": 500, "row_height": 27},
    "condition_responses_page_2b": {"page": 2, "y_start": 360, "row_height": 27},
    "repair_condition_yes": {"page": 3, "x": 487, "y": 728},
    "repair_condition_no": {"page": 3, "x": 58, "y": 713},
    "flood_responses": {"page": 3, "y_start": 650, "row_height": 27},
    "flood_claim_yes": {"page": 3, "x": 208, "y": 190},
    "flood_claim_no": {"page": 3, "x": 258, "y": 190},
    "fema_yes": {"page": 3, "x": 145, "y": 119},
    "fema_no": {"page": 3, "x": 195, "y": 119},
    "other_disclosures_page_4": {"page": 4, "y_start": 690, "row_height": 28},
    "seller_signature_1": {"page": 4, "x": 45, "y": 177, "width": 235},
    "seller_date_1": {"page": 4, "x": 255, "y": 177, "width": 70},
    "seller_signature_2": {"page": 4, "x": 345, "y": 177, "width": 235},
    "seller_date_2": {"page": 4, "x": 550, "y": 177, "width": 45},
    "purchaser_signature_1": {"page": 4, "x": 45, "y": 92, "width": 235},
    "purchaser_date_1": {"page": 4, "x": 255, "y": 92, "width": 70},
    "purchaser_signature_2": {"page": 4, "x": 345, "y": 92, "width": 235},
    "purchaser_date_2": {"page": 4, "x": 550, "y": 92, "width": 45},
}

TREC_61_0_MAP = {
    "property_address_page_1": {"page": 1, "x": 220, "y": 634, "width": 350},
    "groundwater_district_yes": {"page": 1, "x": 408, "y": 258},
    "groundwater_district_no": {"page": 1, "x": 453, "y": 258},
    "groundwater_district_unknown": {"page": 1, "x": 497, "y": 258},
    "water_well_yes": {"page": 1, "x": 383, "y": 222},
    "water_well_no": {"page": 1, "x": 427, "y": 222},
    "well_owned_seller": {"page": 1, "x": 48, "y": 126},
    "well_other_party": {"page": 1, "x": 48, "y": 82},
    "seller_signature_1": {"page": 2, "x": 42, "y": 144, "width": 235},
    "seller_date_1": {"page": 2, "x": 255, "y": 144, "width": 70},
    "seller_signature_2": {"page": 2, "x": 345, "y": 144, "width": 235},
    "seller_date_2": {"page": 2, "x": 550, "y": 144, "width": 45},
    "buyer_signature_1": {"page": 2, "x": 42, "y": 98, "width": 235},
    "buyer_date_1": {"page": 2, "x": 255, "y": 98, "width": 70},
    "buyer_signature_2": {"page": 2, "x": 345, "y": 98, "width": 235},
    "buyer_date_2": {"page": 2, "x": 550, "y": 98, "width": 45},
}

def source_contract(form_code: str) -> dict[str, Any]:
    if form_code == "TREC-55-1":
        return {"form_code": form_code, "page_count": TREC_55_1_PAGE_COUNT, "field_map": TREC_55_1_MAP, "source_sha256": TREC_55_1_SOURCE_SHA256, "activation_status": "pending_visual_qa"}
    if form_code == "TREC-61-0":
        return {"form_code": form_code, "page_count": TREC_61_0_PAGE_COUNT, "field_map": TREC_61_0_MAP, "source_sha256": TREC_61_0_SOURCE_SHA256, "activation_status": "pending_visual_qa"}
    raise ValueError("Unsupported seller disclosure form.")

def validate_source_bytes(form_code: str, source_pdf_bytes: bytes) -> None:
    """Reject a private source unless its fingerprint matches the approved PDF."""
    expected = source_contract(form_code)["source_sha256"]
    actual = hashlib.sha256(source_pdf_bytes).hexdigest()
    if actual != expected:
        raise ValueError(f"{form_code} source fingerprint does not match the approved revision.")


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())

def _draw(c: Canvas, value: Any, x: float, y: float, *, size: float = 8) -> None:
    value = _clean(value)
    if value:
        c.setFont("Helvetica", size)
        c.drawString(x, y, value)

def _check(c: Canvas, x: float, y: float) -> None:
    c.setLineWidth(1.2)
    c.line(x, y, x + 6, y + 6)
    c.line(x + 6, y + 6, x + 13, y - 4)

def render_unsigned_preview(source_pdf_bytes: bytes, form_code: str, values: dict[str, Any], *, qa_mode: bool = False) -> bytes:
    """Render a local unsigned preview only; never creates a sendable packet."""
    if not qa_mode:
        raise ValueError("Unsigned seller-disclosure preview requires explicit qa_mode=True.")
    contract = source_contract(form_code)
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != contract["page_count"]:
        raise ValueError(f"{form_code} source must contain exactly {contract['page_count']} pages.")
    field_map = contract["field_map"]
    overlays = []
    for page_number in range(1, contract["page_count"] + 1):
        overlay_stream = BytesIO()
        canvas = Canvas(overlay_stream, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
        if form_code == "TREC-55-1" and page_number == 1:
            _draw(canvas, values.get("propertyAddress"), 185, 674, size=8)
            for key in ("seller_occupancy_yes", "seller_occupancy_no"):
                if values.get(key):
                    _check(canvas, field_map[key]["x"], field_map[key]["y"])
        if form_code == "TREC-55-1" and page_number == 3:
            _draw(canvas, values.get("repairDescription"), 330, 112, size=7)
        if form_code == "TREC-55-1" and page_number == 4:
            if values.get("sellerSignature1"):
                _draw(canvas, values["sellerSignature1"], 45, 177, size=8)
            if values.get("sellerDate1"):
                _draw(canvas, values["sellerDate1"], 255, 177, size=8)
        if form_code == "TREC-61-0" and page_number == 1:
            _draw(canvas, values.get("propertyAddress"), 220, 634, size=8)
            for key in ("groundwater_district_yes", "groundwater_district_no", "groundwater_district_unknown"):
                if values.get(key):
                    _check(canvas, field_map[key]["x"], field_map[key]["y"])
        canvas.save()
        overlay_stream.seek(0)
        overlays.append(PdfReader(overlay_stream).pages[0])
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        page.merge_page(overlays[index])
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()

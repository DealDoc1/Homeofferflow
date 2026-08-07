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
    "seller_signature_1": {"page": 4, "x": 45, "y": 205, "width": 235},
    "seller_date_1": {"page": 4, "x": 255, "y": 205, "width": 70},
    "seller_signature_2": {"page": 4, "x": 345, "y": 205, "width": 235},
    "seller_date_2": {"page": 4, "x": 550, "y": 205, "width": 45},
    "purchaser_signature_1": {"page": 4, "x": 45, "y": 115, "width": 235},
    "purchaser_date_1": {"page": 4, "x": 255, "y": 115, "width": 70},
    "purchaser_signature_2": {"page": 4, "x": 345, "y": 115, "width": 235},
    "purchaser_date_2": {"page": 4, "x": 550, "y": 115, "width": 45},
}

TREC_61_0_MAP = {
    "property_address_page_1": {"page": 1, "x": 220, "y": 634, "width": 350},
    "groundwater_district_yes": {"page": 1, "x": 408, "y": 258},
    "groundwater_district_no": {"page": 1, "x": 453, "y": 258},
    "groundwater_district_unknown": {"page": 1, "x": 497, "y": 258},
    "water_well_yes": {"page": 1, "x": 383, "y": 258},
    "water_well_no": {"page": 1, "x": 427, "y": 258},
    "well_owned_seller": {"page": 1, "x": 48, "y": 145},
    "well_other_party": {"page": 1, "x": 48, "y": 120},
    "water_other_property_yes": {"page": 2, "x": 281, "y": 698},
    "water_other_property_no": {"page": 2, "x": 322, "y": 698},
    "outside_groundwater_rights_yes": {"page": 2, "x": 410, "y": 625},
    "outside_groundwater_rights_no": {"page": 2, "x": 451, "y": 625},
    "rights_severed_yes": {"page": 2, "x": 72, "y": 545},
    "rights_severed_no": {"page": 2, "x": 112, "y": 545},
    "surface_water_right_yes": {"page": 2, "x": 428, "y": 485},
    "surface_water_right_no": {"page": 2, "x": 468, "y": 485},
    "pond_lake_tank_yes": {"page": 2, "x": 72, "y": 390},
    "pond_lake_tank_no": {"page": 2, "x": 112, "y": 390},
    "seller_signature_1": {"page": 2, "x": 42, "y": 178, "width": 235},
    "seller_date_1": {"page": 2, "x": 255, "y": 178, "width": 70},
    "seller_signature_2": {"page": 2, "x": 345, "y": 178, "width": 235},
    "seller_date_2": {"page": 2, "x": 550, "y": 178, "width": 45},
    "buyer_signature_1": {"page": 2, "x": 42, "y": 122, "width": 235},
    "buyer_date_1": {"page": 2, "x": 255, "y": 122, "width": 70},
    "buyer_signature_2": {"page": 2, "x": 345, "y": 122, "width": 235},
    "buyer_date_2": {"page": 2, "x": 550, "y": 122, "width": 45},
}

TREC_55_1_CONDITION_ROWS = (
    ("defect_interior_walls", 58, 500),
    ("defect_ceilings", 238, 500),
    ("defect_floors", 408, 500),
    ("defect_other_structural_components", 255, 405),
)

TREC_55_1_ITEM_ROWS = (
    ("range", 58, 570),
    ("oven", 211, 570),
    ("microwave", 391, 570),
    ("dishwasher", 58, 552),
    ("trash_compactor", 211, 552),
    ("disposal", 391, 552),
    ("washer_dryer_hookups", 58, 534),
    ("window_screens", 211, 534),
    ("rain_gutters", 391, 534),
    ("security_system", 58, 516),
    ("fire_detection_equipment", 211, 516),
    ("intercom_system", 391, 516),
    ("tv_antenna", 58, 426),
    ("cable_tv_wiring", 211, 426),
    ("satellite_dish", 391, 426),
)

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

def _response(c: Canvas, value: Any, x: float, y: float) -> None:
    value = _clean(value).upper()
    if value in {"Y", "N", "U"}:
        _draw(c, value, x, y, size=8)

def _check(c: Canvas, x: float, y: float) -> None:
    c.setLineWidth(1.2)
    c.line(x, y, x + 6, y + 6)
    c.line(x + 6, y + 6, x + 13, y - 4)

def render_unsigned_preview(source_pdf_bytes: bytes, form_code: str, values: dict[str, Any], *, qa_mode: bool = False) -> bytes:
    """Render a local unsigned preview only; never creates a sendable packet."""
    if not qa_mode:
        raise ValueError("Unsigned seller-disclosure preview requires explicit qa_mode=True.")
    contract = source_contract(form_code)
    validate_source_bytes(form_code, source_pdf_bytes)
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
            _draw(canvas, values.get("seller_occupancy_duration"), 492, 596, size=8)
            for key, x, y in TREC_55_1_ITEM_ROWS:
                _response(canvas, values.get(key), x, y)
        if form_code == "TREC-55-1" and page_number == 3:
            for key in ("repair_condition_yes", "repair_condition_no"):
                if values.get(key):
                    _check(canvas, field_map[key]["x"], field_map[key]["y"])
            _draw(canvas, values.get("repairDescription"), 330, 717, size=7)
        if form_code == "TREC-55-1" and page_number == 2:
            for key in ("smoke_detectors_yes", "smoke_detectors_no", "smoke_detectors_unknown"):
                if values.get(key):
                    _check(canvas, field_map[key]["x"], field_map[key]["y"])
            for key, x, y in TREC_55_1_CONDITION_ROWS:
                _response(canvas, values.get(key), x, y)
        if form_code == "TREC-55-1" and page_number == 4:
            for value_key, map_key in (
                ("sellerSignature1", "seller_signature_1"),
                ("sellerDate1", "seller_date_1"),
                ("sellerSignature2", "seller_signature_2"),
                ("sellerDate2", "seller_date_2"),
                ("purchaserSignature1", "purchaser_signature_1"),
                ("purchaserDate1", "purchaser_date_1"),
                ("purchaserSignature2", "purchaser_signature_2"),
                ("purchaserDate2", "purchaser_date_2"),
            ):
                if values.get(value_key):
                    anchor = field_map[map_key]
                    _draw(canvas, values[value_key], anchor["x"], anchor["y"], size=8)
        if form_code == "TREC-61-0" and page_number == 1:
            _draw(canvas, values.get("propertyAddress"), 220, 634, size=8)
            for key in (
                "groundwater_district_yes",
                "groundwater_district_no",
                "groundwater_district_unknown",
                "water_well_yes",
                "water_well_no",
                "well_owned_seller",
                "well_other_party",
            ):
                if values.get(key):
                    _check(canvas, field_map[key]["x"], field_map[key]["y"])
        if form_code == "TREC-61-0" and page_number == 2:
            for key in (
                "water_other_property_yes",
                "water_other_property_no",
                "outside_groundwater_rights_yes",
                "outside_groundwater_rights_no",
                "rights_severed_yes",
                "rights_severed_no",
                "surface_water_right_yes",
                "surface_water_right_no",
                "pond_lake_tank_yes",
                "pond_lake_tank_no",
            ):
                if values.get(key):
                    _check(canvas, field_map[key]["x"], field_map[key]["y"])
            for value_key, map_key in (
                ("sellerSignature1", "seller_signature_1"),
                ("sellerDate1", "seller_date_1"),
                ("sellerSignature2", "seller_signature_2"),
                ("sellerDate2", "seller_date_2"),
                ("buyerSignature1", "buyer_signature_1"),
                ("buyerDate1", "buyer_date_1"),
                ("buyerSignature2", "buyer_signature_2"),
                ("buyerDate2", "buyer_date_2"),
            ):
                if values.get(value_key):
                    anchor = field_map[map_key]
                    _draw(canvas, values[value_key], anchor["x"], anchor["y"], size=8)
        canvas.showPage()
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


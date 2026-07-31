"""Private TXR-1507 short-form draft renderer.

This module deliberately does not contain a Texas REALTORS form PDF.  The
caller must provide the exact, approved source revision fetched server-side
from the private brokerage form-source vault.  Coordinates are provisional
until each completed scenario passes rendered visual QA; this renderer is not
wired into signing until that gate is complete.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Iterable, List, Mapping, Tuple
import textwrap

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


FORM_CODE = "TXR-1507"
EXPECTED_PAGE_COUNT = 2
CHECK = "X"
DEFAULT_FONT = "Helvetica"
DEFAULT_FONT_SIZE = 8.5


class TXR1507RenderError(ValueError):
    """Raised when a draft cannot be safely rendered."""


def _text(value: Any, field: str, max_length: int = 300) -> str:
    value = " ".join(str(value or "").split())
    if not value:
        raise TXR1507RenderError(f"{field} is required.")
    if len(value) > max_length:
        raise TXR1507RenderError(f"{field} is too long.")
    return value


def _optional_text(value: Any, field: str, max_length: int = 300) -> str:
    value = " ".join(str(value or "").split())
    if len(value) > max_length:
        raise TXR1507RenderError(f"{field} is too long.")
    return value


def _source_guard(source_pdf: bytes, source_revision: str) -> PdfReader:
    if not isinstance(source_pdf, (bytes, bytearray)) or len(source_pdf) < 100:
        raise TXR1507RenderError("An approved private TXR-1507 source PDF is required.")
    revision = _text(source_revision, "Source revision", 80)
    if "1507" not in revision and "06-15-26" not in revision:
        raise TXR1507RenderError("The approved source revision is not recognized as TXR-1507.")
    reader = PdfReader(BytesIO(bytes(source_pdf)))
    if len(reader.pages) != EXPECTED_PAGE_COUNT:
        raise TXR1507RenderError("The approved TXR-1507 source must contain exactly two pages.")
    return reader


def _clients(data: Mapping[str, Any]) -> List[str]:
    values = data.get("client_names") or data.get("clientNames")
    if not isinstance(values, list) or not 1 <= len(values) <= 2:
        raise TXR1507RenderError("TXR-1507 requires one or two clients.")
    names = [_text(v, "Client name", 180) for v in values]
    if len({n.casefold() for n in names}) != len(names):
        raise TXR1507RenderError("Client names must be unique.")
    return names


def _date(value: Any, field: str) -> str:
    value = _text(value, field, 30)
    import re
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise TXR1507RenderError(f"{field} must use YYYY-MM-DD.")
    return value


def _money(value: Any, field: str) -> str:
    value = _optional_text(value, field, 30)
    if not value:
        return ""
    import re
    if not re.fullmatch(r"\$?\d{1,9}(?:\.\d{1,2})?", value):
        raise TXR1507RenderError(f"{field} must be a dollar amount.")
    return value.replace("$", "")


def _percent(value: Any, field: str) -> str:
    value = _optional_text(value, field, 20)
    if not value:
        return ""
    import re
    if not re.fullmatch(r"\d{1,3}(?:\.\d{1,3})?", value) or float(value) > 100:
        raise TXR1507RenderError(f"{field} must be a percentage.")
    return value


def normalize_txr_1507_data(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalize the persisted draft shape before any PDF overlay occurs."""
    clients = _clients(data)
    service_level = str(data.get("service_level") or data.get("serviceLevel") or "").strip()
    if service_level not in {"full_services", "showing_services"}:
        raise TXR1507RenderError("Choose Full Services or Showing Services.")
    intermediary = str(data.get("intermediary") or "").strip()
    if intermediary not in {"authorized", "not_authorized"}:
        raise TXR1507RenderError("Choose whether intermediary is authorized.")
    showing_fee = _money(data.get("showing_fee", data.get("showingFee")), "Showing-services fee")
    if service_level == "showing_services" and not showing_fee:
        raise TXR1507RenderError("Showing Services requires an execution fee.")

    purchase_percentage = _percent(data.get("purchase_percentage", data.get("purchasePercentage")), "Purchase percentage")
    purchase_flat_fee = _money(data.get("purchase_flat_fee", data.get("purchaseFlatFee")), "Purchase flat fee")
    lease_one_month_percentage = _percent(data.get("lease_one_month_percentage", data.get("leaseOneMonthPercentage")), "Lease one-month percentage")
    lease_total_rents_percentage = _percent(data.get("lease_total_rents_percentage", data.get("leaseTotalRentsPercentage")), "Lease total-rents percentage")
    lease_flat_fee = _money(data.get("lease_flat_fee", data.get("leaseFlatFee")), "Lease flat fee")
    if not any((purchase_percentage, purchase_flat_fee, lease_one_month_percentage, lease_total_rents_percentage, lease_flat_fee)):
        raise TXR1507RenderError("At least one compensation term is required.")

    return {
        "client_names": clients,
        "market_area": _text(data.get("market_area", data.get("marketArea")), "Market area", 800),
        "term_start": _date(data.get("term_start", data.get("termStart")), "Term start date"),
        "term_end": _date(data.get("term_end", data.get("termEnd")), "Term end date"),
        "service_level": service_level,
        "showing_fee": showing_fee,
        "purchase_percentage": purchase_percentage,
        "purchase_flat_fee": purchase_flat_fee,
        "lease_one_month_percentage": lease_one_month_percentage,
        "lease_total_rents_percentage": lease_total_rents_percentage,
        "lease_flat_fee": lease_flat_fee,
        "intermediary": intermediary,
    }


def _fmt_date(value: str) -> str:
    year, month, day = value.split("-")
    return f"{month}/{day}/{year}"


def _entry(x: float, y: float, value: Any, size: float = DEFAULT_FONT_SIZE) -> Tuple[float, float, str, float]:
    return (x, y, str(value), size)


def _check(x: float, y: float) -> Tuple[float, float, str, float]:
    return (x, y, CHECK, 10)


def overlay_entries(data: Mapping[str, Any], broker: Mapping[str, Any]) -> Dict[int, List[Tuple[float, float, str, float]]]:
    """Return the page-coordinate map; all coordinates are source-specific."""
    normalized = normalize_txr_1507_data(data)
    broker_name = _text(broker.get("broker_name") or broker.get("name"), "Broker name", 180)
    broker_license = _optional_text(broker.get("broker_license") or broker.get("license"), "Broker license", 40)
    associate_name = _optional_text(broker.get("associate_name") or broker.get("agent_name"), "Associate name", 180)
    associate_license = _optional_text(broker.get("associate_license") or broker.get("agent_license"), "Associate license", 40)
    clients = normalized["client_names"]
    client_line = " and ".join(clients)

    p1: List[Tuple[float, float, str, float]] = []
    # Paragraph 1; baseline coordinates are intentionally conservative and
    # must be visually confirmed against the authorized source revision.
    p1 += [_entry(280, 639, client_line), _entry(430, 639, broker_name)]
    market_lines = textwrap.wrap(normalized["market_area"], width=78)[:3]
    p1 += [_entry(92, 561 - (index * 12), line, 8) for index, line in enumerate(market_lines)]
    p1 += [_entry(240, 512, _fmt_date(normalized["term_start"]), 8), _entry(450, 512, _fmt_date(normalized["term_end"]), 8)]
    p1 += [_check(57, 457) if normalized["service_level"] == "full_services" else _check(57, 421)]
    if normalized["service_level"] == "showing_services":
        p1.append(_entry(500, 417, normalized["showing_fee"], 8))
    p1 += [
        _entry(215, 197, normalized["purchase_percentage"], 8),
        _entry(520, 197, normalized["purchase_flat_fee"], 8),
        _entry(225, 178, normalized["lease_one_month_percentage"], 8),
        _entry(375, 178, normalized["lease_total_rents_percentage"], 8),
        _entry(520, 178, normalized["lease_flat_fee"], 8),
    ]

    p2: List[Tuple[float, float, str, float]] = []
    p2 += [_check(176, 632) if normalized["intermediary"] == "authorized" else _check(232, 632)]
    p2 += [_entry(92, 291, broker_name), _entry(453, 291, broker_license, 8)]
    p2 += [_entry(330, 291, clients[0], 8)]
    if associate_name:
        p2 += [_entry(92, 214, associate_name, 8), _entry(453, 214, associate_license, 8)]
    # Printed names only are appropriate for a draft. Signature/date and
    # initials are deliberately left blank until the signer plan is approved.
    if len(clients) > 1:
        p2.append(_entry(330, 214, clients[1], 8))
    return {0: p1, 1: p2}


def _make_overlay(entries: Iterable[Tuple[float, float, str, float]], width: float, height: float) -> bytes:
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=(width, height))
    c.setFillColorRGB(0, 0, 0)
    for x, y, value, size in entries:
        if not value:
            continue
        c.setFont("Helvetica-Bold" if value == CHECK else DEFAULT_FONT, size)
        c.drawString(x + (1 if value == CHECK else 0), y + (1 if value == CHECK else 0), value)
    c.save()
    return out.getvalue()


def render_txr_1507_draft(source_pdf: bytes, source_revision: str, data: Mapping[str, Any], broker: Mapping[str, Any]) -> bytes:
    """Overlay a validated draft onto an approved private source PDF."""
    reader = _source_guard(source_pdf, source_revision)
    entries = overlay_entries(data, broker)
    writer = PdfWriter()
    for index, page in enumerate(reader.pages):
        writer.add_page(page)
        page_entries = entries.get(index, [])
        if page_entries:
            overlay = PdfReader(BytesIO(_make_overlay(page_entries, float(page.mediabox.width), float(page.mediabox.height))))
            writer.pages[index].merge_page(overlay.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()

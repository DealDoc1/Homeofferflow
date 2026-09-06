"""Texas buyer/tenant representation agreement packet utilities.

The short-form agreement is intentionally kept separate from offer generation.
Agents provide the commercial terms through a small interview, then may review
the finished agreement before requesting the client and broker signatures.
"""

import base64
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SHORT_FORM = ROOT / "buyer_tenant_representation_short_form_1507.pdf"
CHECK = "X"


def _text(value, limit=240):
    return str(value or "").strip()[:limit]


def _choice(value, choices, default):
    return value if value in choices else default


def _overlay(width, height, entries):
    output = BytesIO()
    page = canvas.Canvas(output, pagesize=(width, height))
    page.setFont("Helvetica", 8)
    for entry in entries:
        x, y, value, *rest = entry
        if not value:
            continue
        size = rest[0] if rest else 8
        page.setFont("Helvetica", size)
        page.drawString(x, y, str(value))
    page.save()
    output.seek(0)
    return PdfReader(output).pages[0]


def build_short_form(data):
    """Return a filled TXR 1507 short-form agreement as PDF bytes.

    This function deliberately fills only explicit interview values. It does not
    invent compensation, dates, market areas, or intermediary authorization.
    """
    if not SHORT_FORM.is_file():
        raise FileNotFoundError("Buyer/tenant representation short-form source is unavailable")

    client = _text(data.get("clientName"), 120)
    broker = _text(data.get("brokerName"), 120)
    market_area = _text(data.get("marketArea"), 300)
    start_date = _text(data.get("startDate"), 30)
    end_date = _text(data.get("endDate"), 30)
    service_level = _choice(data.get("serviceLevel"), {"full", "showing"}, "full")
    showing_fee = _text(data.get("showingFee"), 30)
    purchase_kind = _choice(data.get("purchaseCompType"), {"percent", "flat"}, "percent")
    purchase_value = _text(data.get("purchaseCompValue"), 30)
    lease_kind = _choice(data.get("leaseCompType"), {"month_percent", "rent_percent", "flat"}, "month_percent")
    lease_value = _text(data.get("leaseCompValue"), 30)
    intermediary = _choice(data.get("intermediaryAuthorized"), {"yes", "no"}, "no")
    broker_license = _text(data.get("brokerLicense"), 40)
    associate = _text(data.get("associateName"), 120)
    associate_license = _text(data.get("associateLicense"), 40)

    reader = PdfReader(str(SHORT_FORM))
    writer = PdfWriter()

    page1 = [
        (55, 633, client), (315, 633, broker),
        (55, 558, market_area[:85], 8),
        (55, 542, market_area[85:170], 8),
        (215, 522, start_date), (430, 522, end_date),
        (56, 462, CHECK if service_level == "full" else "", 10),
        (56, 430, CHECK if service_level == "showing" else "", 10),
        (340, 421, showing_fee if service_level == "showing" else ""),
        (172, 198, purchase_value if purchase_kind == "percent" else ""),
        (392, 198, purchase_value if purchase_kind == "flat" else ""),
        (170, 177, lease_value if lease_kind == "month_percent" else ""),
        (315, 177, lease_value if lease_kind == "rent_percent" else ""),
        (392, 160, lease_value if lease_kind == "flat" else ""),
    ]
    page2 = [
        (250, 752, client),
        (152, 640, CHECK if intermediary == "yes" else "", 10),
        (232, 640, CHECK if intermediary == "no" else "", 10),
        (55, 260, broker), (250, 260, broker_license),
        (55, 183, associate), (250, 183, associate_license),
        (325, 260, client), (325, 183, _text(data.get("clientTwoName"), 120)),
    ]

    for index, source_page in enumerate(reader.pages):
        overlay = _overlay(float(source_page.mediabox.width), float(source_page.mediabox.height), page1 if index == 0 else page2)
        source_page.merge_page(overlay)
        writer.add_page(source_page)

    result = BytesIO()
    writer.write(result)
    return result.getvalue()


def build_short_form_signwell_fields(data):
    """Return SignWell field definitions for client and broker signatures."""
    fields = [
        {"api_id": "client_signature", "type": "signature", "page": 2, "x": 325, "y": 505, "width": 180, "height": 24, "recipient_id": "1"},
        {"api_id": "client_sign_date", "type": "date_signed", "page": 2, "x": 535, "y": 505, "width": 55, "height": 18, "recipient_id": "1", "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        {"api_id": "broker_signature", "type": "signature", "page": 2, "x": 55, "y": 505, "width": 180, "height": 24, "recipient_id": "2"},
        {"api_id": "broker_sign_date", "type": "date_signed", "page": 2, "x": 260, "y": 505, "width": 55, "height": 18, "recipient_id": "2", "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if _text(data.get("clientTwoEmail")):
        fields.extend([
            {"api_id": "client_two_signature", "type": "signature", "page": 2, "x": 325, "y": 588, "width": 180, "height": 24, "recipient_id": "3"},
            {"api_id": "client_two_sign_date", "type": "date_signed", "page": 2, "x": 535, "y": 588, "width": 55, "height": 18, "recipient_id": "3", "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    return [fields]


def build_short_form_signwell_payload(data, pdf_bytes, test_mode=False):
    """Build, but do not transmit, the SignWell request for this agreement."""
    client_email = _text(data.get("clientEmail"), 254)
    broker_email = _text(data.get("brokerEmail"), 254)
    if not client_email or not broker_email:
        raise ValueError("Client and broker email are required for a signature request")

    client_name = _text(data.get("clientName"), 120) or "Client"
    broker_name = _text(data.get("brokerName"), 120) or "Broker"
    recipients = [
        {"id": "1", "name": client_name, "email": client_email},
        {"id": "2", "name": broker_name, "email": broker_email},
    ]
    client_two_email = _text(data.get("clientTwoEmail"), 254)
    if client_two_email:
        recipients.append({
            "id": "3",
            "name": _text(data.get("clientTwoName"), 120) or "Second Client",
            "email": client_two_email,
        })

    safe_client = "".join(ch if ch.isalnum() else "_" for ch in client_name).strip("_") or "client"
    return {
        "test_mode": bool(test_mode),
        "draft": False,
        "reminders": True,
        "apply_signing_order": False,
        "embedded_signing": False,
        "with_signature_page": False,
        "custom_requester_name": "HomeOfferFlow",
        "name": f"HomeOfferFlow Representation Agreement — {client_name}",
        "subject": f"Review and sign your representation agreement — {broker_name}",
        "message": "Please review the agreement carefully before signing. Contact your broker or agent with questions about the agreement.",
        "recipients": recipients,
        "files": [{
            "name": f"HomeOfferFlow_Representation_Agreement_{safe_client}.pdf",
            "file_base64": base64.b64encode(pdf_bytes).decode("ascii"),
        }],
        "fields": build_short_form_signwell_fields(data),
        "metadata": {
            "source": "HomeOfferFlow",
            "agreement_type": "TXR-1507-short-form",
            "client_email": client_email,
            "test_mode": str(bool(test_mode)).lower(),
        },
    }


def send_short_form_signature_request(data, pdf_bytes, api_key, test_mode=False):
    """Transmit a reviewed agreement to SignWell and return only safe result data."""
    if not api_key:
        raise ValueError("SignWell is not configured")
    payload = build_short_form_signwell_payload(data, pdf_bytes, test_mode=test_mode)
    response = httpx.post(
        "https://www.signwell.com/api/v1/documents",
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=45,
    )
    if response.status_code not in {200, 201, 202}:
        raise RuntimeError("SignWell could not create the signature request")
    data = response.json()
    return {
        "ok": True,
        "document_id": data.get("id") or data.get("document_id"),
        "test_mode": bool(test_mode),
    }

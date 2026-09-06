"""TXR 1501 long-form buyer/tenant representation agreement packet utilities.

This is intentionally a separate, advanced path.  The standard short form
remains the default interview for ordinary purchase and lease representation.
"""

import base64
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
LONG_FORM = ROOT / "buyer_tenant_representation_long_form_1501.pdf"
CHECK = "X"


def _text(value, limit=240):
    return str(value or "").strip()[:limit]


def _choice(value, choices, default):
    return value if value in choices else default


def _overlay(width, height, entries):
    output = BytesIO()
    page = canvas.Canvas(output, pagesize=(width, height))
    for x, y, value, *rest in entries:
        if not value:
            continue
        page.setFont("Helvetica", rest[0] if rest else 8)
        page.drawString(x, y, str(value))
    # ReportLab does not emit a page when every optional value is blank.  The
    # source page still needs an overlay page so a partly completed interview
    # can safely produce a packet.
    page.showPage()
    page.save()
    output.seek(0)
    return PdfReader(output).pages[0]


def build_long_form(data):
    """Return a prefilled TXR 1501 long-form agreement.

    Values come only from the detailed interview; omitted advanced terms stay
    blank rather than being inferred by the application.
    """
    if not LONG_FORM.is_file():
        raise FileNotFoundError("Buyer/tenant representation long-form source is unavailable")

    client = _text(data.get("clientName"), 120)
    client_two = _text(data.get("clientTwoName"), 120)
    broker = _text(data.get("brokerName"), 120)
    associate = _text(data.get("associateName"), 120)
    purchase_kind = _choice(data.get("purchaseCompType"), {"percent", "flat"}, "percent")
    lease_kind = _choice(data.get("leaseCompType"), {"month_percent", "rent_percent", "flat"}, "month_percent")
    intermediary = _choice(data.get("intermediaryAuthorized"), {"yes", "no"}, "no")

    pages = {
        0: [
            (150, 614, client), (150, 600, client_two),
            (145, 586, _text(data.get("clientAddress"), 180)),
            (170, 573, _text(data.get("clientCityStateZip"), 120)),
            (140, 560, _text(data.get("clientPhone"), 40)), (360, 560, _text(data.get("clientTwoPhone"), 40)),
            (140, 547, _text(data.get("clientEmail"), 120)), (360, 547, _text(data.get("clientTwoEmail"), 120)),
            (150, 524, broker),
            (145, 500, _text(data.get("brokerAddress"), 180)),
            (170, 487, _text(data.get("brokerCityStateZip"), 120)),
            (140, 474, _text(data.get("brokerPhone"), 40)), (360, 474, _text(data.get("brokerTwoPhone"), 40)),
            (140, 461, _text(data.get("brokerEmail"), 120)), (360, 461, _text(data.get("brokerTwoEmail"), 120)),
            (80, 305, _text(data.get("marketArea"), 180), 8), (80, 292, _text(data.get("marketArea"), 360)[180:], 8),
            (250, 183, _text(data.get("startDate"), 30)), (465, 183, _text(data.get("endDate"), 30)),
        ],
        1: [
            (171, 477, _text(data.get("purchaseCompValue"), 30) if purchase_kind == "percent" else ""),
            (410, 477, _text(data.get("purchaseCompValue"), 30) if purchase_kind == "flat" else ""),
            (171, 455, _text(data.get("leaseCompValue"), 30) if lease_kind == "month_percent" else ""),
            (342, 455, _text(data.get("leaseCompValue"), 30) if lease_kind == "rent_percent" else ""),
            (352, 443, _text(data.get("leaseCompValue"), 30) if lease_kind == "flat" else ""),
            (185, 421, _text(data.get("retainerAmount"), 30)),
            (263, 421, CHECK if _choice(data.get("retainerApplied"), {"yes", "no"}, "no") == "yes" else ""),
            (321, 421, CHECK if _choice(data.get("retainerApplied"), {"yes", "no"}, "no") == "no" and _text(data.get("retainerAmount")) else ""),
        ],
        2: [
            (108, 494, _text(data.get("protectionPeriodDays"), 15)),
            (374, 321, _text(data.get("paymentCounty"), 60)),
            (265, 176, _text(data.get("relocationBenefitProvider"), 180)),
        ],
        3: [
            (49, 716, CHECK if intermediary == "yes" else "", 10),
            (49, 460, CHECK if intermediary == "no" else "", 10),
        ],
        4: [
            (64, 248, _text(data.get("specialProvisions"), 220), 8),
            (64, 235, _text(data.get("specialProvisions"), 440)[220:], 8),
            # The General Information and Notice to Consumers option is the
            # fourth addendum checkbox, not the heading above the list.
            (66, 294, CHECK if str(data.get("includeConsumerNotice") or "").lower() == "yes" else "", 10),
        ],
        5: [
            (55, 385, broker), (235, 385, _text(data.get("brokerLicense"), 40)),
            (320, 385, client), (320, 310, client_two),
            (55, 310, associate), (235, 310, _text(data.get("associateLicense"), 40)),
        ],
    }

    reader = PdfReader(str(LONG_FORM))
    writer = PdfWriter()
    for index, source_page in enumerate(reader.pages):
        writer.add_page(source_page)
        target_page = writer.pages[-1]
        target_page.merge_page(_overlay(float(target_page.mediabox.width), float(target_page.mediabox.height), pages.get(index, [])))
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


def build_long_form_signwell_fields(data):
    """Return the initials and signature fields for the detailed agreement."""
    fields = []
    for page in range(1, 6):
        fields.extend([
            {"api_id": f"broker_initials_{page}", "type": "initials", "page": page, "x": 322, "y": 50, "width": 55, "height": 16, "recipient_id": "2"},
            {"api_id": f"client_initials_{page}", "type": "initials", "page": page, "x": 401, "y": 50, "width": 55, "height": 16, "recipient_id": "1"},
        ])
        if _text(data.get("clientTwoEmail")):
            fields.append({"api_id": f"client_two_initials_{page}", "type": "initials", "page": page, "x": 467, "y": 50, "width": 55, "height": 16, "recipient_id": "3"})

    fields.extend([
        {"api_id": "broker_signature", "type": "signature", "page": 6, "x": 55, "y": 350, "width": 180, "height": 24, "recipient_id": "2"},
        {"api_id": "broker_sign_date", "type": "date_signed", "page": 6, "x": 250, "y": 350, "width": 55, "height": 18, "recipient_id": "2", "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        {"api_id": "client_signature", "type": "signature", "page": 6, "x": 320, "y": 350, "width": 180, "height": 24, "recipient_id": "1"},
        {"api_id": "client_sign_date", "type": "date_signed", "page": 6, "x": 535, "y": 350, "width": 55, "height": 18, "recipient_id": "1", "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ])
    if _text(data.get("clientTwoEmail")):
        fields.extend([
            {"api_id": "client_two_signature", "type": "signature", "page": 6, "x": 320, "y": 270, "width": 180, "height": 24, "recipient_id": "3"},
            {"api_id": "client_two_sign_date", "type": "date_signed", "page": 6, "x": 535, "y": 270, "width": 55, "height": 18, "recipient_id": "3", "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    return [fields]


def build_long_form_signwell_payload(data, pdf_bytes, test_mode=False):
    """Build, but do not transmit, the SignWell request for the detailed agreement."""
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
        recipients.append({"id": "3", "name": _text(data.get("clientTwoName"), 120) or "Second Client", "email": client_two_email})

    safe_client = "".join(ch if ch.isalnum() else "_" for ch in client_name).strip("_") or "client"
    return {
        "test_mode": bool(test_mode), "draft": False, "reminders": True,
        "apply_signing_order": False, "embedded_signing": False, "with_signature_page": False,
        "custom_requester_name": "HomeOfferFlow",
        "name": f"HomeOfferFlow Detailed Representation Agreement — {client_name}",
        "subject": f"Review and sign your representation agreement — {broker_name}",
        "message": "Please review the agreement carefully before signing. Contact your broker or agent with questions about the agreement.",
        "recipients": recipients,
        "files": [{"name": f"HomeOfferFlow_Detailed_Representation_Agreement_{safe_client}.pdf", "file_base64": base64.b64encode(pdf_bytes).decode("ascii")}],
        "fields": build_long_form_signwell_fields(data),
        "metadata": {"source": "HomeOfferFlow", "agreement_type": "TXR-1501-long-form", "client_email": client_email, "test_mode": str(bool(test_mode)).lower()},
    }


def send_long_form_signature_request(data, pdf_bytes, api_key, test_mode=False):
    """Transmit a reviewed detailed agreement to SignWell."""
    if not api_key:
        raise ValueError("SignWell is not configured")
    payload = build_long_form_signwell_payload(data, pdf_bytes, test_mode=test_mode)
    response = httpx.post(
        "https://www.signwell.com/api/v1/documents",
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=45,
    )
    if response.status_code not in {200, 201, 202}:
        raise RuntimeError("SignWell could not create the signature request")
    result = response.json()
    return {"ok": True, "document_id": result.get("id") or result.get("document_id"), "test_mode": bool(test_mode)}

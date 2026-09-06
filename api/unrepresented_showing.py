"""TXR 1508 unrepresented-customer showing-form packet utilities.

The form is used for a single neutral property showing.  It deliberately does
not create representation, compensation, or a broader service relationship.
"""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SHOWING_FORM = ROOT / "unrepresented_customer_showing_form_1508.pdf"
CHECK = "X"


def _text(value, limit=240):
    return str(value or "").strip()[:limit]


def _overlay(width, height, entries):
    output = BytesIO()
    page = canvas.Canvas(output, pagesize=(width, height))
    for x, y, value, size in entries:
        if value:
            page.setFont("Helvetica", size)
            page.drawString(x, y, str(value))
    page.save()
    output.seek(0)
    return PdfReader(output).pages[0]


def build_showing_form(data):
    """Return a prefilled TXR 1508 showing form.

    Initials and dates are intentionally left for the signature step.  The
    preparation step fills only the customer, property, and broker details
    gathered for the actual showing.
    """
    if not SHOWING_FORM.is_file():
        raise FileNotFoundError("Unrepresented customer showing-form source is unavailable")

    property_address = _text(data.get("propertyAddress"), 300)
    broker_name = _text(data.get("brokerName"), 120)
    broker_license = _text(data.get("brokerLicense"), 40)
    associate_name = _text(data.get("associateName"), 120)
    associate_license = _text(data.get("associateLicense"), 40)
    customer_name = _text(data.get("customerName"), 120)
    customer_two_name = _text(data.get("customerTwoName"), 120)
    customer_has_representation = str(data.get("customerHasRepresentation") or "").lower() == "yes"
    customer_two_has_representation = str(data.get("customerTwoHasRepresentation") or "").lower() == "yes"

    reader = PdfReader(str(SHOWING_FORM))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    page = writer.pages[0]
    entries = [
        (101, 658, property_address, 8),
        (188, 323, broker_name, 8), (490, 323, broker_license, 8),
        (188, 304, associate_name, 8), (490, 304, associate_license, 8),
        (155, 242, customer_name, 8),
        (155, 199, customer_two_name, 8),
        # Center the mark inside the source form's small representation boxes.
        (301, 216, CHECK if customer_has_representation else "", 10),
        (301, 173, CHECK if customer_two_has_representation else "", 10),
    ]
    page.merge_page(_overlay(float(page.mediabox.width), float(page.mediabox.height), entries))
    result = BytesIO()
    writer.write(result)
    return result.getvalue()

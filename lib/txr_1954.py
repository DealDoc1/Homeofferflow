"""Private-source renderer for TXR-1954 fixture-lease review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_addenda_layout import SourceAnswers, draw_entries
from lib.txr_source_imprint import remove_known_source_imprint


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = "txr-1954-2026-09-18-neutral-source-v4"


def answer_layout(data):
    # Text stays above measured rules in the supplied 11-07-2022 edition.
    answers = SourceAnswers(data, "TXR-1954 CONTINUATION EXHIBIT", 1)
    answers.put(data.get("property_address"), [(243, 664, 313)], "Property address")
    if "other" in (data.get("leased_fixture_types") or []):
        answers.put(data.get("leased_fixtures_other"), [(476, 594, 99)], "Other Leased Fixture")
    if "other" in (data.get("assumed_fixture_leases") or []):
        answers.put(data.get("assumed_fixture_leases_other"), [(100, 533, 237)], "Other Assumed Fixture Lease")
    answers.put(data.get("buyer_first_cost"), [(481, 533, 94)], "Buyer first cost")
    if data.get("delivery_choice") == "oral_notice":
        answers.put(data.get("oral_fixture_lease_notice"), [(456, 335, 117), (85, 324.5, 490)],
                    "Oral Fixture Lease Notice")
    answers.names(1, (195, 118), [("Buyer", 49, 249), ("Seller", 315, 240)])
    return answers


def _mark(canvas, x, y):
    # Printed checkbox centers from the 11-07-2022 source edition.
    canvas.setFont("Helvetica-Bold", 6)
    canvas.drawCentredString(x, y - 2.15, "X")


def _marks(canvas, values, positions):
    for value, position in zip(values, positions):
        if value:
            _mark(canvas, *position)


def render_txr_1954(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1954 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1954 source must contain exactly one page.")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    answers = answer_layout(data)
    draw_entries(canvas, answers.pages[1])

    leased = set(data.get("leased_fixture_types") or [])
    _marks(canvas, ["solar_panels" in leased, "propane_tanks" in leased, "water_softener" in leased, "security_system" in leased, "other" in leased],
           [(81.46, 595.98), (165.82, 595.98), (263.56, 595.98), (362.50, 595.98), (465.58, 595.98)])

    assumed = set(data.get("assumed_fixture_leases") or [])
    _marks(canvas, ["solar_panels" in assumed, "propane_tanks" in assumed, "water_softener" in assumed, "security_system" in assumed],
           [(89.44, 549.48), (201.76, 549.48), (325.78, 549.48), (456.10, 549.48)])
    if "other" in assumed:
        _mark(canvas, 89.44, 535.08)

    if data.get("removal_choice") == "will":
        _mark(canvas, 210.82, 477.84)
    elif data.get("removal_choice") == "will_not":
        _mark(canvas, 256.54, 477.84)

    delivery = data.get("delivery_choice")
    if delivery == "received":
        _mark(canvas, 53.68, 409.92)
    elif delivery == "not_received":
        _mark(canvas, 53.68, 395.46)
    elif delivery == "oral_notice":
        _mark(canvas, 53.56, 348.96)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    remove_known_source_imprint(writer, source_pdf_bytes, 'TXR-1954')
    writer.pages[0].merge_page(overlay.pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1954(data, *, client_count=None):
    """Return source-specific Buyer and Seller signature fields.

    TXR-1954 is signed by the transaction parties only. Recipient ids follow
    the stored Buyer-then-Seller name order used by the authenticated signing
    route, so no brokerage seat or agent signature is inferred.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1954 requires one or two Buyers and one or two Sellers.")

    fields = [
        # Keep each party signature on its source rule, above the printed
        # Buyer/Seller caption. The second source row is lower than the old
        # map, which left its signer box visibly detached from the rule.
        {"api_id": "txr1954_buyer1_signature_p1", "type": "signature", "page": 1, "x": 64, "y": 774, "recipient_id": "1", "required": True, "width": 335, "height": 26},
        {"api_id": "txr1954_seller1_signature_p1", "type": "signature", "page": 1, "x": 418, "y": 774, "recipient_id": str(len(buyers) + 1), "required": True, "width": 324, "height": 26},
    ]
    if len(buyers) == 2:
        fields.append(
            {"api_id": "txr1954_buyer2_signature_p1", "type": "signature", "page": 1, "x": 64, "y": 876, "recipient_id": "2", "required": True, "width": 335, "height": 26}
        )
    if len(sellers) == 2:
        fields.append(
            {"api_id": "txr1954_seller2_signature_p1", "type": "signature", "page": 1, "x": 418, "y": 876, "recipient_id": str(len(buyers) + 2), "required": True, "width": 324, "height": 26}
        )
    fields.extend(answer_layout(data).continuation_fields(2, "txr1954"))
    return [fields]

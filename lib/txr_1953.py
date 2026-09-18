"""Private-source renderer for TXR-1953 residential-lease review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_addenda_layout import SourceAnswers, draw_entries
from lib.txr_source_imprint import remove_known_source_imprint


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = "txr-1953-2026-09-18-neutral-source-v4"


def answer_layout(data):
    # Text stays above measured rules in the supplied 11-07-2022 edition.
    answers = SourceAnswers(data, "TXR-1953 CONTINUATION EXHIBIT", 1)
    answers.put(data.get("property_address"), [(243, 687, 313)], "Property address")
    if data.get("lease_status") == "assignment":
        if data.get("delivery_choice") == "not_received":
            answers.put(data.get("delivery_days"), [(103, 489.5, 22)], "Termination period after receipt (days)")
        elif data.get("delivery_choice") == "oral_notice":
            answers.put(data.get("oral_lease_notice"), [(103, 458, 475)], "Oral Residential Lease Notice")
        answers.put(data.get("explanation"),
                    [(480, 318, 88), (85, 308, 483), (85, 298, 483), (85, 288, 483)],
                    "Residential Lease Explanation")
    answers.names(1, (174, 119), [("Buyer", 54, 226), ("Seller", 332, 222)])
    return answers


def _mark(canvas, x, y):
    # Coordinates are the printed checkbox centers, not text baselines.
    # A compact X stays inside the source box after SignWell completion.
    canvas.setFont("Helvetica-Bold", 6)
    canvas.drawCentredString(x, y - 2.15, "X")


def render_txr_1953(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1953 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1953 source must contain exactly one page.")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    answers = answer_layout(data)
    draw_entries(canvas, answers.pages[1])
    status = data.get("lease_status")
    if status == "termination":
        _mark(canvas, 34.77, 612.24)
    elif status == "assignment":
        _mark(canvas, 34.77, 557.70)
        delivery = data.get("delivery_choice")
        if delivery == "received":
            _mark(canvas, 75.27, 523.80)
        elif delivery == "not_received":
            _mark(canvas, 75.27, 512.16)
        elif delivery == "oral_notice":
            _mark(canvas, 75.27, 474.06)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    remove_known_source_imprint(writer, source_pdf_bytes, 'TXR-1953')
    writer.pages[0].merge_page(overlay.pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1953(data, *, client_count=None):
    """Return source-specific Buyer and Seller signature fields.

    TXR-1953 is a contract addendum signed by the named Buyers and Sellers;
    it does not add an agent or broker signer. SignWell uses a 96-DPI,
    top-origin letter-page coordinate space in the HomeOfferFlow integration.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1953 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1953_buyer1_signature_p1", "type": "signature", "page": 1, "x": 70, "y": 802, "recipient_id": "1", "required": True, "width": 306, "height": 26},
        {"api_id": "txr1953_seller1_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 802, "recipient_id": str(len(buyers) + 1), "required": True, "width": 302, "height": 26},
    ]
    if len(buyers) == 2:
        fields.append(
            {"api_id": "txr1953_buyer2_signature_p1", "type": "signature", "page": 1, "x": 70, "y": 875, "recipient_id": "2", "required": True, "width": 306, "height": 26}
        )
    if len(sellers) == 2:
        fields.append(
            {"api_id": "txr1953_seller2_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 875, "recipient_id": str(len(buyers) + 2), "required": True, "width": 302, "height": 26}
        )
    fields.extend(answer_layout(data).continuation_fields(2, "txr1953"))
    return [fields]

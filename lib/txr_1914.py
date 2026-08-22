"""Private-source renderer for TXR-1914 seller-financing review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, *, size=8):
    value = _clean(value)
    if value:
        canvas.setFont("Helvetica", size)
        canvas.drawString(x, y, value)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(x, y, "X")


def _page_one(data):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 240, 651, size=9)
    _draw(canvas, data.get("credit_days"), 132, 525)
    docs = set(data.get("credit_documents") or [])
    for key, x, y in (
        ("credit_report", 407, 526), ("employment", 488, 526),
        ("funds", 189, 503), ("financial_statement", 69, 503), ("other", 362, 503),
    ):
        if key in docs:
            _mark(canvas, x, y)
    if "other" in docs:
        _draw(canvas, data.get("credit_other"), 438, 497)
    _draw(canvas, data.get("note_amount"), 399, 350)
    _draw(canvas, data.get("interest_rate"), 230, 333)
    payment = data.get("payment") or {}
    if payment.get("plan") == "one_payment":
        _mark(canvas, 70, 249)
        _draw(canvas, payment.get("due_after_months"), 204, 243)
        timing = payment.get("interest_timing")
        for value, x in (("maturity", 211), ("monthly", 284), ("quarterly", 347)):
            if timing == value:
                _mark(canvas, x, 231)
    elif payment.get("plan") == "monthly_installments":
        _mark(canvas, 70, 219)
        _draw(canvas, payment.get("installment_amount"), 260, 219)
        _mark(canvas, 338 if payment.get("interest_style") == "including_interest" else 450, 219)
        _draw(canvas, payment.get("begins_after_months"), 290, 203)
        _draw(canvas, payment.get("payoff_after_months"), 227, 188)
    else:
        _mark(canvas, 70, 164)
        _draw(canvas, payment.get("interest_only_months"), 424, 164)
        _draw(canvas, payment.get("installment_amount"), 249, 148)
        _mark(canvas, 290 if payment.get("interest_style") == "including_interest" else 403, 148)
        _draw(canvas, payment.get("begins_after_months"), 244, 132)
        _draw(canvas, payment.get("payoff_after_months"), 228, 117)
    if data.get("property_transfer") == "consent_not_required":
        _mark(canvas, 84, 58)
    canvas.save()
    packet.seek(0)
    return packet.read()


def _page_two(data):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 238, 745, size=9)
    if data.get("property_transfer") == "consent_required":
        _mark(canvas, 72, 693)
    if data.get("casualty_insurance") == "required":
        _mark(canvas, 414, 568)
    else:
        _mark(canvas, 465, 568)
    escrow = data.get("escrow") or {}
    if escrow.get("choice") == "not_required":
        _mark(canvas, 78, 517)
    else:
        _mark(canvas, 77, 477)
        _mark(canvas, 105 if escrow.get("third_party_servicer") == "will" else 167, 374)
        _mark(canvas, 411 if escrow.get("cost_paid_by") == "buyer" else 465, 374)
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    _draw(canvas, buyers[0] if buyers else "", 58, 258, size=9)
    _draw(canvas, sellers[0] if sellers else "", 332, 258, size=9)
    if len(buyers) > 1:
        _draw(canvas, buyers[1], 58, 162, size=9)
    if len(sellers) > 1:
        _draw(canvas, sellers[1], 332, 162, size=9)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1914(source_pdf_bytes, data):
    """Overlay review values without creating any signature fields or send path."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 2:
        raise ValueError("TXR-1914 source must contain exactly two pages.")
    overlays = [PdfReader(BytesIO(_page_one(data))), PdfReader(BytesIO(_page_two(data)))]
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        page.merge_page(overlays[index].pages[0])
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()

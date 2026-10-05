"""Official-source renderer and parallel Buyer/Seller signing map for TREC 39-11."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.txr_addenda_layout import SourceAnswers, draw_entries


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = "trec-39-11-2026-10-05-source-v1"

CHANGE_MARKS = {
    "sales_price": (39, 654),
    "repairs": (39, 608),
    "closing_date": (39, 528),
    "seller_expense": (39, 516),
    "settlement_expenses": (39, 500),
    "lender_repairs": (39, 458),
    "option_extension": (39, 433),
    "option_waiver": (39, 383),
    "buyer_approval_date": (39, 368),
    "other": (38, 342),
}


def _money(value):
    value = str(value or "").replace(",", "").strip()
    if not value:
        return ""
    try:
        return f"{Decimal(value):,.2f}"
    except InvalidOperation:
        return value


def _date_parts(value):
    value = str(value or "").strip()
    try:
        parsed = datetime.strptime(value, "%m/%d/%Y")
    except ValueError:
        return value, ""
    return f"{parsed.strftime('%B')} {parsed.day}", parsed.strftime("%y")


def answer_layout(data):
    """Map only agent-entered choices onto the official one-page source."""
    answers = SourceAnswers(data, "TREC 39-11 - Amendment Continuation", 1)
    answers.put(data.get("property_address"), [(126, 690, 358)], "Property address", size=9)
    changes = set(data.get("changes") or [])
    for change in changes:
        x, y = CHANGE_MARKS[change]
        answers.put("X", [(x, y, 11)], f"Amendment choice: {change}", size=10)

    if "sales_price" in changes:
        price = data.get("sales_price") or {}
        answers.put(_money(price.get("cash")), [(470, 642, 89)], "Cash portion", size=8)
        answers.put(_money(price.get("financing")), [(470, 630, 89)], "Financing portion", size=8)
        answers.put(_money(price.get("total")), [(470, 618, 89)], "Sales price", size=8)

    if "repairs" in changes:
        answers.put(
            data.get("repairs_text"),
            [(196, 574, 362), (69, 562, 487), (69, 550, 487), (69, 539, 487)],
            "Repairs and treatments",
            size=8,
        )

    if "closing_date" in changes:
        month_day, year = _date_parts(data.get("closing_date"))
        answers.put(month_day, [(347, 527, 148)], "Closing date", size=8)
        answers.put(year, [(519, 527, 36)], "Closing year", size=8)

    if "seller_expense" in changes:
        answers.put(_money(data.get("seller_expense")), [(415, 515, 97)], "Seller expense", size=8)

    if "settlement_expenses" in changes:
        expenses = data.get("settlement_expenses") or {}
        for party, y in (("seller", 486), ("buyer", 472)):
            item = expenses.get(party) or {}
            if not item.get("type"):
                continue
            answers.put("X", [(76, y, 10)], f"{party.title()} expense change", size=9)
            if item["type"] == "amount":
                answers.put("X", [(299, y, 10)], f"{party.title()} amount choice", size=9)
                answers.put(_money(item.get("value")), [(316, y - 1, 52)], f"{party.title()} amount", size=7)
            else:
                answers.put("X", [(400, y, 10)], f"{party.title()} percentage choice", size=9)
                answers.put(item.get("value"), [(413, y - 1, 33)], f"{party.title()} percentage", size=7)

    if "lender_repairs" in changes:
        payments = data.get("lender_repairs") or {}
        answers.put(_money(payments.get("seller")), [(139, 443, 136)], "Seller lender-required repairs", size=8)
        answers.put(_money(payments.get("buyer")), [(341, 443, 143)], "Buyer lender-required repairs", size=8)

    if "option_extension" in changes:
        option = data.get("option_extension") or {}
        month_day, year = _date_parts(option.get("date"))
        answers.put(_money(option.get("fee")), [(330, 430, 112)], "Additional option fee", size=8)
        answers.put(month_day, [(72, 405, 145)], "Option extension date", size=8)
        answers.put(year, [(239, 405, 32)], "Option extension year", size=8)
        mark_x = 414 if option.get("credited") is True else 449
        answers.put("X", [(mark_x, 405, 10)], "Option fee credit choice", size=9)

    if "buyer_approval_date" in changes:
        month_day, year = _date_parts(data.get("buyer_approval_date"))
        answers.put(month_day, [(391, 353, 104)], "Buyer approval notice date", size=8)
        answers.put(year, [(517, 353, 37)], "Buyer approval notice year", size=8)

    if "other" in changes:
        answers.put(
            data.get("other_modifications"),
            [(71, 329, 485), (71, 316, 485), (71, 305, 485)],
            "Other modifications",
            size=8,
        )
    return answers


def _overlay(answers):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    draw_entries(canvas, answers.pages[1])
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_trec_39_11(source_pdf_bytes, data):
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TREC 39-11 source must contain exactly one page.")
    answers = answer_layout(data)
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    writer.pages[0].merge_page(PdfReader(BytesIO(_overlay(answers))).pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_trec3911(data, *, client_count=None):
    """Return Buyer/Seller signature fields in SignWell's 96-DPI space."""
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TREC 39-11 requires one or two Buyers and one or two Sellers.")
    fields = []
    party_rows = (
        (buyers, ((48, 790, 346), (47, 847, 348))),
        (sellers, ((419, 790, 351), (420, 846, 349))),
    )
    recipient = 1
    for role, (names, rows) in zip(("buyer", "seller"), party_rows):
        for index in range(len(names)):
            x, y, width = rows[index]
            fields.append({
                "api_id": f"trec3911_{role}{index + 1}_signature_p1",
                "type": "signature",
                "page": 1,
                "x": x,
                "y": y,
                "recipient_id": str(recipient),
                "required": True,
                "width": width,
                "height": 32,
            })
            recipient += 1
    fields.extend(answer_layout(data).continuation_fields(2, "trec3911"))
    return [fields]

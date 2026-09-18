"""Private-source renderer for TXR-1919 loan-assumption review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.pdf_text import draw_text, text_width
from lib.repair_continuation import render_text_continuation, continuation_field
from lib.txr_source_imprint import remove_known_source_imprint


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = 'txr-1919-2026-09-18-neutral-source-v3'

# (x, PDF baseline, available width), measured from the 11-07-2022 source.
BLANKS = {
    'address1': [(40, 662, 532)], 'address2': [(42, 731, 524)],
    'credit_days': [(99, 577, 38)],
    'credit_other': [(196, 555, 362), (64, 544, 491)],
    'first_lender': [(447, 370, 111), (95, 359, 166)],
    'second_lender': [(487, 320, 71), (95, 309, 163)],
    'first_balance': [(475, 359, 83)], 'second_balance': [(473, 309, 85)],
    'first_payment': [(105, 337, 83)], 'second_payment': [(105, 287, 86)],
    'threshold': [(70, 237, 56)],
    'first_fee_cap': [(319, 161, 50)], 'second_fee_cap': [(438, 161, 66)],
    'first_rate_cap': [(314, 139, 30)], 'second_rate_cap': [(412, 139, 27)],
}
CHECK_CENTERS = {
    'credit_report': (391.39, 579.24), 'employment': (480.13, 579.24),
    'funds': (219.61, 568.26), 'financial_statement': (515.71, 568.26),
    'other': (188.47, 557.22), 'first': (66.73, 372.24), 'second': (66.73, 322.26),
    'cash': (200.59, 261.24), 'sales_price': (338.23, 261.24),
}


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, *, size=8):
    value = _clean(value)
    if value:
        draw_text(canvas, value, x, y, size)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 6)
    canvas.drawCentredString(x, y - 2.15, "X")


def _inline(value, blanks, size=8):
    value = _clean(value)
    if not value:
        return []
    for half in range(int(size * 2), 13, -1):
        point_size = half / 2
        words = value.split()
        entries = []
        for x, y, width in blanks:
            line = []
            while words and text_width(' '.join(line + [words[0]]), 'Helvetica', point_size) <= width:
                line.append(words.pop(0))
            if line:
                entries.append((x, y, ' '.join(line), point_size))
        if not words:
            return entries
    return None


def answer_layout(data):
    """Lossless source placement shared by PDF creation and continuation maps."""
    pages = {1: [], 2: []}
    overflow = {}

    def put(key, value, label, page=1, size=8):
        entries = _inline(value, BLANKS[key], size)
        if entries is None:
            overflow[label] = _clean(value)
            entries = _inline('Exhibit', BLANKS[key][:1], 7)
        pages[page].extend(entries)

    put('address1', data.get('property_address'), 'Property address', size=9)
    put('address2', data.get('property_address'), 'Property address', page=2, size=9)
    put('credit_days', data.get('credit_days'), 'Paragraph A - delivery time')
    if 'other' in (data.get('credit_documents') or []):
        put('credit_other', data.get('credit_other'), 'Paragraph A - other credit documentation')
    loans = data.get('loans') or {}
    terms = data.get('loan_terms') or {}
    for index, key in enumerate(('first', 'second'), 1):
        loan = loans.get(key) or {}
        if not loan.get('enabled'):
            continue
        for field, value_key in (('lender', 'lender'), ('balance', 'balance'), ('payment', 'monthly_payment')):
            put(key + '_' + field, loan.get(value_key), f'Paragraph C({index}) - {field}')
        for field, label in (('fee_cap', 'assumption fee cap'), ('rate_cap', 'interest rate cap')):
            put(key + '_' + field, terms.get(key + '_' + field), f'Paragraph D - {key}-lien {label}')
    put('threshold', (data.get('variance') or {}).get('termination_threshold'), 'Paragraph C - variance termination threshold')
    # Compute any name overflow for both review and signing copies so the
    # continuation page count never depends on the review-only name overlay.
    for role, x in (('Buyer', 48), ('Seller', 326)):
        for index, name in enumerate((data.get(role.lower() + '_names') or [])[:2]):
            blanks = [(x, 302 if index == 0 else 240, 240)]
            entries = _inline(name, blanks, 9)
            if entries is None:
                overflow[f'{role} {index + 1}'] = _clean(name)
                entries = _inline(f'{role} {index + 1} - see exhibit', blanks, 8)
            if not data.get('_for_signing'):
                pages[2].extend(entries)
    return pages, overflow


def _continuation(data, overflow):
    if not overflow:
        return None
    parties = {'property_address': _clean(data.get('property_address')),
               'buyer1': (data.get('buyer_names') or [''])[0],
               'buyer2': (data.get('buyer_names') or ['', ''])[1] if len(data.get('buyer_names') or []) > 1 else '',
               'seller': ' and '.join(data.get('seller_names') or [])}
    return render_text_continuation(parties, 'TXR-1919 - Loan Assumption Continuation',
                                    '\n\n'.join(label + ': ' + value for label, value in overflow.items()))


def _page_one(data, entries):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    for x, y, value, size in entries:
        _draw(canvas, value, x, y, size=size)
    docs = set(data.get("credit_documents") or [])
    for key in ('credit_report', 'employment', 'funds', 'financial_statement', 'other'):
        if key in docs:
            _mark(canvas, *CHECK_CENTERS[key])
    loans = data.get("loans") or {}
    for key in ('first', 'second'):
        loan = loans.get(key) or {}
        if loan.get("enabled"):
            _mark(canvas, *CHECK_CENTERS[key])
    variance = data.get("variance") or {}
    if variance.get('adjustment') in ('cash', 'sales_price'):
        _mark(canvas, *CHECK_CENTERS[variance['adjustment']])
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.read()


def _page_two(entries):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    for x, y, value, size in entries:
        _draw(canvas, value, x, y, size=size)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1919(source_pdf_bytes, data):
    """Overlay review values without creating signature fields or a send path."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 2:
        raise ValueError("TXR-1919 source must contain exactly two pages.")
    pages, overflow = answer_layout(data)
    overlays = [PdfReader(BytesIO(_page_one(data, pages[1]))), PdfReader(BytesIO(_page_two(pages[2])))]
    writer = PdfWriter()
    for page in source.pages:
        writer.add_page(page)
    remove_known_source_imprint(writer, source_pdf_bytes, 'TXR-1919')
    for index in range(len(source.pages)):
        writer.pages[index].merge_page(overlays[index].pages[0])
    continuation = _continuation(data, overflow)
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1919(data, *, client_count=None):
    """Return the TXR-1919 Buyer and Seller signature fields.

    TXR-1919 has two Buyer/Seller execution rows on page two. Coordinates are
    calibrated from those printed source rules in the 96-DPI, top-origin
    coordinate space required by the SignWell integration. The map stays
    isolated until a completed provider PDF verifies the live widget output.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1919 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1919_buyer1_signature_p2", "type": "signature", "page": 2, "x": 60, "y": 632, "recipient_id": "1", "required": True, "width": 325, "height": 24},
        {"api_id": "txr1919_seller1_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 632, "recipient_id": str(len(buyers) + 1), "required": True, "width": 325, "height": 24},
    ]
    if len(buyers) == 2:
        fields.append({"api_id": "txr1919_buyer2_signature_p2", "type": "signature", "page": 2, "x": 60, "y": 716, "recipient_id": "2", "required": True, "width": 325, "height": 24})
    if len(sellers) == 2:
        fields.append({"api_id": "txr1919_seller2_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 716, "recipient_id": str(len(buyers) + 2), "required": True, "width": 325, "height": 24})
    recipients = [('buyer', index + 1, str(index + 1), index + 1)
                  for index in range(len(buyers))]
    recipients += [('seller', index + 1, str(len(buyers) + index + 1), index + 3)
                   for index in range(len(sellers))]
    for role, index, recipient, _ in recipients:
        x = (191 + (index - 1) * 42) if role == 'buyer' else (326 + (index - 1) * 32)
        width = 38 if role == 'buyer' else 29
        fields.append({'api_id': f'txr1919_{role}{index}_initials_p1', 'type': 'initials',
                       'page': 1, 'x': x * 4 / 3, 'y': 992, 'width': width * 4 / 3,
                       'height': 10, 'recipient_id': recipient, 'required': True})
    continuation = _continuation(data, answer_layout(data)[1])
    if continuation:
        for index in range(len(PdfReader(BytesIO(continuation)).pages)):
            for role, number, recipient, canonical in recipients:
                field = continuation_field(str(canonical), index + 3, index + 1, prefix='txr1919')
                field['recipient_id'] = recipient
                field['api_id'] = f'txr1919_continuation_{index + 1}_{role}{number}_initials'
                fields.append(field)
    return [fields]

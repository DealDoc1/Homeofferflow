"""Private-source renderer for the TXR-1914 seller-financing addendum."""
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_addenda_layout import SourceAnswers, clean, draw_entries, mark_cell

PAGE_WIDTH, PAGE_HEIGHT = 612, 792
RENDER_REVISION = 'txr-1914-2026-09-18-source-blanks-v2'
# Source 11-07-2022; PDF points, bottom-origin baselines and cell centers.
BLANKS = {
    'address1': [(38, 654, 534)], 'address2': [(40, 731, 526)],
    'credit_days': [(130, 523, 42)],
    'credit_other': [(398, 500, 155), (68, 489, 481)],
    'note_amount': [(387, 351, 71)], 'interest_rate': [(81, 330, 23)],
    'one_due': [(205, 245, 214)],
    'monthly_amount': [(248, 215, 78)], 'monthly_begins': [(226, 204, 115)],
    'monthly_payoff': [(211, 193, 69)],
    'interest_only_months': [(350, 163, 65)],
    'later_amount': [(184, 152, 96)], 'later_begins': [(182, 141, 111)],
    'later_payoff': [(167, 130, 65)],
}
CELLS = {
    1: {'credit_report': (407.59, 524.58), 'employment': (489.79, 524.58),
        'funds': (250.75, 513.54), 'financial_statement': (71.23, 502.56),
        'other': (361.69, 502.56), 'one_payment': (71.23, 247.56),
        'maturity': (211.39, 236.58), 'monthly': (286.21, 236.58),
        'quarterly': (345.67, 236.58), 'monthly_installments': (71.23, 217.56),
        'monthly_including_interest': (341.89, 217.56), 'monthly_plus_interest': (450.79, 217.56),
        'interest_only_then_installments': (71.23, 165.54),
        'later_including_interest': (291.25, 154.56), 'later_plus_interest': (399.85, 154.56),
        'consent_not_required': (84.73, 75.54)},
    2: {'consent_required': (74.29, 691.74),
        'insurance_required': (414.61, 565.74), 'insurance_not_required': (465.61, 565.74),
        'escrow_not_required': (78.79, 516.72), 'escrow_required': (78.79, 475.74),
        'will': (110.29, 376.74), 'will_not': (155.83, 376.74),
        'buyer': (411.79, 376.74), 'seller': (463.45, 376.74)},
}


def _months(value):
    value = clean(value)
    return value + (' month' if value == '1' else ' months') if value else ''


def answer_layout(data):
    answers = SourceAnswers(data, 'TXR-1914 - Seller Financing Continuation', 2)
    def put(key, value, label, page=1, size=8):
        answers.put(value, BLANKS[key], label, page=page, size=size)
    put('address1', data.get('property_address'), 'Property address', size=9)
    put('address2', data.get('property_address'), 'Property address', page=2, size=9)
    put('credit_days', data.get('credit_days'), 'Paragraph A - delivery days')
    if 'other' in (data.get('credit_documents') or []):
        put('credit_other', data.get('credit_other'), 'Paragraph A - other credit documentation')
    put('note_amount', data.get('note_amount'), 'Paragraph C - note amount')
    put('interest_rate', data.get('interest_rate'), 'Paragraph C - annual interest percentage')
    payment = data.get('payment') or {}
    plan = payment.get('plan')
    if plan == 'one_payment':
        put('one_due', _months(payment.get('due_after_months')), 'Paragraph C(1) - due after date of note')
    elif plan in ('monthly_installments', 'interest_only_then_installments'):
        prefix = 'monthly' if plan == 'monthly_installments' else 'later'
        paragraph = 'C(2)' if prefix == 'monthly' else 'C(3)'
        put(prefix + '_amount', payment.get('installment_amount'), f'Paragraph {paragraph} - installment amount')
        put(prefix + '_begins', _months(payment.get('begins_after_months')),
            f'Paragraph {paragraph} - installments begin after date of note')
        put(prefix + '_payoff', payment.get('payoff_after_months'), f'Paragraph {paragraph} - payoff months')
        if prefix == 'later':
            put('interest_only_months', payment.get('interest_only_months'), 'Paragraph C(3) - interest-only months')
    answers.names(2, (239, 162), [('Buyer', 58, 238), ('Seller', 315, 242)])
    return answers


def selected_cells(data):
    selected = {1: set(data.get('credit_documents') or []) &
                {'credit_report', 'employment', 'funds', 'financial_statement', 'other'}, 2: set()}
    payment = data.get('payment') or {}
    plan = payment.get('plan')
    if plan == 'one_payment':
        selected[1].add(plan)
        if payment.get('interest_timing') in ('maturity', 'monthly', 'quarterly'):
            selected[1].add(payment['interest_timing'])
    elif plan in ('monthly_installments', 'interest_only_then_installments'):
        selected[1].add(plan)
        if payment.get('interest_style') in ('including_interest', 'plus_interest'):
            prefix = 'monthly' if plan == 'monthly_installments' else 'later'
            selected[1].add(prefix + '_' + payment['interest_style'])
    transfer = data.get('property_transfer')
    if transfer in ('consent_required', 'consent_not_required'):
        selected[2 if transfer == 'consent_required' else 1].add(transfer)
    if data.get('casualty_insurance') in ('required', 'not_required'):
        selected[2].add('insurance_' + data['casualty_insurance'])
    escrow = data.get('escrow') or {}
    if escrow.get('choice') in ('required', 'not_required'):
        selected[2].add('escrow_' + escrow['choice'])
    if escrow.get('choice') == 'required':
        if escrow.get('third_party_servicer') in ('will', 'will_not'):
            selected[2].add(escrow['third_party_servicer'])
        if escrow.get('cost_paid_by') in ('buyer', 'seller'):
            selected[2].add(escrow['cost_paid_by'])
    return selected


def _page(data, answers, number):
    output = BytesIO()
    canvas = Canvas(output, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    draw_entries(canvas, answers.pages[number])
    for key in sorted(selected_cells(data)[number]):
        mark_cell(canvas, *CELLS[number][key])
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def render_txr_1914(source_pdf_bytes, data):
    """Copy entered terms into their source blanks without sending a document."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 2:
        raise ValueError('TXR-1914 source must contain exactly two pages.')
    answers = answer_layout(data)
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        writer.add_page(page)
        writer.pages[index].merge_page(PdfReader(BytesIO(_page(data, answers, index + 1))).pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1914(data, *, client_count=None):
    """Local source-aligned candidate; completed provider rendering still needed."""
    buyers, sellers = data.get('buyer_names') or [], data.get('seller_names') or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError('TXR-1914 requires one or two Buyers and one or two Sellers.')
    fields = []
    for role, parties in [('buyer', buyers), ('seller', sellers)]:
        for index in range(len(parties)):
            recipient = str(index + 1 + (len(buyers) if role == 'seller' else 0))
            x, width = (56, 240) if role == 'buyer' else (313, 244)
            fields.append({'api_id': f'txr1914_{role}{index + 1}_signature_p2',
                           'type': 'signature', 'page': 2, 'x': x * 4 / 3,
                           'y': 715 if index == 0 else 818, 'recipient_id': recipient,
                           'required': True, 'width': width * 4 / 3, 'height': 24})
            x = (196 + index * 42) if role == 'buyer' else (345 + index * 32)
            fields.append({'api_id': f'txr1914_{role}{index + 1}_initials_p1',
                           'type': 'initials', 'page': 1, 'x': x * 4 / 3,
                           'y': 1015, 'recipient_id': recipient, 'required': True,
                           'width': (38 if role == 'buyer' else 29) * 4 / 3, 'height': 10})
    fields.sort(key=lambda field: (field['page'], field['y'], field['x']))
    fields.extend(answer_layout(data).continuation_fields(3, 'txr1914'))
    return [fields]

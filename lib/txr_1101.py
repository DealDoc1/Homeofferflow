"""Source-specific TXR-1101 sale-listing answers, overlay and signing map.

This module does not select fees, give legal advice, publish a listing, infer
seller disclosures, attach other documents or send invitations. The interview
must collect explicit choices and the existing review/send API owns delivery.
Coordinates apply only to the reviewed 06-15-26 ten-page English source.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
from io import BytesIO
import re

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.brokerage_defaults import broker_license
from lib.pdf_text import draw_text
from lib.txr_addenda_layout import inline, clean
from lib.txr1501_answers import render_continuation, continuation_fields


SOURCE_SHA256 = 'eeec91ef481059834262cf7f842afc045bf17c09b5be9e79fe2508112310b068'
SOURCE_PAGES = 10
REVISION = 'txr-1101-2026-06-15-overlay-v1'
FINANCING = ('conventional', 'va', 'fha', 'cash', 'texas_veterans', 'owner', 'other')
INTERVIEW_CHOICES = ('built_before_1978', 'request_hoa_information')
TEXT_LIMITS = {
    'client_address': 300, 'client_city_state_zip': 180, 'client_phone': 80,
    'client_email': 180, 'client_email_2': 180, 'property_address': 400,
    'lot': 150, 'block': 150, 'subdivision': 600, 'city': 180, 'county': 120,
    'exclusions': 2000, 'other_compensation': 2000, 'other_fees': 2000,
    'payment_county': 120, 'mls_delay_purpose': 1500, 'scheduling_companies': 800,
    'financial_exceptions': 2000, 'liens': 2000, 'relocation_entity': 500,
    'districts': 2000, 'special_provisions': 4000, 'other_documents': 2000,
}
CHOICES = {
    'hoa': ('yes', 'no'),
    'fee_basis': ('percentage', 'flat', 'none'),
    'additional_fee_basis': ('percentage', 'flat', 'none'),
    'disclose_buyer_expenses': ('yes', 'no'),
    'mls_filing': ('standard', 'delayed', 'none'),
    'internet_display': ('full', 'hide_address', 'hide_listing', 'not_applicable'),
    'keybox': ('yes', 'no'),
    'intermediary': ('authorized', 'not_authorized'),
    'foreign_person': ('yes', 'no', 'unanswered'),
    'signer_plan': ('clients_and_associate', 'clients_and_broker'),
}


def _number(value, label, *, maximum=Decimal('999999999999.99'), places=2):
    # Reject booleans, exponents, NaN and precision loss instead of silently
    # rounding a negotiated contract term. Explicit zero is distinct from blank.
    raw = str(value if value is not None else '').strip()
    if not re.fullmatch(r'\d+(?:\.\d{1,' + str(places) + r'})?', raw):
        raise ValueError(f'Enter a valid {label}.')
    try:
        number = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f'Enter a valid {label}.')
    if not 0 <= number <= maximum:
        raise ValueError(f'Enter a valid {label}.')
    return format(number, 'f')


def validate_answers(data):
    """Validate the internal, reusable listing-interview answer contract.

    No source-host organization or brokerage membership is an input. Signing
    identity/ownership and approved source lookup stay with the existing API.
    Unknown tax status stays unanswered; no personal-data inference is made.
    """
    if not isinstance(data, dict):
        raise ValueError('Enter the listing agreement details.')
    allowed = set(TEXT_LIMITS) | set(CHOICES) | set(INTERVIEW_CHOICES) | {
        'client_names', 'term_start', 'term_end', 'listing_price', 'fee_amount',
        'additional_fee_amount', 'protection_days', 'mls_delay_days',
        'financing', 'addenda', '_for_signing',
    }
    if set(data) - allowed:
        raise ValueError('Some listing answers are not supported.')
    result = {}
    names = data.get('client_names')
    if (not isinstance(names, list) or len(names) not in (1, 2)
            or any(not isinstance(n, str) or not clean(n) or len(n) > 300 for n in names)):
        raise ValueError('Enter one or two seller names.')
    result['client_names'] = [clean(n) for n in names]
    for key, limit in TEXT_LIMITS.items():
        value = data.get(key, '')
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError('Check ' + key.replace('_', ' ') + '.')
        result[key] = clean(value)
    if not result['property_address']:
        raise ValueError('Enter the property address.')
    for key in ('client_email', 'client_email_2'):
        if result[key] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', result[key]):
            raise ValueError('Enter a valid seller email address.')
    for key, options in CHOICES.items():
        value = data.get(key)
        if value not in options:
            raise ValueError('Choose ' + key.replace('_', ' ') + '.')
        result[key] = value
    for key in INTERVIEW_CHOICES:
        value = data.get(key, 'unanswered')
        if value not in ('yes', 'no', 'unanswered'):
            raise ValueError('Check the related-document questions.')
        result[key] = value
    for key in ('term_start', 'term_end'):
        try:
            value = data.get(key)
            if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError
            result[key] = date.fromisoformat(value).isoformat()
        except (TypeError, ValueError):
            raise ValueError('Enter valid listing start and end dates.')
    if result['term_end'] < result['term_start']:
        raise ValueError('The listing end date must be on or after its start date.')
    result['listing_price'] = _number(data.get('listing_price'), 'listing price')
    if Decimal(result['listing_price']) == 0:
        raise ValueError('The listing price must be greater than zero.')
    for prefix in ('fee', 'additional_fee'):
        basis = result[prefix + '_basis']
        value = data.get(prefix + '_amount')
        if basis == 'none':
            if value not in (None, ''):
                raise ValueError('Remove the amount for the unselected compensation option.')
            result[prefix + '_amount'] = ''
        else:
            result[prefix + '_amount'] = _number(value, 'compensation amount',
                maximum=Decimal('100') if basis == 'percentage' else Decimal('999999999999.99'),
                places=4 if basis == 'percentage' else 2)
    if (result['fee_basis'] == result['additional_fee_basis'] == 'none'
            and not result['other_compensation']):
        raise ValueError('Enter the agreed compensation, including zero if applicable.')
    for key in ('protection_days', 'mls_delay_days'):
        raw = str(data.get(key, '')).strip()
        if raw and (not re.fullmatch(r'\d{1,4}', raw) or not 0 <= int(raw) <= 9999):
            raise ValueError('Enter whole ' + key.replace('_', ' ') + ' from 0 to 9999.')
        result[key] = str(int(raw)) if raw else ''
    if result['mls_filing'] == 'delayed':
        if not result['mls_delay_days'] or int(result['mls_delay_days']) < 1 or not result['mls_delay_purpose']:
            raise ValueError('Enter the MLS delay and its purpose.')
    elif result['mls_delay_days'] or result['mls_delay_purpose']:
        raise ValueError('Remove delay details when MLS filing is not delayed.')
    if (result['mls_filing'] == 'none') != (result['internet_display'] == 'not_applicable'):
        raise ValueError('Choose Internet display instructions that match the MLS filing choice.')
    for key, options in (('financing', FINANCING), ('addenda', tuple('ABCDEFGHIJKLMNOP'))):
        values = data.get(key, [])
        if (not isinstance(values, list) or any(not isinstance(v, str) or v not in options for v in values)
                or len(values) != len(set(values))):
            raise ValueError('Choose the applicable ' + key + ' options once each.')
        result[key] = [value for value in options if value in values]
    # Keep the interview's explicit facts on reopening, and do not allow a
    # checklist toggle to contradict a known pre-1978 disclosure requirement.
    if result['built_before_1978'] == 'yes' and 'C' not in result['addenda']:
        result['addenda'].append('C')
    if (result['hoa'] == 'yes' and result['request_hoa_information'] == 'yes'
            and 'G' not in result['addenda']):
        result['addenda'].append('G')
    result['addenda'].sort()
    if '_for_signing' in data:
        if not isinstance(data['_for_signing'], bool):
            raise ValueError('Invalid document rendering choice.')
        result['_for_signing'] = data['_for_signing']
    return result


# (source page, source-blank baseline rectangles). Bottom-origin PDF points.
BLANKS = {
    'client_address': (1, [(120, 605, 454)]),
    'client_city_state_zip': (1, [(152, 593, 422)]),
    'client_phone': (1, [(112, 580, 462)]),
    'client_email': (1, [(129, 568, 196)]),
    'client_email_2': (1, [(384, 568, 190)]),
    'lot': (1, [(123, 432, 163)]), 'block': (1, [(326, 432, 104)]),
    'subdivision': (1, [(440, 432, 134), (74, 420, 248)]),
    'city': (1, [(409, 420, 165)]), 'county': (1, [(86, 404, 215)]),
    'property_address': (1, [(432, 404, 142), (74, 392, 401)]),
    'exclusions': (1, [(226, 155, 348)]), 'listing_price': (1, [(478, 108, 96)]),
    'term_start': (2, [(184, 717, 111)]), 'term_end': (2, [(433, 717, 105)]),
    'other_compensation': (2, [(91, 521, 411)]),
    'other_fees': (3, [(310, 679, 264), (92, 666, 477)]),
    'protection_days': (3, [(368, 622, 62)]),
    'payment_county': (3, [(386, 462, 188), (74, 449, 278)]),
    'mls_delay_days': (3, [(457, 224, 117)]),
    'mls_delay_purpose': (3, [(417, 211, 157), (94, 198, 475)]),
    'scheduling_companies': (4, [(272, 210, 296)]),
    'financial_exceptions': (7, [(250, 679, 324), (76, 666, 493)]),
    'liens': (7, [(484, 651, 90), (76, 638, 493)]),
    'relocation_entity': (7, [(187, 566, 381)]),
    'districts': (7, [(401, 496, 167), (77, 480, 492)]),
    'special_provisions': (8, [(38, 597, 536), (38, 584, 536)]),
}
CHECKS = {
    'hoa': {'yes': (1, 251, 138), 'no': (1, 294, 138)},
    'disclose_buyer_expenses': {'yes': (2, 421, 496), 'no': (2, 474, 496)},
    'mls_filing': {'standard': (3, 74, 266), 'delayed': (3, 74, 224), 'none': (3, 56, 76)},
    'keybox': {'yes': (4, 128, 101), 'no': (4, 167, 101)},
    'intermediary': {'authorized': (5, 38, 579), 'not_authorized': (5, 38, 295)},
    'internet_display': {'hide_listing': (6, 55, 607), 'hide_address': (6, 55, 591)},
    'foreign_person': {'yes': (9, 528, 142), 'no': (9, 74, 126)},
    'signer_plan': {'clients_and_broker': (10, 28, 558), 'clients_and_associate': (10, 28, 548)},
}
FINANCE_CELLS = dict(zip(FINANCING,
    [(55, 532), (55, 516), (55, 500), (55, 485), (200, 532), (200, 516), (200, 500)]))
ADDENDA_Y = (353, 337, 321, 293, 277, 262, 246, 230, 215, 199, 183, 168, 152, 137, 121, 105)


def answer_layout(data, brokerage, associate):
    """Return bounded text placements and a complete, lossless continuation."""
    data = validate_answers(data)
    pages, overflow = {p: [] for p in range(1, 11)}, {}
    def put(page, value, label, blanks, size=8):
        entries = inline(value, blanks, size)
        if entries is None:
            overflow[label] = clean(value)
            entries = inline('See exhibit', blanks[:1], 7) or inline('Exhibit', blanks[:1], 7)
            if entries is None:
                raise ValueError('The answer reference does not fit its listing-agreement blank.')
        pages[page].extend(entries)
    broker = brokerage.get('legal_name') or brokerage.get('name') or brokerage.get('dba_name') or ''
    for key, (page, blanks) in BLANKS.items():
        value = data[key]
        if key in ('term_start', 'term_end'):
            value = date.fromisoformat(value).strftime('%m/%d/%Y')
        put(page, value, key.replace('_', ' ').title(), blanks)
    put(1, ', '.join(data['client_names']), 'Paragraph 1 - Sellers', [(92, 632, 482), (92, 619, 482)])
    put(1, broker, 'Paragraph 1 - Broker', [(95, 556, 479)])
    for key, x, y, width in [('address',120,543,454), ('city_state_zip',152,530,422),
                             ('phone',112,518,462), ('email',129,505,196), ('email_2',384,505,190)]:
        put(1, brokerage.get(key), 'Broker '+key.replace('_',' '), [(x,y,width)])
    for prefix, row, x_percent, x_flat, w_percent, w_flat in (
            ('fee', 580, 91, 322, 51, 72), ('additional_fee', 557, 158, 394, 56, 72)):
        basis = data[prefix+'_basis']
        if basis != 'none':
            put(2, data[prefix+'_amount'], prefix.replace('_',' ').title(),
                [(x_percent if basis == 'percentage' else x_flat, row,
                  w_percent if basis == 'percentage' else w_flat)])
    for page in range(2, 11):
        header = inline(data['property_address'], [(158, 755, 410)], 8)
        if header is None:
            header = inline('Property identified in Paragraph 2', [(158,755,410)], 8)
        pages[page].extend(header)
    for value, label, x, y, width in (
        (broker, 'Broker printed name', 29, 610, 195),
        (broker_license(broker, brokerage.get('license_number')), 'Broker license', 230, 610, 56),
        (associate.get('name') or associate.get('agent_name'), 'Associate printed name', 29, 517, 195),
        (associate.get('license_number'), 'Associate license', 230, 517, 56),
        (data['client_names'][0], 'Seller 1 printed name', 326, 610, 248),
        (data['client_names'][1] if len(data['client_names']) == 2 else '', 'Seller 2 printed name', 326, 517, 248)):
        put(10, value, 'Execution - '+label, [(x,y,width)], 8)
    other = data['other_documents']
    if overflow:
        other = '; '.join(filter(None, [other, 'Answer continuation (attached)']))
    entries = inline(other, [(73,89,501),(73,76,495)], 8)
    if entries is None:
        overflow['Paragraph 19Q - Other documents'] = data['other_documents']
        entries = inline('Answer continuation (attached)', [(73,89,501)], 8)
    pages[8].extend(entries)
    return pages, overflow


def _mark(canvas, x, y):
    canvas.setLineWidth(.8)
    canvas.line(x, y, x+4.5, y+4.5)
    canvas.line(x, y+4.5, x+4.5, y)


def _overlay(data, brokerage, associate):
    data = validate_answers(data)
    pages, overflow = answer_layout(data, brokerage, associate)
    marks = {p: [] for p in range(1, 11)}
    for key, choices in CHECKS.items():
        if data[key] in choices:
            page, x, y = choices[data[key]]
            marks[page].append((x,y))
    for key, y in (('fee_basis', 581), ('additional_fee_basis', 558)):
        if data[key] != 'none': marks[2].append((56,y))
    if data['other_compensation']: marks[2].append((56,522))
    if data['mls_filing'] != 'none': marks[3].append((56,283))
    marks[6].extend(FINANCE_CELLS[value] for value in data['financing'])
    marks[8].extend((38, ADDENDA_Y[ord(value)-ord('A')]) for value in data['addenda'])
    if data['other_documents'] or overflow: marks[8].append((38,90))
    output = BytesIO()
    canvas = Canvas(output, pagesize=(612,792))
    for page in range(1, 11):
        for x,y,value,size in pages[page]: draw_text(canvas, value, x, y, size)
        for x,y in marks[page]: _mark(canvas,x,y)
        canvas.showPage()
    canvas.save()
    return output.getvalue(), overflow


def _remove_member_footer(writer):
    """Remove only the two supplier imprints in the exact hashed source.

    Validate every page first. This never touches form/copyright text, an
    arbitrary source, an executed PDF, or the original source file on disk.
    """
    pending = []
    for page in writer.pages:
        content = page.get_contents()
        operations = content.operations
        remove = []
        for i,(args,op) in enumerate(operations):
            if op != b'Tj' or i < 5 or i+2 >= len(operations) or len(args) != 1:
                continue
            digest = hashlib.sha256(str(args[0]).encode()).hexdigest()
            y = FOOTER_TEXT_HASHES.get(digest)
            if y is None: continue
            if (operations[i-5] != ([],b'BT')
                    or operations[i-1] != ([1,0,0,1,16,y],b'Tm')
                    or operations[i+1:i+3] != [([],b'T*'),([],b'ET')]):
                raise ValueError('The listing source footer has changed; review this revision before use.')
            remove.append(i)
        if len(remove) != 2:
            raise ValueError('The listing source footer has changed; review this revision before use.')
        pending.append((page,content,remove))
    for page,content,remove in pending:
        content.operations = [v for i,v in enumerate(content.operations) if i not in remove]
        page.replace_contents(content)


FOOTER_TEXT_HASHES = {
    '9af34afef310d43bd5bb7925b890286bd20f56aa51c0f42d4e801a542e83296e': 26,
    'd7302b22a0db22a2ea1e77c6090b69323fe6b3c5e70bb71c2c00d5d320b24f46': 16,
}


def render_txr_1101(source_pdf_bytes, data, brokerage, associate):
    if hashlib.sha256(source_pdf_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError('Use the reviewed June 15, 2026 listing-agreement source.')
    data = validate_answers(data)
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != SOURCE_PAGES or any(
            abs(float(p.mediabox.width)-612) > .01 or abs(float(p.mediabox.height)-792) > .01
            for p in source.pages):
        raise ValueError('The listing agreement must contain all ten original Letter pages.')
    overlay_bytes, overflow = _overlay(data, brokerage, associate)
    overlay = PdfReader(BytesIO(overlay_bytes))
    writer = PdfWriter()
    for page in source.pages: writer.add_page(page)
    _remove_member_footer(writer)
    for i,page in enumerate(overlay.pages): writer.pages[i].merge_page(page)
    if overflow:
        overflow = {'Property': data['property_address'],
                    'Seller(s)': ', '.join(data['client_names']),
                    'Broker': brokerage.get('legal_name') or brokerage.get('name') or brokerage.get('dba_name') or '',
                    **overflow}
    continuation = render_continuation(data, overflow, title='TXR-1101 - Answer Continuation',
        party_label='Seller', description='Entered answers referenced in the attached sale-listing agreement.')
    if continuation: writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1101(data, *, client_count=1, page_count=10):
    data = validate_answers(data)
    if (isinstance(client_count,bool) or client_count not in (1,2)
            or client_count != len(data['client_names'])):
        raise ValueError('The signing recipients must match the named sellers.')
    if isinstance(page_count,bool) or not isinstance(page_count,int) or not 10 <= page_count <= 100:
        raise ValueError('The listing packet must include its ten source pages and valid continuation pages.')
    role = 'associate' if data['signer_plan']=='clients_and_associate' else 'broker'
    fields = []
    def field(key, kind, page, x, y, width, height, recipient):
        result = {'api_id':f'txr1101_{key}_p{page}', 'type':kind, 'page':page,
                  'x':x*4/3, 'y':(792-y-height)*4/3, 'width':width*4/3,
                  'height':height*4/3, 'recipient_id':recipient, 'required':True}
        if kind=='date': result.update(date_format='MM/DD/YYYY',lock_sign_date=True)
        fields.append(result)
    for label,recipient,x,y,width in (
            ('seller1','1',324,567,252), (role,role,27,567,261),
            *([('seller2','2',324,474,252)] if client_count==2 else [])):
        field(label+'_signature','signature',10,x,y,180,22,recipient)
        field(label+'_date','date',10,x+width-54,y,54,18,recipient)
    for page in range(1,10):
        for label,recipient,x,width in (
                (role,role,326,34),('seller1','1',407,36),
                *([('seller2','2',448,32)] if client_count==2 else [])):
            field(label+'_initials','initials',page,x,47, width,11,recipient)
    fields.extend(continuation_fields(data, client_count, page_count, source_pages=10,prefix='txr1101'))
    return [fields]

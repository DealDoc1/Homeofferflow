"""Official TREC 48-1 field completion and source-bound signing map.

This module does not send documents or select a risk allocation for the parties.
The purchase-interview and combined-packet integration is a separate caller.
"""
from decimal import Decimal, InvalidOperation
import hashlib
from io import BytesIO
from pathlib import Path
import re

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
from reportlab.pdfbase.pdfmetrics import stringWidth

SOURCE_URL = 'https://www.trec.texas.gov/sites/default/files/pdf-forms/48-1.pdf'
SOURCE_SHA256 = '3eb6e7ced0723ceaab6bef2645fcd7868ee3c2cd2734a6a5f03dbe049bd5df6a'
SOURCE_PATH = Path(__file__).resolve().parents[1] / 'hydrostatic_testing_48-1.pdf'
RENDER_REVISION = 'trec-48-1-acroform-v1'
ADDRESS_FIELD = 'Street Address and City'
AMOUNT_FIELD = 'exceed'
RISK_FIELDS = {
    'seller': '1 Seller shall be liable for damages caused by the hydrostatic plumbing test',
    'buyer': '2 Buyer shall be liable for damages caused by the hydrostatic plumbing test',
    'buyer_capped': '3 Buyer shall be liable for damages caused by the hydrostatic plumbing test in an amount not to',
}
SIGNATURE_FIELDS = ('Signature1', 'Signature2', 'Signature3', 'Signature4')


def validate_hydrostatic_terms(data):
    if not isinstance(data, dict):
        raise ValueError('Enter the hydrostatic-testing terms.')
    if not isinstance(data.get('property_address'), str):
        raise ValueError('Enter the property street address and city.')
    address = ' '.join(data['property_address'].split())
    if not address:
        raise ValueError('Enter the property street address and city.')
    if stringWidth(address, 'Helvetica', 7) > 312:
        raise ValueError('The property address is too long for the form. Use its street address and city.')
    risk = data.get('risk_allocation')
    if not isinstance(risk, str) or risk not in RISK_FIELDS:
        raise ValueError('Choose the agreed responsibility for damage from testing.')
    raw = str(data.get('buyer_liability_limit') if data.get('buyer_liability_limit') is not None else '').strip()
    amount = ''
    if risk == 'buyer_capped':
        if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?', raw):
            raise ValueError('Enter the agreed buyer liability limit as a dollar amount.')
        try:
            value = Decimal(raw.replace(',', ''))
        except InvalidOperation:
            raise ValueError('Enter a valid buyer liability limit.') from None
        if not value.is_finite() or value < 0 or value > Decimal('999999999.99'):
            raise ValueError('Enter a buyer liability limit between 0 and 999,999,999.99.')
        amount = f'{value:,.2f}'
    return {'property_address': address, 'risk_allocation': risk, 'buyer_liability_limit': amount}


def verified_source(source_bytes=None):
    raw = SOURCE_PATH.read_bytes() if source_bytes is None else source_bytes
    if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The hydrostatic-testing form does not match its verified source.')
    reader = PdfReader(BytesIO(raw))
    if len(reader.pages) != 1 or tuple(reader.pages[0].mediabox) != (0, 0, 612, 792):
        raise ValueError('The hydrostatic-testing source page is invalid.')
    fields = reader.get_fields() or {}
    expected = {ADDRESS_FIELD, AMOUNT_FIELD, *RISK_FIELDS.values(), *SIGNATURE_FIELDS}
    if set(fields) != expected:
        raise ValueError('The hydrostatic-testing source fields have changed.')
    # This exact source has shared canonical/widget objects, not orphaned fields.
    canonical = {ref.idnum for ref in reader.trailer['/Root']['/AcroForm']['/Fields']}
    widgets = {ref.idnum for ref in reader.pages[0]['/Annots']}
    if canonical != widgets:
        raise ValueError('The hydrostatic-testing field structure is inconsistent.')
    return reader


def render_trec_48_1(data, *, source_bytes=None):
    """Fill canonical fields and appearances; preserve an editable unsigned PDF."""
    terms = validate_hydrostatic_terms(data)
    reader = verified_source(source_bytes)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    address_size = min(9, 9 * 312 / max(stringWidth(terms['property_address'], 'Helvetica', 9), 1))
    for reference in writer.pages[0]['/Annots']:
        widget = reference.get_object()
        if widget.get('/T') == ADDRESS_FIELD:
            widget[NameObject('/DA')] = TextStringObject(f'/Helv {address_size:.3f} Tf 0 g')
    values = {ADDRESS_FIELD: terms['property_address'], AMOUNT_FIELD: terms['buyer_liability_limit']}
    values.update({name: '/On' if risk == terms['risk_allocation'] else '/Off'
                   for risk, name in RISK_FIELDS.items()})
    writer.update_page_form_field_values(None, values, auto_regenerate=False)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_trec48_1(*, buyer_count, seller_count, page=1):
    """Core-packet party IDs: Buyers 1/2, Sellers 3/4. No unprinted date fields."""
    if type(buyer_count) is not int or type(seller_count) is not int or buyer_count not in (1, 2) or seller_count not in (1, 2):
        raise ValueError('Include one or two buyers and one or two sellers.')
    if type(page) is not int or page < 1:
        raise ValueError('Choose a valid packet page.')
    reader = verified_source()
    widgets = {ref.get_object()['/T']: ref.get_object() for ref in reader.pages[0]['/Annots']}
    selected = [('Signature1', '1', 'buyer1'), ('Signature3', '3', 'seller1')]
    if buyer_count == 2:
        selected.append(('Signature2', '2', 'buyer2'))
    if seller_count == 2:
        selected.append(('Signature4', '4', 'seller2'))
    fields = []
    for name, recipient, role in selected:
        left, bottom, right, _ = map(float, widgets[name]['/Rect'])
        fields.append({'api_id': f'trec48_1_{role}_signature', 'type': 'signature',
                       'page': page, 'x': round((left + 2) * 4 / 3, 2),
                       'y': round((792 - bottom - 20) * 4 / 3, 2),
                       'width': round((right - left - 4) * 4 / 3, 2), 'height': 24,
                       'recipient_id': recipient, 'required': True})
    return [fields]

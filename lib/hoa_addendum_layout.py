"""Source-measured TREC 36-11 answers; preserve complete text on overflow."""
from lib.contract_money import format_currency
from lib.txr_addenda_layout import SourceAnswers


RENDER_REVISION = 'trec-36-11-2026-09-18-bounded-answers-v1'
TEXT_BLANKS = {
    'address': (38, 662, 536), 'association': (38, 635.5, 536),
    'seller_days': (105, 555.5, 66), 'buyer_days': (105, 499.5, 66),
    'cap': (370.5, 309.5, 82),
}
CHECK_CENTERS = {
    'seller': (49, 559.3), 'buyer': (49, 503.3), 'received': (49, 455.3),
    'notRequired': (49, 405.4), 'updated_yes': (537.5, 455.3),
    'updated_no': (75.6, 446.3), 'cost_buyer': (231.5, 236.3),
    'cost_seller': (278.8, 236.3),
}
BUYER_SIGNATURE_BOXES = ((58, 828, 316, 26), (58, 902, 316, 26))


def first(offer, *keys, default=''):
    return next((offer[key] for key in keys if offer.get(key) not in (None, '')), default)


def validate_hoa_answers(offer):
    if offer.get('hoa') in ('yes', 'unknown') and offer.get('hoaSubdivisionInfo') == 'received':
        if offer.get('hoaUpdatedResaleCertificate') not in ('yes', 'no'):
            raise ValueError('Choose whether the buyer requires an updated HOA resale certificate.')


def answer_layout(offer):
    validate_hoa_answers(offer)
    address = f"{offer.get('address','')}, {offer.get('city','')}, TX {offer.get('zip','')}".strip(', ')
    data = {'property_address': address, 'buyer_names': [offer.get('buyer1') or 'Buyer'] +
            ([offer.get('buyer2') or 'Buyer 2'] if offer.get('buyer2Email') else []),
            'seller': offer.get('seller') or '', '_for_signing': True}
    answers = SourceAnswers(data, 'TREC 36-11 - HOA Addendum Continuation', 1)
    name = str(first(offer, 'hoaName', 'associationName', 'poaName'))
    phone = str(offer.get('hoaPhone') or '').strip()
    association = ', '.join(value for value in (name, phone) if value)
    values = [('address', address, 'Property address'),
              ('association', association, 'Association name and phone number'),
              ('cap', format_currency(first(offer, 'hoaTransferFeeCap', 'hoaReserves', default='0')),
               'Paragraph C - Buyer fee and reserve cap')]
    # Retain the existing legacy defaults; newly entered interview choices are
    # explicit. Irrelevant delivery-day and resale-certificate answers are ignored.
    delivery = offer.get('hoaSubdivisionInfo') or 'seller'
    if delivery in ('seller', 'buyer'):
        values.append((delivery + '_days', first(offer, 'hoaDays', 'hoaDeliveryDays', default='7'),
                       'Paragraph A - Delivery period (days)'))
    for key, value, label in values:
        answers.put(value, [TEXT_BLANKS[key]], label, size=9)
    checks = [delivery, 'cost_' + (offer.get('hoaTitleCost') or 'seller')]
    if delivery == 'received':
        checks.append('updated_' + offer['hoaUpdatedResaleCertificate'])
    answers.checks = [key for key in checks if key in CHECK_CENTERS]
    return answers


def page_entries(answers):
    entries = [(*entry, 'text') for entry in answers.pages[1]]
    for key in answers.checks:
        x, y = CHECK_CENTERS[key]
        entries.append((x - 2, y - 2.15, 'X', 6, 'check_cell'))
    return entries

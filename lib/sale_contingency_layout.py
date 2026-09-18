"""Lossless, source-measured answers for the TREC 10-6 purchase addendum."""
from datetime import datetime
from lib.contract_money import format_currency
from lib.txr_addenda_layout import SourceAnswers


RENDER_REVISION = 'trec-10-6-2026-09-18-bounded-answers-v1'
TEXT_BLANKS = {
    'address': (56, 626, 499), 'sale_property': (67, 559, 499),
    'month_day': (176, 548, 196), 'year': (397, 548, 36),
    'waiver_days': (148, 451.5, 94), 'earnest': (506, 417.5, 60),
}
BUYER_SIGNATURE_BOXES = ((75, 690, 322, 26), (75, 771, 322, 26))


def date_parts(value):
    """Place the interview date in blanks following the source's printed 20."""
    if not value:
        return '', ''
    try:
        date = datetime.strptime(str(value), '%Y-%m-%d')
    except (ValueError, TypeError):
        raise ValueError('Enter the sale contingency deadline as a valid date.') from None
    if not 2000 <= date.year <= 2099:
        raise ValueError('The sale contingency form supports dates from 2000 through 2099.')
    return date.strftime('%B %d').replace(' 0', ' '), str(date.year)[-2:]


def answer_layout(offer):
    address = f"{offer.get('address','')}, {offer.get('city','')}, TX {offer.get('zip','')}".strip(', ')
    data = {'property_address': address, 'buyer_names': [offer.get('buyer1') or 'Buyer'] +
            ([offer.get('buyer2') or 'Buyer 2'] if offer.get('buyer2Email') else []),
            'seller': offer.get('seller') or '', '_for_signing': True}
    answers = SourceAnswers(data, 'TREC 10-6 - Sale Contingency Continuation', 1)
    sale_address = next((offer[k] for k in ('salePropertyAddr', 'salePropertyAddress', 'buyerSalePropertyAddress')
                         if offer.get(k) not in (None, '')), '')
    month_day, year = date_parts(offer.get('saleContingencyDate'))
    for key, value, label in (
        ('address', address, 'Property being purchased'),
        ('sale_property', sale_address, "Paragraph A - Buyer's property to sell"),
        ('month_day', month_day, 'Paragraph A - Contingency deadline'),
        ('year', year, 'Paragraph A - Contingency year (after printed 20)'),
        ('waiver_days', offer.get('saleWaiverDays', '3'), 'Paragraph B - Waiver period (days)'),
        ('earnest', format_currency(offer.get('saleAdditionalEarnest')), 'Paragraph C - Additional earnest money'),
    ):
        answers.put(value, [TEXT_BLANKS[key]], label, size=9)
    return answers


def page_entries(answers):
    # A literal user-entered "X" must remain text, not become a checkbox mark.
    return [(*entry, 'text') for entry in answers.pages[1]]

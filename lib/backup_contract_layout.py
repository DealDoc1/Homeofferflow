"""Source-measured answers and execution areas for TREC 11-9."""
from datetime import datetime
from lib.contract_money import format_currency
from lib.txr_addenda_layout import SourceAnswers


RENDER_REVISION = 'trec-11-9-2026-09-18-bounded-answers-v1'
TEXT_BLANKS = {
    'address': (57, 659, 500), 'address_p2': (179, 739, 323),
    'earnest': (344, 524, 53), 'option': (88, 513, 53), 'days': (278, 513, 33),
    'first_month_day': (151, 224, 160), 'first_year': (340, 224, 35),
    'termination_month_day': (343, 179, 153), 'termination_year': (522, 179, 33),
}
BUYER_INITIAL_BOXES = ((275, 1017, 40, 16), (319, 1017, 40, 16))
BUYER_SIGNATURE_BOXES = ((89, 205, 313, 26), (89, 305, 313, 26))
ALIASES = {
    'first': ('bkupFirstContractDate', 'backupFirstContractDate', 'firstContractDate', 'firstContractEffectiveDate'),
    'termination': ('bkupTerminateDate', 'backupTerminateDate', 'backupTerminationDate', 'backupContractTerminationDate'),
    'earnest': ('bkupAdditionalEarnest', 'backupAdditionalEarnest', 'backupAddlEarnest'),
    'option': ('bkupAdditionalOption', 'backupAdditionalOption', 'backupAdditionalOptionFee', 'backupAddlOption', 'backupAddlOptionFee'),
    'days': ('bkupAdditionalDays', 'backupAdditionalDays', 'backupAddlDays'),
}


def first_value(offer, key):
    return next((offer[k] for k in ALIASES[key] if offer.get(k) not in (None, '')), '')


def date_parts(value):
    if not value:
        return '', ''
    try:
        date = datetime.strptime(str(value), '%Y-%m-%d')
    except (ValueError, TypeError):
        raise ValueError('Enter the backup contract dates as valid dates.') from None
    if not 2000 <= date.year <= 2099:
        raise ValueError('The backup contract form supports dates from 2000 through 2099.')
    return date.strftime('%B %d').replace(' 0', ' '), str(date.year)[-2:]


def answer_layout(offer):
    address = f"{offer.get('address','')}, {offer.get('city','')}, TX {offer.get('zip','')}".strip(', ')
    data = {'property_address': address, 'buyer_names': [offer.get('buyer1') or 'Buyer'] +
            ([offer.get('buyer2') or 'Buyer 2'] if offer.get('buyer2Email') else []),
            'seller': offer.get('seller') or '', '_for_signing': True}
    answers = SourceAnswers(data, 'TREC 11-9 - Backup Contract Continuation', 2)
    first_md, first_yy = date_parts(first_value(offer, 'first'))
    term_md, term_yy = date_parts(first_value(offer, 'termination'))
    for key, value, label in (
        ('address', address, 'Property'),
        ('earnest', format_currency(first_value(offer, 'earnest')), 'Paragraph A(2) - Additional earnest money'),
        ('option', format_currency(first_value(offer, 'option')), 'Paragraph A(2) - Additional option fee'),
        ('days', first_value(offer, 'days'), 'Paragraph A(2) - Days to deliver additional funds'),
        ('first_month_day', first_md, 'Paragraph G - First contract date'),
        ('first_year', first_yy, 'Paragraph G - First contract year (after printed 20)'),
        ('termination_month_day', term_md, 'Paragraph H - Termination deadline'),
        ('termination_year', term_yy, 'Paragraph H - Termination year (after printed 20)'),
    ):
        answers.put(value, [TEXT_BLANKS[key]], label, size=9)
    answers.put(address, [TEXT_BLANKS['address_p2']], 'Property', page=2, size=9)
    return answers


def page_entries(answers):
    return {page - 1: [(*entry, 'text') for entry in entries]
            for page, entries in answers.pages.items()}

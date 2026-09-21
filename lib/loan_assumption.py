"""Validate source-form loan-assumption answers without lender/credit decisions."""
from decimal import Decimal
import re


SOURCE_SHA256 = '048dfe44ddd32b2106fbc07189f410ba554defb30ba6ab072ac420eddb10b27f'


def money(value, label, *, positive=False):
    raw = str(value if value is not None else '').strip()
    if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?', raw):
        raise ValueError(f'Enter a valid {label}, with no more than two decimal places.')
    amount = Decimal(raw.replace(',', ''))
    if amount > Decimal('999999999.99') or (positive and amount <= 0):
        raise ValueError(f'Enter a valid {label}.')
    return amount


def display_money(value):
    amount = Decimal(str(value).replace(',', ''))
    return format(amount, ',.2f') if amount != amount.to_integral_value() else format(amount, ',.0f')


def parse_terms(offer):
    """Return renderer terms plus the exact total of selected assumed balances.

    Loan amount is derived here, not trusted from a previous financing choice.
    No names, source bytes, acknowledgments, or external calls belong here.
    """
    days = str(offer.get('assumptionCreditDays') or '').strip()
    if not re.fullmatch(r'\d{1,3}', days) or int(days) < 1:
        raise ValueError('Enter credit-document delivery time from 1 to 999 days.')
    docs = offer.get('assumptionCreditDocuments')
    allowed = ('credit_report', 'employment', 'funds', 'financial_statement', 'other')
    if not isinstance(docs, list) or not docs or any(v not in allowed for v in docs):
        raise ValueError('Choose at least one credit-documentation item.')
    other = ' '.join(str(offer.get('assumptionCreditOther') or '').split()) if 'other' in docs else ''
    if 'other' in docs and (not other or len(other) > 500):
        raise ValueError('Describe the other credit documentation in 500 characters or fewer.')
    loans, limits, total = {}, {}, Decimal('0')
    for key in ('first', 'second'):
        prefix = 'assumption' + key.capitalize()
        enabled = offer.get(prefix + 'Enabled') in (True, 'yes')
        if not enabled:
            loans[key] = {'enabled': False}
            limits.update({key + '_fee_cap': '', key + '_rate_cap': ''})
            continue
        lender = ' '.join(str(offer.get(prefix + 'Lender') or '').split())
        if not lender or len(lender) > 500:
            raise ValueError(f'Enter the {key}-lien lender in 500 characters or fewer.')
        balance = money(offer.get(prefix + 'Balance'), f'{key}-lien unpaid balance', positive=True)
        payment = money(offer.get(prefix + 'Payment'), f'{key}-lien monthly payment')
        fee = money(offer.get(prefix + 'FeeCap'), f'{key}-lien assumption-fee cap')
        rate = str(offer.get(prefix + 'RateCap') if offer.get(prefix + 'RateCap') is not None else '').strip()
        if not re.fullmatch(r'\d{1,3}(?:\.\d{1,4})?', rate) or Decimal(rate) > 100:
            raise ValueError(f'Enter the {key}-lien interest-rate cap from 0 to 100%.')
        loans[key] = {'enabled': True, 'lender': lender, 'balance': display_money(balance),
                      'monthly_payment': display_money(payment)}
        limits.update({key + '_fee_cap': display_money(fee), key + '_rate_cap': rate})
        total += balance
    if not total:
        raise ValueError('Choose at least one existing loan to assume.')
    adjustment = offer.get('assumptionVarianceAdjustment')
    if adjustment not in ('cash', 'sales_price'):
        raise ValueError('Choose whether a loan-balance variance adjusts cash or sales price.')
    threshold = money(offer.get('assumptionVarianceThreshold'), 'loan-balance variance threshold')
    price = money(offer.get('price'), 'sales price', positive=True)
    if total > price:
        raise ValueError('Assumed loan balances exceed the sales price. Review the financing amounts.')
    return {'credit_days': str(int(days)), 'credit_documents': list(dict.fromkeys(docs)),
            'credit_other': other, 'loans': loans, 'loan_terms': limits,
            'variance': {'adjustment': adjustment, 'termination_threshold': display_money(threshold)}}, total, price

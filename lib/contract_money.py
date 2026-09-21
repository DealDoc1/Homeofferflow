"""Exact currency amounts for contract text; never truncate cents."""
from decimal import Decimal, InvalidOperation


class CurrencyInputError(ValueError):
    """A user-supplied amount cannot be represented accurately in cents."""


def currency_amount(value):
    if value is None or value == '':
        return Decimal('0')
    try:
        amount = Decimal(str(value).replace(',', '').strip())
        if not amount.is_finite() or amount != amount.quantize(Decimal('0.01')):
            raise CurrencyInputError('Enter monetary amounts with no more than two decimal places.')
        return amount
    except (InvalidOperation, TypeError) as exc:
        raise CurrencyInputError('Enter a valid monetary amount.') from exc


def format_currency(value):
    if value is None or value == '':
        return ''
    amount = currency_amount(value)
    return format(amount, ',.0f') if amount == amount.to_integral_value() else format(amount, ',.2f')

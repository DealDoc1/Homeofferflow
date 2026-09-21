"""Lossless answers within the 02-25-26 showing form's measured blanks."""
from lib.txr_addenda_layout import inline, clean
from lib.txr1501_answers import render_continuation as _continuation
from lib.txr1501_answers import continuation_fields as _fields


def answer_layout(data, brokerage, associate):
    entries, overflow = [], {}
    customers = data.get('client_names') or []
    broker = brokerage.get('legal_name') or brokerage.get('name') or brokerage.get('dba_name') or ''
    agent = associate.get('name') or associate.get('agent_name') or ''
    # Baselines leave clearance for descenders above the actual printed rules.
    # Names stop before the adjoining license/initials label, never under it.
    for label, value, x, y, width in [
        ('Property address and city', data.get('property_address'), 110, 654, 464),
        ('Broker or firm name', broker, 190, 316, 212),
        ('Broker license number', brokerage.get('license_number'), 478, 316, 80),
        ('Associate name', agent, 190, 297, 212),
        ('Associate license number', associate.get('license_number'), 478, 297, 80),
        ('Customer 1 name', customers[0] if customers else '', 140, 235, 153),
        ('Customer 2 name', customers[1] if len(customers) > 1 else '', 140, 192, 153),
    ]:
        placed = inline(value, [(x, y, width)], 8)
        if placed is None:
            overflow[label] = clean(value)
            placed = inline('See exhibit', [(x, y, width)], 7)
            if placed is None:
                raise ValueError('Source blank cannot hold an answer-continuation reference')
        entries.extend(placed)
    return entries, overflow


def _continuation_data(data):
    # Only adapt the shared layout helper's role convention. The persisted
    # showing-form answers and recipient IDs retain their existing contract.
    return {**data, 'signer_plan': 'clients_and_associate'
            if data.get('signer_plan') == 'associate_and_clients' else 'clients_and_broker'}


def render_continuation(data, overflow):
    return _continuation(_continuation_data(data), overflow,
        title='TXR-1508 - Answer Continuation', party_label='Customer',
        description='Continuation of entered answers referenced in the attached showing form.')


def continuation_fields(data, client_count, page_count):
    return _fields(_continuation_data(data), client_count, page_count,
                   source_pages=1, prefix='txr1508')

"""Source-bounded consumer notice answers, with clear signing areas."""
from lib.txr_addenda_layout import inline, clean
from lib.txr1501_answers import render_continuation as _continuation
from lib.txr1501_answers import continuation_fields as _fields


def answer_layout(data, brokerage):
    pages = {page: [] for page in range(1, 7)}
    overflow = {}

    def put(page, value, label, blanks, *, visible=True):
        placed = inline(value, blanks, 8)
        if placed is None:
            overflow[label] = clean(value)
            placed = inline('See exhibit', blanks[:1], 7)
            if placed is None:
                raise ValueError('Source blank cannot hold an answer-continuation reference')
        if visible:
            pages[page].extend(placed)

    consumers = data.get('client_names') or []
    # These are the source's consumer-identification blanks, separate from
    # the final receipt signatures. Long values remain available in full.
    for page in range(2, 7):
        put(page, ', '.join(consumers), 'Consumer names', [(234, 756, 268)])
    put(6, data.get('additional_notice'), 'Other information',
        [(38, 324, 534), (38, 311, 534)])
    broker = brokerage.get('legal_name') or brokerage.get('name') or brokerage.get('dba_name') or ''
    put(6, broker, 'Broker printed name', [(38, 214, 248)])
    for index, value in enumerate(consumers[:2]):
        # Unsigned drafts identify the intended consumer. The signing copy
        # must leave this space clear for the person's actual signature.
        put(6, value, f'Consumer {index + 1} name', [(38, 109 if index == 0 else 75, 248)],
            visible=not data.get('_for_signing'))
    if 'Consumer names' in overflow:
        # Identify each consumer once, rather than repeating the combined
        # header list and the same individual names on the attachment.
        overflow = {
            **{f'Consumer {index + 1} name': clean(value) for index, value in enumerate(consumers[:2])},
            **{label: value for label, value in overflow.items() if label != 'Consumer names'},
        }
    return pages, overflow


def _continuation_data(data):
    return {**data, 'signer_plan': 'clients_and_associate'
            if data.get('signer_plan') == 'consumers_and_associate' else 'clients_and_broker'}


def render_continuation(data, overflow):
    return _continuation(_continuation_data(data), overflow,
        title='TXR-1506 - Answer Continuation', party_label='Consumer',
        description='Continuation of entered answers referenced in the attached consumer notice.')


def continuation_fields(data, client_count, page_count):
    return _fields(_continuation_data(data), client_count, page_count,
                   source_pages=6, prefix='txr1506')

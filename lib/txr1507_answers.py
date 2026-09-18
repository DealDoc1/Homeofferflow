"""Source-measured short-form answers, without truncation or inferred terms."""
from lib.txr_addenda_layout import inline, clean
from lib.txr1501_answers import render_continuation as _continuation
from lib.txr1501_answers import continuation_fields as _fields


def answer_layout(data, brokerage, associate):
    pages = {1: [], 2: []}
    overflow = {}

    def put(page, value, label, blanks):
        entries = inline(value, blanks, 8)
        if entries is None:
            overflow[label] = clean(value)
            entries = inline('See exhibit', blanks[:1], 7)
            if entries is None:
                entries = inline('Exhibit', blanks[:1], 7)
            if entries is None:
                raise ValueError('Source blank cannot hold an answer-continuation reference')
        pages[page].extend(entries)

    clients = data.get('client_names') or []
    broker = brokerage.get('legal_name') or brokerage.get('name') or brokerage.get('dba_name') or ''
    agent = associate.get('name') or associate.get('agent_name') or ''
    put(1, ', '.join(clients), 'Paragraph 1 - Clients', [(278, 647, 296), (56, 634, 125)])
    put(1, broker, 'Paragraph 1 - Broker', [(314, 634, 209)])
    put(1, data.get('market_area'), 'Paragraph 3 - Market Area',
        [(475, 571, 99), (56, 555, 518), (56, 539, 512)])
    put(1, data.get('term_start'), 'Paragraph 4 - Start date', [(225, 521, 70)])
    put(1, data.get('term_end'), 'Paragraph 4 - End date', [(432, 521, 97)])
    if data.get('service_level') == 'showing_services':
        put(1, data.get('showing_fee'), 'Paragraph 5 - Showing fee', [(322, 415, 63)])
    for key, label, x, y, width in [
        ('purchase_percentage', 'Purchase percentage', 158, 196, 56),
        ('purchase_flat_fee', 'Purchase flat fee', 405, 196, 97),
        ('lease_one_month_percentage', 'One month rent percentage', 140, 177, 38),
        ('lease_total_rents_percentage', 'Total rents percentage', 315, 177, 43),
        ('lease_flat_fee', 'Lease flat fee', 223, 164, 99),
    ]:
        put(1, (data.get('compensation') or {}).get(key), 'Paragraph 7A - ' + label, [(x, y, width)])
    for label, value, x, y, width in [
        ('Broker printed name', broker, 38, 292, 196),
        ('Broker license', brokerage.get('license_number'), 240, 292, 46),
        ('Associate printed name', agent, 38, 219, 196),
        ('Associate license', associate.get('license_number'), 240, 219, 46),
        ('Client 1 printed name', clients[0] if clients else '', 326, 292, 248),
        ('Client 2 printed name', clients[1] if len(clients) > 1 else '', 326, 219, 248),
    ]:
        put(2, value, 'Execution - ' + label, [(x, y, width)])
    return pages, overflow


def render_continuation(data, overflow):
    return _continuation(data, overflow, title='TXR-1507 - Answer Continuation')


def continuation_fields(data, client_count, page_count):
    return _fields(data, client_count, page_count, source_pages=2, prefix='txr1507')

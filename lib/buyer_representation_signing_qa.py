"""Fixed fictional buyer/notice/IABS specimen shared by local and protected QA.

No credentials, network, database writes or delivery side effects.
"""
from hashlib import sha256
from io import BytesIO
from copy import deepcopy
import base64
import json

from pypdf import PdfReader
from lib.representation_package import compose_representation_package
from lib.txr_1507 import render_txr_1507, build_signwell_fields_txr1507
from lib.txr_1506 import render_txr_1506, build_signwell_fields_txr1506
from lib.purchase_signing_qa import QA_OPERATOR_EMAILS, QA_RECIPIENTS

SOURCE_HASHES = {
    'TXR1507': 'ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46f',
    'TXR1506': 'df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4',
}
CASES = ('ordinary', 'two-client', 'broker', 'long-unicode')


def load_sources(directory, iabs_sha256):
    if len(iabs_sha256) != 64 or any(c not in '0123456789abcdef' for c in iabs_sha256):
        raise ValueError('Supply the verified saved-profile IABS SHA-256.')
    sources = {}
    for code, expected in {**SOURCE_HASHES, 'IABS': iabs_sha256}.items():
        value = (directory / (code + '.pdf')).read_bytes()
        if sha256(value).hexdigest() != expected:
            raise ValueError(f'{code} source hash differs from the reviewed source.')
        sources[code] = value
    return sources


def case_data(case):
    if case not in CASES:
        raise ValueError('Unknown fixed QA case.')
    clients = ['QA Buyer One']
    if case in ('two-client', 'long-unicode'):
        clients.append('QA Buyer Two')
    if case == 'long-unicode':
        clients = ['QA María-José ' + 'Fernández de la Fuente ' * 8,
                   'QA André ' + 'Müller de la Rivière ' * 8]
    role = 'broker' if case == 'broker' else 'associate'
    agreement = {
        'client_names': clients, 'market_area': 'Fictional QA market, Texas',
        'term_start': '2026-11-04', 'term_end': '2026-11-05',
        'service_level': 'full_services', 'compensation': {'purchase_percentage': '3'},
        'intermediary': 'authorized', 'signer_plan': 'clients_and_' + role,
    }
    notice = {'client_names': clients, 'signer_plan': 'consumers_and_' + role,
              '_for_signing': True,
              'additional_notice': 'Fictional QA only. Not a client engagement.'}
    if case == 'long-unicode':
        agreement['market_area'] = 'Fictional QA market area; ' * 50
        notice['additional_notice'] = 'Fictional QA: café, résumé, façade. ' * 60
    return agreement, notice, [str(i + 1) for i in range(len(clients))] + [role]


def build_case(sources, case):
    agreement, notice, recipients = case_data(case)
    brokerage = {'legal_name': 'Fictional QA Brokerage', 'license_number': '0000000'}
    associate = {'name': 'Fictional QA Associate', 'license_number': '0000000'}
    primary = render_txr_1507(sources['TXR1507'], agreement, brokerage, associate)
    related = render_txr_1506(sources['TXR1506'], notice, brokerage)
    count = len(agreement['client_names'])
    primary_fields = build_signwell_fields_txr1507(
        agreement, client_count=count, page_count=len(PdfReader(BytesIO(primary)).pages))
    related_fields = build_signwell_fields_txr1506(
        notice, client_count=count, page_count=len(PdfReader(BytesIO(related)).pages))
    return compose_representation_package(
        primary, primary_fields, related, related_fields, recipients=recipients,
        information_documents=[('IABS', sources['IABS'])])


IABS_SHA256 = '81fd0005afc341aeceb2af0f9446db566bd8f3bf2479306763c03be3788806ff'
QA_REVISION = 'ordinary-buyer-notice-iabs-2026-11-04-v1'
QA_SCENARIO = 'ordinary-buyer-package-provider-placement'
REVIEWED_SOURCE_COMMIT = '0e1e390bbd328980023ed983b9d7fc6052c8da01'
RENDER_REVISION = 'txr1507-v3-txr1506-composed-2026-11-04'
DOCUMENT_PREFIX = 'QA ONLY - ordinary buyer package - '
QA_TITLE = 'Ordinary buyer representation, consumer notice and saved IABS'
QA_DESCRIPTION = 'One fictional buyer and associate, parallel invitations; IABS information only.'
TEST_LABEL = 'buyer representation package signing'
VERIFY_DRAFT = True
LAYOUT_SHA256 = '82092c5ca574ff4a10d7fdd42e6d815a5ace9b16ac2c57f3505d84059c6cfdfd'
PACKET_SHA256 = '92a27bf2e5f7b3c4448a7e92e8b42faf48430a5787951b9a25c9dddca8c00faa'


def build_packet(sources):
    if not isinstance(sources, dict) or set(sources) != {'TXR1507', 'TXR1506', 'IABS'}:
        raise ValueError('Use exactly the reviewed buyer QA sources.')
    for code, digest in {**SOURCE_HASHES, 'IABS': IABS_SHA256}.items():
        if not isinstance(sources[code], bytes) or sha256(sources[code]).hexdigest() != digest:
            raise ValueError('The buyer QA source differs from its reviewed PDF.')
    package = build_case(sources, 'ordinary')
    roles = {'1': 'qa_a', 'associate': 'qa_b'}
    fields = [[{**field, 'recipient_id': roles[field['recipient_id']]}
               for field in package.fields[0]]]
    pages = package.manifest['page_count']
    return package.pdf, fields, [{'case': 'ordinary-buyer-notice-iabs',
        'source_pages': list(range(1, pages + 1)), 'output_pages': list(range(1, pages + 1)),
        'field_count': len(fields[0])}]


def layout_fingerprint(packet, fields):
    reader = PdfReader(BytesIO(packet))
    value = {'sources': {**SOURCE_HASHES, 'IABS': IABS_SHA256},
             'pages': [{'size': list(map(float, page.mediabox)),
                        'content': sha256(page.get_contents().get_data()).hexdigest()}
                       for page in reader.pages], 'fields': fields}
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def build_payload(packet, fields, release_sha):
    if release_sha != REVIEWED_SOURCE_COMMIT:
        raise ValueError('Use the exact reviewed buyer QA revision.')
    if (not isinstance(packet, bytes) or sha256(packet).hexdigest() != PACKET_SHA256
            or not LAYOUT_SHA256 or layout_fingerprint(packet, fields) != LAYOUT_SHA256):
        raise ValueError('The buyer specimen differs from its reviewed layout.')
    return {'test_mode': True, 'draft': True, 'apply_signing_order': False,
        'reminders': False, 'with_signature_page': False,
        'name': DOCUMENT_PREFIX + release_sha[:12],
        'subject': 'TEST ONLY: buyer representation package placement',
        'message': 'Fictional nonbinding QA, not a client agreement. QA Signer A is the buyer; QA Signer B is the associate. Complete both the representation agreement and consumer notice. The saved IABS is informational and has no signing fields. Both recipients may sign independently.',
        'recipients': [dict(item) for item in QA_RECIPIENTS],
        'files': [{'name': 'QA_ONLY_ordinary_buyer_package.pdf',
                   'file_base64': base64.b64encode(packet).decode('ascii')}],
        'fields': deepcopy(fields), 'checkbox_groups': [], 'conditional_rules': [],
        'metadata': {'qa_kind': 'ordinary-buyer-representation-package',
            'qa_revision': QA_REVISION, 'release_sha': release_sha,
            'layout_sha256': LAYOUT_SHA256}}

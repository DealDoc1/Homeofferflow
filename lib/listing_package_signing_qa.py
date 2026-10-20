"""One ordinary fictional listing/lead packet, using the actual candidate maps.

No client inputs, credentials or arbitrary document/recipient settings. This is
one transaction, not a concatenated matrix of unrelated examples.
"""
import base64
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader
from lib import txr_1101
from lib.listing_lead_disclosure import prepare_listing_lead
from lib.listing_packet import PreparedDocument, assemble_listing_packet
from lib.purchase_signing_qa import QA_RECIPIENTS, QA_OPERATOR_EMAILS

SOURCE_SHA256 = txr_1101.SOURCE_SHA256
SOURCE_ID = '02993d63-76de-4e7b-8c74-17c2c90b9443'
QA_REVISION = 'txr1101-ordinary-listing-lead-2026-10-19-v1'
QA_SCENARIO = 'txr1101-ordinary-listing-provider-placement'
REVIEWED_SOURCE_COMMIT = '42d32a7deeca39c1de0ccbd5f3860bb499bd030d'
RENDER_REVISION = txr_1101.REVISION
DOCUMENT_PREFIX = 'QA ONLY - ordinary listing package - '
QA_TITLE = 'Ordinary TXR-1101 listing and lead disclosure'
QA_DESCRIPTION = 'One fictional seller and associate; listing initials/execution and seller lead choices/details, with parallel invitations.'
TEST_LABEL = 'ordinary listing package'
VERIFY_DRAFT = True
LAYOUT_SHA256 = '49c620a7f1f61a21385b65085f53a218bc8b9f4f4214686b56a8a31c7cbe2533'


def answers():
    return {
        'client_names': ['QA Signer A'], 'client_address': '100 Fictional Lane',
        'client_city_state_zip': 'Example City, TX 75001',
        'client_phone': '214-555-0101', 'client_email': 'andrewchri@gmail.com',
        'property_address': 'QA ONLY - 100 Fictional Example Lane, Example City, TX 75001',
        'lot': '12', 'block': 'A', 'subdivision': 'QA Example Estates',
        'city': 'Example City', 'county': 'Example County', 'listing_price': '625000',
        'term_start': '2026-10-19', 'term_end': '2027-04-19', 'hoa': 'no',
        'fee_basis': 'percentage', 'fee_amount': '2.5', 'additional_fee_basis': 'none',
        'disclose_buyer_expenses': 'yes', 'protection_days': '30',
        'payment_county': 'Example County', 'mls_filing': 'standard',
        'internet_display': 'full', 'scheduling_companies': 'QA Showing Service',
        'keybox': 'yes', 'intermediary': 'authorized', 'foreign_person': 'no',
        'financing': ['conventional', 'cash'], 'addenda': ['C'],
        'signer_plan': 'clients_and_associate', '_for_signing': True,
        'special_provisions': 'QA ONLY - fictional nonbinding signing-placement test; not a client agreement.',
    }


def _recipient(value):
    if value not in {'1', 'associate'}:
        raise ValueError('Only the two fixed fictional listing roles may sign this test.')
    return 'qa_a' if value == '1' else 'qa_b'


def completion_controls():
    groups, rules = [], []
    for key in ('knowledge', 'records'):
        prefix = 'listing_C_lead_' + key
        positive = prefix + '_positive'
        groups.append({'group_name': prefix, 'recipient_id': 'qa_a',
            'checkbox_ids': [positive, prefix + '_negative'],
            'validation': 'exact', 'required': True, 'exact_value': 1})
        rules.append({'target_id': positive, 'action_type': 'require',
            'action_field_ids': [prefix + '_explanation'],
            'conditions': [{'condition_type': 'all_of', 'status': 'completed',
                'field_api_ids': [positive], 'position': 1}]})
    return groups, rules


def layout_fingerprint(packet, fields):
    groups, rules = completion_controls()
    reader = PdfReader(BytesIO(packet))
    return hashlib.sha256(json.dumps({
        'source': SOURCE_SHA256, 'revision': RENDER_REVISION,
        'pages': [hashlib.sha256(page.get_contents().get_data()).hexdigest() for page in reader.pages],
        'fields': fields, 'groups': groups, 'rules': rules,
    }, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def build_packet(source):
    if not isinstance(source, bytes) or hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('Use the exact registered, reviewed TXR-1101 source.')
    data = answers()
    brokerage = {'legal_name': 'QA Review Realty', 'license_number': '0000000',
        'address': '10 Fictional Lane', 'city_state_zip': 'Example City, TX 75001',
        'phone': '214-555-0100', 'email': 'qa-office@example.test'}
    associate = {'agent_name': 'QA Signer B', 'license_number': '0000001'}
    listing = txr_1101.render_txr_1101(source, data, brokerage, associate)
    listing_fields = txr_1101.build_signwell_fields_txr1101(data, client_count=1,
        page_count=len(PdfReader(BytesIO(listing)).pages))
    lead = prepare_listing_lead((Path(__file__).resolve().parents[1] / 'lead_based_paint_56-0.pdf').read_bytes(), data)
    related = PreparedDocument('C', lead.pdf, lead.fields, {'1': '1', 'associate': 'associate'},
        lead.content_fingerprint, lead.checkbox_groups, lead.conditional_rules)
    result = assemble_listing_packet(data, listing, listing_fields, documents=[related])
    fields = [[{**field, 'recipient_id': _recipient(field['recipient_id'])} for field in result.fields[0]]]
    groups = [{**group, 'recipient_id': _recipient(group['recipient_id'])} for group in result.checkbox_groups]
    if (groups, result.conditional_rules) != completion_controls() or result.manifest['pending']:
        raise ValueError('Review the actual listing completion controls before sending.')
    if result.manifest['page_count'] != 12 or len(fields[0]) != 34:
        raise ValueError('The ordinary listing packet shape changed; review it before sending.')
    manifest = [{'case': 'ordinary-one-seller-and-associate', 'source_pages': list(range(1, 11)),
        'output_pages': list(range(1, 13)), 'field_count': len(fields[0])}]
    return result.pdf, fields, manifest


def build_payload(packet, fields, release_sha):
    if release_sha != REVIEWED_SOURCE_COMMIT:
        raise ValueError('Use the exact reviewed listing renderer revision.')
    if not LAYOUT_SHA256 or layout_fingerprint(packet, fields) != LAYOUT_SHA256:
        raise ValueError('The ordinary listing packet has not matched its reviewed layout.')
    groups, rules = completion_controls()
    return {'test_mode': True, 'draft': True, 'apply_signing_order': False,
        'reminders': False, 'with_signature_page': False,
        'name': DOCUMENT_PREFIX + release_sha[:12],
        'subject': 'TEST ONLY: one ordinary listing agreement and lead disclosure',
        'message': 'Fictional nonbinding QA, not a client agreement. QA Signer A is the Seller and QA Signer B is the Associate. Seller: choose known lead hazards and no reports, and enter a short QA-only explanation. Both recipients may sign independently. This is one transaction, not multiple example contracts.',
        'recipients': [dict(item) for item in QA_RECIPIENTS],
        'files': [{'name': 'QA_ONLY_ordinary_listing_and_lead.pdf',
            'file_base64': base64.b64encode(packet).decode('ascii')}],
        'fields': deepcopy(fields), 'checkbox_groups': groups, 'conditional_rules': rules,
        'metadata': {'qa_kind': 'ordinary-txr1101-listing', 'qa_revision': QA_REVISION,
            'release_sha': release_sha, 'layout_sha256': LAYOUT_SHA256}}

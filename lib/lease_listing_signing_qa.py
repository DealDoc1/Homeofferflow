"""One fictional rental listing, not a concatenated customer-facing QA matrix.

Pure preparation only: no source lookup, credentials, provider calls or sends.
Uses the same source renderers, field maps and composer as the lease workflow.
"""
import base64
from copy import deepcopy
import hashlib
from io import BytesIO
import json

from pypdf import PdfReader
from lib import txr_1102
from lib.lease_disclosures import SOURCES, prepare_lease_disclosure
from lib.listing_packet import PreparedDocument, assemble_lease_listing_packet
from lib.purchase_signing_qa import QA_OPERATOR_EMAILS, QA_RECIPIENTS

SOURCE_ID = '562ded06-26f0-44e3-9162-a7895932b3cc'
SOURCE_SHA256 = txr_1102.SOURCE_SHA256
QA_REVISION = 'txr1102-ordinary-rental-disclosures-2026-10-20-v1'
QA_SCENARIO = 'txr1102-ordinary-lease-provider-placement'
REVIEWED_SOURCE_COMMIT = '3d912b0c837df38ed879bb3b289036e977fe7b80'
RENDER_REVISION = txr_1102.REVISION
DOCUMENT_PREFIX = 'QA ONLY - ordinary lease listing - '
QA_TITLE = 'Ordinary lease listing and landlord disclosures'
QA_DESCRIPTION = 'One fictional landlord and associate; rental flood/lead choices and lower signature row, with parallel invitations.'
TEST_LABEL = 'ordinary lease listing package'
VERIFY_DRAFT = True
LAYOUT_SHA256 = '43da47ab3b15cb1c0f1d3ed238690684c10628d0b3f48b64ec87fbdff3adbd74'


def answers():
    return {
        'client_names': ['QA Signer A'], 'client_address': '200 Fictional Client Lane',
        'client_city_state_zip': 'Example City, TX 75001', 'client_phone': '214-555-0101',
        'client_email': 'andrewchri@gmail.com',
        'property_address': 'QA ONLY - 100 Fictional Rental Lane, Example City, TX 75001',
        'lot': '12', 'block': 'A', 'subdivision': 'QA Example Estates',
        'city': 'Example City', 'county': 'Example County', 'listing_price': '2500',
        'lease_min_months': '12', 'lease_max_months': '24',
        'term_start': '2026-11-01', 'term_end': '2027-03-01', 'hoa': 'no',
        'fee_scope': 'with_other_broker', 'fee_basis': 'month_percentage', 'fee_amount': '100',
        'cobroker_basis': 'month_percentage', 'cobroker_amount': '50',
        'renewal_basis': 'total_percentage', 'renewal_amount': '2.5',
        'sale_fee_basis': 'percentage', 'sale_fee_amount': '3',
        'protection_days': '30', 'payment_county': 'Example County',
        'mls_filing': 'standard', 'internet_display': 'full', 'keybox': 'yes',
        'intermediary': 'authorized', 'make_ready': 'not_authorized',
        'signer_plan': 'clients_and_associate', 'addenda': ['B', 'C'],
        'built_before_1978': 'yes', '_for_signing': True,
        'special_provisions': 'QA ONLY - fictional nonbinding placement test. Not a client agreement.',
    }


def _recipient(value):
    if value not in {'1', 'associate'}:
        raise ValueError('Only the two fixed fictional lease roles may sign this test.')
    return 'qa_a' if value == '1' else 'qa_b'


def completion_controls():
    groups, rules = [], []
    for key in ('floodplain', 'flooding_last_five_years'):
        prefix = 'listing_B_lease2015_' + key
        groups.append({'group_name': prefix, 'recipient_id': 'qa_a',
            'checkbox_ids': [prefix + '_aware', prefix + '_not_aware'],
            'validation': 'exact', 'required': True, 'exact_value': 1})
    for key in ('knowledge', 'records'):
        prefix = 'listing_C_lease2008_' + key
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
    return hashlib.sha256(json.dumps({
        'sources': {'TXR-1102': SOURCE_SHA256, **{k: v['sha256'] for k, v in SOURCES.items()}},
        'revisions': [RENDER_REVISION] + [v['render_revision'] for v in SOURCES.values()],
        'pages': [hashlib.sha256(p.get_contents().get_data()).hexdigest()
                  for p in PdfReader(BytesIO(packet)).pages],
        'fields': fields, 'groups': groups, 'rules': rules,
    }, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def build_packet(sources):
    if not isinstance(sources, dict) or set(sources) != {'TXR-1102', *SOURCES}:
        raise ValueError('Use exactly the three reviewed private lease sources.')
    data = answers()
    brokerage = {'legal_name': 'QA Review Realty', 'license_number': '0000000',
        'address': '10 Fictional Office Lane', 'city_state_zip': 'Example City, TX 75001',
        'phone': '214-555-0100', 'email': 'qa-office@example.test'}
    associate = {'agent_name': 'QA Signer B', 'license_number': '0000001'}
    primary = txr_1102.render_txr_1102(sources['TXR-1102'], data, brokerage, associate)
    primary_fields = txr_1102.build_signwell_fields_txr1102(data, client_count=1,
        page_count=len(PdfReader(BytesIO(primary)).pages))
    documents = []
    for code, form_code in [('B', 'TXR-2015'), ('C', 'TXR-2008')]:
        prepared = prepare_lease_disclosure(form_code, sources[form_code], data)
        documents.append(PreparedDocument(code, prepared.pdf, prepared.fields,
            {'1': '1', 'associate': 'associate'}, prepared.content_fingerprint,
            prepared.checkbox_groups, prepared.conditional_rules,
            remaining_actions=prepared.remaining_actions))
    result = assemble_lease_listing_packet(data, primary, primary_fields, documents=documents)
    fields = [[{**f, 'recipient_id': _recipient(f['recipient_id'])} for f in result.fields[0]]]
    groups = [{**g, 'recipient_id': _recipient(g['recipient_id'])} for g in result.checkbox_groups]
    if (groups, result.conditional_rules) != completion_controls() or result.manifest['pending']:
        raise ValueError('Review the actual lease completion controls before provider use.')
    if result.manifest['page_count'] != 14:
        raise ValueError('Review the changed ordinary lease packet page count.')
    manifest = [{'case': 'ordinary-one-landlord-and-associate',
        'source_pages': list(range(1, 12)), 'output_pages': list(range(1, 15)),
        'field_count': len(fields[0])}]
    return result.pdf, fields, manifest


def build_payload(packet, fields, release_sha):
    import re
    if not re.fullmatch(r'[0-9a-f]{40}', REVIEWED_SOURCE_COMMIT) or release_sha != REVIEWED_SOURCE_COMMIT:
        raise ValueError('Use the exact reviewed lease renderer revision.')
    if not LAYOUT_SHA256 or layout_fingerprint(packet, fields) != LAYOUT_SHA256:
        raise ValueError('The lease specimen has not matched its reviewed layout.')
    groups, rules = completion_controls()
    return {'test_mode': True, 'draft': True, 'apply_signing_order': False,
        'reminders': False, 'with_signature_page': False,
        'name': DOCUMENT_PREFIX + release_sha[:12],
        'subject': 'TEST ONLY: one lease listing and landlord disclosures',
        'message': 'Fictional nonbinding QA, not a client agreement. QA Signer A is the Landlord and QA Signer B is the Associate. Landlord: select not aware of the floodplain, aware of flooding, known lead hazards, and no lead reports; enter a short fictional explanation. Both recipients may sign independently. Tenant receipt/signature and lead pamphlet/report delivery are not completed by this test.',
        'recipients': [dict(item) for item in QA_RECIPIENTS],
        'files': [{'name': 'QA_ONLY_ordinary_lease_listing.pdf',
                   'file_base64': base64.b64encode(packet).decode('ascii')}],
        'fields': deepcopy(fields), 'checkbox_groups': groups, 'conditional_rules': rules,
        'metadata': {'qa_kind': 'ordinary-txr1102-listing', 'qa_revision': QA_REVISION,
            'release_sha': release_sha, 'layout_sha256': LAYOUT_SHA256}}

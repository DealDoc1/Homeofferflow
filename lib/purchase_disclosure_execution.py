"""Server-side composition for a reviewed, not-yet-signed seller disclosure.

Not a public API or delivery authorization. Callers must read the owned offer,
draft and review links from the database, fetch approved private sources, and
atomically bind the returned revision before any provider send. This module
has no network or database side effects and is not customer-activated yet.
"""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import uuid

from pypdf import PdfReader, PdfWriter

from lib.purchase_disclosure_receipt import address_matches
from lib.seller_disclosure_explanations import (
    RENDER_REVISION, append_explanations, continuation_fields,
)
from lib.seller_questionnaire import parse_answers
from lib.seller_review_access import current_review, normalize_email, normalize_seller_name
from lib.trec_seller_disclosure import build_signwell_fields, render_unsigned_preview


class DisclosureNotReady(ValueError):
    """Leave this optional document pending, not the other ready documents."""


@dataclass(frozen=True)
class PurchaseDisclosureExecution:
    pdf: bytes
    fields: list
    recipients: list
    binding: dict
    content_fingerprint: str
    pdf_sha256: str
    continuation_pages: tuple


def _identifier(value):
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        raise PermissionError('A verified account and saved offer are required.') from None


def _names(offer):
    def first(keys):
        return next((str(offer[key]).strip() for key in keys if str(offer.get(key) or '').strip()), '')
    return [value for value in (first(('seller1Name','seller1','seller')), first(('seller2Name','seller2'))) if value]


def prepare_execution(record, draft, review_links, *, user_id, source_pdf, water_pdf=None, for_retry=False):
    """Prepare exact reviewed facts and roles from authoritative server reads.

    Missing/incomplete disclosure raises DisclosureNotReady. Wrong ownership
    raises PermissionError; neither condition may be silently replaced with a
    browser-provided PDF or signer plan. Buyer IDs remain 1/2, Seller IDs 3/4.
    """
    user_id = _identifier(user_id)
    offer_id = _identifier(record.get('id'))
    if record.get('user_id') != user_id:
        raise PermissionError('The saved offer belongs to another account.')
    if draft is None:
        raise DisclosureNotReady('Complete the seller disclosure separately when it is ready.')
    if draft.get('agent_user_id') != user_id:
        raise PermissionError('The private disclosure belongs to another account.')
    draft_id = _identifier(draft.get('id'))
    offer = record.get('offer_data')
    if not isinstance(offer, dict):
        raise ValueError('Review the saved offer before including a disclosure.')
    journal = offer.get('_hof_signature_delivery')
    previous_binding = journal.get('seller_disclosure') if isinstance(journal, dict) else None
    retry = bool(for_retry and record.get('signwell_document_id')
        and isinstance(journal, dict) and journal.get('document_id') == record['signwell_document_id']
        and draft.get('signature_offer_id') == offer_id and isinstance(previous_binding, dict)
        and previous_binding.get('id') == draft_id and previous_binding.get('offer_id') == offer_id
        and previous_binding.get('user_id') == user_id)
    if not retry and (record.get('signwell_document_id') or '_hof_signature_delivery' in offer
            or str(record.get('status') or 'draft').lower() not in {'draft','generating','generated','generation failed'}):
        raise DisclosureNotReady('This offer has a signing request. Check its status before preparing another.')
    if (draft.get('status') != 'draft' or draft.get('signwell_document_id')
            or draft.get('signature_packet_id') or (draft.get('signature_offer_id') and not retry)
            or '_hof_signature_delivery' in (draft.get('response_data') or {})
            or draft.get('seller_review_attested') is not True
            or draft.get('seller_review_render_revision') != RENDER_REVISION):
        raise DisclosureNotReady('The disclosure needs current seller review or has a separate signing request.')
    sellers = draft.get('seller_names')
    offer_sellers = _names(offer)
    if not isinstance(sellers, list) or not 1 <= len(sellers) <= 2 or draft.get('buyer_names'):
        raise DisclosureNotReady('Choose a seller-only disclosure for this purchase.')
    normalized = [normalize_seller_name(name) for name in sellers]
    if (not all(normalized) or len(set(normalized)) != len(normalized)
            or len(offer_sellers) != len(sellers)
            or set(normalized) != {normalize_seller_name(name) for name in offer_sellers}
            or not address_matches(draft.get('property_address'), offer)):
        raise DisclosureNotReady('Choose the disclosure for this property and these sellers.')
    water = bool(draft.get('water_source_id'))
    if (draft.get('disclosure_source_revision') != '05-04-2026'
            or water and draft.get('water_source_revision') != '05-04-2026'
            or water != (water_pdf is not None)):
        raise DisclosureNotReady('Load the complete approved disclosure sources before continuing.')
    main = draft.get('response_data') or {}
    answers = {key: value for key, value in main.items() if not key.startswith('_')}
    try:
        revision, answers, water_answers = parse_answers({
            'reviewContentRevision': draft.get('review_content_revision'),
            'responseData': answers, 'waterRightsData': draft.get('water_rights_data') or {},
        }, has_water=water, require_complete=True)
    except ValueError as error:
        raise DisclosureNotReady(str(error)) from error

    recipients, buyer_names = [], []
    for index, name_key, email_key in ((1, 'buyer1', 'buyerEmail'), (2, 'buyer2', 'buyer2Email')):
        name, email = str(offer.get(name_key) or '').strip(), offer.get(email_key)
        if index == 2 and not name and not email:
            continue
        if not name:
            raise ValueError('Enter each buyer name and signing email.')
        recipients.append({'id': str(index), 'name': name, 'email': normalize_email(email)})
        buyer_names.append(name)

    if not isinstance(review_links, list):
        raise DisclosureNotReady('Every seller must confirm the current disclosure answers.')
    proofs = []
    for index, name in enumerate(sellers, 1):
        candidates = [link for link in review_links if isinstance(link, dict)
                      and type(link.get('seller_index')) is int and link['seller_index'] == index
                      and link.get('draft_id') == draft_id and link.get('agent_user_id') == user_id
                      and link.get('brokerage_id') == draft.get('brokerage_id')
                      and current_review(link, draft, RENDER_REVISION)
                      and normalize_seller_name(link.get('seller_name')) == normalized[index - 1]
                      and normalize_seller_name(link.get('seller_attested_name')) == normalized[index - 1]
                      and link.get('seller_attested_at')]
        if len(candidates) != 1:
            raise DisclosureNotReady('Every seller must confirm the current disclosure answers.')
        link = candidates[0]
        # Use the reviewed seller's verified destination, never an offer alias.
        email = normalize_email(link.get('seller_email'))
        offer_index = [normalize_seller_name(value) for value in offer_sellers].index(normalized[index - 1])
        recipients.append({'id': str(offer_index + 3), 'name': str(name).strip(), 'email': email})
        proofs.append({'id': link['id'], 'seller_index': index, 'email': email,
                       'attested_at': link['seller_attested_at']})
    if len({row['email'] for row in recipients}) != len(recipients):
        raise ValueError('Each buyer and seller must use a different signing email.')

    parties = {'seller_names': sellers, 'buyer_names': buyer_names}
    explanations = []
    address = draft['property_address']
    pdf = render_unsigned_preview(source_pdf, 'TREC-55-1', {**answers, 'propertyAddress': address},
                                  qa_mode=True, continuation_sink=explanations)
    fields = build_signwell_fields('TREC-55-1', parties)[0]
    if water:
        extra = render_unsigned_preview(water_pdf, 'TREC-61-0',
            {**water_answers, 'propertyAddress': address}, qa_mode=True, continuation_sink=explanations)
        writer, output = PdfWriter(), BytesIO()
        for payload in (pdf, extra):
            writer.append(PdfReader(BytesIO(payload)))
        writer.write(output)
        pdf = output.getvalue()
        fields.extend(build_signwell_fields('TREC-61-0', parties, page_offset=4)[0])
    pdf, pages = append_explanations(pdf, explanations, property_address=address, parties=parties)
    fields.extend(continuation_fields(parties, pages))
    role_ids = {str(i): str([normalize_seller_name(value) for value in offer_sellers].index(name) + 3)
                for i, name in enumerate(normalized, 1)}
    role_ids.update({str(len(sellers) + i): str(i) for i in range(1, len(buyer_names) + 1)})
    fields = [{**field, 'api_id': 'purchase_disclosure_' + field['api_id'],
               'recipient_id': role_ids[field['recipient_id']]} for field in fields]
    recipients.sort(key=lambda row: int(row['id']))
    binding = {'id': draft_id, 'revision': revision, 'render_revision': RENDER_REVISION,
               'offer_id': offer_id, 'user_id': user_id}
    identity = {'binding': binding, 'sources': [hashlib.sha256(source_pdf).hexdigest(),
                hashlib.sha256(water_pdf).hexdigest() if water else None],
                'answers': answers, 'water': water_answers, 'address': address,
                'recipients': recipients, 'proofs': proofs, 'fields': fields}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    binding = {**binding, 'fingerprint': fingerprint}
    if retry and binding != previous_binding:
        raise DisclosureNotReady('The saved disclosure no longer matches this signing request. Check the existing request instead.')
    return PurchaseDisclosureExecution(pdf, fields, recipients, binding, fingerprint,
        hashlib.sha256(pdf).hexdigest(), tuple(pages))


def append_execution(packet_pdf, plan):
    """Append the exact prepared PDF and offset its fields, without delivery."""
    if hashlib.sha256(plan.pdf).hexdigest() != plan.pdf_sha256:
        raise ValueError('The disclosure changed. Prepare the reviewed package again.')
    packet = PdfReader(BytesIO(packet_pdf))
    offset = len(packet.pages)
    writer, output = PdfWriter(), BytesIO()
    writer.append(packet)
    writer.append(PdfReader(BytesIO(plan.pdf)))
    writer.write(output)
    return output.getvalue(), [{**field, 'page': field['page'] + offset} for field in plan.fields]

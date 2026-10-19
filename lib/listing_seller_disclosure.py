"""Attach a reviewed seller disclosure without inventing parties or answers."""
import hashlib
import json

from lib.listing_packet import PreparedDocument
from lib.seller_disclosure_explanations import RENDER_REVISION, continuation_fields
from lib.seller_questionnaire import parse_answers
from lib.seller_review_access import normalize_seller_name
from lib.trec_seller_disclosure import build_signwell_fields


def matching_sellers(listing, disclosure):
    listing_names = [normalize_seller_name(n) for n in listing.get('client_names') or []]
    names = [normalize_seller_name(n) for n in disclosure.get('seller_names') or []]
    if (not 1 <= len(names) <= 2 or len(names) != len(listing_names)
            or len(set(names)) != len(names) or set(names) != set(listing_names)
            or disclosure.get('buyer_names')
            or normalize_seller_name(listing.get('property_address')) != normalize_seller_name(disclosure.get('property_address'))):
        return None
    return {str(i): str(listing_names.index(name)+1) for i,name in enumerate(names,1)}


def prepare_reviewed_disclosure(listing, disclosure, packet, render_context, layout_context):
    recipients = matching_sellers(listing, disclosure)
    if recipients is None:
        raise ValueError('Choose the disclosure for this property and these sellers.')
    water = bool(disclosure.get('water_source_id'))
    if water and 'P' not in listing.get('addenda', []):
        raise ValueError('This disclosure includes water rights. Include that document or complete the disclosure separately.')
    parse_answers({'reviewContentRevision':disclosure.get('review_content_revision'),
                   'responseData':{k:v for k,v in (disclosure.get('response_data') or {}).items() if not k.startswith('_')},
                   'waterRightsData':disclosure.get('water_rights_data') or {}},has_water=water,require_complete=True)
    parties = {'seller_names':disclosure['seller_names'],'buyer_names':[]}
    fields = build_signwell_fields('TREC-55-1',parties)[0]
    if water: fields.extend(build_signwell_fields('TREC-61-0',parties,page_offset=4)[0])
    fields.extend(continuation_fields(parties,layout_context.get('continuation_pages',[])))
    identity = {'draft':disclosure['id'],'version':disclosure['review_content_revision'],
                'render':RENDER_REVISION,'sources':render_context,'parties':parties,
                'answers':disclosure.get('response_data') or {},'water':disclosure.get('water_rights_data') or {},
                'property':disclosure.get('property_address'),'fields':fields,'recipients':recipients}
    fingerprint = hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    return PreparedDocument('B',packet,[fields],recipients,fingerprint,
                            contained_documents={'P':(5,6)} if water else {},
                            disclosure_binding={'id':disclosure['id'],'revision':disclosure['review_content_revision'],
                                                'render_revision':RENDER_REVISION})

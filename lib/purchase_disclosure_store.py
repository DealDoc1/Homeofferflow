"""Read-only, owner-scoped reconstruction of a purchase disclosure plan.

No caller-supplied PDF, answers, recipients or field plan is accepted. Sources
stay private and server-side. Delivery must additionally checkpoint the plan's
binding through the coordinated purchase-disclosure database guard.
"""
from urllib.parse import quote
import uuid

import httpx

from lib.purchase_disclosure_execution import DisclosureNotReady, prepare_execution


def _uuid(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Choose a saved offer and seller disclosure.') from None


class PurchaseDisclosureStore:
    def __init__(self, *, supabase_url, service_key, client=None):
        if not supabase_url or not service_key:
            raise RuntimeError('Your saved disclosure is temporarily unavailable.')
        self.url = supabase_url.rstrip('/')
        self.headers = {'apikey': service_key, 'Authorization': 'Bearer ' + service_key}
        self.client = client or httpx

    def _rows(self, table, params):
        response = self.client.get(self.url + '/rest/v1/' + table, headers=self.headers,
                                   params=params, timeout=20)
        if response.status_code != 200:
            raise RuntimeError('Your saved disclosure could not be loaded. Please try again.')
        rows = response.json()
        if not isinstance(rows, list):
            raise RuntimeError('Your saved disclosure could not be confirmed.')
        return rows

    def _source(self, source_id, code, revision):
        source_id = _uuid(source_id)
        rows = self._rows('hof_brokerage_form_sources', {
            'id': 'eq.' + source_id, 'form_code': 'eq.' + code,
            'status': 'eq.approved', 'authorization_attested': 'eq.true',
            'select': 'id,form_code,status,authorization_attested,source_revision,storage_bucket,storage_path', 'limit': '1',
        })
        if (len(rows) != 1 or rows[0].get('id') != source_id or rows[0].get('form_code') != code
                or rows[0].get('status') != 'approved' or rows[0].get('authorization_attested') is not True
                or rows[0].get('source_revision') != revision
                or not rows[0].get('storage_bucket') or not rows[0].get('storage_path')):
            raise DisclosureNotReady('The approved disclosure source is unavailable. Complete it separately when ready.')
        row = rows[0]
        response = self.client.get(self.url + '/storage/v1/object/'
            + quote(row['storage_bucket'], safe='') + '/' + quote(row['storage_path'], safe='/'),
            headers=self.headers, timeout=20)
        if response.status_code != 200 or not response.content.startswith(b'%PDF-') or len(response.content) > 2 * 1024 * 1024:
            raise DisclosureNotReady('The complete disclosure PDF is temporarily unavailable.')
        return response.content

    def prepare(self, *, user_id, offer_id, draft_id):
        user_id, offer_id, draft_id = map(_uuid, (user_id, offer_id, draft_id))
        offers = self._rows('hof_offers', {'id': 'eq.' + offer_id, 'user_id': 'eq.' + user_id,
            'select': 'id,user_id,status,signwell_document_id,offer_data,last_updated', 'limit': '1'})
        if len(offers) != 1 or offers[0].get('id') != offer_id or offers[0].get('user_id') != user_id:
            raise PermissionError('The saved offer is unavailable for this account.')
        if (offers[0].get('signwell_document_id')
                or str(offers[0].get('status') or 'draft').lower() not in {'draft','generating','generated','generation failed'}):
            raise DisclosureNotReady('This offer has a signing request. Check its status before preparing another.')
        drafts = self._rows('hof_seller_disclosure_drafts', {'id': 'eq.' + draft_id,
            'agent_user_id': 'eq.' + user_id, 'select': '*', 'limit': '1'})
        # One owned row, never an account-wide table export. Optional listing
        # binding column is retained when that separate additive release exists.
        if len(drafts) != 1 or drafts[0].get('id') != draft_id or drafts[0].get('agent_user_id') != user_id:
            raise PermissionError('The private disclosure is unavailable for this account.')
        draft = drafts[0]
        if (draft.get('status') != 'draft' or draft.get('seller_review_attested') is not True
                or draft.get('signwell_document_id') or draft.get('signature_packet_id') or draft.get('signature_offer_id')):
            raise DisclosureNotReady('The disclosure needs seller review or has a separate signing request.')
        links = self._rows('hof_seller_disclosure_review_links', {
            'draft_id': 'eq.' + draft_id, 'agent_user_id': 'eq.' + user_id,
            'brokerage_id': 'eq.' + _uuid(draft.get('brokerage_id')),
            'review_content_revision': 'eq.' + _uuid(draft.get('review_content_revision')),
            'revoked_at': 'is.null', 'seller_attested_at': 'not.is.null',
            'select': 'id,draft_id,agent_user_id,brokerage_id,seller_index,seller_name,seller_email,seller_attested_name,seller_attested_at,review_content_revision,review_render_revision,revoked_at',
        })
        main = self._source(draft.get('disclosure_source_id'), 'TREC-55-1', draft.get('disclosure_source_revision'))
        water = self._source(draft['water_source_id'], 'TREC-61-0', draft.get('water_source_revision')) if draft.get('water_source_id') else None
        return prepare_execution(offers[0], draft, links, user_id=user_id, source_pdf=main, water_pdf=water)

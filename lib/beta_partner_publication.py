"""Owner-authorized, no-charge creative publication; never agreement execution."""
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit
import uuid

import httpx
from lib.partner_public_profile import PUBLIC_PROFILE_COLUMNS, approved_public_profile

FIELDS = 'id,company_name,partner_type,partner_program,status,onboarding_website_url,onboarding_logo_url,onboarding_market_area,market_area,partner_agreement_status,partner_agreement_signed_at,message,' + ','.join(PUBLIC_PROFILE_COLUMNS)


def _https_url(value):
    text = str(value or '').strip()
    url = urlsplit(text)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or len(text) > 500:
        raise ValueError('Save a valid HTTPS website and logo before publishing the beta profile.')
    return text


async def publish(supabase_url, service_key, lead_id, authorized_by):
    """Caller must be a platform admin or the reviewed protected production job."""
    lead_id = str(uuid.UUID(str(lead_id)))
    actor = ' '.join(str(authorized_by or '').split())
    if not actor or len(actor) > 250:
        raise ValueError('Publication needs its HomeOfferFlow operator recorded.')
    if not supabase_url or not service_key or service_key.startswith('sb_publishable_'):
        raise RuntimeError('Partner publication connection is not configured.')
    base = supabase_url.rstrip('/') + '/rest/v1/'
    headers = {'apikey': service_key, 'Prefer': 'return=representation'}
    if not service_key.startswith('sb_secret_'):
        headers['Authorization'] = 'Bearer ' + service_key
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        response = await client.get(base + 'hof_partner_leads?' + urlencode({'id': 'eq.' + lead_id, 'select': FIELDS, 'limit': 1}))
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError('That beta application is unavailable.')
        lead = rows[0]
        if lead.get('id') != lead_id or lead.get('partner_program') != 'beta' or lead.get('status') != 'qualified':
            raise ValueError('Publish only a qualified no-charge beta application.')
        profile = approved_public_profile(lead)
        if lead.get('onboarding_public_contact_phone') and not profile['public_contact_phone']:
            raise ValueError('Save a valid explicitly public contact number before publishing.')
        name = str(lead.get('company_name') or '').strip()
        market = str(lead.get('onboarding_market_area') or lead.get('market_area') or '').strip()
        if not name or len(name) > 250 or not market or len(market) > 300 or not profile['public_description']:
            raise ValueError('Save the company, market and public description before publishing.')
        website, logo = _https_url(lead.get('onboarding_website_url')), _https_url(lead.get('onboarding_logo_url'))
        if lead.get('partner_type') not in {'roofing', 'general_contractor', 'hvac', 'plumbing', 'electrical', 'foundation_structural', 'pest_termite', 'septic_well', 'restoration', 'repairs_handyman', 'photography_video', 'staging', 'cleaning', 'moving_storage', 'lawn_pool', 'security_smart_home', 'home_warranty', 'insurance', 'other'}:
            raise ValueError('Use the signed-agreement placement workflow for this category.')
        query = urlencode({'source_lead_id': 'eq.' + lead_id, 'is_active': 'eq.true', 'select': 'id,source_lead_id,monthly_fee,brokerage_id', 'limit': 1})
        existing = await client.get(base + 'hof_partner_placements?' + query)
        existing.raise_for_status()
        active = existing.json()
        if active:
            if active[0].get('monthly_fee') != 0 or active[0].get('brokerage_id') is not None:
                raise ValueError('Existing placement is not a platform-wide free beta profile.')
            return {'placementId': active[0]['id'], 'published': True, 'alreadyPublished': True, 'monthlyFee': 0}
        now = datetime.now(timezone.utc).isoformat()
        marker = 'HomeOfferFlow-authorized free beta publication'
        message = str(lead.get('message') or '')
        if marker not in message:
            message += f'\n\n{marker} by {actor} at {now}. No charge or automatic paid conversion; no partner signature is asserted.'
        update = await client.patch(base + 'hof_partner_leads?' + urlencode({'id': 'eq.' + lead_id, 'partner_program': 'eq.beta', 'status': 'eq.qualified'}), json={'onboarding_status': 'complete', 'onboarding_completed_at': now, 'onboarding_token_hash': None, 'onboarding_token_expires_at': None, 'message': message, 'updated_at': now})
        update.raise_for_status()
        if not update.json():
            raise RuntimeError('Beta application changed while publication was prepared.')
        record = {'brokerage_id': None, 'source_lead_id': lead_id, 'partner_name': name, 'partner_type': lead['partner_type'], 'website_url': website, 'logo_url': logo, 'market_area': market, 'placement_tier': 'founding', 'monthly_fee': 0, 'is_active': True, 'activated_at': now, 'agreement_confirmed_at': lead.get('partner_agreement_signed_at') if lead.get('partner_agreement_status') == 'signed' else None}
        saved = await client.post(base + 'hof_partner_placements', json=record)
        # The existing unique index is the race-safe boundary. A retry after
        # a simultaneous successful publish must not create another placement.
        if saved.status_code == 409:
            active = await client.get(base + 'hof_partner_placements?' + query)
            active.raise_for_status()
            rows = active.json()
            if rows and rows[0].get('monthly_fee') == 0 and rows[0].get('brokerage_id') is None:
                return {'placementId': rows[0]['id'], 'published': True, 'alreadyPublished': True, 'monthlyFee': 0}
        saved.raise_for_status()
        result = saved.json()
        if not isinstance(result, list) or len(result) != 1 or not result[0].get('id'):
            raise RuntimeError('Published beta profile was not returned.')
        return {'placementId': result[0]['id'], 'published': True, 'alreadyPublished': False, 'monthlyFee': 0}

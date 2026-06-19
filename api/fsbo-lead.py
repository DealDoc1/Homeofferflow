import os
import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone

import httpx

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    or os.environ.get('SUPABASE_SERVICE_ROLE')
    or os.environ.get('SUPABASE_SERVICE_KEY')
    or ''
)
MAX_BODY_BYTES = 60_000


def _send(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(body)


def _text(value, max_len=500):
    if value is None:
        return None
    value = ' '.join(str(value).strip().split())
    return value[:max_len] if value else None


def _money(value):
    try:
        if value is None or value == '':
            return None
        return float(str(value).replace('$', '').replace(',', ''))
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _send(self, 204, {})

    def do_POST(self):
        try:
            if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
                return _send(self, 500, {'error': 'Supabase service role is not configured.'})
            length = int(self.headers.get('Content-Length', '0') or '0')
            if length <= 0 or length > MAX_BODY_BYTES:
                return _send(self, 400, {'error': 'Invalid request size.'})
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            property_address = _text(data.get('property_address') or data.get('address'), 500)
            seller_email = _text(data.get('seller_email') or data.get('email'), 250)
            if not property_address or not seller_email:
                return _send(self, 400, {'error': 'Property address and seller email are required.'})

            payload = {
                'seller_type': 'fsbo',
                'property_address': property_address,
                'seller_name': _text(data.get('seller_name') or data.get('name'), 250),
                'seller_email': seller_email,
                'seller_phone': _text(data.get('seller_phone') or data.get('phone'), 80),
                'asking_price': _money(data.get('asking_price')),
                'mortgage_balance': _money(data.get('mortgage_balance')),
                'desired_close_date': _text(data.get('desired_close_date'), 40),
                'notes': _text(data.get('notes'), 1500),
                'status': _text(data.get('status'), 80) or 'new',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }

            headers = {
                'apikey': SUPABASE_SERVICE_ROLE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation',
            }
            url = f'{SUPABASE_URL}/rest/v1/hof_seller_leads'
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, headers=headers, json=payload)
            if resp.status_code >= 300:
                return _send(self, 500, {'error': 'Could not save seller lead.', 'detail': resp.text[:500]})
            row = resp.json()[0] if resp.text and resp.text.strip().startswith('[') else {}
            return _send(self, 200, {'ok': True, 'seller_lead_id': row.get('id')})
        except Exception as exc:
            return _send(self, 500, {'error': str(exc)[:500]})

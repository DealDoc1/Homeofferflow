"""Render one fictional saved questionnaire through the real API; no network."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import httpx
from lib.seller_questionnaire import parse_answers

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('normal_questionnaire_api', ROOT / 'api/admin-dashboard.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = '11111111-1111-4111-8111-111111111111'
DRAFT = '22222222-2222-4222-8222-222222222222'
MAIN = '33333333-3333-4333-8333-333333333333'
WATER = '66666666-6666-4666-8666-666666666666'
REAL_CLIENT = httpx.AsyncClient


def render(data, source, water_source=None):
    revision, answers, water = parse_answers(data, has_water=water_source is not None, require_complete=True)
    row = {'id': DRAFT, 'agent_user_id': OWNER, 'brokerage_id': OWNER, 'status': 'draft',
           'property_address': '100 Example Lane, Frisco, TX', 'seller_names': ['Example Seller'], 'buyer_names': [],
           'response_data': answers, 'water_rights_data': water, 'review_content_revision': revision,
           'disclosure_source_id': MAIN, 'disclosure_source_revision': '05-04-2026',
           'water_source_id': WATER if water_source else None, 'water_source_revision': '05-04-2026' if water_source else None}
    async def get(path):
        if path.startswith('hof_seller_disclosure_drafts?'): return [row]
        if path.startswith('hof_brokerage_form_sources?'):
            source_id = WATER if 'id=eq.' + WATER in path else MAIN
            return [{'id': source_id, 'source_revision': '05-04-2026',
                     'storage_bucket': 'fictional-sources', 'storage_path': source_id + '.pdf'}]
        raise AssertionError('Unexpected fixture read')
    def transport(request):
        if request.method != 'GET' or request.url.host != 'fictional.supabase.test' or not request.url.path.startswith('/storage/'):
            raise AssertionError('No real request or external write is permitted')
        return httpx.Response(200, content=water_source if WATER in request.url.path else source)
    with patch.object(API, '_get', get), patch.object(API, 'SUPABASE_URL', 'https://fictional.supabase.test'), \
         patch.object(API.httpx, 'AsyncClient', lambda **kw: REAL_CLIENT(transport=httpx.MockTransport(transport))):
        return asyncio.run(API._render_seller_disclosure_draft_preview(
            {'id': OWNER}, DRAFT, expected_review_revision=revision))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    sys.stdout.buffer.write(render(json.loads(sys.stdin.read(250001)), args.source.read_bytes()))

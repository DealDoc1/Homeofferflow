"""Local real-source directory + API preview, never production activation/sends."""
import importlib.util
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('SUPABASE_URL', 'https://example.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'fixture-only')
spec = importlib.util.spec_from_file_location('profile_preview_api', ROOT/'api/fsbo-lead.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
LEAD_ID = 'b7b2ede6-bca8-400f-86d7-6ec80a5a2575'
PROFILE = {'id':LEAD_ID, 'partner_program':'beta', 'onboarding_public_contact_name':'Tedd Hansen',
           'onboarding_public_contact_phone':'+19728376378',
           'onboarding_public_description':'Locally owned roofing and construction serving DFW and surrounding communities. Roof inspections, storm damage restoration, roof replacements and insurance claim assistance.'}
PLACEMENT = {'id':'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','source_lead_id':LEAD_ID,
             'partner_name':'Integrity First Roofing & Construction', 'partner_type':'roofing',
             'market_area':'DFW and surrounding communities','placement_tier':'founding',
             'website_url':'https://www.constructionwithintegrity.com/', 'logo_url':'http://127.0.0.1:8879/preview-logo.jpg'}
LOGO = Path('/private/tmp/992b53c2a1da2f69179ec4e72994adfff.jpg')

class Client:
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def get(self,url,**kwargs):
        rows = [PLACEMENT.copy()] if 'hof_partner_placements?' in url else [PROFILE.copy()]
        class Response:
            status_code=200
            text='fixture'
            def json(self): return rows
        return Response()

class Handler(BaseHTTPRequestHandler):
    def send(self,body,kind='application/json'):
        self.send_response(200); self.send_header('Content-Type',kind); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=self.path.split('?')[0]
        if path=='/api/fsbo-lead':
            with patch.object(api.httpx,'Client',return_value=Client()): rows=api._list_public_partner_placements()
            self.send(json.dumps({'partners':rows}).encode()); return
        if path=='/preview-logo.jpg': self.send(LOGO.read_bytes(),'image/jpeg'); return
        if path in ('/directory','/directory.html'):
            html=(ROOT/'directory.html').read_text().replace('<main>','<main><p style="background:#fff;color:#173f35;padding:1rem">LOCAL PREVIEW — not a live partner placement. No calls, leads, invitations or charges are submitted.</p>')
            self.send(html.encode(),'text/html'); return
        if path=='/assets/partner-profile.js': self.send((ROOT/path.lstrip('/')).read_bytes(),'text/javascript'); return
        self.send(b'','text/plain')
    def do_POST(self): self.send(b'{"ok":true}')

if __name__=='__main__':
    print('Local preview http://127.0.0.1:8879/directory',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8879),Handler).serve_forever()

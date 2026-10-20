"""Loopback-only real picker/API/store fixture. Fictional identities; no sends."""
import argparse
from copy import deepcopy
import importlib.util
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from types import SimpleNamespace
from urllib.parse import urlparse

from tests.test_purchase_disclosure_execution import fixture, USER, OFFER, DRAFT, OTHER
import lib.purchase_disclosure_store as store_module

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('picker_fixture_api', ROOT / 'api/admin-dashboard.py')
API = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(API)


def serve(source):
    record, draft, links = fixture()
    initial = deepcopy(record['offer_data'])
    hold = threading.Event(); hold.set()
    source_bytes = source.read_bytes()
    class Client:
        def get(self, url, *, params=None, headers=None, timeout=None):
            if '/storage/v1/object/' in url:
                return SimpleNamespace(status_code=200, content=source_bytes)
            table = url.rsplit('/',1)[-1]
            rows = []
            if table == 'hof_offers' and params['id']=='eq.'+OFFER and params['user_id']=='eq.'+USER: rows=[record]
            if table == 'hof_seller_disclosure_drafts' and params['id']=='eq.'+DRAFT and params['agent_user_id']=='eq.'+USER: rows=[draft]
            if table == 'hof_seller_disclosure_review_links': rows=links
            if table == 'hof_brokerage_form_sources':
                rows=[{'id':draft['disclosure_source_id'],'form_code':'TREC-55-1','status':'approved','authorization_attested':True,
                       'source_revision':'05-04-2026','storage_bucket':'private-fixture','storage_path':'source.pdf'}]
            return SimpleNamespace(status_code=200,json=lambda:deepcopy(rows))
    store_module.httpx=Client()
    API.SUPABASE_URL='https://fixture.invalid'; API.SUPABASE_SERVICE_ROLE_KEY='fictional-only'
    async def verified(token): return {'id':USER} if token=='Bearer fictional' else None
    API._verified_user=verified
    preview=API._preview_purchase_disclosure_execution
    def held_preview(user,data):
        result=preview(user,data)
        if not hold.wait(20): raise ValueError('Fictional preview hold expired.')
        return result
    API._preview_purchase_disclosure_execution=held_preview
    html=(ROOT/'index.html').read_text()
    css=html.split('<style>',1)[1].split('</style>',1)[0]
    css+='\n'+re.search(r'<style id="hof-txr1507-drafts-v1">(.*?)</style>',html,re.S).group(1)
    page='''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local disclosure picker QA</title>
<style>'''+css+'''\nmain{max-width:700px;margin:24px auto;padding:16px}.qa-controls{position:fixed;right:8px;bottom:8px;z-index:99999;background:#fff;color:#111;padding:8px}.qa-controls button{margin:3px}input{width:100%}</style>
<main><p>LOCAL QA — fictional account and property</p><h1>Seller's disclosure</h1><p>Include the seller's reviewed answers or a signed copy. You can continue without a disclosure that is still pending.</p>
<label for="propAddress">Property address</label><input id="propAddress" value="123 QA Road"><input id="propCity" type="hidden" value="Dallas"><input id="propState" type="hidden" value="TX"><input id="propZip" type="hidden" value="75201">
<button type="button" class="btn-secondary" onclick="hofChooseSavedDisclosure(this)">Use a saved seller disclosure</button>
<div id="purchaseDisclosureSelection" class="notice gold" hidden></div><p id="uploadedDocsStatus" role="status"></p><p id="cloudStatus"></p><p id="previewSignal"></p>
<div id="uploadedDocsList"></div><p id="attachedCount">0 attached</p><p id="selectionState">No reviewed disclosure selected</p>
<details class="qa-controls"><summary>QA controls</summary><button onclick="fetch('/hold')">Hold next preview</button><button onclick="hofAuth.session.user.id='''+repr(OTHER)+''';hofAuth.session.access_token='other';fetch('/release')">Switch fictional account</button><button onclick="state.data={...state.data,_hofOfferId:'''+repr(OTHER)+'''};fetch('/release')">Switch fictional draft</button><button onclick="fetch('/release')">Release preview</button><button onclick="location.reload()">Reset fixture</button></details>
<script>var state={data:'''+json.dumps(initial)+'''};
window.hofAuth={session:{user:{id:'''+json.dumps(USER)+'''},access_token:'fictional'}};
window.setUploadedDisclosureStatus=text=>document.getElementById('uploadedDocsStatus').textContent=text;
window.saveOfferDraftToSupabase=async()=>{const r=await fetch('/save',{method:'POST',body:JSON.stringify(state.data)});const row=await r.json();state.data._hofOfferId=row.id;document.getElementById('cloudStatus').textContent='Saved to dashboard';return row;};
window.renderUploadedDocsList=()=>{document.getElementById('attachedCount').textContent=(window.hofUploadedDisclosureDocs||[]).length+' attached';window.hofRenderPurchaseDisclosureSelection?.();};
window.saveDraft=()=>{document.getElementById('selectionState').textContent=state.data.purchaseSellerDisclosureId?'Reviewed disclosure selected — no PDF stored in draft':'No reviewed disclosure selected';window.renderUploadedDocsList();};
window.hofShowPdfPreview=blob=>document.getElementById('previewSignal').textContent='PDF preview ready ('+blob.size+' bytes)';
</script><script src="/assets/saved-disclosure-attachment.js"></script></main>'''
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def json(self,body):
            payload=json.dumps(body).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload)
        def do_GET(self):
            path=urlparse(self.path).path
            if path=='/hold':hold.clear();return self.json({'ok':True})
            if path=='/release':hold.set();return self.json({'ok':True})
            if path=='/api/admin-dashboard':
                signed={**draft,'id':OTHER,'status':'signed','signwell_document_id':'fictional-signed'}
                return self.json({'drafts':[draft,signed,{**draft,'id':'bound','signature_offer_id':OTHER},{**draft,'id':'unfinished','seller_review_attested':False}]})
            if path=='/assets/saved-disclosure-attachment.js':
                self.send_response(200);self.send_header('Content-Type','text/javascript');self.end_headers();return self.wfile.write((ROOT/'assets/saved-disclosure-attachment.js').read_bytes())
            record['offer_data']=deepcopy(initial);record['signwell_document_id']=None;hold.set()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src data:")
            self.end_headers();self.wfile.write(page.encode())
        def do_POST(self):
            path=urlparse(self.path).path
            if path=='/api/admin-dashboard':return API.handler.do_POST(self)
            data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            if path=='/save':
                record['offer_data']=data
                return self.json({'id':OFFER,'user_id':USER,'offer_data':data})
            if path=='/api/signwell-status':
                import base64,hashlib
                return self.json({'ok':True,'attachment':{'name':'fictional-signed-disclosure.pdf','type':'seller_disclosure','size':len(source_bytes),
                    'base64':base64.b64encode(source_bytes).decode(),'homeOfferFlowDisclosureReceipt':{'sourceDisclosureId':OTHER,'sha256':hashlib.sha256(source_bytes).hexdigest()}}})
            self.send_error(404)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    print('Local fictional picker: http://127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:hold.set();server.server_close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    serve(parser.parse_args().source)

"""Loopback-only real component/API-function fixture; all partner rows are fictional.

No production auth, database, upload, email, agreement, charge or provider send.
The portrait artwork is the public HomeOfferFlow test icon, not a partner photo.
"""
import importlib.util
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
os.environ['SUPABASE_URL'] = 'https://example.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'fictional-local-only'
spec = importlib.util.spec_from_file_location('portrait_preview_api', ROOT/'api/fsbo-lead.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
INDEX = (ROOT/'index.html').read_text()
ART = 'https://www.homeofferflow.com/assets/homeofferflow-app-icon-192.png'
ASSETS = {'/assets/'+name for name in ('partner-profile.js','partner-profile.css',
          'inspection-partners.js','insurance-partners.js','inspection-partners.css')}
IDS = ['11111111-1111-4111-8111-111111111111', '22222222-2222-4222-8222-222222222222']
LEADS = [{'id':identifier, 'company_name':'Fictional QA '+kind.title(), 'partner_program':'beta',
          'partner_type':kind,'payment_status':'not_started','status':'qualified',
          'onboarding_token_hash':api._onboarding_token_hash('A'*32),'onboarding_token_expires_at':'2030-01-01T00:00:00Z',
          'onboarding_website_url':'https://example.com','onboarding_logo_url':ART,
          'onboarding_market_area':'Fictional QA market','onboarding_public_contact_name':'QA Contact',
          'onboarding_public_contact_phone':'+12145550100','onboarding_public_headshot_url':ART,
          'onboarding_public_description':'Fictional local service profile for optional-photo layout testing.'}
         for identifier,kind in zip(IDS,['insurance','roofing'])]
PLACEMENTS = [{'id':identifier,'source_lead_id':identifier,'partner_name':row['company_name'],
               'partner_type':row['partner_type'],'website_url':'https://example.com',
               'logo_url':'http://127.0.0.1:8884/qa-logo.svg','market_area':'Fictional QA market','placement_tier':'founding'}
              for identifier,row in zip(IDS,LEADS)]

class Response:
    status_code=200
    text='fixture'
    def __init__(self,rows): self.rows=rows
    def json(self): return self.rows

class Client:
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def get(self,url,**kwargs):
        query=parse_qs(urlsplit(url).query)
        if 'hof_partner_placements?' in url:
            category=query.get('partner_type',[''])[0].removeprefix('eq.')
            return Response([row.copy() for row in PLACEMENTS if not category or row['partner_type']==category])
        return Response([LEADS[0].copy()] if 'onboarding_token_hash' in query else [r.copy() for r in LEADS])
    def patch(self,url,**kwargs):
        LEADS[0].update(kwargs['json']); return Response([LEADS[0].copy()])
    def post(self,url,**kwargs):
        if '/storage/v1/object/upload/sign/' not in url: raise RuntimeError('External request prohibited')
        return Response({'token':'fictional-short-lived-token'})

LABEL='<aside class="qa-label">LOCAL QA ONLY — fictional businesses. Test icon stands in for a headshot; no real partner photo, call, lead, invitation or charge.</aside>'

def page(mode):
    styles=''.join('<style>'+s+'</style>' for s in re.findall(r'<style[^>]*>(.*?)</style>', INDEX,re.S))
    script=''
    if mode=='inspection':
        content='<section id="step6" class="active"><h2>Inspections</h2><div id="hofInspectionPartners" hidden></div></section>'
    elif mode=='insurance':
        content='<section id="step4" class="active"><h2>Plan your home insurance</h2><details id="paymentCalcCard" open><summary>Explore your monthly costs</summary><div id="hofInsurancePartners" hidden></div></details></section>'
    elif mode=='followup':
        content='<section class="now-what"><h2>Your next steps</h2><div id="nowWhatPartnerDirectory"></div></section>'
        constants=INDEX[INDEX.index('  const NOW_WHAT_PARTNER_LABELS'):INDEX.index('  function nowWhatFormatDate')]
        start=INDEX.index('  function nowWhatPartnerSort(')
        sort=INDEX[start:INDEX.index('\n  function ',start+20)]
        render=INDEX[INDEX.index('  function renderNowWhatDirectory('):INDEX.index('  async function renderNowWhatPartnerJourney(')]
        script=constants+sort+'\nfunction bindOfferCompletionPartnerClicks(){} function trackPartnerDirectoryImpressions(){}\n'+render+'\nwindow.hofPartnerProfile.load().then(renderNowWhatDirectory);'
    else:
        content='<h2>Optional headshot setup</h2><p>The photo and contact details below belong only to this fictional local fixture.</p>'
        start=INDEX.index('  function setupPartnerOnboardingModal(')
        script=INDEX[start:INDEX.index('  async function recoverPartnerCheckoutSetup(',start)]
        script="function value(id){return String(document.getElementById(id)?.value||'').trim();}\n"+script
        script+="\nwindow.hofCustomerActionError=e=>e.message;window.hofAuth={client:{storage:{from:()=>({uploadToSignedUrl:async()=>({error:null})})}}};retainPartnerOnboardingToken('"+'A'*32+"');window.openPartnerOnboarding();"
    return '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Partner photo local QA</title>'+styles+'<link rel="stylesheet" href="/assets/inspection-partners.css"><link rel="stylesheet" href="/assets/partner-profile.css"><script src="/assets/partner-profile.js"></script><script src="/assets/inspection-partners.js" defer></script><script src="/assets/insurance-partners.js" defer></script><style>main{max-width:980px;margin:24px auto;padding:16px}.qa-label{font:13px system-ui;background:#fff;color:#173f35;padding:14px}body{min-height:100vh}</style></head><body>'+LABEL+'<main>'+content+'</main><script>'+script+'</script></body></html>'

class Handler(BaseHTTPRequestHandler):
    def reply(self,body,kind='application/json',status=200):
        self.send_response(status);self.send_header('Content-Type',kind);self.end_headers()
        self.wfile.write(body.encode() if isinstance(body,str) else body)
    def do_GET(self):
        route=urlsplit(self.path).path
        if route=='/api/fsbo-lead':
            with patch.object(api.httpx,'Client',return_value=Client()):
                category=parse_qs(urlsplit(self.path).query).get('category',[None])[0]
                self.reply(json.dumps({'ok':True,'partners':api._list_public_partner_placements(category)}))
        elif route in ('/directory','/directory.html'):
            absent=parse_qs(urlsplit(self.path).query).get('photo',[''])[0]=='none'
            for row in LEADS: row['onboarding_public_headshot_url']=None if absent else ART
            self.reply((ROOT/'directory.html').read_text().replace('<main>','<main>'+LABEL),'text/html')
        elif route in ASSETS:
            target=ROOT/route.lstrip('/');kind='text/css' if target.suffix=='.css' else 'application/javascript'
            self.reply(target.read_bytes(),kind)
        elif route=='/qa-logo.svg':
            self.reply('<svg xmlns="http://www.w3.org/2000/svg" width="220" height="96"><rect width="220" height="96" fill="#fff"/><text x="15" y="43" font-size="23" font-family="Arial" fill="#173f35">FICTIONAL QA</text><text x="15" y="71" font-size="16" font-family="Arial" fill="#173f35">LOCAL SERVICE</text></svg>','image/svg+xml')
        elif route in ('/inspection','/insurance','/followup','/setup'): self.reply(page(route[1:]),'text/html')
        else: self.reply('',status=404)
    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or '{}')
        action=data.get('request_type')
        try:
            with patch.object(api.httpx,'Client',return_value=Client()), \
                 patch.object(api,'_record_partner_onboarding_event'), \
                 patch.object(api,'_dispatch_partner_agreement_after_onboarding'):
                if action=='partner_onboarding_get': result={'partner':api._public_partner_onboarding(api._get_partner_onboarding(data.get('onboarding_token')))}
                elif action=='partner_onboarding_submit': result={'partner':api._complete_partner_onboarding(data.get('onboarding_token'),data)}
                elif action=='partner_onboarding_logo_upload': result={'upload':api._create_partner_logo_upload(data.get('onboarding_token'),data)}
                else: result={}
            self.reply(json.dumps({'ok':True,**result}))
        except Exception as error: self.reply(json.dumps({'ok':False,'error':str(error)}),status=400)

if __name__=='__main__':
    print('Local fictional partner QA http://127.0.0.1:8884/directory',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8884),Handler).serve_forever()

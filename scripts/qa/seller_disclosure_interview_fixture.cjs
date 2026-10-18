// Actual interview helpers with fictional device-only persistence; no APIs.
const fs = require('node:fs'), http = require('node:http'), path = require('node:path');
const rootDir = path.resolve(__dirname, '../..');
const source = fs.readFileSync(path.join(rootDir, 'index.html'), 'utf8');
function between(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  if (a < 0 || b <= a) throw Error('Interview source anchors changed.');
  return source.slice(a, b);
}
const css = between('<style id="hof-seller-disclosure-draft-ui-v1">', '</style>').replace(/^[\s\S]*?>/, '');
const declarations = fs.readFileSync(path.join(rootDir,'assets/seller-disclosure-interview.js'),'utf8') +
  '\nconst draftCache=new Map();const {renderResponses,renderWaterResponses,collectDisclosureResponses,syncDisclosureDetails}=window.hofDisclosureInterview;';
const visibility = between('  function syncWaterRightsVisibility()', '  root.loadSellerDisclosureDraft = function');
const load = between('  root.loadSellerDisclosureDraft = function', '  let listingDisclosureHandoffRevision');
const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fictional disclosure interview check</title><style>
:root{--white:#f6f2e8;--gray-light:#b7c4cd;--muted:#b7c4cd;--primary:#c8973f;--gold-light:#e8b86d}
body{background:#0d1f35;color:var(--white);font:16px -apple-system,BlinkMacSystemFont,sans-serif;margin:0;padding:16px}
main{max-width:800px;margin:auto}h1{font-size:26px}label{display:block;margin:10px 0}
select,input,textarea{background:#152840;color:#fff;border:1px solid #667085;border-radius:6px;padding:9px;font-size:16px;box-sizing:border-box}
select{max-width:100%}button{background:#c8973f;color:#0d1f35;border:0;padding:12px;border-radius:8px;font-weight:bold;margin:10px 8px 10px 0}
summary{cursor:pointer;padding:12px 0}details{border-bottom:1px solid #334155}.qa{font-size:13px;color:#b7c4cd}
.hof-seller-explanation textarea{background:#152840;color:#fff}${css}
</style></head><body><main><h1>Seller disclosure</h1>
<p class="qa">Fictional local QA only. Actual interview controls with isolated device storage. No live accounts, emails, or signing requests.</p>
<div id="hofSellerDisclosureCard" class="hof-seller-disclosure-card"><details id="hofSellerDisclosureWorkspace" open><summary>Property details</summary>
<div id="mainResponses"></div><label>Water-rights disclosure<select id="hofWaterSource"><option value="">Do not include</option><option value="qa-water">Include fictional water-rights disclosure</option></select></label>
<div id="hofSellerWaterResponses" hidden></div></details><button id="fixtureSave">Save fictional draft</button><button id="fixtureReopen">Reopen fictional draft</button><p id="hofSellerDraftStatus" role="status"></p></div>
<div hidden><select id="hofSellerWorkspace"></select><input id="hofSellerAddress"><select id="hofSellerSource"></select><input id="hofSeller1"><input id="hofSeller2"><input id="hofSellerEmail"><input id="hofSeller2Email"><input id="hofBuyer1"><input id="hofBuyer2"><button id="hofSendSellerReview"></button></div>
</main><script>
const root=window,escape=v=>String(v??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
${declarations}
${visibility}
${load}
document.getElementById('mainResponses').innerHTML=renderResponses();
document.getElementById('hofSellerWaterResponses').innerHTML=renderWaterResponses();
const card=document.getElementById('hofSellerDisclosureCard');
card.addEventListener('change',()=>syncDisclosureDetails(card));
card.addEventListener('input',()=>syncDisclosureDetails(card));
document.getElementById('hofWaterSource').addEventListener('change',syncWaterRightsVisibility);
syncDisclosureDetails(card);
function fixtureLoad(){const raw=localStorage.getItem('hof-fictional-conditional-disclosure');if(!raw)return;const draft=JSON.parse(raw);draftCache.set(draft.id,draft);root.loadSellerDisclosureDraft(draft.id);}
document.getElementById('fixtureSave').addEventListener('click',()=>{
 const old=draftCache.get('fictional-draft')||{};
 const draft={id:'fictional-draft',property_address:'100 Fictional QA Lane',seller_names:['QA Seller'],buyer_names:[],
 water_source_id:document.getElementById('hofWaterSource').value,
 response_data:collectDisclosureResponses(card,'seller',old.response_data||{}),water_rights_data:collectDisclosureResponses(card,'water',old.water_rights_data||{})};
 localStorage.setItem('hof-fictional-conditional-disclosure',JSON.stringify(draft));draftCache.set(draft.id,draft);
 document.getElementById('hofSellerDraftStatus').textContent='Fictional draft saved on this device only.';
});
document.getElementById('fixtureReopen').addEventListener('click',fixtureLoad);fixtureLoad();
</script></body></html>`;
http.createServer((req,res)=>{
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store',
 'Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'"});
 res.end(page);
}).listen(8782,'127.0.0.1',()=>console.log('Fictional-only actual-source interview fixture: http://127.0.0.1:8782'));

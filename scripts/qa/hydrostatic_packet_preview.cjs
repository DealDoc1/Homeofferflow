// Local-only browser bridge: actual interview markup/helpers/collector -> real PDF builder.
// HOF_QA_PYTHON=/path/to/python PYTHONPATH=.:/path/to/deps node scripts/qa/hydrostatic_packet_preview.cjs
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {spawn}=require('node:child_process');
const root=path.resolve(__dirname,'../..'),source=fs.readFileSync(path.join(root,'index.html'),'utf8');
const environmental=Boolean(process.env.HOF_QA_ENVIRONMENTAL_SOURCE),mineral=Boolean(process.env.HOF_QA_MINERAL_SOURCE);
const assumption=Boolean(process.env.HOF_QA_ASSUMPTION_SOURCE);
const kind=assumption?'assumption':environmental?'environmental':mineral?'mineral':'hydrostatic';
const label=assumption?'Loan assumption':environmental?'Environmental review':mineral?'Mineral reservation':'Hydrostatic';
function section(start,end){
  const a=source.indexOf(start),b=source.indexOf(end,a);
  if(a<0||b<=a)throw Error('Missing production section: '+start);
  return source.slice(a,b);
}
const question=assumption ? section('    <div class="wizard-step" id="step3">','    <div class="wizard-step" id="step5">') : section(environmental?'      <div class="radio-group-label" style="margin-top:1.5rem;">Do you need environmental review rights?':mineral?'      <div class="radio-group-label" style="margin-top:1.5rem;">Will the seller reserve mineral rights?':'      <div class="radio-group-label" style="margin-top:1.5rem;">Are you requesting a hydrostatic',
  '      <div style="margin-top:1.5rem; padding-top:1.25rem;');
const sellers=section('        <div id="sellerSigningFields"','        <div id="sellerTemporaryLeaseFields"');
const scripts=section('  function getVal(', '  function selectPlan(')
  +section('  function hydrostaticSigningSummary(', '  function validateSellerTemporaryLeaseInputs(')
  +section('  function selectCard(', '  function getCurrentFinancingChoice(')
  +(assumption ? section('  function setRadioValue(', '  function updateSurveyExistingDetails(')
    +section('  function getCurrentFinancingChoice(', '  function sanitizeBuyerMailingAddressAutofill(')
    +section('  function setAppraisalAddendumRequired(', '  function validateCurrentStep(')
    +section('  function setDefaultValue(', '  function applySmartDefaults(')
    +section('  function numFromEl(', '  function forcePaymentRecalcSoon(')
    +section('  function syncFinancingFieldsFromPrice(', '  function saveDraft(') : '');
const page=`<!doctype html><html lang="en"><meta charset="utf-8"><title>${label} packet — local QA</title>
<style>body{font:17px system-ui;max-width:800px;margin:30px auto;padding:0 20px;color:#183347;background:#f8fafb}
.radio-cards,.field-group{gap:15px;flex-wrap:wrap}.radio-cards{display:flex}.radio-card{border:1px solid #b7c7cd;padding:12px;cursor:pointer;border-radius:6px}
.radio-card.selected{background:#d9f2ea}.radio-card-text{display:inline-block}.radio-card-text small{display:block}
.field{margin:12px 0;min-width:300px}label{display:block}select,input:not([type=radio]):not([type=checkbox]){font:inherit;padding:8px;box-sizing:border-box;width:100%}
button{font:inherit;padding:10px;margin:15px 0}pre{white-space:pre-wrap;font:13px monospace}#status{color:#9b162b}#sellerSigningFields p{flex-basis:100%}</style>
<h1>${label} packet — local QA only</h1><p>Synthetic purchase: QA Buyer, 100 QA Street, Frisco. Actual interview controls and PDF builder; isolated from production. No emails or signature requests.</p>
${question}${sellers}
<input id="seller1" type="hidden" value="QA Seller"><input id="possession" type="hidden" value="funding">
<input id="closingDate" type="hidden" value="2026-10-30">
<button type="button" id="generate">Build local unsigned packet</button><p id="status" role="status"></p>
<p id="scope"></p><a id="pdf" hidden target="_blank">Open local unsigned packet</a><pre id="result"></pre>
<script>
const state={step:0,data:{buyer1:'QA Buyer',buyerEmail:'buyer@example.test',leases:'no'}};
let steps=${assumption ? "['step3','step7']" : "['step5','step7']"};
const getCurrentSteps=()=>steps;
function setInputIfEmpty(id,value){const el=document.getElementById(id);if(el&&!el.value&&value)el.value=value;}
function setPaymentStatus(value){document.getElementById('status').textContent=value;}
${scripts}
function toggleHelper(id){const el=document.getElementById(id);if(el)el.hidden=!el.hidden;}
document.getElementById('generate').onclick=async()=>{
 const button=document.getElementById('generate');if(button.disabled)return;
 document.getElementById('pdf').hidden=true;document.getElementById('result').textContent='';
 const missing=[];markHydrostaticInterviewIssues(missing,true);
 markMineralInterviewIssues(missing,true);
 markEnvironmentalInterviewIssues(missing,true);
 markAssumptionInterviewIssues(missing,true);
 if(missing.length){setPaymentStatus(missing.join('; '));return;}
 for(state.step=0;state.step<steps.length;state.step++)collectData();state.step=0;
 if(!validateHydrostaticInputs(state.data))return;
 if(!validateMineralInputs(state.data))return;
 if(!validateEnvironmentalInputs(state.data))return;
 if(!validateAssumptionInputs(state.data))return;
 button.disabled=true;setPaymentStatus('Building locally...');
 document.getElementById('scope').textContent=state.data.financing==='assumption'?'Loan Assumption Addendum included. Local unsigned preview only.':state.data.environmentalAssessment==='yes'?environmentalSigningSummary(state.data):state.data.mineralReservation==='yes'?mineralSigningSummary(state.data):state.data.hydrostaticTesting==='yes'?hydrostaticSigningSummary(state.data):'No additional authorization selected.';
 try{
  const response=await fetch('/packet',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.data)});
  const result=await response.json();if(!response.ok)throw Error(result.error);
  document.getElementById('result').textContent=JSON.stringify({submitted:state.data,...result},null,2);
  const link=document.getElementById('pdf');link.href=result.pdf;link.hidden=false;
  setPaymentStatus('Local unsigned packet ready. Nothing sent.');
 }catch(error){setPaymentStatus(error.message);}finally{button.disabled=false;}
};
</script></html>`;
let sequence=0,busy=false;
const outputs=new Map();
const server=http.createServer((req,res)=>{
 const origin='http://127.0.0.1:'+server.address().port;
 if(req.headers.host!==new URL(origin).host){res.writeHead(403);res.end();return;}
 const headers={'Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'none'; frame-ancestors 'none'"};
 if(req.method==='GET'&&req.url==='/'){res.writeHead(200,{...headers,'Content-Type':'text/html; charset=utf-8'});res.end(page);return;}
 if(req.method==='GET'&&outputs.has(req.url)){res.writeHead(200,{'Content-Type':'application/pdf','Cache-Control':'no-store'});fs.createReadStream(outputs.get(req.url)).pipe(res);return;}
 if(req.url==='/favicon.ico'){res.writeHead(204);res.end();return;}
 if(req.method!=='POST'||req.url!=='/packet'){res.writeHead(404);res.end();return;}
 if(req.headers.origin!==origin||req.headers['content-type']!=='application/json'||busy){res.writeHead(403);res.end();return;}
 let body='';req.on('data',chunk=>{body+=chunk;if(body.length>16000)req.destroy();});
 req.on('end',()=>{
  let parsed;try{parsed=JSON.parse(body);if(!parsed||Array.isArray(parsed)||typeof parsed!=='object')throw Error();}catch{res.writeHead(400);res.end();return;}
  busy=true;const name='packet-'+(++sequence)+'.pdf',file=path.join(root,'tmp/pdfs/'+kind+'-browser',name);
  const child=spawn(process.env.HOF_QA_PYTHON||'python3',['scripts/qa/hydrostatic_browser_packet.py',file],{cwd:root,env:process.env});
  let stdout='',stderr='';child.stdout.on('data',data=>stdout+=data);child.stderr.on('data',data=>stderr+=data);
  const timer=setTimeout(()=>child.kill(),30000);
  let settled=false;
  function finish(code){if(settled)return;settled=true;clearTimeout(timer);busy=false;
   let result;try{if(code!==0)throw Error(stderr);result=JSON.parse(stdout);outputs.set('/'+name,file);result.pdf='/'+name;}
   catch{res.writeHead(500,{'Content-Type':'application/json'});res.end(JSON.stringify({error:'Local packet build failed; inspect the QA terminal.'}));console.error(stderr||stdout);return;}
   res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(result));console.log(name+': '+result.pages+' pages; '+result.widgetsChecked+' hydrostatic widgets verified');
  }
  child.on('error',error=>{stderr=error.message;finish(1);});child.on('close',finish);child.stdin.end(JSON.stringify(parsed));
 });
});
server.listen(0,'127.0.0.1',()=>console.log(label+' QA: http://127.0.0.1:'+server.address().port+'/'));

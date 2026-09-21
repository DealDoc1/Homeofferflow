// Local, no-network fixture for real browser form-submit event lifetime.
// Run: node scripts/qa/txr_draft_save_preview.cjs
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../../index.html'),'utf8');
const scripts=[1919,1917].map(code=>{
  const marker=`<script id="hof-txr${code}-drafts-v1">`,start=source.indexOf(marker);
  if(start<0)throw Error(`Missing TXR-${code} interview`);
  return source.slice(start,source.indexOf('</script>',start)+9);
}).join('\n');
const page=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TXR draft save — local QA only</title>
<style>
body{font:16px system-ui;max-width:880px;margin:24px auto;padding:0 18px;color:#152840;background:#f7f9fb}
label{display:block;margin:10px 0}input:not([type=checkbox]),select{font:inherit;display:block;padding:7px;width:95%;box-sizing:border-box}
button{font:inherit;padding:9px;margin:5px;cursor:pointer}button:disabled{cursor:default}
.account-card,.hof-agreement-dialog{background:white;border:1px solid #cbd3dc;border-radius:8px;padding:20px;margin:14px 0}
.hof-agreement-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px}.hof-agreement-wide{grid-column:1/-1}
.hof-iabs-status{padding:12px}.error{color:#a4001c}.ready{color:#14552f}
.qa-tools{position:sticky;top:0;background:#edf4ff;border:2px solid #516889;padding:12px;z-index:2}
@media(max-width:550px){.hof-agreement-grid{grid-template-columns:1fr}}
</style>
<h1>TXR draft save — local QA only</h1><p>Actual interview scripts, fake parties and simulated API responses. No external requests, saved documents or signing invitations.</p>
<section class="qa-tools"><button id="fill" type="button">Fill synthetic test answers</button><button id="finish" type="button">Complete simulated save</button>
<label><input type="checkbox" id="fail"> Reject the next simulated save</label><div id="stats" role="status">Requests: 0; pending: 0; review opens: 0</div></section>
<div id="accountPanelRelationships"></div><div id="review"></div>
<script>
let requests=0,pending=[],reviews=0;
const stats=()=>{document.getElementById('stats').textContent='Requests: '+requests+'; pending: '+pending.length+'; review opens: '+reviews;};
window.hofAuth={role:'agent',session:{user:{id:'qa-user'},access_token:'synthetic-not-a-credential'}};
window.hofLoadApprovedBrokerageSource=async()=>({id:'qa-source',source_revision:'QA ONLY'});
window.hofOpenPreparedAgreement=async()=>{reviews++;document.getElementById('review').textContent='Simulated review queue opened. No signature request was sent.';stats();};
window.fetch=async(url,options)=>{
  const action=JSON.parse(options.body).action;
  if(url!=='/api/admin-dashboard'||!['create_txr_1919_draft','create_txr_1917_draft'].includes(action))throw Error('Unexpected request blocked by fixture');
  requests++;return new Promise(resolve=>{pending.push(resolve);stats();});
};
document.getElementById('finish').onclick=()=>{
  const ok=!document.getElementById('fail').checked,tasks=pending;pending=[];
  tasks.forEach(resolve=>resolve({ok,json:async()=>ok?{id:'qa-draft'}:{error:'Simulated validation error. Please check the entered terms.'}}));stats();
};
document.getElementById('fill').onclick=()=>{
  const values={propertyAddress:'100 QA Street',address:'100 QA Street',buyerOne:'QA Buyer',b1:'QA Buyer',sellerOne:'QA Seller',s1:'QA Seller',creditDays:'5',days:'7',varianceAdjustment:'cash',varianceTerminationThreshold:'1000',firstLoanLender:'QA Lender',firstLoanBalance:'100000',firstLoanPayment:'1000',firstAssumptionFeeCap:'500',firstInterestRateCap:'5'};
  for(const form of document.querySelectorAll('form')){
    for(const input of form.elements){
      if(Object.hasOwn(values,input.name))input.value=values[input.name];
      if(input.type==='checkbox')input.checked=['ack','loanAssumptionReviewAcknowledgment','firstLoanEnabled'].includes(input.name)||['credit_report','environmental'].includes(input.value);
      input.dispatchEvent(new Event('change',{bubbles:true}));
    }
  }
};
</script>${scripts}</html>`;
const server=http.createServer((req,res)=>{
  if(req.url==='/favicon.ico'){res.writeHead(204);res.end();return;}
  if(req.url!=='/'){res.writeHead(404);res.end('Not found');return;}
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'"});res.end(page);
});
server.listen(0,'127.0.0.1',()=>console.log('TXR draft-save QA: http://127.0.0.1:'+server.address().port+'/'));

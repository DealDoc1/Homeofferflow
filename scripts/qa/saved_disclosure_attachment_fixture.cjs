// Real component + real status handler; fictional read-only dependencies only.
const fs=require('node:fs'),http=require('node:http'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const styles=[...html.matchAll(/<style(?:\s[^>]*)?>([\s\S]*?)<\/style>/g)].map(m=>m[1]).join('\n');
const draft={id:'fictional-disclosure',agent_user_id:'owner',status:'signed',signwell_document_id:'fictional-document',
  property_address:'123 QA Test Road, Dallas, TX 75201',seller_names:['Fictional QA Seller'],buyer_names:[],disclosure_source_revision:'05-04-2026'};
const response=(data)=>({ok:true,status:200,text:async()=>JSON.stringify(data),json:async()=>data,
  arrayBuffer:async()=>Buffer.from('%PDF-fictional-browser-fixture')});
const context={module:{exports:{}},process:{env:{SUPABASE_URL:'https://fictional.database.test',SUPABASE_SERVICE_ROLE_KEY:'fictional',SIGNWELL_API_KEY:'fictional'}},
  require,Buffer,console,fetch:async(url,options={})=>{
    assert.equal(options.method||'GET','GET','No external writes allowed');
    if(url.includes('/auth/v1/user'))return response({id:'owner',email:'fictional@example.com'});
    if(url.includes('/rest/v1/hof_seller_disclosure_drafts?')){
      assert.ok(url.includes('agent_user_id=eq.owner'));return response([draft]);
    }
    if(url==='https://www.signwell.com/api/v1/documents/fictional-document')return response({status:'completed',test_mode:false,
      metadata:{seller_disclosure_draft_id:draft.id,form_code:'TREC-55-1'}});
    if(url.includes('/fictional-document/completed_pdf?'))return response({});
    throw Error('Blocked unexpected fixture request');
  }};
vm.runInNewContext(fs.readFileSync(path.join(root,'api/signwell-status.js'),'utf8'),context);
let hold=false,pending=[];
const page=`<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fictional disclosure reuse check</title><style>${styles}</style>
<main style="max-width:800px;margin:20px auto;padding:18px"><h1>Local fictional check</h1><p>Real component and API handler; no real email, provider request, save or signature.</p>
<div class="account-card"><label>Property address<input id="propAddress" value="123 QA Test Road"></label><input id="propCity" value="Dallas"><input id="propState" value="TX"><input id="propZip" value="75201">
<button type="button" class="btn-secondary" onclick="hofChooseSavedDisclosure(this)">Use a saved seller disclosure</button>
<div id="uploadedDocsList"></div><label><input type="checkbox" id="uploadedDisclosureAck">Review attachments</label><p id="status" role="status"></p><p id="count">0 attached</p></div>
<button class="btn-secondary" onclick="fetch('/hold')">Hold next addition</button><button class="btn-secondary" onclick="hofAuth.session.user.id='other';fetch('/release')">Switch fictional account</button>
<script>var state={data:{}};window.hofAuth={session:{user:{id:'owner'},access_token:'fictional'}};
window.setUploadedDisclosureStatus=t=>document.getElementById('status').textContent=t;
window.resetUploadedDisclosureAcknowledgement=()=>document.getElementById('uploadedDisclosureAck').checked=false;
window.renderUploadedDocsList=()=>{const docs=window.hofUploadedDisclosureDocs||[];document.getElementById('count').textContent=docs.length+' attached';document.getElementById('uploadedDocsList').textContent=docs.map(d=>d.name+' — Buyer acknowledgments included automatically').join(', ');};</script>
<script src="/assets/saved-disclosure-attachment.js"></script></main>`;
http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://127.0.0.1');
  const json=data=>{res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
  if(url.pathname==='/hold'){hold=true;return json({ok:true});}
  if(url.pathname==='/release'){hold=false;pending.splice(0).forEach(f=>f());return json({ok:true});}
  if(url.pathname==='/api/admin-dashboard')return json({drafts:[draft,{...draft,id:'pending',status:'sent'},{...draft,id:'other-property',property_address:'124 QA Test Road'}]});
  if(url.pathname==='/api/signwell-status'){
    let raw='';for await(const chunk of req)raw+=chunk;
    const run=()=>context.module.exports({method:'POST',headers:{authorization:'Bearer fictional'},body:JSON.parse(raw)},
      {status(code){this.code=code;return this},setHeader(k,v){res.setHeader(k,v)},json(data){res.writeHead(this.code||200,{'Content-Type':'application/json'});res.end(JSON.stringify(data));return this;}});
    if(hold)pending.push(run);else await run();return;
  }
  if(url.pathname==='/assets/saved-disclosure-attachment.js'){
    res.writeHead(200,{'Content-Type':'text/javascript','Cache-Control':'no-store'});return res.end(fs.readFileSync(path.join(root,url.pathname)));
  }
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store',
    'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'"});res.end(page);
}).listen(8786,'127.0.0.1',()=>console.log('Fictional reuse fixture: http://127.0.0.1:8786'));

// Real seller page and scripts, fictional localhost-only API. Nothing sent.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),vm=require('node:vm');
const root=path.resolve(__dirname,'../..');
const ui=fs.readFileSync(path.join(root,'assets/seller-disclosure-interview.js'),'utf8');
const sandbox={window:{}};vm.runInNewContext(ui,sandbox);
const form=sandbox.window.hofDisclosureInterview;
const responses=Object.fromEntries([...form.renderResponses().matchAll(/<select data-seller-response="([^"]+)"/g)]
  .filter(m=>!m[1].endsWith('_extent')).map(m=>[m[1],'N']));
responses.seller_occupancy='Y';responses.working_smoke_detectors='Y';responses.roof_type='Composition';responses.roof_age='8 years';
let revision='44444444-4444-4444-8444-444444444444';
const draft=()=>({questionnaireEnabled:true,reviewContentRevision:revision,propertyAddress:'100 Fictional QA Lane, Frisco, TX',
  sellerName:'QA Seller One',sellerNames:['QA Seller One'],responseData:responses,waterRightsData:{},hasWaterRights:false,canSignSeparately:true,
  expiresAt:'2099-01-01T00:00:00Z'});
const page=()=>fs.readFileSync(path.join(root,'seller-review.html'),'utf8').replace('<main>',
 '<main><p style="background:#fff3cd;padding:12px">Local fictional preview — not live. No email or signature invitation can be sent.</p>');
http.createServer((req,res)=>{
 const url=new URL(req.url,'http://127.0.0.1');
 const json=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
 if(url.pathname==='/api/admin-dashboard'){
  if(req.method==='POST'){
   let bytes='';req.on('data',b=>bytes+=b);req.on('end',()=>{
    const body=JSON.parse(bytes||'{}');
    if(url.searchParams.has('verify_seller_review'))return json(200,{sessionToken:'fictional-session-000000000000000000000000'});
    if(url.searchParams.has('save_seller_questionnaire')){Object.keys(responses).forEach(k=>delete responses[k]);Object.assign(responses,body.responseData);revision='55555555-5555-4555-8555-555555555555';return json(200,{saved:true,reviewContentRevision:revision});}
    if(url.searchParams.has('attest_seller_review'))return json(200,{ok:true,allSellersAttested:true});
    if(url.searchParams.has('sign_seller_questionnaire'))return json(200,{ok:true,sent:true,message:'Fictional only; nothing sent.'});
    return json(400,{error:'Unsupported fixture action'});
   });return;
  }
  if(url.searchParams.has('seller_review_session'))return json(200,draft());
  if(url.searchParams.has('seller_review_pdf'))return json(503,{error:'The fixture deliberately does not simulate a PDF or provider pass.'});
  return json(200,{ok:true});
 }
 const assets={'/assets/seller-disclosure-interview.js':ui,
  '/assets/seller-disclosure-questionnaire.js':fs.readFileSync(path.join(root,'assets/seller-disclosure-questionnaire.js'),'utf8')};
 res.writeHead(200,{'Content-Type':url.pathname in assets?'text/javascript':'text/html; charset=utf-8','Cache-Control':'no-store',
  'Content-Security-Policy':"default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-src blob:; img-src 'self'"});
 res.end(assets[url.pathname]||page());
}).listen(8784,'127.0.0.1',()=>console.log('Local fictional questionnaire: http://127.0.0.1:8784/?token=fictional-link-000000000000000000000000'));

// Local, fictional visual fixture using the account page's real CSS and interview.
const fs=require('node:fs'),http=require('node:http'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const styles=[...html.matchAll(/<style(?:\s[^>]*)?>([\s\S]*?)<\/style>/g)].map(m=>m[1]).join('\n');
const sandbox={window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root,'assets/seller-disclosure-interview.js'),'utf8'),sandbox);
const questions=sandbox.window.hofDisclosureInterview.renderResponses();
http.createServer((_req,res)=>{
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store',
    'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; img-src 'none'"});
  res.end(`<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local disclosure contrast check</title><style>${styles}</style>
    <main style="padding:16px;max-width:1120px;margin:auto"><p>Local fictional visual check. Nothing is saved or sent.</p>
    <div class="account-card hof-seller-disclosure-card"><h4>Seller disclosure</h4>
    <details class="hof-seller-step" open><summary><span class="hof-seller-step-number">1</span><span class="hof-seller-step-copy"><strong>Property and people</strong><small>Tell us who is involved and select the disclosure form.</small></span></summary>
    <div class="hof-seller-grid"><label>Property address<input value="123 QA Test Road, Dallas, TX 75201"></label><label>Seller 1 name<input value="QA Seller - Fictional Test Only"></label><label>Disclosure form<select><option>05-04-2026</option></select></label></div></details>
    <details class="hof-seller-step" open><summary><span class="hof-seller-step-number">2</span><strong>Property details</strong></summary>${questions}</details></div></main>`);
}).listen(8785,'127.0.0.1',()=>console.log('Local contrast fixture: http://127.0.0.1:8785'));

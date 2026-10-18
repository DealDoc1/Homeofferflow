// Isolated owner-QA component: actual markup/styles/controller, fake transport.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),out=path.resolve(process.argv[2]||'/private/tmp/hof-listing-lead-control-qa');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const start=html.indexOf('  async function runPurchaseSigningTest('),end=html.indexOf('  async function loadAdminDashboard(',start);
const summary=html.indexOf('<summary>Listing lead disclosure test</summary>');
if(start<0||end<0||summary<0)throw new Error('Current owner QA control is missing');
const component=html.slice(html.lastIndexOf('<details',summary),html.indexOf('</details>',summary)+10).replace('<details ','<details open ');
// The main stylesheet owns this admin component. Do not collect style strings
// embedded inside later iframe-preview JavaScript, which are not page CSS.
const styles=html.match(/<style>([\s\S]*?)<\/style>/)?.[1];
if(!styles)throw new Error('The main component stylesheet is missing');
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'index.html'),`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'"><title>Local owner QA control</title><style>${styles}</style></head><body><main style="max-width:720px;padding:24px;margin:40px auto"><h2>Local owner QA preview</h2><p>Fictional preview only. No documents, invitations or external requests.</p><section class="admin-section"><h4>Delivery Connections</h4>${component}</section><p id="proof" role="status"></p></main><script>
window.hofAuth={session:{access_token:'fictional'}};let recorded=false;
window.fetch=async(url,options)=>{const action=JSON.parse(options.body).action;
if(url!='/api/admin-dashboard'||!['send_listing_lead_signing_test','check_listing_lead_signing_test'].includes(action))throw new Error('Only the local fixed QA control is allowed');
if(action==='send_listing_lead_signing_test')recorded=true;
document.getElementById('proof').textContent='Local simulation: '+action;
return {ok:true,json:async()=>({signingTest:{phase:recorded?'created':'not_started',message:recorded?'Local simulation: one fictional test is recorded; no invitation was sent.':'No listing lead disclosure test has been sent.'}})};};
${html.slice(start,end)}
</script></body></html>`);
console.log(out);

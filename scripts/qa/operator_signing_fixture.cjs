// Offline fixture of the actual owner QA control and action handler. Never sends.
const fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, '../..'), output = path.resolve(process.argv[2]);
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const summary = html.indexOf('<summary>Lease listing package test</summary>');
const start = html.lastIndexOf('<details', summary), end = html.indexOf('</details>', summary);
const handlerStart = html.indexOf('  async function runPurchaseSigningTest(');
const handlerEnd = html.indexOf('  async function loadAdminDashboard(', handlerStart);
if (start < 0 || end <= start || handlerStart < 0 || handlerEnd <= handlerStart) throw new Error('QA controls not found');
const styles = [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/g)].map(match => match[1]).join('\n');
const control = html.slice(start, end + '</details>'.length).replace('<details ', '<details open ');
fs.mkdirSync(output, {recursive: true});
fs.writeFileSync(path.join(output, 'index.html'), `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'"><title>Local QA - owner signing controls</title><style>${styles}</style></head><body><main class="admin-section" style="max-width:700px;margin:2rem auto;padding:1rem;color:var(--white)"><h4>Local QA - not connected to SignWell</h4>${control}<pre id="requests" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></main><script>
const hofAuth={session:{access_token:'FICTIONAL'}};
window.fetch=async(url,options)=>{
 if(url!=='/api/admin-dashboard')throw new Error('No external request is permitted');
 const data=JSON.parse(options.body);
 document.getElementById('requests').textContent=JSON.stringify(data,null,2);
 if(data.action.startsWith('send_'))return {ok:false,json:async()=>({error:'No invitation can be sent from this fixture.'})};
 if(data.action!=='check_lease_listing_signing_test')throw new Error('Wrong QA action');
 return {ok:true,json:async()=>({signingTest:{phase:'not_started',message:'No lease listing test has been sent. Local fixture only.'}})};
};
${html.slice(handlerStart, handlerEnd)}
</script></body></html>`);
console.log(output);

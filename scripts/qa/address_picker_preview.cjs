// Loopback-only QA page: real picker code, synthetic Google responses, no API key.
// Run: node scripts/qa/address_picker_preview.cjs
// This does not test Google availability, billing, credentials, or persistence.
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../../index.html'), 'utf8');
function source(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  if (a < 0 || b <= a) throw new Error(`Missing source boundary: ${start}`);
  return html.slice(a, b);
}
const picker = source('  let _autocompleteService =', '  const _headCallback')
  + source('  function _addressInputState(', '  function fillBrandOfficeAddressFields(');
const page = `<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Address picker — local QA only</title>
<style>
body{font:17px system-ui;margin:32px auto;max-width:660px;padding:0 20px;background:#f7f9fb;color:#152840}
label{display:block;margin:16px 0 6px}input:not([type=checkbox]){box-sizing:border-box;width:100%;padding:12px;border:1px solid #667789;border-radius:6px;font:inherit}
input:focus,button:focus{outline:3px solid #b17c1d;outline-offset:2px}button{font:inherit;padding:10px;margin-top:18px}
pre{white-space:pre-wrap;background:white;padding:16px}small{display:block;margin:12px 0}
</style>
<h1>Address picker — local QA only</h1>
<p>Real HomeOfferFlow picker code with synthetic responses. No Google or other external requests.</p>
<label><input id="hold" type="checkbox"> Hold address details until released</label>
<label for="propAddress">Property address</label><input id="propAddress" autocomplete="off">
<label for="propCity">City</label><input id="propCity">
<label for="propState">State</label><input id="propState">
<label for="propZip">ZIP code</label><input id="propZip">
<label for="propCounty">County</label><input id="propCounty">
<button id="release" type="button">Release address details</button>
<small id="stats" aria-live="polite"></small><pre id="values"></pre>
<script>
let searches=0,details=0,pending=[];
const byId=id=>document.getElementById(id);
function display(){
  byId('stats').textContent='Synthetic searches: '+searches+'; details: '+details+'; pending: '+pending.length;
  byId('values').textContent=JSON.stringify(Object.fromEntries(['propAddress','propCity','propState','propZip','propCounty'].map(id=>[id,byId(id).value])),null,2);
}
window._AutocompleteSessionToken=class{};
window._AutocompleteSuggestion={fetchAutocompleteSuggestions:async()=>{
  searches++;display();return {suggestions:[100,200].map(number=>({placePrediction:{
    mainText:number+' Test Street',secondaryText:'Test City, TX',text:number+' Test Street, Test City, TX 75001',
    toPlace:()=>({formattedAddress:number+' Test Street, Test City, TX 75001',
      addressComponents:[['street_number',String(number)],['route','Test Street'],['subpremise','4'],['locality','Test City'],['administrative_area_level_1','TX'],['administrative_area_level_2','Test County'],['postal_code','75001'],['postal_code_suffix','1234']].map(([type,text])=>({types:[type],longText:text,shortText:text})),
      fetchFields:()=>{details++;if(!byId('hold').checked){display();return Promise.resolve();}return new Promise(resolve=>{pending.push(resolve);display();});}})
  }}))};
}};
${picker}
_wireGoogleAutocomplete(byId('propAddress'),fillAddressFields);
document.addEventListener('input',display);document.addEventListener('change',display);
byId('release').addEventListener('mousedown',e=>e.preventDefault());
byId('release').addEventListener('click',()=>{const tasks=pending;pending=[];tasks.forEach(resolve=>resolve());display();});
display();
</script></html>`;
const server = http.createServer((req, res) => {
  if (req.url === '/favicon.ico') { res.writeHead(204); res.end(); return; }
  if (req.url !== '/') { res.writeHead(404); res.end('Not found'); return; }
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store',
    'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; form-action 'none'"
  });
  res.end(page);
});
server.listen(0, '127.0.0.1', () => {
  console.log(`Address picker QA: http://127.0.0.1:${server.address().port}/`);
});

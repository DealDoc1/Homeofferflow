// Read-only display of real source components and the live public directory.
// No customer packet, contact request, signature invitation or charge is sent.
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname,'../..');
const label = '<aside style="max-width:980px;margin:15px auto;padding:10px;font:13px system-ui;color:#ddd">READ-ONLY DISPLAY CHECK — actual components with live published profiles; no customer packet sent</aside>';
let providers = [];
function page(mode) {
  const index = fs.readFileSync(path.join(root,'index.html'),'utf8');
  const styles = [...index.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(m=>'<style>'+m[1]+'</style>').join('');
  let content, script='';
  if(mode==='planning') {
    const start=index.indexOf('<details class="payment-calc-card"');
    content='<section id="step4" class="wizard-step active"><h2>Estimate monthly payment</h2>'+index.slice(start,index.indexOf('</details>',start)+10).replace('id="paymentCalcCard"','id="paymentCalcCard" open')+'</section>';
  } else {
    const start=index.indexOf('        <section class="now-what" id="nowWhatPartnerJourney"');
    content=index.slice(start,index.indexOf('\n        </section>',start)+19);
    const constants=index.slice(index.indexOf('  const NOW_WHAT_PARTNER_LABELS'),index.indexOf('  function nowWhatFormatDate'));
    const render=index.slice(index.indexOf('  function renderNowWhatDirectory('),index.indexOf('  async function renderNowWhatPartnerJourney('));
    const sortStart=index.indexOf('  function nowWhatPartnerSort(');
    const sort=index.slice(sortStart,index.indexOf('\n  function ',sortStart+20));
    script=constants+sort+'\nfunction bindOfferCompletionPartnerClicks(){} function trackPartnerDirectoryImpressions(){}\n'+render+'\nwindow.hofPartnerProfile.load().then(renderNowWhatDirectory);';
  }
  return '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Insurance partner '+mode+' display check</title>'+styles+'<link rel="stylesheet" href="/assets/inspection-partners.css"><script src="/assets/partner-profile.js"></script><script src="/assets/insurance-partners.js" defer></script><style>main{max-width:980px;margin:20px auto;padding:0 16px}.wizard-step.active{display:block}body{min-height:100vh}</style></head><body>'+label+'<main>'+content+'</main><script>'+script+'</script></body></html>';
}
const assets=new Set(['/assets/partner-profile.js','/assets/insurance-partners.js','/assets/inspection-partners.css']);
async function start() {
  const result=await fetch('https://www.homeofferflow.com/api/fsbo-lead?partner_directory=1').then(r=>r.json());
  providers=result.partners;
  if(!result.ok || !providers.some(p=>p.partner_type==='insurance'))throw Error('Published insurance profile missing');
  http.createServer((request,response)=>{
    const route=new URL(request.url,'http://127.0.0.1').pathname;
    if(route==='/api/fsbo-lead'){response.writeHead(200,{'Content-Type':'application/json'});response.end(JSON.stringify(request.method==='GET'?{ok:true,partners:providers}:{ok:true}));return;}
    if(assets.has(route)){response.writeHead(200,{'Content-Type':route.endsWith('.css')?'text/css':'application/javascript'});response.end(fs.readFileSync(root+route));return;}
    if(['/planning','/followup'].includes(route)){response.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});response.end(page(route.slice(1)));return;}
    response.writeHead(404);response.end();
  }).listen(8778,'127.0.0.1',()=>console.log('Read-only display check http://127.0.0.1:8778'));
}
start().catch(error=>{console.error(error.message);process.exitCode=1;});

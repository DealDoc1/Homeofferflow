const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('index.html', 'utf8');
const start = html.indexOf('  let activeOfferPdfRequest;');
const end = html.indexOf('  root.hofRenderOfferWorkspaceV10', start);

(async () => {
  let expire;
  const calls = [], notes = [], previews = [], notices = [];
  let response = {ok:true,headers:{get:()=> 'application/pdf'},blob:async()=>({pdf:true})};
  const actions = {prepend:node=>calls.push({open:node})};
  const modal = {dataset:{blobUrl:'blob:fictional'},querySelector:s=>s.includes('actions')?actions:{after:node=>notes.push(node.textContent)}};
  const root = {hofAuth:{session:{access_token:'fictional'}},announceWorkspaceStatus:m=>notices.push(m),hofShowPdfPreview:(...p)=>previews.push(p)};
  vm.runInNewContext(html.slice(start,end), {root, AbortController, setTimeout:(run,ms)=>{assert.equal(ms,60000);expire=run;return 1;},clearTimeout:id=>{assert.equal(id,1);expire=null;}, document:{getElementById:()=>modal,createElement:()=>({style:{}})},fetch:async(url,opts)=>{calls.push({url,body:JSON.parse(opts.body)});return typeof response === 'function' ? response(opts.signal) : response;}});
  const button = {textContent:'Print unsigned copy',disabled:false};
  await root.hofOpenOfferPdf('saved-offer',button);
  assert.deepEqual(calls[0],{url:'/api/fill-pdf',body:{offerId:'saved-offer',action:'print_offer_pdf'}});
  assert.equal(previews[0][1],'Unsigned offer copy');
  assert.match(notes[0],/does not send invitations or use another packet/);
  assert.equal(calls[1].open.href,'blob:fictional');
  assert.equal(calls[1].open.target,'_blank');
  assert.equal(calls[1].open.textContent,'Open to print');
  assert.equal(button.disabled,false);assert.equal(button.textContent,'Print unsigned copy');
  calls.length=0;
  await root.hofOpenOfferPdf('signed-offer',button,true);
  assert.deepEqual(calls[0],{url:'/api/signwell-status',body:{offerId:'signed-offer',action:'download_completed_pdf'}});
  assert.equal(previews[1][1],'Signed offer');
  response={ok:false,json:async()=>({error:'Document version changed'})};
  await root.hofOpenOfferPdf('saved-offer',button);
  assert.equal(notices.at(-1),'Document version changed');
  assert.equal(button.disabled,false);assert.equal(previews.length,2);
  response={ok:true,headers:{get:()=> 'text/html'}};
  await root.hofOpenOfferPdf('saved-offer',button);
  assert.match(notices.at(-1),/could not be confirmed/);assert.equal(previews.length,2);
  root.hofAuth.session=null;calls.length=0;
  await root.hofOpenOfferPdf('saved-offer',button);
  assert.equal(calls.length,0);assert.match(notices.at(-1),/Sign in again/);
  for (const signed of [false, true]) {
    for (const session of [null, {access_token:'different-account'}]) {
      root.hofAuth.session={access_token:'original-account'};
      const before=previews.length;
      response={ok:true,headers:{get:()=> 'application/pdf'},blob:async()=>{
        root.hofAuth.session=session;
        return {privatePdf:true};
      }};
      await root.hofOpenOfferPdf('saved-offer',button,signed);
      assert.equal(previews.length,before,'An old account PDF must not open after the session changes');
      assert.equal(button.disabled,false);
    }
  }
  root.hofAuth.session={access_token:'original-account'};
  const beforeNotices=notices.length;
  response={ok:false,json:async()=>{
    root.hofAuth.session={access_token:'different-account'};
    return {error:'Old account error'};
  }};
  await root.hofOpenOfferPdf('saved-offer',button);
  assert.equal(notices.length,beforeNotices,'Old account errors must not appear in the new account');
  root.hofAuth.session={access_token:'fictional'};
  response=signal=>new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(signal.reason),{once:true}));
  const pending=root.hofOpenOfferPdf('saved-offer',button);
  assert.equal(button.disabled,true);
  const callsBeforeDuplicate=calls.length;
  await root.hofOpenOfferPdf('saved-offer',button);
  assert.equal(calls.length,callsBeforeDuplicate);
  expire();
  await pending;
  assert.equal(expire,null);
  assert.equal(button.disabled,false);
  assert.match(notices.at(-1),/took too long/);
  response={ok:true,headers:{get:()=> 'application/pdf'},blob:async()=>({pdf:true})};
  await root.hofOpenOfferPdf('saved-offer',button);
  assert.equal(previews.at(-1)[1],'Unsigned offer copy');
  const previewCount = previews.length;
  const noticeCount = notices.length;
  let markOlderBodyStarted, finishOlderPdf, olderSignal;
  const olderBodyStarted = new Promise(resolve=>{markOlderBodyStarted=resolve;});
  response = signal => {
    olderSignal = signal;
    return {ok:true,headers:{get:()=> 'application/pdf'},blob:()=>new Promise(resolve=>{
      finishOlderPdf=resolve;
      markOlderBodyStarted();
    })};
  };
  const older = root.hofOpenOfferPdf('older-offer',button);
  await olderBodyStarted;
  const nextButton = {textContent:'Signed PDF',disabled:false};
  response = {ok:true,headers:{get:()=> 'application/pdf'},blob:async()=>({latest:true})};
  await root.hofOpenOfferPdf('newer-offer',nextButton,true);
  assert.equal(olderSignal.aborted,true);
  finishOlderPdf({stale:true});
  await older;
  assert.deepEqual(previews.slice(previewCount),[[{latest:true},'Signed offer']]);
  assert.equal(notices.length,noticeCount);
  assert.equal(button.disabled,false);
  assert.equal(nextButton.disabled,false);
  console.log('Offer PDF runtime: routing, recovery, request ordering, and session-change privacy passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('index.html', 'utf8');
const start = html.indexOf('  function filterPreparedAgreementRows(');
const end = html.indexOf('  const previous = root.renderAccountDashboard;', start);
assert.ok(start > 0 && end > start);
const source = html.slice(start, end);
const decode = value => value.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
function node() {
  return {value:'',textContent:'',events:{},dataset:{},style:{},isConnected:true,
    addEventListener(name, callback) { this.events[name] = callback; },
    focus() { focused = this; }, remove() { this.isConnected = false; }, scrollIntoView() {}};
}
let focused;
(async () => {
  const loaderStart = html.indexOf('  async function loadAgreements(');
  const loaderEnd = html.indexOf('  async function openSendDialog(', loaderStart);
  let expire, request, cleared = 0, stallBody = true;
  const loadPage = vm.runInNewContext(html.slice(loaderStart, loaderEnd) + '\nloadAgreements;', {
    AbortController,
    token: () => 'fictional-session',
    setTimeout(callback, milliseconds) {
      assert.equal(milliseconds, 30000);
      expire = callback;
      return 1;
    },
    clearTimeout(timer) { assert.equal(timer, 1); cleared++; },
    fetch: async (url, { headers, signal }) => {
      request = { url, headers, signal };
      return { ok: true, json: () => stallBody
        ? new Promise((_, reject) => signal.addEventListener('abort', () => reject(signal.reason), { once: true }))
        : Promise.resolve({ agreements: [] }) };
    }
  });
  const stalled = loadPage(100);
  await Promise.resolve();
  assert.equal(request.url, '/api/admin-dashboard?scope=standalone_agreements&offset=100');
  assert.equal(request.headers.Authorization, 'Bearer fictional-session');
  expire();
  await assert.rejects(stalled, /Could not load/);
  assert.equal(cleared, 1);
  stallBody = false;
  assert.deepEqual((await loadPage()).agreements, []);
  assert.ok(request.url.endsWith('offset=0'));
  assert.equal(request.signal.aborted, false);
  assert.equal(cleared, 2);

  let active = true, refreshPromise, loads = 0, fail = false, paged = false, pages = {}, hold = null;
  const offsets = [];
  let agreements = [
    {id:'signed',form_code:'TXR-1507',client_names:['Jordan Reyes'],status:'signed',signwell_document_id:'tracked-signed'},
    {id:'sent',form_code:'TXR-1507',client_names:['Jordan Reyes'],status:'sent',signwell_document_id:'tracked-sent'},
    {id:'notice',form_code:'TXR-1506',client_names:['María López'],status:'draft'},
    {id:'literal',form_code:'TXR-1501',client_names:['<img src=x onerror=QA>'],status:'draft'},
  ];
  const search=node(), clear=node(), status=node(), list=node(), panel=node(), more=node(), moreStatus=node();
  let rows=[], buttons={}, listHtml='';
  let recovery;
  Object.defineProperty(list,'innerHTML',{get:()=>listHtml,set(value) {
    listHtml=value;
    rows=[...value.matchAll(/data-agreement-search="([^"]*)"/g)].map(match=>({...node(),dataset:{agreementSearch:decode(match[1])}}));
    buttons={};
    for (const attribute of ['preview','send','refresh-signing','download-completed','edit-listing']) {
      const key=attribute.replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
      buttons[`[data-${attribute}]`]=[...value.matchAll(new RegExp(`data-${attribute}="([^"]*)"`,'g'))].map((match,index)=>({...node(),dataset:{[key]:decode(match[1])},closest:()=>rows[index]}));
    }
    if (value.includes('data-retry-prepared-documents')) buttons['[data-retry-prepared-documents]'] = [node()];
  }});
  list.querySelectorAll=selector=>selector==='[data-agreement-search]'?rows:(buttons[selector]||[]);
  list.querySelector=selector=>selector==='[data-prepared-document-load-error]'?recovery:list.querySelectorAll(selector)[0];
  list.appendChild=element=>{ recovery=element; };
  list.replaceChildren=()=>{ list.innerHTML=''; recovery=undefined; };
  let card;
  const children={'#hofStandaloneAgreementList':list,'#hofStandaloneAgreementSearch':search,
    '#hofStandaloneAgreementSearchClear':clear,'#hofStandaloneAgreementSearchStatus':status,
    '#hofStandaloneAgreementMore':more,'#hofStandaloneAgreementMoreStatus':moreStatus};
  const root={hofCustomerActionError:(_,fallback)=>fallback};
  const context={root,window:root,document:{get activeElement(){return focused;},body:node(),getElementById:id=>id==='accountPanelDashboard'?panel:id==='hofStandaloneAgreementCard'?card:null,
    createElement:()=>{
      if (card) {
        const retry = node();
        buttons['[data-retry-prepared-documents]'] = [retry];
        return {...node(), setAttribute(){}, querySelector:()=>retry, remove(){ recovery=undefined; }};
      }
      card=node();card.querySelectorAll=list.querySelectorAll;card.querySelector=selector=>children[selector]||buttons['[data-preview]']?.[0];return card;
    }},
    activeAgent:()=>true,captureViewer:()=>({id:'fictional-agent',epoch:0}),viewerIsCurrent:()=>active,
    escape:value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])),
    loadAgreements:async(offset=0)=>{loads++;offsets.push(offset);
      const result=paged?pages[offset]:{agreements};
      if(hold?.offset===offset){const wait=hold.promise;hold=null;await wait;}
      if(fail)throw Error('QA unavailable');
      return {...result,signingEnabled:true,signingFormCodes:['TXR-1501','TXR-1506','TXR-1507']};},
    refreshAgreementSignWellStatus:(_,__,refresh)=>{refreshPromise=refresh();},
    console:{error(){}},Set,Array,String};
  panel.appendChild=()=>{};
  await vm.runInNewContext(`(async()=>{${source}\nawait renderCard();})()`,context);
  const input=query=>{search.value=query;search.events.input();};
  const visible=()=>rows.filter(row=>!row.hidden).length;
  assert.equal(visible(),4);assert.match(status.textContent,/4 of 4/);
  input('jOrDaN signed');assert.equal(visible(),1);
  assert.match(rows.find(row=>!row.hidden).dataset.agreementSearch,/signed/);
  assert.equal(buttons['[data-download-completed]'].length,1);
  assert.ok(!buttons['[data-send]'].some(button=>button.dataset.send==='signed'));
  input('TXR1507');assert.equal(visible(),2);
  input('maria lopez');assert.equal(visible(),1);
  input('<img');assert.equal(visible(),1);assert.ok(!listHtml.includes('<img'));
  input('no such client');assert.equal(visible(),0);assert.match(status.textContent,/No documents match/);
  assert.ok(rows.every(row=>row.style.display==='none'));
  clear.events.click();assert.equal(search.value,'');assert.equal(visible(),4);assert.equal(focused,search);
  input('Jordan');
  agreements=[...agreements,{id:'new',form_code:'TXR-1506',client_names:['Jordan Reyes'],status:'draft'}];
  buttons['[data-refresh-signing]'][0].events.click();await refreshPromise;
  assert.equal(search.value,'Jordan');assert.equal(visible(),3);assert.match(status.textContent,/3 of 5/);
  input('no match');
  assert.equal(await root.hofOpenPreparedAgreement('notice'),true);
  assert.equal(search.value,'');assert.equal(visible(),5);assert.equal(focused.dataset.preview,'notice');
  paged=true;
  const firstPage=Array.from({length:100},(_,i)=>({id:'page-'+i,form_code:'TXR-1507',client_names:['Recent QA '+i],status:'draft'}));
  const secondPage=[{...firstPage[0],status:'signed',signwell_document_id:'tracked'},...Array.from({length:99},(_,i)=>({id:'old-'+i,form_code:'TXR-1506',client_names:[i===0?'Older Client':'Archive QA '+i],status:'draft'}))];
  pages={0:{agreements:firstPage,pagination:{hasMore:true,nextOffset:100}},100:{agreements:secondPage,pagination:{hasMore:true,nextOffset:200}},200:{agreements:[],pagination:{hasMore:false,nextOffset:null}}};
  await root.hofOpenPreparedAgreement();assert.equal(more.hidden,false);
  input('Older Client');assert.equal(visible(),0);
  const beforeFailure=listHtml;fail=true;await more.events.click();
  assert.equal(listHtml,beforeFailure);assert.match(moreStatus.textContent,/unchanged/);assert.equal(more.disabled,false);
  fail=false;
  let resume;hold={offset:100,promise:new Promise(resolve=>resume=resolve)};
  const beforePage=loads;const pageRequest=more.events.click();await more.events.click();
  assert.equal(loads,beforePage+1);assert.equal(more.disabled,true);resume();await pageRequest;
  assert.equal(search.value,'Older Client');assert.equal(rows.length,199);assert.equal(visible(),1);
  assert.equal(offsets.at(-1),100);assert.equal(buttons['[data-download-completed]'].length,1);assert.equal(focused.dataset.preview,'old-0');
  pages[200]={agreements:[],pagination:{hasMore:true,nextOffset:200}};
  const beforeBadPage=listHtml;await more.events.click();assert.equal(listHtml,beforeBadPage);assert.equal(more.hidden,false);
  pages[200]={agreements:[],pagination:{hasMore:false,nextOffset:null}};
  await more.events.click();assert.equal(more.hidden,true);assert.equal(rows.length,199);
  await root.hofOpenPreparedAgreement();
  let finishOld;hold={offset:100,promise:new Promise(resolve=>finishOld=resolve)};
  const oldPage=more.events.click();await root.hofOpenPreparedAgreement('page-0');
  assert.equal(rows.length,100);finishOld();await oldPage;assert.equal(rows.length,100);
  paged=false;await root.hofOpenPreparedAgreement();
  input('Jordan');fail=true;
  buttons['[data-refresh-signing]'][0].events.click();await refreshPromise;
  assert.match(status.textContent,/3 of 5/);assert.equal(search.value,'Jordan');
  assert.equal(visible(),3);
  assert.match(recovery.innerHTML,/last loaded results/);
  assert.equal(buttons['[data-download-completed]'].length,1);
  const retry=list.querySelector('[data-retry-prepared-documents]');
  fail=false;
  let finishRetry;hold={offset:0,promise:new Promise(resolve=>finishRetry=resolve)};
  const beforeRetry=loads;const retryRequest=retry.events.click();await retry.events.click();
  assert.equal(loads,beforeRetry+1);assert.equal(retry.disabled,true);assert.equal(focused,search);
  finishRetry();await retryRequest;
  assert.equal(search.value,'Jordan');assert.equal(visible(),3);
  assert.equal(recovery,undefined);
  fail=false;agreements=[];await root.hofOpenPreparedAgreement();
  assert.equal(status.textContent,'');assert.match(listHtml,/No standalone/);
  paged=true;await root.hofOpenPreparedAgreement();
  let finishOther;hold={offset:100,promise:new Promise(resolve=>finishOther=resolve)};
  const otherAccountPage=more.events.click();const beforeSwitch=listHtml;
  active=false;finishOther();await otherAccountPage;assert.equal(listHtml,beforeSwitch);
  const beforeLoads=loads;search.value='private query';status.textContent='unchanged';
  search.events.input();clear.events.click();assert.equal(status.textContent,'unchanged');assert.equal(search.value,'private query');
  assert.equal(await root.hofOpenPreparedAgreement(),false);assert.equal(loads,beforeLoads);assert.equal(card.isConnected,false);
  console.log('Prepared document search: matching, Unicode, signed actions, refresh, focus, paging, retries and account isolation passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});

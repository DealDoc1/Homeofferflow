const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const assert = require('node:assert/strict'), {test} = require('node:test');
const root = path.join(__dirname, '..');
const html = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', process.env.HOF_TEST_SOURCE_REF + ':index.html'], {cwd:root, encoding:'utf8', maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const customerErrorMatch = html.match(/<script id="hof-customer-action-error-v1">([\s\S]*?)<\/script>/);
assert.ok(customerErrorMatch, 'Customer action error filter is available');
const tick = () => new Promise(setImmediate);
function deferred() { let resolve, reject; const promise = new Promise((y,n) => {resolve=y;reject=n;}); return {promise,resolve,reject}; }

async function setup(code) {
  const marker = `<script id="hof-txr${code}-drafts-v1">`;
  const start = html.indexOf(marker) + marker.length;
  assert.ok(start >= marker.length);
  const script = html.slice(start, html.indexOf('</script>', start));
  const ids = new Map(), ready = [], requests = [];
  let reviews = 0;
  class Element {
    constructor() { this.children=[];this.selectors=new Map();this.listeners={};this.style={};this.attrs={};this.dataset={};this.value='';this.disabled=false;this.checked=false;this.isConnected=true; }
    set innerHTML(value) { this._html=value;this._text='';this.selectors.clear(); }
    get innerHTML() { return this._html || ''; }
    set textContent(value) { this._text=value;this._html='';this.selectors.clear(); }
    get textContent() { return this._text || ''; }
    appendChild(node) { this.children.push(node);if(node.id)ids.set(node.id,node); }
    querySelector(selector) { if(/^#txr\d+AgreementForm$/.test(selector))selector='form';if(!this.selectors.has(selector))this.selectors.set(selector,new Element());return this.selectors.get(selector); }
    querySelectorAll(selector) { return [this.querySelector(selector)]; }
    addEventListener(name, callback) { this.listeners[name]=callback; }
    setAttribute(name,value) { this.attrs[name]=value; }
    removeAttribute(name) { delete this.attrs[name]; }
    remove() { this.isConnected=false;ids.delete(this.id); }
  }
  const panel = new Element(), body = new Element();ids.set('accountPanelRelationships',panel);
  const document = {body,readyState:'loading',getElementById:id=>ids.get(id)||null,createElement:()=>new Element(),addEventListener:(_,callback)=>ready.push(callback)};
  const values = {propertyAddress:'100 QA Street',address:'100 QA Street',buyerOne:'QA Buyer',b1:'QA Buyer',sellerOne:'QA Seller',s1:'QA Seller',clientOne:'QA Client',customerOne:'QA Client',consumerOne:'QA Client',creditDays:'5',days:'7',ack:'on',loanAssumptionReviewAcknowledgment:'on',review:['environmental'],creditDocument:['credit_report']};
  const window = {hofAuth:{role:'agent',session:{user:{id:'qa-user'},access_token:'qa-token'}},hofLoadApprovedBrokerageSource:async()=>({id:'qa-source',source_revision:'QA'}),hofOpenPreparedAgreement:async()=>{reviews++;}};
  const context = vm.createContext({window,document,console:{error(){}},FormData:class{constructor(form){assert.ok(form, 'FormData needs the form during event dispatch');}get(k){return values[k]??null;}getAll(k){return values[k]||[];}},fetch:(url,options)=>{const d=deferred();requests.push({url,options,...d});return d.promise;}});
  vm.runInContext(customerErrorMatch[1],context);
  vm.runInContext(script,context);ready.forEach(callback=>callback());await tick();
  const opener=panel.children[0].children[0];(opener.onclick||opener.listeners.click)();
  const modal = body.children[0], form = modal.querySelector('form'), button = form.querySelector('button[type="submit"]');
  const initialLabel=modal.innerHTML.match(/<button[^>]*type="submit"[^>]*>([^<]+)<\/button>/)[1];
  button.textContent=initialLabel;
  const status=modal.querySelector(code===1917?'.hof-iabs-status':`#txr${code}DraftStatus`);
  const submit=()=>{
    const event={currentTarget:form,preventDefault(){}};
    const result=(form.listeners.submit||form.onsubmit)(event);
    // The DOM clears currentTarget when dispatch ends, before awaited fetch.
    event.currentTarget=null;
    return Promise.resolve(result).then(tick);
  };
  const reply=(index,ok=true,error='Please check the entered terms.')=>requests[index].resolve({ok,json:async()=>ok?{id:'qa-draft'}:{error}});
  return {submit,reply,requests,button,status,modal,values,initialLabel,reviews:()=>reviews};
}

for(const code of [1501,1506,1507,1508,1905,1914,1917,1919,1948,1953,1954]) {
  test(`TXR-${code} successful save survives currentTarget clearing`,async()=>{
    const x=await setup(code),pending=x.submit();x.reply(0);await pending;
    assert.equal(x.status.className,'hof-iabs-status ready');assert.match(x.status.innerHTML,/Review and send/);
    assert.equal(x.button.disabled,true);assert.equal(x.button.attrs['aria-busy'],'false');
    assert.equal(x.button.textContent,'Draft ready');
    const payload=JSON.parse(x.requests[0].options.body);assert.equal(payload.action,`create_txr_${code}_draft`);
    if('propertyAddress' in payload)assert.equal(payload.propertyAddress,'100 QA Street');
    if('buyerNames' in payload)assert.deepEqual(payload.buyerNames,['QA Buyer']);
    if('clientNames' in payload)assert.deepEqual(payload.clientNames,['QA Client']);
  });
  test(`TXR-${code} blocks duplicate submissions while saving and after success`,async()=>{
    const x=await setup(code),first=x.submit(),second=x.submit();assert.equal(x.requests.length,1);
    assert.equal(x.button.disabled,true);assert.equal(x.button.attrs['aria-busy'],'true');
    x.reply(0);await Promise.all([first,second]);await x.submit();assert.equal(x.requests.length,1);
  });
  test(`TXR-${code} rejected save keeps answers and allows a deliberate retry`,async()=>{
    const x=await setup(code),first=x.submit();x.reply(0,false);await first;
    assert.equal(x.status.className,'hof-iabs-status error');assert.equal(x.status.textContent,'Please check the entered terms.');
    assert.equal(x.button.disabled,false);assert.equal(x.button.attrs['aria-busy'],'false');assert.equal(x.button.textContent,x.initialLabel);
    const second=x.submit();assert.equal(x.requests.length,2);assert.equal(x.requests[1].options.body,x.requests[0].options.body);
    x.reply(1);await second;assert.equal(x.status.className,'hof-iabs-status ready');
  });
  test(`TXR-${code} network error restores the save control without retrying automatically`,async()=>{
    const x=await setup(code),pending=x.submit();x.requests[0].reject(new Error('Connection lost'));await pending;
    assert.equal(x.button.disabled,false);assert.equal(x.button.attrs['aria-busy'],'false');assert.equal(x.requests.length,1);
    assert.equal(x.status.className,'hof-iabs-status error');
  });
  test(`TXR-${code} review action opens the queue without sending a signing request`,async()=>{
    const x=await setup(code),pending=x.submit();x.reply(0);await pending;
    assert.equal(x.status.className,'hof-iabs-status ready');await x.status.querySelector('button').listeners.click();
    assert.equal(x.modal.isConnected,false);assert.equal(x.reviews(),1);assert.equal(x.requests.length,1);
  });
}

const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), {test} = require('node:test');
const asset = fs.readFileSync(path.join(__dirname, '..', 'assets', 'trec-39-11-amendment.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
test('a failed source load rejects the guided opener so its caller can show retry', async () => {
  const problem = new Error('Synthetic temporary source outage');
  const announcements = [];
  const root = {hofLoadApprovedBrokerageSource:async()=>{throw problem;},
    announceWorkspaceStatus:message=>announcements.push(message)};
  const document = {readyState:'loading',addEventListener(){}};
  vm.runInNewContext(asset, {window:root,document});
  await assert.rejects(root.hofOpenTrec3911Draft(), error=>error===problem);
  assert.ok(announcements.length<=1);
});
test('actual guided handoff keeps a retry after the amendment source rejects', async () => {
  const start = html.indexOf('    const openRelationshipDraft = (openerName, onOpened, request)');
  const end = html.indexOf('    const openRelationshipPackage =',start);
  assert.ok(start>0&&end>start);
  const nodes=new Map(), timers=[];
  function node(tag) {
    return {tag,id:'',textContent:'',children:[],setAttribute(){},style:{},
      appendChild(child){this.children.push(child);},
      addEventListener(event,action){this[event]=action;},
      remove(){nodes.delete(this.id);this.removed=true;}};
  }
  const panel=node('div'); panel.prepend=child=>nodes.set(child.id,child);
  nodes.set('accountPanelRelationships',panel);
  const document={readyState:'loading',addEventListener(){},getElementById:id=>nodes.get(id),createElement:node};
  const root={setTimeout:fn=>timers.push(fn),hofLoadApprovedBrokerageSource:async()=>{throw Error('Synthetic source failure');}};
  const context=vm.createContext({window:root,document,kind:'purchase',showAccountTab(){}});
  vm.runInContext(asset,context);
  vm.runInContext(html.slice(start,end)+'\nthis.openSelected=openRelationshipDraft;',context);
  let opened=0;
  context.openSelected('hofOpenTrec3911Draft',()=>opened++,{formCode:'TREC-39-11'});
  timers.shift()();
  await new Promise(setImmediate);
  const status=nodes.get('hofAgentDocumentOpenStatus');
  assert.ok(status && !status.removed);
  assert.match(status.textContent,/try again/i);
  assert.equal(status.children.length,1);
  assert.equal(status.children[0].textContent,'Try again');
  assert.equal(opened,0);
});

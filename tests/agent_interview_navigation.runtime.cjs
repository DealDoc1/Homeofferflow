const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('    const returnFocus =', html.indexOf('  window.hofOpenAgentPackageInterview = function'));
const end = html.indexOf('    const recordPackageWorkspaceStart =', start);
assert.ok(start >= 0 && end > start, 'Interview keyboard helpers must be present');
const source = html.slice(start, end);

function setup() {
  const document = {activeElement:null, choices:[], querySelectorAll(){return this.choices;}};
  class Element {
    constructor(id, options = {}) {
      Object.assign(this, {id, tabIndex:0, isConnected:true, hidden:false, disabled:false, visible:true, dataset:{}}, options);
    }
    focus(options) { this.focusOptions = options; document.activeElement = this; }
    matches() { return this.disabled; }
    closest() { return this.hidden ? this : null; }
    getClientRects() { return this.visible ? [{}] : []; }
    setAttribute(name,value) { this[name] = value; }
  }
  const launcher = new Element('purchase-launcher');
  document.activeElement = launcher;
  const context = {document, HTMLElement:Element, kind:'purchase'};
  vm.runInNewContext(source + '\nthis.bind = bindPackageQuestionKeys; this.restore = restorePackageFocus;', context);
  const first = new Element('first');
  const middle = new Element('middle');
  const last = new Element('back');
  const dialog = new Element('dialog', {tabIndex:-1});
  const handlers = {};
  const modal = {
    controls:[first,middle,last],
    addEventListener(name,handler){handlers[name]=handler;},
    querySelectorAll(){return this.controls;},
    querySelector(){return dialog;},
  };
  let closed = 0;
  context.bind(modal,()=>{closed++;context.restore();});
  const press = (key,shiftKey=false) => {
    const event={key,shiftKey,prevented:false,stopped:false,
      preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;}};
    handlers.keydown(event);
    return event;
  };
  return {document,Element,context,launcher,first,middle,last,dialog,modal,press,closed:()=>closed};
}

test('Tab at the last answer wraps to the first answer',()=>{
  const page=setup();page.last.focus();
  assert.equal(page.press('Tab').prevented,true);
  assert.equal(page.document.activeElement,page.first);
});

test('Shift+Tab at the first answer wraps to Back',()=>{
  const page=setup();page.first.focus();
  assert.equal(page.press('Tab',true).prevented,true);
  assert.equal(page.document.activeElement,page.last);
});

test('wrapped focus lets the browser reveal an offscreen answer',()=>{
  const page=setup();page.first.focus();page.press('Tab',true);
  assert.notEqual(page.last.focusOptions?.preventScroll,true);
  page.press('Tab');assert.notEqual(page.first.focusOptions?.preventScroll,true);
});

test('interior answers keep native tab order',()=>{
  const page=setup();page.middle.focus();
  assert.equal(page.press('Tab').prevented,false);
  assert.equal(page.press('Tab',true).prevented,false);
});

test('Escape closes only the active question and restores its launcher',()=>{
  const page=setup();page.first.focus();
  const event=page.press('Escape');
  assert.equal(page.closed(),1);
  assert.equal(event.prevented,true);
  assert.equal(event.stopped,true);
  assert.equal(page.document.activeElement,page.launcher);
});

test('unrelated keys do not close or interfere with a question',()=>{
  const page=setup();page.first.focus();
  assert.equal(page.press('Enter').prevented,false);
  assert.equal(page.closed(),0);
});

test('hidden, disabled, negative-tabindex and nonrendered controls are skipped',()=>{
  const page=setup();
  page.modal.controls=[
    new page.Element('hidden',{hidden:true}),new page.Element('disabled',{disabled:true}),
    page.first,page.last,new page.Element('untabbable',{tabIndex:-1}),new page.Element('not-rendered',{visible:false}),
  ];
  page.last.focus();page.press('Tab');
  assert.equal(page.document.activeElement,page.first);
  page.first.focus();page.press('Tab',true);
  assert.equal(page.document.activeElement,page.last);
});

test('a temporarily empty dialog keeps keyboard focus and can still be closed',()=>{
  const page=setup();page.modal.controls=[];
  assert.equal(page.press('Tab').prevented,true);
  assert.equal(page.document.activeElement,page.dialog);
  assert.equal(page.dialog.tabindex,'-1');
  page.press('Escape');assert.equal(page.closed(),1);
});

test('controls added after opening participate in the focus order',()=>{
  const page=setup();const added=new page.Element('late-answer');
  page.modal.controls.push(added);added.focus();page.press('Tab');
  assert.equal(page.document.activeElement,page.first);
  page.press('Tab',true);assert.equal(page.document.activeElement,added);
});

test('lost focus is recovered in the direction requested by the user',()=>{
  const page=setup();page.launcher.focus();page.press('Tab');
  assert.equal(page.document.activeElement,page.first);
  page.launcher.focus();page.press('Tab',true);
  assert.equal(page.document.activeElement,page.last);
});

test('a replaced launcher returns focus to the matching transaction choice',()=>{
  const page=setup();page.launcher.isConnected=false;
  const other=new page.Element('lease',{dataset:{agentWorkflowChoice:'lease_listing'}});
  const replacement=new page.Element('new-purchase',{dataset:{agentWorkflowChoice:'purchase'}});
  page.document.choices=[other,replacement];page.first.focus();page.context.restore();
  assert.equal(page.document.activeElement,replacement);
});

test('nested questions keep the original launcher instead of a removed answer',()=>{
  const page=setup();const removedAnswer=new page.Element('old-answer',{isConnected:false});
  page.document.activeElement=removedAnswer;page.context.restore();
  assert.equal(page.document.activeElement,page.launcher);
});

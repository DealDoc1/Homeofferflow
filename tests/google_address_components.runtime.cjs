const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'),{test}=require('node:test');
const root=path.join(__dirname,'..');
const html=process.env.HOF_TEST_SOURCE_REF
  ?execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024})
  :fs.readFileSync(path.join(root,'index.html'),'utf8');
function source(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a,start);return html.slice(a,b);}
const component=(type,long,short=long)=>({types:[type],long_name:long,short_name:short});
const complete=[component('street_number','42'),component('route','Example Road'),component('locality','Austin'),component('administrative_area_level_2','Travis County'),component('administrative_area_level_1','Texas','TX'),component('postal_code','78701')];
function setup(){
  const elements=new Map(),events=[],timers=[],legacy=[],marked=[];
  function field(id,value='old value',name=''){const el={id,name,value,isConnected:true,dataset:{},style:{},setAttribute(){},
    dispatchEvent(e){events.push({id,type:e.type,values:Object.fromEntries([...elements].map(([key,node])=>[key,node.value]))});},focus(){}};elements.set(id,el);return el;}
  for(const id of ['propAddress','propCity','propCounty','propState','propZip','buyerMailAddr','clientCityStateZip','brandOfficeCity','brandOfficeState','brandOfficeZip','fsboPropertyAddress','fsboPropertyCity','fsboPropertyCounty','fsboPropertyState','fsboPropertyZip','fsboSellerEmail'])field(id);
  const document={getElementById:id=>elements.get(id)||null,querySelector:selector=>selector.includes('clientCityStateZip')?elements.get('clientCityStateZip'):null,querySelectorAll:()=>[...elements.values()]};
  class LegacyAutocomplete {
    constructor(input){this.input=input;this.listeners={};this.place={};legacy.push(this);}
    addListener(name,fn){this.listeners[name]=fn;}
    getPlace(){return this.place;}
  }
  const google={maps:{places:{Autocomplete:LegacyAutocomplete}}};
  const c=vm.createContext({document,google,window:{google,setTimeout:fn=>timers.push(fn)},markGoogleAddressSelected:input=>marked.push(input),setTimeout:fn=>timers.push(fn),Event:class{constructor(type){this.type=type;}},
    HOF_LEGACY_ADDRESS_KEYS:new Set(),isHofAddressInput:()=>true});
  // Use the actual value/event helper when present, not a second implementation.
  vm.runInContext(source('  let _autocompleteService =','  const _headCallback'),c);
  if(html.includes('  function _addressInputState('))vm.runInContext(source('  function _addressInputState(','  function _wireGoogleAutocomplete('),c);
  vm.runInContext(source('  function _debounce(','  function tryInitAutocomplete('),c);
  vm.runInContext(source('  function addressAutocompleteInputs()','  // Apply the fallback semantics'),c);
  vm.runInContext(source('  function wireLegacyGoogleAddressInputs()','  // Load and attach Places'),c);
  return {c,elements,events,field,timers,legacy,marked};
}
test('new property clears missing city county state and ZIP instead of reusing old values',()=>{
  const x=setup();x.c.fillAddressFields([component('street_number','42'),component('route','Example Road')]);
  assert.equal(x.elements.get('propAddress').value,'42 Example Road');
  for(const id of ['propCity','propCounty','propState','propZip'])assert.equal(x.elements.get(id).value,'',id);
});
test('complete property fills all components before any change listener observes them',()=>{
  const x=setup();x.c.fillAddressFields(complete);
  const expected={propAddress:'42 Example Road',propCity:'Austin',propCounty:'Travis',propState:'TX',propZip:'78701'};
  for(const [id,value]of Object.entries(expected)){assert.equal(x.elements.get(id).value,value);assert.ok(x.events.some(e=>e.id===id&&e.type==='input'));assert.ok(x.events.some(e=>e.id===id&&e.type==='change'));}
  for(const e of x.events)for(const [id,value]of Object.entries(expected))assert.equal(e.values[id],value);
});
test('buyer mailing address preserves unit number and ZIP+4',()=>{
  const x=setup();x.c.fillBuyerMailAddressField([...complete,component('subpremise','5B'),component('postal_code_suffix','1234')]);
  assert.equal(x.elements.get('buyerMailAddr').value,'42 Example Road #5B, Austin, TX 78701-1234');
  assert.ok(x.events.some(e=>e.id==='buyerMailAddr'&&e.type==='change'));
});
test('empty buyer components do not replace selected fallback with invented Texas text',()=>{
  const x=setup();x.elements.get('buyerMailAddr').value='Selected rural mailing address';x.c.fillBuyerMailAddressField([]);
  assert.equal(x.elements.get('buyerMailAddr').value,'Selected rural mailing address');
});
test('property and seller street addresses preserve unit numbers',()=>{
  const x=setup(),components=[...complete,component('subpremise','12')];x.c.fillAddressFields(components);x.c.fillFsboAddressFields(components);
  assert.equal(x.elements.get('propAddress').value,'42 Example Road #12');assert.equal(x.elements.get('fsboPropertyAddress').value,'42 Example Road #12');
});
test('office and client companion fields clear when new place lacks those details',()=>{
  const x=setup();x.c.fillBrandOfficeAddressFields([]);x.c.fillClientMailingAddressFields([]);
  for(const id of ['brandOfficeCity','brandOfficeState','brandOfficeZip','clientCityStateZip'])assert.equal(x.elements.get(id).value,'',id);
});
test('name-only representation address receives its companion-field callback',()=>{
  const x=setup(),input=x.field('','','clientAddress');
  const match=x.c.addressAutocompleteInputs().find(([el])=>el===input);assert.equal(match[1],x.c.fillClientMailingAddressFields);
});
test('seller location fields reflect the new place before its progress event',()=>{
  const x=setup();x.c.fillFsboAddressFields(complete);const event=x.events.find(e=>e.id==='fsboPropertyAddress'&&e.type==='input');
  assert.ok(event);assert.equal(event.values.fsboPropertyCity,'Austin');assert.equal(event.values.fsboPropertyCounty,'Travis');assert.equal(event.values.fsboPropertyZip,'78701');
});
test('sublocality fallback never replaces the supplied city',()=>{
  const x=setup();x.c.fillAddressFields([...complete,component('sublocality_level_1','Neighborhood')]);assert.equal(x.elements.get('propCity').value,'Austin');
});
test('office and client fields preserve non-Texas states and postal suffixes',()=>{
  const x=setup(),values=[component('locality','Denver'),component('administrative_area_level_1','Colorado','CO'),component('postal_code','80202'),component('postal_code_suffix','5555')];
  x.c.fillBrandOfficeAddressFields(values);x.c.fillClientMailingAddressFields(values);
  assert.equal(x.elements.get('brandOfficeState').value,'CO');assert.equal(x.elements.get('brandOfficeZip').value,'80202-5555');
  assert.equal(x.elements.get('clientCityStateZip').value,'Denver, CO 80202-5555');
});
test('property fallback remains intact when Google supplies no street components',()=>{
  const x=setup();x.elements.get('propAddress').value='Selected Rural Property';x.c.fillAddressFields([]);
  assert.equal(x.elements.get('propAddress').value,'Selected Rural Property');assert.equal(x.elements.get('propCounty').value,'');
});
test('a street number without a route never replaces the complete selected address',()=>{
  const x=setup();x.elements.get('propAddress').value='42 Selected Rural Property';x.c.fillAddressFields([component('street_number','42')]);
  assert.equal(x.elements.get('propAddress').value,'42 Selected Rural Property');
});
test('an empty legacy place event does not clear or falsely confirm manual entry',()=>{
  const x=setup();x.c.wireLegacyGoogleAddressInputs();const picker=x.legacy.find(p=>p.input.id==='propAddress');
  picker.listeners.place_changed();assert.equal(x.elements.get('propAddress').value,'old value');assert.equal(x.elements.get('propCounty').value,'old value');assert.equal(x.marked.length,0);
});
test('legacy Google selection also clears old location data when components are absent',()=>{
  const x=setup();x.c.wireLegacyGoogleAddressInputs();const picker=x.legacy.find(p=>p.input.id==='propAddress');
  picker.place={formatted_address:'Selected Rural Property'};picker.listeners.place_changed();
  assert.equal(x.elements.get('propAddress').value,'Selected Rural Property');for(const id of ['propCity','propState','propCounty','propZip'])assert.equal(x.elements.get(id).value,'');
  assert.equal(x.events[0].values.propAddress,'Selected Rural Property');assert.equal(x.events[0].values.propCounty,'');
});
test('legacy events from removed controls cannot fill a newly rendered form',()=>{
  const x=setup();x.c.wireLegacyGoogleAddressInputs();const picker=x.legacy.find(p=>p.input.id==='propAddress');picker.input.isConnected=false;
  picker.place={formatted_address:'Different Property',address_components:complete};picker.listeners.place_changed();
  assert.equal(x.elements.get('propCounty').value,'old value');assert.equal(x.marked.length,0);
});
test('new selection companion discovery uses name when an input also has another id',()=>{
  const x=setup(),input=x.field('dynamic-mailing','','clientAddress');
  assert.equal(x.c._googleAddressCompanions(input)[0],x.elements.get('clientCityStateZip'));
});
function collect(x,step){
  Object.assign(x.c,{state:{data:{county:'Previous County'},step:0},getCurrentSteps:()=>[step],
    getVal:id=>x.elements.get(id)?.value||'',getRadio:()=>'',checkedValues:()=>[],moneyNumber:()=>0,buildLegalDescription:()=>''});
  vm.runInContext(source('  function collectData()','  function selectPlan('),x.c);x.c.collectData();return x.c.state.data;
}
test('offer collection receives the new property without the previous county or ZIP',()=>{
  const x=setup();x.c.fillAddressFields([component('street_number','42'),component('route','Example Road'),component('subpremise','7')]);
  const data=collect(x,'step2');assert.equal(data.address,'42 Example Road #7');assert.equal(data.city,'');assert.equal(data.county,'');assert.equal(data.zip,'');
});
test('buyer collection retains the full selected mailing unit and postal suffix',()=>{
  const x=setup();x.c.fillBuyerMailAddressField([...complete,component('subpremise','5B'),component('postal_code_suffix','1234')]);
  assert.equal(collect(x,'step1').buyerMailAddr,'42 Example Road #5B, Austin, TX 78701-1234');
});

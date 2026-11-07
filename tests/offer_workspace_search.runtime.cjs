const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('index.html', 'utf8');
const script = html.split('<script id="hof-agent-workspace-v10-js">')[1].split('</script>')[0];
const cards = {innerHTML:''}, summary = {innerHTML:''};
const exportButton = {};
let inputValue = '', valueWrites = 0, containerWrites = 0;
const input = {selectionStart:0, selectionEnd:0};
Object.defineProperty(input, 'value', {get:()=>inputValue, set:value=>{inputValue=value; valueWrites++; input.selectionStart=value.length;}});
const list = {querySelector:selector=>selector === '.offer-workspace-list' ? cards : summary};
const document = {activeElement:input, getElementById:id=>id === 'myOffersList' ? list : id === 'offerWorkspaceSearch' ? input : id === 'offerWorkspaceExport' ? exportButton : null};
Object.defineProperty(list, 'innerHTML', {set:()=>{containerWrites++; document.activeElement=null;}});
const saved = {};
const root = {};
vm.runInNewContext(script, {window:root,document,sessionStorage:{getItem:()=>null,setItem:(key,value)=>saved[key]=value},console,URLSearchParams,Date});
const offers = [
 {id:'fictional-a',property_address:'123 Maple Lane',buyer_name:'Alex Lee',status:'Draft',last_updated:'2026-11-04'},
 {id:'fictional-b',property_address:'456 Oak Road',buyer_name:'Bob Lee',status:'Draft',last_updated:'2026-11-03'}
];
assert.match(root.hofRenderOfferWorkspaceV10(offers), /offerWorkspaceSearch/);
for (const query of ['M','Ma','Map','Mapl','Maple']) {
 inputValue=query; input.selectionStart=query.length; input.selectionEnd=query.length;
 const beforeWrites=valueWrites;
 root.hofSetOfferWorkspaceSearch(query);
 assert.equal(document.activeElement,input);
 assert.equal(input.selectionStart,query.length);
 assert.equal(valueWrites,beforeWrites,'Typing must not assign input.value and disrupt selection/composition');
 assert.match(cards.innerHTML,/123 Maple Lane/);
 assert.doesNotMatch(cards.innerHTML,/456 Oak Road/);
 assert.match(summary.innerHTML, /<strong>1<\/strong> of 2/);
 assert.equal(JSON.parse(saved.hof_offer_workspace_state_v1).query,query);
}
// Editing in the middle, Unicode composition, no matches, backspace and native clear.
for (const [query,caret] of [['MapXle',4],['Maple',3],['家',1],['Ma',2],['',0]]) {
 inputValue=query; input.selectionStart=caret; input.selectionEnd=caret;
 root.hofSetOfferWorkspaceSearch(query);
 assert.equal(document.activeElement,input); assert.equal(input.selectionStart,caret);
 assert.equal(input.selectionEnd,caret); assert.equal(input.value,query);
 if (query === '家' || query === 'MapXle') {assert.match(cards.innerHTML,/No saved purchase offers/);assert.match(summary.innerHTML,/<strong>0<\/strong>/);}
}
assert.equal(containerWrites,0,'Search must never replace the input parent');
assert.match(cards.innerHTML,/123 Maple Lane/); assert.match(cards.innerHTML,/456 Oak Road/);
assert.doesNotMatch(summary.innerHTML,/Reset view/);
root.hofSetOfferWorkspaceSearch('Oak');
assert.equal(input.value,'Oak'); assert.match(cards.innerHTML,/456 Oak Road/);
assert.match(summary.innerHTML,/Reset view/);
root.hofRenderOfferWorkspaceV10([...offers,
 {id:'fictional-c',property_address:'17 Saint-Clair Avenue',buyer_name:'María José O’Neal',buyer_email:'maria@example.test',status:'Draft',last_updated:'2026-11-02'},
 {id:'fictional-d',property_address:'88 Sakura Way',buyer_name:'李小龙',status:'Draft',last_updated:'2026-11-01'}
]);
for (const [query,property] of [
 ['Alex Maple','123 Maple Lane'], ['MAPLE   alex','123 Maple Lane'],
 ['maria clair','17 Saint-Clair Avenue'], ['JOSE ONEAL','17 Saint-Clair Avenue'],
 ["O'Neal maria",'17 Saint-Clair Avenue'], ['mari\u0301a@example.test','17 Saint-Clair Avenue'],
 ['小龙 sakura','88 Sakura Way']
]) {
 root.hofSetOfferWorkspaceSearch(query);
 assert.ok(cards.innerHTML.includes(property),'Search must combine words from the same offer and normalize accented names: '+query);
 assert.match(summary.innerHTML,/<strong>1<\/strong> of 4/);
 assert.equal(document.activeElement,input);
}
for (const query of ['Alex Clair','Maria Maple','小龙 Oak']) {
 root.hofSetOfferWorkspaceSearch(query);
 assert.match(cards.innerHTML,/No saved purchase offers/,'Words from separate offers must not combine into a match');
}
root.hofSetOfferWorkspaceSearch('   ');
assert.match(summary.innerHTML,/<strong>4<\/strong> of 4/);
assert.doesNotMatch(summary.innerHTML,/Reset view/);
assert.equal(containerWrites,0);
console.log('Offer search: focus/caret, multiword and Unicode matching, empty states, clearing and persistence passed.');

root.hofSetOfferWorkspaceSearch('no matching offer');
assert.equal(exportButton.textContent,'Download CSV (0)');
assert.equal(exportButton.disabled,true);
input.focus=()=>{document.activeElement=input;};
document.activeElement={};
root.hofClearOfferWorkspaceFilters();
assert.equal(document.activeElement,input);
assert.equal(root.hofOfferWorkspaceV10.query,'');
root.hofSetOfferWorkspaceSearch('Maple');
assert.equal(exportButton.textContent,'Download CSV (1)');
assert.equal(exportButton.disabled,false);

const attentionOffers = [
 {id:'attention-a',property_address:'Maple Lane',status:'Draft',last_updated:'2021-01-01',offer_price:100},
 {id:'attention-b',property_address:'Oak Road',status:'Draft',last_updated:'2021-01-02',offer_price:200},
 {id:'recent',property_address:'Pine Street',status:'Draft',last_updated:new Date().toISOString(),offer_price:300}
];
assert.match(root.hofRenderOfferWorkspaceV10(attentionOffers), /hofReviewAllOffersNeedingAttention\(\)">Review all 2 needing attention/);
root.hofSetOfferWorkspaceSort('price_desc');
root.hofSetOfferWorkspaceSearch('Maple');
assert.doesNotMatch(cards.innerHTML,/Oak Road/);
summary.focus=()=>{document.activeElement=summary;};
document.querySelector=selector=>selector==='#myOffersList .offer-workspace-result-summary'?summary:null;
root.hofReviewAllOffersNeedingAttention();
assert.equal(root.hofOfferWorkspaceV10.query,'');
assert.equal(root.hofOfferWorkspaceV10.filter,'attention');
assert.equal(root.hofOfferWorkspaceV10.sort,'price_desc');
assert.equal(document.activeElement,summary);
root.hofSetOfferWorkspaceSearch('');
assert.match(cards.innerHTML,/Oak Road[\s\S]*Maple Lane/);
assert.doesNotMatch(cards.innerHTML,/Pine Street/);

const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const assert=require('node:assert/strict'), {test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
function code(start,end){const a=html.indexOf(start), b=html.indexOf(end,a);assert.ok(a>=0&&b>a);return html.slice(a,b);}
function setup(){
 const fields=new Map(), root={};
 const get=id=>{if(!fields.has(id))fields.set(id,{value:'',dataset:{},scrollIntoView(){},disabled:false});return fields.get(id);};
 const nodes={seller:[],water:[]};
 const card=get('hofSellerDisclosureCard');
 card.querySelectorAll=selector=>nodes[selector.includes('water')?'water':'seller'];
 const c={root,document:{getElementById:get,querySelectorAll:card.querySelectorAll},syncWaterRightsVisibility(){},
  escape:v=>String(v??'').replace(/[&<>"]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[x]))};
 vm.createContext(c);
 vm.runInContext(code('  const responseGroups = [','  async function approvedSources()')+
   '\nthis.qa={renderResponses,renderWaterResponses,collectDisclosureResponses,cache:draftCache};',c);
 for(const kind of ['seller','water']){
  const markup=kind==='seller'?c.qa.renderResponses():c.qa.renderWaterResponses();
  for(const match of markup.matchAll(new RegExp('data-'+kind+'-response="([^"]+)"','g'))){
   const n={value:'',dataset:{[kind==='seller'?'sellerResponse':'waterResponse']:match[1]}};nodes[kind].push(n);
  }
 }
 vm.runInContext(code('  root.loadSellerDisclosureDraft = function','  let listingDisclosureHandoffRevision'),c);
 return {c,root,get,nodes,card};
}
test('the actual rendered interview exposes distinct main and water explanation controls',()=>{
 const x=setup(), main=x.c.qa.renderResponses(), water=x.c.qa.renderWaterResponses();
 for(const key of ['property_item_condition_description','smoke_detector_explanation','known_defects_explanation',
  'conditions_explanation','repair_explanation','flood_history_explanation','flood_claim_explanation',
  'fema_assistance_explanation','additional_disclosures_explanation'])assert.ok(main.includes('data-seller-response="'+key+'"'));
 for(const key of ['groundwater_district_name','well_agreement','other_property_well_explanation',
  'outside_groundwater_explanation','severed_groundwater_explanation','surface_water_ownership'])assert.ok(water.includes('data-water-response="'+key+'"'));
 assert.ok(main.includes('maxlength="3000"'));assert.ok(water.includes('maxlength="3000"'));
 assert.equal(new Set(x.nodes.seller.map(n=>n.dataset.sellerResponse)).size,x.nodes.seller.length);
 assert.equal(new Set(x.nodes.water.map(n=>n.dataset.waterResponse)).size,x.nodes.water.length);
});
test('saved explanations reopen with literal Unicode, markup and paragraph breaks unchanged',()=>{
 const x=setup(), text='Élodie reviewed <paint> & trim.\n张伟 noted the repair.';
 const draft={id:'fictional-draft',seller_names:['QA Seller'],buyer_names:[],
  response_data:{conditions_explanation:text,water_heater_gas:false},
  water_rights_data:{well_agreement:text}};
 x.c.qa.cache.set(draft.id,draft);x.root.loadSellerDisclosureDraft(draft.id);
 assert.equal(x.nodes.seller.find(n=>n.dataset.sellerResponse==='conditions_explanation').value,text);
 assert.equal(x.nodes.water.find(n=>n.dataset.waterResponse==='well_agreement').value,text);
 assert.equal(x.nodes.seller.find(n=>n.dataset.sellerResponse==='water_heater_gas').value,'N');
 assert.equal(x.card.dataset.loadedDraftId,draft.id);
 assert.equal(x.c.qa.collectDisclosureResponses(x.card,'seller',draft.response_data).conditions_explanation,text);
 assert.equal(x.c.qa.collectDisclosureResponses(x.card,'water',draft.water_rights_data).well_agreement,text);
});
test('explicitly clearing a field removes it but preserves older unrepresented answers',()=>{
 const x=setup();const previous={notes_legacy:'Keep this older saved note',roof_type:'Metal',
  conditions_explanation:'Replace this',_hof_signature_delivery:{private:'not client input'}};
 const result=x.c.qa.collectDisclosureResponses(x.card,'seller',previous);
 assert.equal(result.notes_legacy,previous.notes_legacy);assert.equal(result.roof_type,'Metal');
 assert.equal(result.conditions_explanation,undefined);assert.equal(result._hof_signature_delivery,undefined);
});

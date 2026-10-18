const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const assert=require('node:assert/strict'), {test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const shared=fs.readFileSync(path.join(__dirname,'..','assets/seller-disclosure-interview.js'),'utf8');
test('Unknown answers are explained without source-incompatible automatic choices',()=>{
 assert.ok(shared.includes('Where the form only offers Yes or No, an Unknown answer appears in the attached details without selecting either answer.'));
});
function code(start,end){const a=html.indexOf(start), b=html.indexOf(end,a);assert.ok(a>=0&&b>a);return html.slice(a,b);}
function setup(){
 const fields=new Map(), root={};
 const get=id=>{if(!fields.has(id))fields.set(id,{value:'',dataset:{},scrollIntoView(){},disabled:false});return fields.get(id);};
 const nodes={seller:[],water:[]};
 const card=get('hofSellerDisclosureCard');
 card.querySelectorAll=selector=>nodes[selector.includes('water')?'water':'seller'];
 const c={root,document:{getElementById:get,querySelectorAll:card.querySelectorAll,
  createElement:()=>({hidden:false,className:'',textContent:''})},syncWaterRightsVisibility(){},
  escape:v=>String(v??'').replace(/[&<>"]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[x]))};
 vm.createContext(c);
 c.window=root;vm.runInContext(shared,c);
 vm.runInContext('const draftCache=new Map();const {renderResponses,renderWaterResponses,collectDisclosureResponses,disclosureDetailRelevant,syncDisclosureDetails}=window.hofDisclosureInterview;'+
   '\nthis.qa={renderResponses,renderWaterResponses,collectDisclosureResponses,disclosureDetailRelevant,syncDisclosureDetails,cache:draftCache};',c);
 for(const kind of ['seller','water']){
  const markup=kind==='seller'?c.qa.renderResponses():c.qa.renderWaterResponses();
  for(const match of markup.matchAll(new RegExp('data-'+kind+'-response="([^"]+)"','g'))){
   const hints=[],label={hidden:false,classList:{add(){}},
    querySelector:()=>hints.find(h=>h.className==='hof-seller-saved-detail')||null,appendChild:h=>hints.push(h)};
   const n={value:'',dataset:{[kind==='seller'?'sellerResponse':'waterResponse']:match[1]},label,
    closest:tag=>tag==='label'?label:null};nodes[kind].push(n);
  }
 }
 vm.runInContext(code('  root.loadSellerDisclosureDraft = function','  let listingDisclosureHandoffRevision'),c);
 return {c,root,get,nodes,card};
}
function field(x,kind,key){return x.nodes[kind].find(n=>n.dataset[kind==='seller'?'sellerResponse':'waterResponse']===key);}
test('blank follow-up questions hide while roof details and optional notes stay available',()=>{
 const x=setup();x.c.qa.syncDisclosureDetails(x.card);
 for(const [kind,keys] of [['seller',['seller_occupancy_duration','known_defects_explanation','smoke_detector_explanation',
   'flood_claim_explanation','in_100_year_floodplain_extent']],['water',['groundwater_district_name','well_ownership',
   'water_well_count_total','well_agreement','surface_water_right_number']]])
  for(const key of keys)assert.equal(field(x,kind,key).label.hidden,true,key);
 for(const key of ['roof_type','roof_age','notes'])assert.equal(field(x,'seller',key).label.hidden,false,key);
});
test('the actual interview reveals only the selected main disclosure branches',()=>{
 const x=setup();
 for(const [parent,value,child] of [['seller_occupancy','N','seller_occupancy_duration'],
  ['property_items_condition_issue','Y','property_item_condition_description'],['defect_roof','Y','known_defects_explanation'],
  ['active_termites','Y','conditions_explanation'],['working_smoke_detectors','N','smoke_detector_explanation'],
  ['property_needs_repair','Y','repair_explanation'],['in_100_year_floodplain','Y','in_100_year_floodplain_extent'],
  ['filed_flood_claim','Y','flood_claim_explanation'],['received_fema_or_sba_assistance','Y','fema_assistance_explanation'],
  ['hoa_assessments','Y','additional_disclosures_explanation']]){
   field(x,'seller',parent).value=value;x.c.qa.syncDisclosureDetails(x.card);
   assert.equal(field(x,'seller',child).label.hidden,false,child);
   field(x,'seller',parent).value='';x.c.qa.syncDisclosureDetails(x.card);
   assert.equal(field(x,'seller',child).label.hidden,true,child);
 }
 field(x,'seller','working_smoke_detectors').value='U';x.c.qa.syncDisclosureDetails(x.card);
 assert.equal(field(x,'seller','smoke_detector_explanation').label.hidden,false);
});
test('water details follow their own answers and shared-well branch',()=>{
 const x=setup();
 field(x,'water','in_groundwater_district').value='Y';field(x,'water','water_wells_known').value='Y';
 field(x,'water','well_ownership').value='seller_only';x.c.qa.syncDisclosureDetails(x.card);
 for(const key of ['groundwater_district_name','water_well_count_total','well_ownership'])assert.equal(field(x,'water',key).label.hidden,false,key);
 assert.equal(field(x,'water','well_agreement').label.hidden,true);
 field(x,'water','well_ownership').value='other';x.c.qa.syncDisclosureDetails(x.card);
 for(const key of ['well_description','well_owners_operators','well_beneficiary','well_agreement'])assert.equal(field(x,'water',key).label.hidden,false,key);
 for(const [parent,child] of [['water_well_on_another_property','other_property_well_explanation'],
  ['water_well_relies_on_outside_rights','outside_groundwater_explanation'],
  ['groundwater_rights_severed_sold_leased','severed_groundwater_explanation'],['surface_water_right','surface_water_right_number']]){
   field(x,'water',parent).value='Y';x.c.qa.syncDisclosureDetails(x.card);
   assert.equal(field(x,'water',child).label.hidden,false,child);
   field(x,'water',parent).value='N';x.c.qa.syncDisclosureDetails(x.card);
   assert.equal(field(x,'water',child).label.hidden,true,child);
 }
});
test('a changed parent preserves visible saved facts and a single review hint until explicitly cleared',()=>{
 const x=setup(),draft={id:'qa-retained',seller_names:['QA'],response_data:{seller_occupancy:'Y',
  seller_occupancy_duration:'Saved occupancy facts',filed_flood_claim:'N',flood_claim_explanation:'Saved claim facts'},
  water_rights_data:{water_wells_known:'N',well_ownership:'seller_only',water_well_count_capped:0,well_agreement:'Saved agreement'}};
 x.c.qa.cache.set(draft.id,draft);x.root.loadSellerDisclosureDraft(draft.id);
 for(const [kind,key] of [['seller','seller_occupancy_duration'],['seller','flood_claim_explanation'],
  ['water','well_ownership'],['water','water_well_count_capped'],['water','well_agreement']]){
   const n=field(x,kind,key);assert.equal(n.label.hidden,false,key);
   assert.equal(n.label.querySelector().hidden,false,key);
   const hint=n.label.querySelector();x.c.qa.syncDisclosureDetails(x.card);assert.equal(n.label.querySelector(),hint);
   const values=x.c.qa.collectDisclosureResponses(x.card,kind,kind==='seller'?draft.response_data:draft.water_rights_data);
   assert.equal(String(values[key]),String(kind==='seller'?draft.response_data[key]:draft.water_rights_data[key]));
   n.value='';x.c.qa.syncDisclosureDetails(x.card);assert.equal(n.label.hidden,true,key);
 }
});
test('returning to a relevant branch retires the retained-details warning without changing the answer',()=>{
 const x=setup(),n=field(x,'seller','flood_claim_explanation');n.value='Keep these facts.';
 x.c.qa.syncDisclosureDetails(x.card);assert.equal(n.label.querySelector().hidden,false);
 field(x,'seller','filed_flood_claim').value='Y';x.c.qa.syncDisclosureDetails(x.card);
 assert.equal(n.label.hidden,false);assert.equal(n.label.querySelector().hidden,true);assert.equal(n.value,'Keep these facts.');
});
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
 const x=setup();const previous={notes_legacy:'Keep this older saved note',question_legacy:'Keep an older answer',
  conditions_explanation:'Replace this',_hof_signature_delivery:{private:'not client input'}};
 const result=x.c.qa.collectDisclosureResponses(x.card,'seller',previous);
 assert.equal(result.notes_legacy,previous.notes_legacy);assert.equal(result.question_legacy,previous.question_legacy);
 assert.equal(result.conditions_explanation,undefined);assert.equal(result._hof_signature_delivery,undefined);
});
test('new scalar and finite-choice controls roundtrip without losing zero',()=>{
 const x=setup(),draft={id:'qa-layout',seller_names:['QA Seller'],buyer_names:[],
  response_data:{seller_occupancy:'N',seller_occupancy_duration:'2 years',roof_type:'Metal',roof_age:'8 years',
   in_100_year_floodplain_extent:'partly',property_items_condition_issue:'U'},
  water_rights_data:{water_well_count_total:3,water_well_count_in_use:'2',water_well_count_capped:0,well_ownership:'other'}};
 x.c.qa.cache.set(draft.id,draft);x.root.loadSellerDisclosureDraft(draft.id);
 for(const [kind,values] of [['seller',draft.response_data],['water',draft.water_rights_data]]){
  const result=x.c.qa.collectDisclosureResponses(x.card,kind,values);
  for(const [key,value] of Object.entries(values))assert.equal(String(result[key]),String(value));
 }
});

// Generate an isolated local fixture from actual production CSS/JS. No source PDF,
// real identity, provider key, backend or third-party request is used.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),out=path.resolve(process.argv[2] || '/private/tmp/hof-listing-interview-qa-20261017');
const lease=process.argv.includes('--lease'),formCode=lease?'TXR-1102':'TXR-1101';
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const queue=html.match(/<script id="hof-standalone-agreement-signing-v1">([\s\S]*?)<\/script>/)?.[1];
if(!queue)throw new Error('Prepared-document queue was not found');
const styles=[...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/g)].map(match=>match[1]).join('\n');
const model=require(path.join(root,lease?'assets/txr1102-interview.js':'assets/txr1101-interview.js'));
const seedValues={seller_one:'José 李 QA Seller',seller_two:'Zoë QA Seller',property_address:'100 Fictional Lane, Plano, TX',term_start:'2026-10-17',term_end:'2027-04-17',listing_price:'350000',
 fee_basis:'flat',fee_amount:'0',additional_fee_basis:'none',mls_filing:'none',hoa:'yes',disclose_buyer_expenses:'no',keybox:'no',intermediary:'not_authorized',foreign_person:'unanswered',signer_plan:'clients_and_associate',built_before_1978:'yes',request_hoa_information:'yes',
 broker_notice_address:'42 Saved Notice Lane',broker_notice_city_state_zip:'Plano, TX 75024',broker_notice_phone:'214-555-0123',broker_notice_email:'saved-notices@example.test'};
if(lease)Object.assign(seedValues,{listing_price:'2500',lease_min_months:'12',lease_max_months:'24',fee_scope:'with_other_broker',fee_basis:'month_percentage',fee_amount:'100',cobroker_basis:'month_percentage',cobroker_amount:'50',renewal_basis:'total_percentage',renewal_amount:'2.5',sale_fee_basis:'percentage',sale_fee_amount:'3',make_ready:'not_authorized'});
const seeded=model.collect({get:key=>seedValues[key]||'',getAll:key=>key==='addenda'?['A']:[]});
const seedRecord={id:'cccccccc-cccc-4ccc-8ccc-cccccccccccc',form_code:formCode,form_source_id:'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',client_names:seeded.clientNames,agreement_data:seeded.agreementData,status:'draft',updated_at:'2026-10-17T15:00:00Z'};
fs.mkdirSync(path.join(out,'assets'),{recursive:true});
for(const file of ['txr1101-interview.js','txr1102-interview.js','txr1101-interview.css'])fs.copyFileSync(path.join(root,'assets',file),path.join(out,'assets',file));
fs.writeFileSync(path.join(out,'index.html'),`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; font-src 'self'"><title>Local QA — sale listing interview</title><style>${styles}</style><link rel="stylesheet" href="/assets/txr1101-interview.css"></head><body>
<main style="max-width:760px;margin:3rem auto;padding:1rem"><h1>Local listing interview QA</h1><p>Fictional data only. No documents or messages are sent.</p><button class="btn-primary" id="start">Prepare listing agreement</button><button class="btn-secondary" id="edit" hidden>Edit saved listing</button><p id="qaStatus" role="status"></p><section id="accountPanelDashboard"></section><pre id="qaRequests" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></main>
<script>
window.hofAuth={role:'agent',session:{user:{id:'qa-agent'},access_token:'fictional-qa-token'}};
window.hofLoadApprovedBrokerageSource=async()=>({id:'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'});
let record=new URLSearchParams(location.search).get('seed')==='1'?${JSON.stringify(seedRecord)}:null,count=0;const mode=new URLSearchParams(location.search).get('mode');
if(record)document.getElementById('edit').hidden=false;
window.fetch=async(url,options={})=>{
 if(!url.startsWith('/api/admin-dashboard'))throw new Error('External calls are blocked');
 if(url.includes('scope=txr1101_context')||url.includes('scope=txr1102_context'))return mode==='office-down'?{ok:false,status:503,json:async()=>({error:'Synthetic optional defaults failure'})}
   :{ok:true,status:200,json:async()=>({brokerage:{name:'Independent QA Realty',license_number:'9000001'},noticeContacts:{address:'10 Current Office Lane',city_state_zip:'Dallas, TX 75201',phone:'214-555-0100',email:'current-office@example.test',email_2:''},sellerDisclosures:[{id:'22222222-2222-4222-8222-222222222222',propertyAddress:'100 Fictional Lane, Plano, TX',sellerNames:['José 李 QA Seller','Zoë QA Seller'],includesWaterRights:true}]})};
 if(url.includes('scope=standalone_agreements'))return {ok:true,status:200,json:async()=>({agreements:record?[record]:[],signingEnabled:mode==='packet',signingFormCodes:[${JSON.stringify(formCode)}]})};
 if(url.includes('scope=standalone_signing_recipients'))return {ok:true,status:200,json:async()=>({recipients:[{id:'1',name:'QA ${lease?'Landlord':'Seller'} One',label:'${lease?'Landlord':'Seller'} 1',email:'party1@example.test',emailEditable:true},{id:'2',name:'QA ${lease?'Landlord':'Seller'} Two',label:'${lease?'Landlord':'Seller'} 2',email:'party2@example.test',emailEditable:true},{id:'associate',name:'QA Associate',label:'Associate signer (your account)',email:'agent@example.test',emailEditable:false}],packetFingerprint:'a'.repeat(64),packet:${JSON.stringify(lease?{pageCount:15,included:['Lease listing agreement','Information About Brokerage Services','Rental flood disclosure','Lead-based paint disclosure for a lease'],pending:[],followUp:['Tenant receipt and signature remain to be completed.','Give the tenant the lead pamphlet and any listed reports.'],otherDocuments:''}:{pageCount:13,included:['Sale listing agreement','Information About Brokerage Services','Lead-based paint disclosure'],pending:['Seller’s Disclosure Notice'],otherDocuments:''})}})};
 if(!options.method)return {ok:!!record,status:record?200:404,json:async()=>({agreement:record})};
 const body=JSON.parse(options.body);count++;
 document.getElementById('qaRequests').textContent=JSON.stringify({requestCount:count,lastRequest:body},null,2);
 if(body.action==='send_txr_agreement_for_signature')throw new Error('No signing invitation is permitted in local QA.');
 if(mode==='lost-save')throw new Error('Synthetic connection loss');
 if(mode==='conflict')return {ok:false,status:409,json:async()=>({refreshRequired:true,error:'Synthetic ambiguous save'})};
 if(mode==='rejected')return {ok:false,status:400,json:async()=>({error:'Check the listing dates.'})};
 if(mode==='switch-account')window.hofAuth.session.user.id='different-qa-agent';
 record={id:'cccccccc-cccc-4ccc-8ccc-cccccccccccc',form_code:${JSON.stringify(formCode)},form_source_id:body.formSourceId,status:'draft',client_names:body.clientNames,agreement_data:body.agreementData,updated_at:'2026-10-17T15:00:'+String(count).padStart(2,'0')+'Z'};
 document.getElementById('edit').hidden=false;
 return {ok:true,status:body.action.startsWith('update')?200:201,json:async()=>({agreement:record})};
};
window.showAccountTab=()=>{};
window.announceWorkspaceStatus=message=>{document.getElementById('qaStatus').textContent=message;};
</script><script>${queue}</script><script src="/assets/txr1102-interview.js"></script><script src="/assets/txr1101-interview.js"></script><script>
const openListing=${lease?'hofOpenTxr1102Draft':'hofOpenTxr1101Draft'};
document.getElementById('start').onclick=()=>openListing({workspace:{property_address:'100 Fictional Lane, Plano, TX',seller_names:['José 李 QA Seller','Zoë QA Seller']}});
document.getElementById('edit').onclick=()=>openListing({agreementId:record.id});
</script></body></html>`);
console.log(out);

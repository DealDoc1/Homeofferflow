const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const source=html.slice(html.indexOf('  async function uploadPartnerOnboardingImage('),html.indexOf('  async function recoverPartnerCheckoutSetup('));
function setup(){
 const fields={},calls=[],uploads=[];let cleared=0;
 for(const id of ['partnerSetupLogo','partnerSetupHeadshot','partnerSetupMarket','partnerSetupWebsite','partnerSetupCta','partnerSetupPublicName','partnerSetupPublicPhone','partnerSetupPublicDescription'])fields[id]={value:''};
 fields.partnerSetupMarket.value='Fictional QA market';fields.partnerSetupLogo.value='https://example.com/logo.jpg';fields.partnerSetupHeadshot.value='https://example.com/old.jpg';
 fields.partnerSetupLogoFile={files:[]};fields.partnerSetupHeadshotFile={files:[]};fields.partnerSetupHeadshotRemove={checked:false};
 fields.partnerOnboardingFields={style:{display:'block'}};fields.partnerOnboardingStatus={setAttribute(){}};
 const button={setAttribute(){},textContent:'Save setup details',disabled:false};
 const sandbox={window:{hofCustomerActionError:e=>e.message,hofAuth:{client:{storage:{from:bucket=>({uploadToSignedUrl:async(...args)=>{uploads.push({bucket,args});return {error:null};}})}}}},
  document:{getElementById:id=>fields[id],querySelector:()=>button},value:id=>fields[id]?.value||'',onboardingToken:()=>'fictional-token',clearPartnerOnboardingToken:()=>cleared++,
  fetch:async(url,options)=>{const body=JSON.parse(options.body);calls.push({url,body});return {ok:true,json:async()=>body.request_type==='partner_onboarding_logo_upload'?{upload:{bucket:'brokerage-branding',path:'partners/fictional/photo.jpg',token:'short-lived'}}:{ok:true}};}};
 vm.createContext(sandbox);vm.runInContext(source,sandbox);
 return {sandbox,fields,calls,uploads,button,cleared:()=>cleared};
}
test('omission preserves an existing headshot and explicit removal wins without uploading',async()=>{
 const f=setup();assert.equal((await f.sandbox.uploadPartnerOnboardingImage('fictional-token','headshot')).url,'https://example.com/old.jpg');
 f.fields.partnerSetupHeadshotRemove.checked=true;f.fields.partnerSetupHeadshotFile.files=[{type:'image/jpeg',size:1234}];
 const removed=await f.sandbox.uploadPartnerOnboardingImage('fictional-token','headshot');assert.equal(removed.url,'');assert.equal(removed.path,'');assert.equal(f.calls.length,0);
});
test('selected headshot reuses bounded signed-upload endpoint and partner bucket',async()=>{
 const f=setup(),file={type:'image/jpeg',size:1234};f.fields.partnerSetupHeadshotFile.files=[file];
 const result=await f.sandbox.uploadPartnerOnboardingImage('fictional-token','headshot');
 assert.equal(result.path,'partners/fictional/photo.jpg');assert.equal(f.calls[0].body.image_kind,'headshot');
 assert.equal(f.calls[0].body.request_type,'partner_onboarding_logo_upload');assert.equal(f.uploads[0].bucket,'brokerage-branding');
 assert.equal(f.uploads[0].args[2],file);assert.equal(f.uploads[0].args[3].contentType,'image/jpeg');
});
test('invalid photo type and size fail before signed token or storage call',async()=>{
 for(const file of [{type:'image/svg+xml',size:100},{type:'image/png',size:2097153},{type:'image/jpeg',size:0}]){
  const f=setup();f.fields.partnerSetupHeadshotFile.files=[file];await assert.rejects(()=>f.sandbox.uploadPartnerOnboardingImage('fictional-token','headshot'));assert.equal(f.calls.length,0);assert.equal(f.uploads.length,0);
 }
});
test('actual setup submission carries photo path and preserves logo with no activation request',async()=>{
 const f=setup();f.fields.partnerSetupHeadshotFile.files=[{type:'image/webp',size:500}];await f.sandbox.window.submitPartnerOnboarding();
 const body=f.calls.at(-1).body;assert.equal(body.request_type,'partner_onboarding_submit');assert.equal(body.headshot_path,'partners/fictional/photo.jpg');
 assert.equal(body.logo_url,'https://example.com/logo.jpg');assert.equal(body.public_headshot_url,'');assert.equal(f.cleared(),1);
 assert.equal(f.fields.partnerOnboardingFields.style.display,'none');for(const key of ['is_active','payment_status','partner_program','monthly_fee'])assert.equal(key in body,false);
});
test('upload failure retains answers and setup token and restores retry',async()=>{
 const f=setup();f.fields.partnerSetupHeadshotFile.files=[{type:'image/svg+xml',size:100}];await f.sandbox.window.submitPartnerOnboarding();
 assert.equal(f.cleared(),0);assert.equal(f.button.disabled,false);assert.equal(f.fields.partnerOnboardingFields.style.display,'block');
 assert.equal(f.fields.partnerSetupMarket.value,'Fictional QA market');assert.match(f.fields.partnerOnboardingStatus.textContent,/PNG, JPEG, or WebP/);assert.equal(f.calls.length,0);
});

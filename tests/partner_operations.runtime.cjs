const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {test}=require('node:test'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
function extract(name){const start=source.indexOf(`  function ${name}(`);assert.ok(start>=0,name);const tail=source.slice(start+3),next=tail.search(/\n  (?:async )?function /);assert.ok(next>=0,name);return source.slice(start,start+3+next);}
const context=vm.createContext({Date,encodeURIComponent});
for(const name of ['escapeAttr','adminSafe','adminEventMetadata','partnerPlacementLifecycle','partnerLeadFollowUpAction'])vm.runInContext(extract(name),context);
const call=(name,row)=>{context.row=row;return vm.runInContext(name+'(row)',context);};
const live={is_active:true,monthly_fee:0,partner_program:'beta'};
test('complimentary beta never receives a paid countdown, even after 90 days or without a date',()=>{
  for(const activated_at of [new Date().toISOString(),'2020-01-01T00:00:00Z',null]){
    const result=call('partnerPlacementLifecycle',{...live,activated_at});
    assert.equal(result.label,'Complimentary beta');assert.match(result.action,/No automatic paid conversion/);
    assert.doesNotMatch(result.action,/recurring billing begins|agreement-confirmed/);
  }
});
test('an inconsistent beta fee is visible without changing billing or saved input',()=>{
  for(const monthly_fee of [149,null,'']){
    const row={...live,monthly_fee},result=call('partnerPlacementLifecycle',row);
    assert.equal(result.label,'Review beta fee');assert.equal(row.monthly_fee,monthly_fee);
  }
});
test('a zero fee alone does not label an unknown placement as beta or invent future billing',()=>{
  const result=call('partnerPlacementLifecycle',{...live,partner_program:'unknown'});
  assert.equal(result.label,'No-charge placement');assert.doesNotMatch(result.action,/recurring billing begins/);
});
test('commercial launch, renewal and inactive behavior stays unchanged',()=>{
  const paid={...live,partner_program:'commercial',monthly_fee:149};
  assert.match(call('partnerPlacementLifecycle',{...paid,activated_at:new Date().toISOString()}).label,/Launch period/);
  assert.equal(call('partnerPlacementLifecycle',{...paid,activated_at:'2020-01-01T00:00:00Z'}).label,'Renewal review window');
  assert.equal(call('partnerPlacementLifecycle',{...live,is_active:false}).label,'Inactive');
});
test('active beta contact draft describes the live profile without onboarding, checkout or agreement actions',()=>{
  const html=call('partnerLeadFollowUpAction',{id:'fixture',partner_program:'beta',contact_email:'operator@example.test',has_active_placement:true,onboarding_status:'complete',payment_status:'checkout_started'});
  const decoded=decodeURIComponent(html);assert.match(decoded,/partner profile/);assert.match(decoded,/profile is live/);assert.match(decoded,/no automatic paid conversion/);
  assert.doesNotMatch(html,/sendPartnerAgreement|copyPartnerCheckout|copyPartnerOnboarding|emailPartnerOnboarding/);
  assert.doesNotMatch(decoded,/onboarding next step/);assert.match(decoded,/https:\/\/www.homeofferflow.com\/directory/);
});
test('active commercial contact draft does not claim free beta and unpublished beta retains setup actions',()=>{
  const paid=decodeURIComponent(call('partnerLeadFollowUpAction',{contact_email:'operator@example.test',payment_status:'paid',has_active_placement:true}));
  assert.match(paid,/profile is live/);assert.doesNotMatch(paid,/complimentary|automatic paid conversion/);
  const beta=call('partnerLeadFollowUpAction',{id:'fixture',contact_email:'operator@example.test',partner_program:'beta',has_active_placement:false,onboarding_status:'ready'});
  assert.match(beta,/copyPartnerOnboardingLink/);assert.doesNotMatch(decodeURIComponent(beta),/profile is live/);
});

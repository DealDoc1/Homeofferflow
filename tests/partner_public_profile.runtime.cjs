const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
const context = {window:{},URL};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../assets/partner-profile.js'),'utf8'),context);
const profile = context.window.hofPartnerProfile;
const esc = text => String(text || '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const provider = {id:'fixture',partner_type:'roofing',placement_tier:'founding',website_url:'https://example.com',public_contact_phone:'+19728376378',public_contact_name:'Tedd Hansen'};
test('optional portrait exposes only the explicit public image and escapes its identity',()=>{
  assert.equal(profile.portrait({...provider,avatar_url:'https://private.example/photo.jpg'},esc),'');
  for(const url of ['javascript:evil','data:image/svg+xml,evil','http://example.com/photo.jpg','https://user:pass@example.com/photo.jpg'])
    assert.equal(profile.portrait({...provider,public_headshot_url:url},esc),'');
  const html=profile.portrait({...provider,public_headshot_url:'https://example.com/headshot.jpg',public_contact_name:'<QA Contact>'},esc);
  assert.match(html,/width="64" height="64"/); assert.match(html,/referrerpolicy="no-referrer"/);
  assert.match(html,/&lt;QA Contact&gt;/); assert.doesNotMatch(html,/<QA Contact>/);
});
test('failed portrait is hidden without breaking links or company branding',()=>{
  let onError, removed=false;
  const sandbox={window:{},URL,document:{addEventListener:(name,fn,capture)=>{assert.equal(name,'error');assert.equal(capture,true);onError=fn;}}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../assets/partner-profile.js'),'utf8'),sandbox);
  const slot={hidden:false};
  onError({target:{matches:()=>true,parentElement:slot,closest:()=>({classList:{remove:name=>{assert.equal(name,'has-portrait');removed=true;}}})}});
  assert.equal(slot.hidden,true); assert.equal(removed,true);
});
test('website and telephone have distinct destinations and labels',()=>{
  const markup=profile.actions(provider,esc,'data-partner-link');
  assert.match(markup,/href="https:\/\/example.com\/"/);
  assert.match(markup,/Visit website/); assert.match(markup,/href="tel:\+19728376378"/); assert.match(markup,/Call Tedd Hansen/);
  assert.equal((markup.match(/data-partner-link/g)||[]).length,2);
});
test('a phone-only profile remains useful and no private phone is a fallback',()=>{
  assert.match(profile.actions({...provider,website_url:''},esc,'data-partner-link'),/Call Tedd/);
  assert.equal(profile.phoneUrl({contact_phone:'+19728376378'}),'');
  assert.doesNotMatch(profile.actions({...provider,public_contact_phone:''},esc,'data-partner-link'),/tel:/);
});
test('malformed links, credentials and attribute injection cannot become actions',()=>{
  for(const value of ['javascript:alert(1)','tel:+19728376378','https://user:pass@example.com']) assert.equal(profile.websiteUrl(value),'');
  assert.equal(profile.phoneUrl({public_contact_phone:'+19728376378" onclick="evil'}),'');
  const markup=profile.actions({...provider,public_contact_name:'<img onerror="evil">'},esc,'data-partner-link');
  assert.doesNotMatch(markup,/<img/); assert.match(markup,/&lt;img/);
  assert.equal(profile.actions(provider,esc,'onclick="evil"'),'');
});
test('website cannot be misleadingly labeled Call while approved custom labels survive',()=>{
  assert.equal(profile.websiteLabel({cta_label:'Call Tedd'}),'Visit website');
  assert.equal(profile.websiteLabel({cta_label:'Request a roof inspection'}),'Request a roof inspection');
});
test('all completion actions use existing privacy-safe tracking markers',()=>{
  const markup=profile.actions(provider,esc,'data-offer-completion-partner-link');
  assert.equal((markup.match(/data-offer-completion-partner-link/g)||[]).length,2);
  assert.doesNotMatch(markup,/email|message|offer_id|customer/);
});
function completionMarkup(row) {
  const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
  const code=html.slice(html.indexOf('  function renderNowWhatDirectory('),html.indexOf('  async function renderNowWhatPartnerJourney('));
  const target={innerHTML:''};
  const sandbox={window:{hofPartnerProfile:profile},document:{getElementById:id=>id==='nowWhatPartnerDirectory'?target:{value:''}},
    NOW_WHAT_GROUPS:[{types:['roofing'],title:'Roofing',detail:'Home needs',neutral:false}],
    NOW_WHAT_REGULATED_TYPES:new Set(),NOW_WHAT_PARTNER_LABELS:{roofing:'Roofing'},nowWhatPartnerSort:()=>0,
    nowWhatEscape:esc,bindOfferCompletionPartnerClicks:()=>{},trackPartnerDirectoryImpressions:()=>{}};
  vm.runInNewContext(code+'\nrenderNowWhatDirectory(input);',{...sandbox,input:[row]});
  return target.innerHTML;
}
test('actual offer-follow-up renderer carries logo, escaped description, beta label and both actions',()=>{
  const markup=completionMarkup({...provider,partner_name:'Integrity First',partner_program:'beta',
    public_description:'Roofing <script>unsafe</script>',logo_url:'https://example.com/logo.jpg'});
  assert.match(markup,/alt="Integrity First logo"/); assert.match(markup,/Beta partner/);
  assert.match(markup,/&lt;script&gt;/); assert.doesNotMatch(markup,/<script>/);
  assert.match(markup,/tel:\+19728376378/); assert.match(markup,/Visit website/);
});
test('actual offer-follow-up renderer never uses private contacts or unsafe website',()=>{
  const markup=completionMarkup({id:'fixture',partner_type:'roofing',contact_phone:'+19728376378',contact_name:'Private',website_url:'javascript:evil'});
  assert.doesNotMatch(markup,/tel:|javascript:|Private/);
});
test('offer follow-up uses the concise approved service summary rather than repeating the whole company biography',()=>{
  const markup=completionMarkup({...provider,partner_name:'QA Roofing',partner_program:'beta',public_description:
    'We serve DFW homeowners. We handle roof inspections, replacements and storm damage. '+ 'Our mission is careful, dependable service. '.repeat(8)});
  assert.match(markup,/We serve DFW homeowners/);
  assert.match(markup,/storm damage/);
  assert.doesNotMatch(markup,/Our mission/);
});
test('actual offer-follow-up places an optional portrait without changing contact destinations',()=>{
  const html=completionMarkup({...provider,public_headshot_url:'https://example.com/headshot.jpg'});
  assert.match(html,/now-what-partner has-portrait/); assert.match(html,/hof-partner-headshot/);
  assert.match(html,/tel:\+19728376378/); assert.match(html,/href="https:\/\/example.com\/"/);
  assert.doesNotMatch(completionMarkup(provider),/has-portrait|hof-partner-headshot/);
});

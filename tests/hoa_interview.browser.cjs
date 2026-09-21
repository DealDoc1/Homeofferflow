// Real HOA markup and production helpers; no authentication or external calls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
function section(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a);return html.slice(a,b);}
const markup=section('      <div id="hoaDetails"','      <div class="radio-group-label">Sale of other property');
const helpers=section('  function getVal(', '  function buildLegalDescription(')
  +section('  function collectData()', '  function selectPlan(')
  +section('  function updateHoaFollowUpVisibility()', '  function restoreConditionalSections(');
const validate=section("      const hoaChoice = getRadio('hoa')", "      if (getRadio('saleContingency')");
const style=html.match(/<style>([\s\S]*?)<\/style>/)[1];
(async()=>{
  const browser=await chromium.launch({headless:true,channel:'chrome'});
  try {
    const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];
    await page.route('**/*',route=>route.abort());
    page.on('pageerror',e=>errors.push(e.message));
    await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${style}
      body{padding:20px;max-width:760px;margin:auto}.helper-box{display:none}</style></head><body>
      <h2>HOA interview — local QA only</h2><label><input name="hoa" type="radio" value="yes" checked> HOA property</label>
      <label><input name="hoa" type="radio" value="no"> No HOA</label>${markup}
      <script>window.state={step:0,data:{}};function getCurrentSteps(){return ['step5']}
      function toggleHelper(){} ${helpers}
      window.hoaMissing=()=>{const missing=[];function requireField(id,label,list){if(!getVal(id))list.push(id)}${validate}return missing;};
      document.getElementById('hoaDetails').style.display='block';</script></body></html>`);
    const field=id=>page.locator('#'+id);
    await field('hoaName').fill('José 李 Community Association');
    await field('hoaReserves').fill('2500');
    await field('hoaTitleCost').selectOption('seller');
    assert.equal(await field('hoaDays').isVisible(),false);
    assert.equal(await field('hoaUpdatedResaleCertificate').isVisible(),false);
    await field('hoaSubdivisionInfo').selectOption('seller');
    assert.equal(await field('hoaDays').isVisible(),true);
    await field('hoaDays').fill('7');
    await field('hoaSubdivisionInfo').selectOption('received');
    assert.equal(await field('hoaDays').isVisible(),false);
    assert.equal(await field('hoaUpdatedResaleCertificate').isVisible(),true);
    assert.deepEqual(await page.evaluate(()=>hoaMissing()),['hoaUpdatedResaleCertificate']);
    await field('hoaUpdatedResaleCertificate').selectOption('yes');
    assert.deepEqual(await page.evaluate(()=>hoaMissing()),[]);
    const received=await page.evaluate(()=>{collectData();return state.data;});
    assert.equal(received.hoaUpdatedResaleCertificate,'yes');assert.equal(received.hoaDays,'');
    const output=process.argv[2];
    if(output){fs.mkdirSync(output,{recursive:true});fs.writeFileSync(path.join(output,'received.json'),JSON.stringify(received,null,2));await page.screenshot({path:path.join(output,'received-mobile.png'),fullPage:true});}
    await field('hoaSubdivisionInfo').selectOption('notRequired');
    assert.equal(await field('hoaUpdatedResaleCertificate').isVisible(),false);
    assert.equal(await field('hoaDays').isVisible(),false);
    assert.deepEqual(await page.evaluate(()=>hoaMissing()),[]);
    const none=await page.evaluate(()=>{collectData();return state.data;});
    assert.equal(none.hoaUpdatedResaleCertificate,'');assert.equal(none.hoaDays,'');
    await field('hoaSubdivisionInfo').selectOption('buyer');
    assert.equal(await field('hoaDays').inputValue(),'7');
    const buyer=await page.evaluate(()=>{collectData();return state.data;});
    assert.equal(buyer.hoaDays,'7');assert.equal(buyer.hoaUpdatedResaleCertificate,'');
    await field('hoaSubdivisionInfo').selectOption('received');
    assert.equal(await field('hoaUpdatedResaleCertificate').inputValue(),'yes');
    await field('hoaUpdatedResaleCertificate').selectOption('no');
    assert.equal((await page.evaluate(()=>{collectData();return state.data;})).hoaUpdatedResaleCertificate,'no');
    await page.locator('[name="hoa"][value="no"]').check();
    const removed=await page.evaluate(()=>{collectData();return state.data;});
    for(const key of ['hoaName','hoaDays','hoaUpdatedResaleCertificate','hoaSubdivisionInfo','hoaTitleCost'])assert.equal(removed[key],'');
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    if(output){await page.setViewportSize({width:1280,height:1000});await page.locator('[name="hoa"][value="yes"]').check();await page.screenshot({path:path.join(output,'received-desktop.png'),fullPage:true});}
    assert.deepEqual(errors,[]);
    console.log('PASS: actual HOA markup, conditional questions, missing-choice validation, retained answers, collected payloads, mobile bounds; no external requests.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

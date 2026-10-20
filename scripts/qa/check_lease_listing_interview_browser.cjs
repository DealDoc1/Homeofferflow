// Actual interview/queue assets, localhost-only fixture. No real API or provider.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const assert=require('node:assert/strict');
const {chromium}=require('/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fixture=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const saleSmoke=process.argv.includes('--sale-smoke');
const errors=[],payloads=[];let server,browser,origin,checks=0;
const check=(value,label)=>{assert.ok(value,label);checks++;};
async function visit(page,query=''){
  await page.goto(origin+'/'+query);await page.locator(query.includes('seed=1')?'#edit':'#start').click();
  await page.locator('#txr1101Interview').waitFor();
}
async function select(page,name,value){await page.locator(`[name="${name}"]`).selectOption(value);}
async function fill(page,name,value){await page.locator(`[name="${name}"]`).fill(value);}
async function next(page){await page.locator('[data-next]').click();}
async function complete(page,viewport){
  await visit(page);
  for(let step=0;step<7;step++){
    if(step===0){await fill(page,'client_email','landlord-one@example.test');await fill(page,'client_email_2','landlord-two@example.test');}
    if(step===1){for(const [name,value] of Object.entries({listing_price:'2500',lease_min_months:'12',lease_max_months:'24',term_start:'2026-11-01',term_end:'2027-03-01'}))await fill(page,name,value);}
    if(step===2){
      for(const [name,value] of Object.entries({fee_scope:'with_other_broker',fee_basis:'month_percentage',cobroker_basis:'month_percentage',renewal_basis:'total_percentage',sale_fee_basis:'percentage'}))await select(page,name,value);
      for(const [name,value] of Object.entries({fee_amount:'100',cobroker_amount:'50',renewal_amount:'2.5',sale_fee_amount:'3'}))await fill(page,name,value);
    }
    if(step===3){
      await select(page,'mls_filing','delayed');await fill(page,'mls_delay_days','5');await fill(page,'mls_delay_purpose','Landlord preparation');
      for(const [name,value] of Object.entries({internet_display:'full',keybox:'yes',intermediary:'authorized',make_ready:'broker_reimbursed'}))await select(page,name,value);
      await fill(page,'make_ready_limit','250');await fill(page,'make_ready_service_fee','0');
    }
    if(step===4){await select(page,'hoa','no');await select(page,'built_before_1978','unanswered');await fill(page,'non_real_estate_items','Fictional refrigerator');}
    if(step===5){
      await page.locator('[name="include_rental_preferences"]').check();
      await page.locator('[data-step="5"] details').evaluateAll(nodes=>nodes.forEach(n=>n.open=true));
      await select(page,'rent_due','other');await fill(page,'rent_due_other','Fifth day of each month');
      await select(page,'initial_late_basis','flat');await fill(page,'initial_late_amount','0');await fill(page,'security_deposit','2500');
      await select(page,'animals','permitted');await fill(page,'animal_restrictions','Fictional negotiated animal terms');await fill(page,'animal_deposit','300');
      await select(page,'yard','named_contractor');await fill(page,'yard_contractor','Fictional Yard Company');
      await select(page,'pool','other');await fill(page,'pool_other','Fictional pool arrangement');
      await page.locator('[data-step="5"] details').evaluateAll(nodes=>nodes.forEach((n,i)=>n.open=i===0));
    }
    if(step===6)await select(page,'signer_plan','clients_and_associate');
    await page.locator('#txr1101InterviewForm').evaluate(el=>el.scrollTop=0);
    check((await page.locator('#txr1101Progress').textContent()).includes(`${step+1} of 7`),'Correct step and lease progress');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'No page-level horizontal overflow');
    check(await page.locator('#txr1101InterviewForm').evaluate(form=>form.scrollWidth<=form.clientWidth+1),'No dialog horizontal overflow');
    await page.screenshot({path:path.join(out,`${viewport}-step-${step+1}.png`)});
    if(step<6)await next(page);
  }
  await page.locator('[data-save]').click();await page.locator('[data-review-saved]').waitFor();
  const proof=JSON.parse(await page.locator('#qaRequests').textContent());payloads.push(proof.lastRequest);
  check(proof.requestCount===1,'One deliberate save');
  check(proof.lastRequest.action==='create_txr_1102_draft','Correct lease create action');
  check(proof.lastRequest.agreementData.include_rental_preferences===true,'Preference checkbox saved as boolean');
  check(proof.lastRequest.agreementData.initial_late_amount==='0','Explicit zero retained');
  check(proof.lastRequest.agreementData.addenda.includes('C'),'Unknown age keeps lease lead document requested');
  await page.locator('[data-review-saved]').click();await page.locator('[data-edit-listing]').waitFor();
  check((await page.locator('#hofStandaloneAgreementList').textContent()).includes('Lease listing agreement'),'Human queue label');
  await page.screenshot({path:path.join(out,`${viewport}-saved-queue.png`)});
  await page.locator('[data-edit-listing]').click();await page.locator('#txr1101Interview').waitFor();
  for(let i=0;i<5;i++)await next(page);
  check(await page.locator('[name="include_rental_preferences"]').isChecked(),'Saved preferences reopen checked');
  await page.locator('[data-step="5"] details').first().locator('summary').click();
  check(await page.locator('[name="rent_due_other"]').inputValue()==='Fifth day of each month','Saved conditional detail reopens');
  await next(page);await page.locator('[data-save]').click();await page.locator('[data-review-saved]').waitFor();
  const edited=JSON.parse(await page.locator('#qaRequests').textContent());
  check(edited.requestCount===2 && edited.lastRequest.action==='update_txr_1102_draft','Edit uses same lease record');
  check(edited.lastRequest.agreementId==='cccccccc-cccc-4ccc-8ccc-cccccccccccc','Same record identity');
}
async function failedSave(page,mode){
  await visit(page,`?seed=1&mode=${mode}`);
  for(let i=0;i<6;i++)await next(page);
  await page.locator('[data-save]').click();
  await page.waitForFunction(()=>document.querySelector('#txr1101Status')?.textContent.includes('Check your saved documents'));
  check(await page.locator('[data-save]').isDisabled(),'Ambiguous save cannot create another copy');
  check(JSON.parse(await page.locator('#qaRequests').textContent()).requestCount===1,'No duplicate create after uncertain save');
}
async function checkSaleDialog(page,viewport){
  await visit(page,'?seed=1');
  check((await page.locator('#txr1101Title').textContent()).includes('sale listing'),'Existing sale title retained');
  await page.screenshot({path:path.join(out,`${viewport}-sale-parties.png`)});
  for(let i=0;i<5;i++)await next(page);
  check((await page.locator('#txr1101Progress').textContent()).includes('6 of 6'),'Existing six-step sale flow retained');
  await page.screenshot({path:path.join(out,`${viewport}-sale-review.png`)});
  await page.locator('[data-save]').click();await page.locator('[data-review-saved]').waitFor();
  const proof=JSON.parse(await page.locator('#qaRequests').textContent());payloads.push(proof.lastRequest);
  check(proof.lastRequest.action==='update_txr_1101_draft','Sale keeps its own update action');
}
async function main(){
  fs.mkdirSync(out,{recursive:true});
  try{
    server=http.createServer((req,res)=>{
      const file=path.resolve(fixture,'.'+new URL(req.url,'http://localhost').pathname.replace(/\/$/,'/index.html'));
      if(!file.startsWith(fixture+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
      res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':'text/html');res.end(fs.readFileSync(file));
    });
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));origin='http://127.0.0.1:'+server.address().port;
    browser=await chromium.launch({channel:'chrome',headless:true});
    for(const [label,size] of Object.entries({desktop:{width:1280,height:1000},mobile:{width:390,height:844}})){
      const page=await browser.newPage({viewport:size});page.on('pageerror',e=>errors.push(e.message));
      await page.route('**/*',route=>route.request().url().startsWith(origin+'/')?route.continue():route.abort());
      if(saleSmoke)await checkSaleDialog(page,label);else await complete(page,label);
      if(!saleSmoke&&label==='mobile')for(const mode of ['lost-save','conflict'])await failedSave(page,mode);
      await page.close();
    }
    check(errors.length===0,'No browser JavaScript errors: '+errors.join('; '));
    fs.writeFileSync(path.join(out,'browser-proof.json'),JSON.stringify({ok:true,checks,errors,payloads,network:'localhost fixture only',provider_sends:0},null,2));
    console.log(JSON.stringify({ok:true,checks,screenshots:saleSmoke?4:16,provider_sends:0}));
  }finally{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
}
main().catch(error=>{console.error(error);process.exitCode=1;});

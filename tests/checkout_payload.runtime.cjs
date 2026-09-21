const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs'), vm = require('node:vm');
const storage = require('../lib/checkout_payload');
const source = process.env.HOF_TEST_SOURCE_REF
  ? require('node:child_process').execFileSync('git',['show',`${process.env.HOF_TEST_SOURCE_REF}:api/create-checkout.js`],{encoding:'utf8'})
  : fs.readFileSync(require.resolve('../api/create-checkout'), 'utf8');
const cash = {price:500000, earnest:0, optionFee:0, optionDays:0, financing:'cash'};
async function checkout({offer = cash, fail, env} = {}) {
  const events = [], rows = [], sessions = [], errors = [];
  const options = {env:env || {SUPABASE_URL:'https://database.example.test', SUPABASE_SERVICE_ROLE_KEY:'fake-key'},
    fetcher:async (url, req) => {
      events.push(req.method);
      assert.equal(req.redirect, 'error');
      assert.equal(req.headers.apikey, 'fake-key');
      if (fail === req.method) return {ok:false};
      if (fail === 'timeout-'+req.method) throw Error('private provider body');
      if (fail === 'empty-'+req.method) return {ok:true,json:async()=>[]};
      const body = JSON.parse(req.body);
      if (req.method === 'POST') rows.push(body);
      else {
        assert.match(url, /stripe_session_id=is.null/);
        Object.assign(rows[0], body);
      }
      return {ok:true,json:async()=>[fail === 'wrong-'+req.method ? {...rows[0],id:'wrong'} : rows[0]]};
    }};
  const moduleObject = {exports:{}};
  vm.runInNewContext(source, {module:moduleObject, URL, process:{env:{STRIPE_SECRET_KEY:'fake'}},
    console:{error:message=>errors.push(message)}, require(name) {
      if (name === '../lib/checkout_payload') return {
        saveCheckoutPayload:body=>storage.saveCheckoutPayload(body, options),
        bindCheckoutPayload:(ref,id)=>storage.bindCheckoutPayload(ref,id,options)
      };
      assert.equal(name,'stripe');
      return ()=>({checkout:{sessions:{create:async payload=>{
        events.push('stripe'); sessions.push(payload);
        if(fail === 'stripe') throw Error('private Stripe error');
        return {id:'cs_fixture',url:'https://checkout.example.test/session'};
      }, expire:async id=>{assert.equal(id,'cs_fixture');events.push('expire');}}}});
    }});
  const result = {};
  await moduleObject.exports({method:'POST',headers:{},body:{email:'payer@example.test',offerData:offer}},
    {status(code){result.status=code;return this;},json(body){result.body=body;return this;}});
  return {...result,events,rows,sessions,errors};
}
test('2.5 MiB attachments are saved intact before a small reference-only checkout', async()=>{
  const one=Buffer.alloc(2*1024*1024, 65).toString('base64'), two=Buffer.alloc(512*1024, 66).toString('base64');
  const offer={...cash,uploadedDisclosureDocs:[{name:'one.pdf',base64:one},{name:'two.pdf',base64:two}]};
  const r=await checkout({offer});
  assert.equal(r.status,200);
  assert.ok(Object.keys(r.sessions[0].metadata).length <= 50, 'Supported attachments must fit the Stripe metadata key limit');
  assert.deepEqual(r.events,['POST','stripe','PATCH']);
  assert.deepEqual(JSON.parse(r.rows[0].payload_text).uploadedDisclosureDocs,offer.uploadedDisclosureDocs);
  assert.equal(r.rows[0].stripe_session_id,'cs_fixture');
  const meta=r.sessions[0].metadata;
  assert.equal(Object.keys(meta).length,4); assert.ok(JSON.stringify(meta).length<500);
  assert.equal(meta.offer_payload_id,r.rows[0].id); assert.equal(meta.offer_payload_sha256,r.rows[0].payload_sha256);
  assert.equal(meta.offer_parts,undefined); assert.equal(meta.offer_data,undefined);
});
for(const fail of ['POST','timeout-POST','empty-POST','wrong-POST']) test(`${fail}: storage failure cannot start payment`,async()=>{
  const r=await checkout({fail}); assert.equal(r.status,503); assert.deepEqual(r.events,['POST']);
  assert.equal(r.body.url,undefined);assert.equal(JSON.stringify(r.body).includes('private'),false);
});
for(const fail of ['PATCH','timeout-PATCH','empty-PATCH','wrong-PATCH']) test(`${fail}: unconfirmed binding expires session and never exposes URL`,async()=>{
  const r=await checkout({fail}); assert.equal(r.status,503);assert.deepEqual(r.events,['POST','stripe','PATCH','expire']);
  assert.equal(r.body.url,undefined);
});
test('unconfigured storage fails before creating a checkout',async()=>{
  const r=await checkout({env:{}});assert.equal(r.status,503);assert.deepEqual(r.events,[]);
});
test('Stripe failure keeps the saved packet but hides provider error details',async()=>{
  const r=await checkout({fail:'stripe'});assert.equal(r.status,503);assert.deepEqual(r.events,['POST','stripe']);
  assert.equal(r.rows.length,1);assert.equal(JSON.stringify(r).includes('private Stripe'),false);
});
test('oversize packet fails before any service call',async()=>{
  const r=await checkout({offer:{...cash,notes:'x'.repeat(storage.MAX_BYTES)}});
  assert.equal(r.status,413);assert.deepEqual(r.events,[]);
});

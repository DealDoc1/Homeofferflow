const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const { createHmac } = require('node:crypto');
const preflight = require('../lib/checkout_packet_preflight');
const source = fs.readFileSync(path.join(__dirname, '../api/create-checkout.js'), 'utf8');
const env = { STRIPE_SECRET_KEY: 'fake', STRIPE_BUYER_OFFER_PRICE_ID: 'price_owned',
  STRIPE_INTERNAL_CHECKOUT_FORWARD_SECRET: 'local-preflight-secret', VERCEL_ENV: 'production' };
const validResponse = { ok: true, pages: 14, totals: {price:'500000.55',loanAmount:'270000.35',downPayment:'230000.20'} };
const numericOffer = { financing: 'assumption', price:'500000.55', earnest:'5000.45', optionFee:'250.99', optionDays:'7',
  loanAmount:'stale', downPayment:'stale', loanYears:'', interestRateCap:'', originationCap:'' };

async function checkout(offer, fetcher = async () => ({ok:true,status:200,json:async()=>validResponse}), config = env) {
  const events = [], saved = [], sessions = [], module = {exports:{}};
  vm.runInNewContext(source, {module, URL, process:{env:config},console:{error(){}},require(name){
    if(name==='stripe')return ()=>{events.push('stripe');return{checkout:{sessions:{create:async request=>{
      events.push('create');sessions.push(request);return{id:'cs_local',url:'https://checkout.example.test/local'};
    }}}};};
    if(name==='../lib/checkout_payload')return{saveCheckoutPayload:async raw=>{
      events.push('save');saved.push(JSON.parse(raw));return{id:'11111111-1111-4111-8111-111111111111',fingerprint:require('node:crypto').createHash('sha256').update(raw).digest('hex'),raw};
    },bindCheckoutPayload:async()=>events.push('bind')};
    assert.equal(name,'../lib/checkout_packet_preflight');
    return{preflightAssumptionPacket:data=>preflight.preflightAssumptionPacket(data,{env:config,fetcher:async(...args)=>{
      events.push('preflight');return fetcher(...args);
    }})};
  }});
  let result;
  const res={status(code){this.code=code;return this;},json(body){result={status:this.code,body};}};
  await module.exports({method:'POST',headers:{origin:'https://attacker.example'},body:{email:'payer@example.test',offerData:offer}},res);
  return{...result,events,saved,sessions};
}

if (require.main === module) {
  test('assumption checkout uses authoritative totals before storing and creating a payable session',async()=>{
    let request;
    const result=await checkout({...numericOffer,_paragraph4_source_pdf_bytes:{'TXR-1919':'forged'},_signing_source_hashes:{bad:true},paragraph4SourceRevisions:{bad:true}},async(url,options)=>{
      request={url,...options};return{ok:true,status:200,json:async()=>validResponse};
    });
    assert.equal(result.status,200);assert.deepEqual(result.events,['preflight','stripe','save','create','bind']);
    assert.equal(request.url,'https://www.homeofferflow.com/api/fill-pdf.py');assert.equal(request.redirect,'error');
    const sent=JSON.parse(request.body);assert.equal(sent.action,'checkout_packet_preflight');
    assert.equal(sent.offerData._paragraph4_source_pdf_bytes,undefined);assert.equal(sent.offerData.paragraph4SourceRevisions,undefined);
    const sig=request.headers['X-HomeOfferFlow-Preflight-Signature'];const t=sig.split(',')[0].slice(2);
    assert.equal(sig,`t=${t},v1=${createHmac('sha256',env.STRIPE_INTERNAL_CHECKOUT_FORWARD_SECRET).update(`${t}.checkout-preflight.${request.body}`).digest('hex')}`);
    for(const key of Object.keys(validResponse.totals))assert.equal(result.saved[0][key],validResponse.totals[key]);
    assert.equal(result.saved[0].earnest,'5000.45');assert.equal(result.saved[0]._plan,'self');
    assert.equal(result.saved[0]._paymentEmail,'payer@example.test');
    assert.equal(result.saved[0]._signing_source_hashes,undefined);
    assert.deepEqual(JSON.parse(JSON.stringify(result.sessions[0].line_items)),[{price:'price_owned',quantity:1}]);
    assert.equal(Object.keys(result.sessions[0].metadata).some(k=>k.startsWith('assumption')),false);
  });
  for(const scenario of ['network','unauthorized','invalid-answer','source-unavailable','malformed-success','wrong-total-type','wrong-page-count'])test(`${scenario} cannot initialize payment or save a payable packet`,async()=>{
    const result=await checkout(numericOffer,async()=>{
      if(scenario==='network')throw Error('private-key-and-customer-data');
      const status=scenario==='unauthorized'?401:scenario==='invalid-answer'?422:scenario==='source-unavailable'?503:200;
      const payload=scenario==='invalid-answer'?{code:'checkout_answers_invalid',error:'Enter the first-lien unpaid balance.'}
        :scenario==='malformed-success'?{ok:true}:scenario==='wrong-total-type'?{...validResponse,totals:{...validResponse.totals,price:500000.55}}
        :scenario==='wrong-page-count'?{...validResponse,pages:12}:status!==200?{error:'private-key-and-customer-data'}:validResponse;
      return{ok:status===200,status,json:async()=>payload};
    });
    assert.equal(result.status,scenario==='invalid-answer'?422:503);assert.deepEqual(result.events,['preflight']);
    assert.equal(result.saved.length,0);assert.equal(result.sessions.length,0);assert.doesNotMatch(result.body.error,/private-key/);
  });
  test('missing shared secret fails without an external call',async()=>{
    const result=await checkout(numericOffer,()=>assert.fail('no network'),{VERCEL_ENV:'production'});
    assert.equal(result.status,503);assert.deepEqual(result.events,[]);
  });
  test('oversized assumption answers fail before external work',async()=>{
    const result=await checkout({...numericOffer,notes:'x'.repeat(4*1024*1024)},()=>assert.fail('no network'));
    assert.equal(result.status,413);assert.deepEqual(result.events,[]);
  });
  test('preview never forwards private terms to production',async()=>{
    assert.equal(preflight.preflightOrigin({VERCEL_ENV:'preview',VERCEL_URL:'homeofferflow-abc-team.vercel.app'}),'https://homeofferflow-abc-team.vercel.app');
    for(const host of ['', 'evil.example','homeofferflow-abc.vercel.app/redirect','user@homeofferflow-abc.vercel.app'])
      assert.throws(()=>preflight.preflightOrigin({VERCEL_ENV:'preview',VERCEL_URL:host}));
  });
  test('ordinary purchase checkout does not add a render or service call',async()=>{
    const result=await checkout({...numericOffer,financing:'cash'},()=>assert.fail('no preflight for cash'));
    assert.equal(result.status,200);assert.deepEqual(result.events,['stripe','save','create','bind']);
  });
}
module.exports={checkout,env};

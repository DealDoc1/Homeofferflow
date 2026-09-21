// Synthetic, in-memory PostgreSQL fixture only. No network or production writes.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {PGlite} = require(process.env.HOF_PGLITE_MODULE || '@electric-sql/pglite');
(async()=>{
  const db = new PGlite();
  let checks=0;
  const check=(value,message)=>{assert.ok(value,message);checks++;};
  const reject=async(sql,code)=>{await assert.rejects(db.query(sql),e=>e.code===code);checks++;};
  try {
    await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
      grant usage on schema public to anon, authenticated, service_role;`);
    const baseline=fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/20260721000000_homeofferflow_remote_schema_baseline.sql'),'utf8');
    const table=baseline.match(/create table if not exists public\."hof_offers" \([\s\S]*?\n\);/)[0];
    await db.exec(table);
    await db.exec(`alter table public.hof_offers enable row level security;
      grant select,insert,update on public.hof_offers to authenticated,service_role;
      create policy owner_fixture on public.hof_offers to authenticated
        using (user_id='11111111-1111-4111-8111-111111111111')
        with check (user_id='11111111-1111-4111-8111-111111111111');`);
    await db.exec(fs.readFileSync(path.resolve(__dirname,
      '../../supabase/migrations/20260915203004_protect_offer_packet_autosave.sql'),'utf8'));
    await db.exec(`set role authenticated;
      insert into public.hof_offers(id,user_id,status,signwell_document_id,generated_at,offer_data)
      values('33333333-3333-4333-8333-333333333333','11111111-1111-4111-8111-111111111111',
        'Signed','forged',now(),'{"_hof_signature_delivery":{"id":"copied"},"repairsText":"Agreed work","generatedAt":"old"}');`);
    const row=async()=>(await db.query('select * from public.hof_offers')).rows[0];
    let saved=await row();
    check(saved.status==='Draft' && saved.signwell_document_id===null && saved.generated_at===null,'New draft cannot forge packet status');
    check(!saved.offer_data._hof_signature_delivery && saved.offer_data.repairsText==='Agreed work','Copy clears receipt, keeps agreed terms');
    await db.exec(`update public.hof_offers set status='Signed',signwell_status='completed',offer_data='{"price":123,"_hof_signature_delivery":{"fake":true}}';`);
    saved=await row();
    check(saved.status==='Draft' && saved.signwell_status===null && saved.offer_data.price===123 && !saved.offer_data._hof_signature_delivery,
      'Draft edits work without client-authored signing state');
    await reject("update public.hof_offers set user_id='22222222-2222-4222-8222-222222222222'",'42501');
    await db.exec(`reset role; set role service_role;
      update public.hof_offers set status='Buyer Signed',generated_at=now(),signwell_document_id='verified-doc',
        signwell_status='completed',offer_data='{"price":123,"_hof_signature_delivery":{"receipt":"accepted"}}';
      reset role; set role authenticated;`);
    await reject("update public.hof_offers set status='Generated',offer_data='{}'",'55000');
    await reject("update public.hof_offers set offer_price=1",'55000');
    await reject("update public.hof_offers set signwell_document_id=null",'55000');
    await reject("update public.hof_offers set status=null",'55000');
    await reject("update public.hof_offers set status='Deleted',deleted_at=now(),offer_data='{}'",'55000');
    saved=await row();
    check(saved.status==='Buyer Signed' && saved.offer_data._hof_signature_delivery.receipt==='accepted','Rejected stale writes leave original intact');
    await db.exec("update public.hof_offers set last_updated=now()");
    check((await row()).status==='Buyer Signed','Harmless timestamp update does not regress state');
    await db.exec("update public.hof_offers set status='Deleted',deleted_at=now()");
    check((await row()).signwell_document_id==='verified-doc','Soft delete preserves signed record and journal');
    await reject("update public.hof_offers set status='Draft',deleted_at=null",'55000');
    await db.exec(`reset role; set role service_role;
      update public.hof_offers set status='Draft',deleted_at=null,generated_at=null,signwell_document_id=null,
        offer_data='{"signwell":{"response":{"id":"legacy-document"}}}';
      insert into public.hof_offers(id,user_id,status) values
        ('44444444-4444-4444-8444-444444444444','22222222-2222-4222-8222-222222222222','Draft');
      reset role; set role authenticated;`);
    await reject("update public.hof_offers set offer_data='{}'",'55000');
    check((await db.query('select count(*)::int as n from public.hof_offers')).rows[0].n===1,'Other owner remains outside fixture RLS access');
    check((await db.query("update public.hof_offers set buyer_name='not allowed' where id='44444444-4444-4444-8444-444444444444' returning id")).rows.length===0,
      'Protection does not bypass ownership policies');
    await db.exec('reset role');
    const fn=(await db.query("select prosecdef,proconfig from pg_proc where oid='public.hof_protect_offer_packet_autosave()'::regprocedure")).rows[0];
    check(!fn.prosecdef && fn.proconfig.includes('search_path=pg_catalog'),'Trigger is invoker with fixed search path');
    for(const role of ['anon','authenticated'])
      check(!(await db.query("select has_function_privilege($1,'public.hof_protect_offer_packet_autosave()','execute') as ok",[role])).rows[0].ok,
        'Trigger has no public RPC execution grant');
    console.log(JSON.stringify({checks,result:'PASS',scope:'isolated PostgreSQL with synthetic ownership policy'}));
  } finally {await db.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

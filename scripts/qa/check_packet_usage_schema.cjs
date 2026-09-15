// Isolated PostgreSQL contract checks. This script has no production connection.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {PGlite} = require(process.env.HOF_PGLITE_MODULE || '@electric-sql/pglite');

(async()=>{
  const db = new PGlite();
  let checks = 0;
  const check = (value, message)=>{assert.ok(value,message);checks++;};
  const reject = async(sql, params=[])=>{await assert.rejects(db.query(sql,params));checks++;};
  const user = '11111111-1111-4111-8111-111111111111';
  const other = '22222222-2222-4222-8222-222222222222';
  const offer = '33333333-3333-4333-8333-333333333333';
  const attempt = '44444444-4444-4444-8444-444444444444';
  const retry = '55555555-5555-4555-8555-555555555555';
  const hash = 'a'.repeat(64), revised = 'b'.repeat(64);
  const claim = async(u=user,o=offer,h=hash,a=attempt)=>(await db.query(
    'select public.hof_claim_packet_generation($1,$2,$3,$4) as result',[u,o,h,a])).rows[0].result;
  const complete = async(key,a=attempt,u=user)=>(await db.query(
    'select public.hof_complete_packet_generation($1,$2,$3) as result',[u,key,a])).rows[0].result;
  const release = async(key,a=attempt,u=user)=>(await db.query(
    'select public.hof_release_unrendered_packet($1,$2,$3) as result',[u,key,a])).rows[0].result;
  try {
    await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
      grant usage on schema public to anon,authenticated,service_role;
      create table public.hof_subscriptions(id uuid primary key default gen_random_uuid(),
        user_id uuid unique not null,status text not null,packet_limit integer);
      create table public.hof_offers(id uuid primary key,user_id uuid not null);
      create table public.hof_usage_events(id uuid primary key default gen_random_uuid(),user_id uuid not null,
        offer_id uuid,event_type text not null,quantity integer not null default 1,
        billing_month text not null,metadata jsonb not null default '{}',created_at timestamptz default now());
      grant select,insert,update on public.hof_subscriptions,public.hof_offers,public.hof_usage_events to service_role;`);
    await db.query('insert into public.hof_subscriptions(user_id,status,packet_limit) values($1,\'active\',1)',[user]);
    await db.query('insert into public.hof_offers(id,user_id) values($1,$2)',[offer,user]);
    await db.exec(fs.readFileSync(path.resolve(__dirname,
      '../../supabase/migrations/20260915193756_server_owned_packet_usage.sql'),'utf8'));
    check((await db.query("select relrowsecurity from pg_class where oid='public.hof_packet_generations'::regclass")).rows[0].relrowsecurity,
      'New ledger enables RLS');
    const signatures = ['hof_claim_packet_generation(uuid,uuid,text,uuid)',
      'hof_complete_packet_generation(uuid,text,uuid)','hof_release_unrendered_packet(uuid,text,uuid)',
      'hof_packet_usage_summary(uuid)'];
    for(const name of signatures) {
      const fn=(await db.query('select prosecdef,proconfig from pg_proc where oid=$1::regprocedure',['public.'+name])).rows[0];
      check(!fn.prosecdef && fn.proconfig.includes('search_path=pg_catalog'),'RPC uses invoker and fixed search path');
      for(const role of ['anon','authenticated']) {
        check(!(await db.query('select has_function_privilege($1,$2,\'EXECUTE\') as allowed',[role,'public.'+name])).rows[0].allowed,
          'Client cannot execute private quota RPC');
      }
    }
    for(const role of ['anon','authenticated']) {
      await db.exec('set role '+role);
      await reject('select * from public.hof_packet_generations');
      await assert.rejects(claim()); checks++;
      await db.exec('reset role');
    }
    await db.exec('set role service_role');
    check((await claim(other)).outcome==='no_subscription','Missing subscription is not beta access');
    check((await claim(user,other)).outcome==='not_owned','Other or missing offer cannot use allowance');
    await assert.rejects(claim(user,offer,'bad hash'));checks++;
    const first=await claim();
    check(first.outcome==='reserved','First packet reserves allowance');
    const snapshot=async()=>(await db.query('select public.hof_packet_usage_summary($1) as result',[user])).rows[0].result;
    check((await snapshot()).used===0 && (await snapshot()).reserved===1,'Summary distinguishes held allowance from completed usage');
    check(first.billing_month===(await db.query("select to_char(now() at time zone 'UTC','YYYY-MM') as month")).rows[0].month,
      'Server chooses UTC billing month');
    check((await claim(user,offer,hash,retry)).outcome==='busy','Concurrent worker cannot take an active lease');
    check((await claim(user,offer,revised,retry)).outcome==='limit_reached','Reservation occupies last quota slot');
    check((await claim()).generation_key===first.generation_key,'Same worker retry retains key');
    check(!(await release(first.generation_key,retry)),'Wrong token cannot release');
    check(!(await release(first.generation_key,attempt,other)),'Wrong owner cannot release');
    check((await complete(first.generation_key,retry)).outcome==='stale_attempt','Wrong token cannot complete');
    await db.query("update public.hof_packet_generations set lease_until=now()-interval '1 minute' where generation_key=$1",[first.generation_key]);
    const recovered=await claim(user,offer,hash,retry);
    check(recovered.outcome==='reserved' && recovered.generation_key===first.generation_key,'Expired worker recovers same reservation');
    check((await complete(first.generation_key,attempt)).outcome==='stale_attempt','Old worker is fenced after recovery');
    check(!(await release(first.generation_key,attempt)),'Old worker cannot release recovered work');
    const done=await complete(first.generation_key,retry);
    check(done.outcome==='completed' && done.usage_event_id,'Rendered packet stores usage once');
    check((await snapshot()).used===1 && (await snapshot()).reserved===0,'Completion moves one reservation to used, not both');
    check((await complete(first.generation_key,retry)).usage_event_id===done.usage_event_id,'Duplicate completion retains same usage event');
    check((await db.query('select count(*)::int as n from public.hof_usage_events')).rows[0].n===1,'Exactly one event after replay');
    check(!(await release(first.generation_key,retry)),'Completed work cannot release allowance');
    check((await claim()).outcome==='completed','Completed retry works even at limit');
    check((await claim(user,offer,revised)).outcome==='limit_reached','Completed usage occupies allowance');
    await reject(`insert into public.hof_usage_events(user_id,event_type,billing_month,generation_key)
      values($1,'signed_packet','2099-01',$2)`,[user,first.generation_key]);
    await reject('delete from public.hof_packet_generations where generation_key=$1',[first.generation_key]);

    await db.query('update public.hof_subscriptions set packet_limit=2 where user_id=$1',[user]);
    const second=await claim(user,offer,revised);
    check(second.outcome==='reserved','New reviewed answers have a distinct reservation');
    check(await release(second.generation_key),'Definite pre-render failure releases its slot');
    const third=await claim(user,offer,'c'.repeat(64));
    check(third.outcome==='reserved','Released slot is available for another packet');
    check((await claim(user,offer,revised)).outcome==='limit_reached','Released retry checks current quota again');
    await release(third.generation_key);
    await db.query("update public.hof_subscriptions set status='past_due' where user_id=$1",[user]);
    check((await claim(user,offer,revised)).outcome==='inactive','Inactive subscription cannot start new work');
    check((await claim()).outcome==='completed','Existing completed identity is not charged again after cancellation');
    await db.query("update public.hof_subscriptions set status='active',packet_limit=0 where user_id=$1",[user]);
    check((await claim(user,offer,revised)).outcome==='limit_reached','Explicit zero is not replaced with a default limit');
    check((await snapshot()).limit===0,'Display preserves an explicit zero allowance');
    await db.query('update public.hof_subscriptions set packet_limit=2 where user_id=$1',[user]);
    const old=await claim(user,offer,revised);
    await db.query("update public.hof_packet_generations set billing_month='2020-01',lease_until=now()-interval '1 minute' where generation_key=$1",[old.generation_key]);
    check((await claim(user,offer,revised,retry)).billing_month==='2020-01','Recovery does not move reservation into a new billing month');
    const oldDone=await complete(old.generation_key,retry);
    check((await db.query('select billing_month from public.hof_usage_events where id=$1',[oldDone.usage_event_id])).rows[0].billing_month==='2020-01',
      'Completion uses original reserved month, never caller month');
    const legacyOffer='66666666-6666-4666-8666-666666666666';
    await db.query('insert into public.hof_offers(id,user_id) values($1,$2)',[legacyOffer,user]);
    await db.query(`insert into public.hof_usage_events(user_id,offer_id,event_type,billing_month)
      values($1,$2,'signed_packet','2020-01')`,[user,legacyOffer]);
    check((await claim(user,legacyOffer)).outcome==='legacy_packet','Old usage cannot be charged again without a verified packet identity');
    check((await db.query('select count(*)::int as n from public.hof_packet_generations where offer_id=$1',[legacyOffer])).rows[0].n===0,
      'Historical usage is not fabricated into a new generation receipt');
    await db.exec('reset role');
    await db.exec('grant select on public.hof_packet_generations to anon,authenticated');
    for(const role of ['anon','authenticated']) {
      await db.exec('set role '+role);
      check((await db.query('select * from public.hof_packet_generations')).rows.length===0,'Accidental grants remain contained by RLS');
      await db.exec('reset role');
    }
    console.log(JSON.stringify({engine:'isolated PGlite/PostgreSQL',checks,passed:true,
      limitation:'Single embedded database session; multi-connection contention not tested.'}));
  } finally {await db.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});

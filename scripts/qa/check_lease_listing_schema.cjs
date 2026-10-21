// Real isolated PostgreSQL, synthetic rows only. No TCP, cloud credentials or sends.
const fs=require('node:fs');
const path=require('node:path');
const {spawn,execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const modules=process.env.HOF_PG_QA_MODULES;
if(!modules || !path.isAbsolute(modules))throw Error('Set the pinned HOF_PG_QA_MODULES runtime.');
const {Client}=require(path.join(modules,'pg'));
const bin=path.join(modules,'@embedded-postgres/darwin-arm64/native/bin');
const temp=fs.mkdtempSync('/private/tmp/hof-lease-listing-');
const data=path.join(temp,'data'),clients=[];
let server,admin,checks=0,logs='';
const check=(ok,message)=>{assert.ok(ok,message);checks++;};
const reject=async(action,code)=>{await assert.rejects(action,e=>e.code===code);checks++;};
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function connect(role){
  const c=new Client({host:temp,port:55474,user:'hof_qa',database:'postgres',connectionTimeoutMillis:1000,query_timeout:10000});
  await c.connect();clients.push(c);await c.query("set statement_timeout='8s'");
  if(role)await c.query('set role '+role);
  return c;
}
const owner='11111111-1111-4111-8111-111111111111',other='22222222-2222-4222-8222-222222222222';
const migration=name=>fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/'+name),'utf8');
const readiness=async c=>(await c.query('select public.hof_lease_listing_schema_readiness() as result')).rows[0].result;
async function main(){
  try{
    execFileSync(path.join(bin,'initdb'),['-D',data,'-U','hof_qa','--auth-local=trust','--auth-host=reject','--no-locale','-E','UTF8','--no-sync'],{stdio:'pipe'});
    server=spawn(path.join(bin,'postgres'),['-D',data,'-k',temp,'-p','55474','-c','listen_addresses=',
      '-c','unix_socket_permissions=0700','-c','shared_buffers=16MB'],{stdio:['ignore','pipe','pipe']});
    server.stdout.on('data',v=>logs+=v);server.stderr.on('data',v=>logs+=v);
    for(let i=0;i<60;i++){
      try{admin=await connect();break;}catch(e){if(server.exitCode!==null)throw Error(logs.slice(-800));await pause(100);}
    }
    if(!admin)throw Error('Isolated PostgreSQL did not start.');
    check((await admin.query('show listen_addresses')).rows[0].listen_addresses==='','No TCP listener');
    await admin.query(`create role anon;create role authenticated;create role service_role bypassrls;
      grant usage on schema public to anon,authenticated,service_role;
      create table public.hof_standalone_agreements(id bigint generated always as identity primary key,
        agent_user_id uuid not null,form_code text not null);
      alter table public.hof_standalone_agreements enable row level security;
      create policy owner_only on public.hof_standalone_agreements for all to authenticated
        using(agent_user_id=current_setting('request.jwt.claim.sub',true)::uuid)
        with check(agent_user_id=current_setting('request.jwt.claim.sub',true)::uuid);
      grant select,insert,update on public.hof_standalone_agreements to authenticated;
      grant usage on sequence public.hof_standalone_agreements_id_seq to authenticated;
      grant all on public.hof_standalone_agreements to service_role;
      grant usage on sequence public.hof_standalone_agreements_id_seq to service_role;
      create table public.hof_brokerage_form_sources(form_code text not null);
      alter table public.hof_brokerage_form_sources enable row level security;
      grant all on public.hof_brokerage_form_sources to service_role;
      -- Fixture isolates the new wrapper's contract propagation, not the core probe's implementation.
      create function public.hof_release_schema_readiness() returns jsonb language sql stable
        security invoker set search_path=pg_catalog as $$
        select coalesce(nullif(current_setting('hof.qa_baseline',true),''),
          '{"contract":"homeofferflow-release-schema-v1","ready":true,"missing":[]}')::jsonb $$;
      revoke all on function public.hof_release_schema_readiness() from public,anon,authenticated;
      grant execute on function public.hof_release_schema_readiness() to service_role;`);
    await admin.query(migration('20261017131634_add_txr1101_listing_drafts.sql'));
    const before=(await admin.query("select relacl,relrowsecurity from pg_class where oid='public.hof_standalone_agreements'::regclass")).rows[0];
    const policies=(await admin.query("select * from pg_policies where tablename='hof_standalone_agreements'")).rows;
    await reject(()=>admin.query("insert into public.hof_standalone_agreements(agent_user_id,form_code) values($1,'TXR-1102')",[owner]),'23514');
    await admin.query(migration('20261020231654_add_txr1102_lease_listing_drafts.sql'));
    await admin.query(migration('20261005110000_expand_trec_39_11_source_code.sql'));
    const sourceBefore=(await admin.query("select relacl,relrowsecurity from pg_class where oid='public.hof_brokerage_form_sources'::regclass")).rows[0];
    await reject(()=>admin.query("insert into public.hof_brokerage_form_sources values('TXR-2008')"),'23514');
    await admin.query(migration('20261021034227_add_lease_disclosure_source_codes.sql'));
    check(JSON.stringify(sourceBefore)===JSON.stringify((await admin.query("select relacl,relrowsecurity from pg_class where oid='public.hof_brokerage_form_sources'::regclass")).rows[0]),'Source privileges and RLS unchanged');
    for(const code of ['TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TXR-1101','TXR-1102','TXR-1406','TXR-1418','TXR-2008','TXR-2015','TREC-55-1','TREC-61-0','TREC-62-0','TREC-38-8','TREC-39-11']){
      await admin.query('insert into public.hof_brokerage_form_sources values($1)',[code]);checks++;
    }
    await reject(()=>admin.query("insert into public.hof_brokerage_form_sources values('TXR-unknown')"),'23514');
    const after=(await admin.query("select relacl,relrowsecurity from pg_class where oid='public.hof_standalone_agreements'::regclass")).rows[0];
    check(JSON.stringify(before)===JSON.stringify(after),'Table privileges and RLS are unchanged');
    check(JSON.stringify(policies)===JSON.stringify((await admin.query("select * from pg_policies where tablename='hof_standalone_agreements'")).rows),'Ownership policies unchanged');
    for(const code of ['TXR-1101','TXR-1102','TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TREC-62-0','TREC-38-8','TREC-39-11']){
      await admin.query('insert into public.hof_standalone_agreements(agent_user_id,form_code) values($1,$2)',[owner,code]);checks++;
    }
    for(const code of ['TXR-1406','unknown','TXR-1102-injected','TXR-2008','TXR-2015'])await reject(()=>admin.query('insert into public.hof_standalone_agreements(agent_user_id,form_code) values($1,$2)',[owner,code]),'23514');
    const service=await connect('service_role'),actor=await connect('authenticated'),anonymous=await connect('anon');
    await actor.query("select set_config('request.jwt.claim.sub',$1,false)",[owner]);
    await actor.query("insert into public.hof_standalone_agreements(agent_user_id,form_code) values($1,'TXR-1102')",[owner]);checks++;
    await reject(()=>actor.query("insert into public.hof_standalone_agreements(agent_user_id,form_code) values($1,'TXR-1102')",[other]),'42501');
    await admin.query("insert into public.hof_standalone_agreements(agent_user_id,form_code) values($1,'TXR-1102')",[other]);
    check((await actor.query('select * from public.hof_standalone_agreements where agent_user_id=$1',[other])).rowCount===0,'Other owner remains hidden');
    await reject(()=>anonymous.query('select * from public.hof_standalone_agreements'),'42501');
    const proof=await readiness(service);
    check(proof.ready && proof.contract==='homeofferflow-lease-listing-schema-v1' && proof.missing.length===0,'Lease schema ready');
    for(const c of [actor,anonymous])await reject(()=>readiness(c),'42501');
    for(const c of [actor,anonymous])await reject(()=>c.query('select * from public.hof_brokerage_form_sources'),'42501');
    const fn=(await admin.query("select prosecdef,proconfig from pg_proc where oid='public.hof_lease_listing_schema_readiness()'::regprocedure")).rows[0];
    check(!fn.prosecdef && fn.proconfig.includes('search_path=pg_catalog'),'Invoker-only and fixed search path');
    for(const baseline of [{contract:'homeofferflow-release-schema-v1',ready:false,missing:['existing:missing']},
      {contract:'wrong',ready:true,missing:[]},{contract:'homeofferflow-release-schema-v1',ready:false,missing:[]}]){
      await service.query("select set_config('hof.qa_baseline',$1,false)",[JSON.stringify(baseline)]);
      check(!(await readiness(service)).ready,'Baseline failures propagate');
    }
    await service.query("select set_config('hof.qa_baseline','',false)");
    await admin.query('alter table public.hof_brokerage_form_sources drop constraint hof_brokerage_form_sources_form_code_check');
    check((await readiness(service)).missing.includes('form_code:hof_brokerage_form_sources.TXR-2008'),'Missing source constraint fails readiness');
    await admin.query("alter table public.hof_brokerage_form_sources add constraint hof_brokerage_form_sources_form_code_check check(form_code in ('TXR-2008','TXR-2015')) not valid");
    check(!(await readiness(service)).ready,'Unvalidated source constraint fails readiness');
    await admin.query(migration('20261021034227_add_lease_disclosure_source_codes.sql'));
    check((await readiness(service)).ready,'Validated complete source catalog restores readiness');
    await admin.query('alter table public.hof_standalone_agreements drop constraint hof_standalone_agreements_form_code_check');
    check((await readiness(service)).missing.includes('form_code:hof_standalone_agreements.TXR-1102'),'Missing constraint is not ready');
    await admin.query("alter table public.hof_standalone_agreements add constraint hof_standalone_agreements_form_code_check check(form_code in ('TXR-1102')) not valid");
    check(!(await readiness(service)).ready,'Unvalidated constraint is not ready');
    console.log(JSON.stringify({ok:true,assertions:checks,network:'none',provider_sends:0}));
  }finally{
    await Promise.allSettled(clients.map(c=>c.end()));
    if(server && server.exitCode===null){server.kill('SIGTERM');await new Promise(resolve=>server.once('exit',resolve));}
    // Exact mkdtemp-owned target, never a repository or broad temp directory.
    fs.rmSync(temp,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});

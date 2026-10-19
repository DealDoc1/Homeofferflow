// Actual migration, real multi-connection PostgreSQL, synthetic records only.
// No connection URL, TCP listener, credential, email or provider is accepted.
const fs = require('node:fs');
const path = require('node:path');
const {spawn, execFileSync} = require('node:child_process');
const {randomUUID} = require('node:crypto');
const assert = require('node:assert/strict');
const modules = process.env.HOF_PG_QA_MODULES;
if (!modules || !path.isAbsolute(modules)) throw Error('Set HOF_PG_QA_MODULES to the pinned local runtime.');
const {Client} = require(path.join(modules, 'pg'));
const binaries = path.join(modules, '@embedded-postgres/darwin-arm64/native/bin');
const temp = fs.mkdtempSync('/private/tmp/hof-review-revision-');
const data = path.join(temp, 'data');
const config = {host:temp,port:55473,user:'hof_qa',database:'postgres',connectionTimeoutMillis:1500,query_timeout:12000};
const clients = [];
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
let server, admin, serverLog = '', checks = 0;
const check = (condition, message) => {assert.ok(condition, message); checks++;};
const reject = async (action, code) => {await assert.rejects(action, e => e.code === code); checks++;};
async function connect(role) {
  const c = new Client(config); await c.connect(); clients.push(c);
  await c.query("set statement_timeout='8s'");
  if (role) await c.query('set role ' + role);
  c.pid = (await c.query('select pg_backend_pid() as id')).rows[0].id;
  return c;
}
const owner = '11111111-1111-4111-8111-111111111111', brokerage = '22222222-2222-4222-8222-222222222222';
const render = 'seller-disclosure-explanations-2026-10-15-v1';
const row = async id => (await admin.query('select * from public.hof_seller_disclosure_drafts where id=$1', [id])).rows[0];
async function createDraft(sellers=['QA Seller One']) {
  const id=randomUUID();
  await admin.query(`insert into public.hof_seller_disclosure_drafts
    (id,agent_user_id,brokerage_id,property_address,seller_names,buyer_names,disclosure_source_id,disclosure_source_revision)
    values ($1,$2,$3,'100 Fictional QA Lane',$4,'[]',$5,'qa-source')`, [id,owner,brokerage,JSON.stringify(sellers),randomUUID()]);
  return row(id);
}
async function createLink(draft, index=1) {
  const id=randomUUID();
  await admin.query(`insert into public.hof_seller_disclosure_review_links
    (id,draft_id,brokerage_id,agent_user_id,seller_email,seller_name,seller_index,token_hash,
      verification_code_hash,review_content_revision,review_render_revision)
    values ($1,$2,$3,$4,'qa@example.test',$5,$6,$7,'fictional-code',$8,$9)`,
  [id,draft.id,brokerage,owner,draft.seller_names[index-1],index,randomUUID(),draft.review_content_revision,render]);
  return id;
}
const attest = (c,id,name='QA Seller One') => c.query(`update public.hof_seller_disclosure_review_links
  set seller_attested_at=now(),seller_attested_name=$2 where id=$1`, [id,name]);
const cache = (c,draft) => c.query(`update public.hof_seller_disclosure_drafts set
  seller_review_attested=true,seller_review_attested_at=now(),seller_review_attested_by=$2,seller_review_render_revision=$3
  where id=$1 and review_content_revision=$4 returning id`, [draft.id,owner,render,draft.review_content_revision]);
async function blocked(c) {
  for(let i=0;i<60;i++) {
    const state=(await admin.query('select wait_event_type from pg_stat_activity where pid=$1',[c.pid])).rows[0];
    if (state?.wait_event_type==='Lock') {checks++; return;}
    await pause(30);
  }
  throw Error('Expected independent database connection to wait on parent row lock.');
}
async function main() {
  try {
    execFileSync(path.join(binaries,'initdb'),['-D',data,'-U','hof_qa','--auth-local=trust','--auth-host=reject','--no-locale','-E','UTF8','--no-sync'],{stdio:'pipe'});
    server=spawn(path.join(binaries,'postgres'),['-D',data,'-k',temp,'-p','55473','-c','listen_addresses=',
      '-c','unix_socket_permissions=0700','-c','shared_buffers=16MB'],{stdio:['ignore','pipe','pipe']});
    server.stdout.on('data', v=>serverLog+=v); server.stderr.on('data', v=>serverLog+=v);
    for(let i=0;i<60;i++) {
      try {admin=await connect();break;} catch(e) {if(server.exitCode!==null)throw Error(serverLog.slice(-800));await pause(100);}
    }
    if(!admin)throw Error('Local PostgreSQL did not become ready.');
    check((await admin.query('show listen_addresses')).rows[0].listen_addresses==='', 'No TCP listener');
    await admin.query(`create role anon; create role authenticated; create role service_role bypassrls;
      grant usage on schema public to anon,authenticated,service_role;
      create table public.hof_seller_disclosure_drafts (
        id uuid primary key, agent_user_id uuid not null, brokerage_id uuid not null,
        property_address text not null,seller_names jsonb not null,buyer_names jsonb not null,
        disclosure_source_id uuid not null,water_source_id uuid,disclosure_source_revision text not null,water_source_revision text,
        status text not null default 'draft',response_data jsonb not null default '{}',water_rights_data jsonb not null default '{}',
        signwell_document_id text,seller_review_attested boolean not null default false,
        seller_review_attested_at timestamptz,seller_review_attested_by uuid,updated_at timestamptz not null default now(),
        check ((not seller_review_attested and seller_review_attested_at is null and seller_review_attested_by is null)
          or (seller_review_attested and seller_review_attested_at is not null and seller_review_attested_by is not null)));
      create table public.hof_seller_disclosure_review_links (
        id uuid primary key,draft_id uuid not null references public.hof_seller_disclosure_drafts(id),
        agent_user_id uuid not null,brokerage_id uuid not null,seller_email text not null,seller_name text,seller_index int,
        token_hash text unique,verification_code_hash text,revoked_at timestamptz,seller_attested_at timestamptz,seller_attested_name text);
      alter table public.hof_seller_disclosure_drafts enable row level security;
      create policy own on public.hof_seller_disclosure_drafts for all to authenticated
        using(agent_user_id='${owner}') with check(agent_user_id='${owner}');
      alter table public.hof_seller_disclosure_review_links enable row level security;
      grant select,insert,update on public.hof_seller_disclosure_drafts to authenticated;
      grant all on public.hof_seller_disclosure_drafts,public.hof_seller_disclosure_review_links to service_role;`);
    await admin.query(fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/20261015164510_seller_disclosure_review_revision_binding.sql'),'utf8'));
    const service=await connect('service_role'), actor=await connect('authenticated'), a=await connect(), b=await connect();
    check(new Set([admin.pid,service.pid,actor.pid,a.pid,b.pid]).size===5,'Independent PostgreSQL connections');
    for(const fn of ['hof_guard_disclosure_review_content','hof_guard_disclosure_review_link']) {
      const result=(await admin.query(`select prosecdef,proconfig from pg_proc where oid=$1::regprocedure`,['public.'+fn+'()'])).rows[0];
      check(!result.prosecdef && result.proconfig.includes('search_path=pg_catalog'),'Invoker-only fixed search path');
      for(const role of ['anon','authenticated'])check(!(await admin.query('select has_function_privilege($1,$2,\'execute\') as ok',[role,'public.'+fn+'()'])).rows[0].ok,'No public RPC grants');
    }
    const d=await createDraft(['QA Seller One','QA Seller Two']), l1=await createLink(d), l2=await createLink(d,2);
    await reject(()=>cache(service,d),'55000');
    await attest(service,l1); await reject(()=>cache(service,d),'55000');
    await attest(service,l2,'QA Seller Two'); check((await cache(service,d)).rowCount===1,'Every seller reviewed current version');
    const reviewed=await row(d.id);
    await service.query("update public.hof_seller_disclosure_drafts set response_data=response_data || '{\"_hof_signature_delivery\":{\"phase\":\"qa\"}}' where id=$1",[d.id]);
    check((await row(d.id)).review_content_revision===reviewed.review_content_revision,'Delivery-only journal does not invalidate content');
    await reject(()=>service.query("update public.hof_seller_disclosure_drafts set response_data='{}' where id=$1",[d.id]),'55000');
    await service.query("update public.hof_seller_disclosure_drafts set signwell_document_id='fictional-tracked-request' where id=$1",[d.id]);
    await reject(()=>service.query('update public.hof_seller_disclosure_drafts set signwell_document_id=null where id=$1',[d.id]),'55000');
    await reject(()=>service.query("update public.hof_seller_disclosure_drafts set response_data='{\"defect_roof\":\"Y\"}' where id=$1",[d.id]),'55000');
    await reject(()=>service.query('update public.hof_seller_disclosure_review_links set review_content_revision=$2 where id=$1',[l1,randomUUID()]),'55000');
    await reject(()=>service.query('update public.hof_seller_disclosure_review_links set seller_attested_at=null where id=$1',[l1]),'55000');
    await reject(()=>actor.query('update public.hof_seller_disclosure_drafts set seller_review_attested_at=now() where id=$1',[d.id]),'42501');
    await reject(()=>actor.query('select * from public.hof_seller_disclosure_review_links'),'42501');
    const forged=randomUUID();
    await reject(()=>actor.query(`insert into public.hof_seller_disclosure_drafts
      (id,agent_user_id,brokerage_id,property_address,seller_names,buyer_names,disclosure_source_id,disclosure_source_revision,
       seller_review_attested,seller_review_attested_at,seller_review_attested_by)
      values ($1,$2,$3,'Fictional','["QA Seller One"]','[]',$4,'qa',true,now(),$2)`,[forged,owner,brokerage,randomUUID()]),'42501');
    const fields={property_address:"'101 Fictional QA Lane'",seller_names:"'[\"QA Seller Two\"]'::jsonb",
      buyer_names:"'[\"QA Buyer\"]'::jsonb",disclosure_source_id:"gen_random_uuid()",water_source_id:"gen_random_uuid()",
      disclosure_source_revision:"'qa-updated'",water_source_revision:"'qa-water-updated'",
      response_data:"'{\"defect_roof\":\"Y\"}'::jsonb",water_rights_data:"'{\"well_description\":\"fictional\"}'::jsonb"};
    for(const [field,value] of Object.entries(fields)) {
      const candidate=await createDraft();
      await service.query(`update public.hof_seller_disclosure_drafts set ${field}=${value} where id=$1`,[candidate.id]);
      check((await row(candidate.id)).review_content_revision!==candidate.review_content_revision,field+' change rotates review version');
    }
    const unchanged=await createDraft();
    await service.query('update public.hof_seller_disclosure_drafts set property_address=property_address,review_content_revision=$2 where id=$1',[unchanged.id,randomUUID()]);
    check((await row(unchanged.id)).review_content_revision===unchanged.review_content_revision,'No-op saves preserve content version; callers cannot assign it');
    const fresh=await createDraft(), freshLink=await createLink(fresh);
    await attest(service,freshLink); await cache(service,fresh);
    await service.query("update public.hof_seller_disclosure_drafts set response_data='{\"notes\":\"changed\"}' where id=$1",[fresh.id]);
    const changed=await row(fresh.id);
    check(changed.review_content_revision!==fresh.review_content_revision && !changed.seller_review_attested &&
      changed.seller_review_attested_at===null && changed.seller_review_attested_by===null && changed.seller_review_render_revision===null,
      'Actual content change rotates version and clears all approval fields atomically');
    check((await cache(service,fresh)).rowCount===0,'Old aggregate compare-and-set updates zero rows');
    await reject(()=>service.query(`update public.hof_seller_disclosure_drafts set seller_review_attested=true,
      seller_review_attested_at=now(),seller_review_attested_by=$2,seller_review_render_revision=$3 where id=$1`,[fresh.id,owner,render]),'55000');
    await service.query("update public.hof_seller_disclosure_drafts set response_data='{}' where id=$1",[fresh.id]);
    check((await row(fresh.id)).review_content_revision!==fresh.review_content_revision,'Returning to old answers cannot resurrect old reviews');
    const saveFirst=await createDraft(), saveLink=await createLink(saveFirst);
    await a.query('begin'); await a.query("update public.hof_seller_disclosure_drafts set response_data='{\"notes\":\"edited first\"}' where id=$1",[saveFirst.id]);
    const staleAttestation=attest(b,saveLink).then(()=>null,e=>e);
    await blocked(b); await a.query('commit');
    check((await staleAttestation)?.code==='55000','Review waiting behind saved answers is rejected, not rebound');
    const reviewFirst=await createDraft(), reviewLink=await createLink(reviewFirst);
    await a.query('begin'); await attest(a,reviewLink);
    const nextSave=b.query("update public.hof_seller_disclosure_drafts set response_data='{\"notes\":\"edited after review\"}' where id=$1",[reviewFirst.id]);
    await blocked(b); await a.query('commit'); await nextSave;
    const after=await row(reviewFirst.id);
    check(after.review_content_revision!==reviewFirst.review_content_revision && !after.seller_review_attested,'Save waiting behind review invalidates that completed version');
    check((await admin.query('select seller_attested_at from public.hof_seller_disclosure_review_links where id=$1',[reviewLink])).rows[0].seller_attested_at!==null,'Prior completed evidence retained');
    await reject(()=>createLink(reviewFirst),'55000');
    // Extend the same isolated source fixture for seller-editable invitations.
    await admin.query(`alter table public.hof_seller_disclosure_review_links alter column id set default gen_random_uuid();
      alter table public.hof_seller_disclosure_review_links add column expires_at timestamptz not null default now()+interval '7 days',
        add column session_token_hash text unique, add column session_expires_at timestamptz;
      create unique index hof_seller_review_links_draft_seller_active_idx
        on public.hof_seller_disclosure_review_links(draft_id,seller_index)
        where seller_index is not null and revoked_at is null and seller_attested_at is null;`);
    await admin.query(`create function public.hof_release_schema_readiness() returns jsonb language sql as
      'select jsonb_build_object(''contract'',''homeofferflow-release-schema-v1'',''ready'',true,''missing'',''[]''::jsonb)';`);
    await admin.query(fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/20261018134817_seller_disclosure_questionnaire_access.sql'),'utf8'));
    const readiness=(await service.query('select public.hof_seller_disclosure_schema_readiness() as result')).rows[0].result;
    check(readiness.ready && readiness.contract==='homeofferflow-release-schema-v2','Additive readiness delegates the retained baseline and verifies the new schema');
    await reject(()=>actor.query('select public.hof_seller_disclosure_schema_readiness()'),'42501');
    check((await admin.query("select indexdef from pg_indexes where indexname='hof_seller_review_links_draft_seller_active_idx'")).rows[0].indexdef.includes('seller_attested_at IS NULL'),'Legacy pending-request index retained');
    const q=await createDraft(['QA Seller One','QA Seller Two']), q1=await createLink(q), q2=await createLink(q,2);
    await admin.query(`update public.hof_seller_disclosure_review_links set questionnaire_enabled=true,
      session_token_hash='session-'||id::text,session_expires_at=now()+interval '30 minutes' where id=any($1::uuid[])`,[[q1,q2]]);
    const rpc=(client,id,version,action='save',answers={notes:'Seller-entered facts'},water={}) => client.query(
      'select public.hof_save_seller_questionnaire($1,$2,$3,$4,$5,$6) as result',
      ['session-'+id,version,action,JSON.stringify(answers),JSON.stringify(water),render]);
    await reject(()=>rpc(actor,q1,q.review_content_revision),'42501');
    await reject(()=>rpc(service,'missing',q.review_content_revision),'42501');
    await reject(()=>rpc(service,q1,q.review_content_revision,'save',{_hof_signature_delivery:{}}),'22023');
    await reject(()=>rpc(service,q1,q.review_content_revision,'save',{}, {notes:'No water source'}),'22023');
    const saved=(await rpc(service,q1,q.review_content_revision)).rows[0].result;
    check(saved.reviewContentRevision!==q.review_content_revision,'Seller save rotates content version');
    await reject(()=>rpc(service,q2,q.review_content_revision),'40001');
    await rpc(service,q1,saved.reviewContentRevision,'review');
    await rpc(service,q1,saved.reviewContentRevision,'review');
    check((await admin.query('select count(*)::int n from public.hof_seller_disclosure_review_links where draft_id=$1 and seller_attested_at is not null',[q.id])).rows[0].n===1,'Review retry records evidence once');
    await rpc(service,q2,saved.reviewContentRevision,'review');
    check((await cache(service,{...q,review_content_revision:saved.reviewContentRevision})).rowCount===1,'Both seller confirmations authorize current content');
    const qChanged=(await rpc(service,q2,saved.reviewContentRevision,'save',{notes:'Changed by second seller'})).rows[0].result;
    check(!(await row(q.id)).seller_review_attested,'Changed answers invalidate prior seller confirmations');
    check((await admin.query('select count(*)::int n from public.hof_seller_disclosure_review_links where draft_id=$1 and seller_attested_at is not null',[q.id])).rows[0].n===2,'Old confirmation evidence retained unchanged');
    await rpc(service,q1,qChanged.reviewContentRevision,'review');
    await admin.query('update public.hof_seller_disclosure_review_links set session_expires_at=now()-interval \'1 second\' where id=$1',[q2]);
    await reject(()=>rpc(service,q2,qChanged.reviewContentRevision),'42501');
    await admin.query('update public.hof_seller_disclosure_review_links set revoked_at=now() where id=$1',[q1]);
    await reject(()=>rpc(service,q1,qChanged.reviewContentRevision),'42501');
    console.log(JSON.stringify({result:'PASS',checks,scope:'review integrity plus seller questionnaire RPC against isolated PostgreSQL',nothingSent:true,productionChanged:false}));
  } finally {
    for(const c of clients) {try{await c.query('rollback');}catch{} try{await c.end();}catch{}}
    if(server && server.exitCode===null) {
      execFileSync(path.join(binaries,'pg_ctl'),['-D',data,'-m','immediate','-w','stop'],{stdio:'pipe'});
    }
    if(fs.existsSync(path.join(data,'postmaster.pid')))throw Error('Local PostgreSQL did not stop.');
  }
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});

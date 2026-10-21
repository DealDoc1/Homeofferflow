// Isolated actual PostgreSQL. No cloud credentials, TCP listener or provider calls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawn,execFileSync}=require('node:child_process');
const modules=process.env.HOF_PG_QA_MODULES;
if(!modules||!path.isAbsolute(modules))throw Error('Use the pinned absolute PostgreSQL QA runtime.');
const {Client}=require(path.join(modules,'pg')),bin=path.join(modules,'@embedded-postgres/darwin-arm64/native/bin');
const temp=fs.mkdtempSync('/private/tmp/hof-rental-source-'),clients=[];
let server,checks=0,logs='';
const check=(value,message)=>{assert.ok(value,message);checks++;};
const sql=name=>fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/'+name),'utf8');
const probe=async client=>(await client.query('select public.hof_rental_source_schema_readiness() as result')).rows[0].result;
const denied=async action=>{await assert.rejects(action,e=>e.code==='42501');checks++;};
async function connect(role){
 const client=new Client({host:temp,port:55475,user:'hof_qa',database:'postgres',connectionTimeoutMillis:1000,query_timeout:10000});
 await client.connect();clients.push(client);await client.query("set statement_timeout='8s'");
 if(role)await client.query('set role '+role);
 return client;
}
(async()=>{try{
 execFileSync(path.join(bin,'initdb'),['-D',path.join(temp,'data'),'-U','hof_qa','--auth-local=trust','--auth-host=reject','--no-locale','-E','UTF8','--no-sync'],{stdio:'pipe'});
 server=spawn(path.join(bin,'postgres'),['-D',path.join(temp,'data'),'-k',temp,'-p','55475','-c','listen_addresses=','-c','unix_socket_permissions=0700','-c','shared_buffers=16MB'],{stdio:['ignore','pipe','pipe']});
 server.stdout.on('data',v=>logs+=v);server.stderr.on('data',v=>logs+=v);
 let admin;
 for(let n=0;n<60;n++){try{admin=await connect();break;}catch(e){if(server.exitCode!==null)throw Error(logs.slice(-800));await new Promise(r=>setTimeout(r,100));}}
 if(!admin)throw Error('Isolated PostgreSQL failed to start.');
 check((await admin.query('show listen_addresses')).rows[0].listen_addresses==='','No TCP listener');
 await admin.query(`create role anon;create role authenticated;create role service_role bypassrls;
 grant usage on schema public to anon,authenticated,service_role;
 create table public.hof_brokerage_form_sources(form_code text not null);
 alter table public.hof_brokerage_form_sources enable row level security;
 grant insert,update,delete on public.hof_brokerage_form_sources to authenticated;
 grant all on public.hof_brokerage_form_sources to service_role;`);
 await admin.query(sql('20261005110000_expand_trec_39_11_source_code.sql'));
 const snapshot=async()=>JSON.stringify((await admin.query("select relacl,relrowsecurity from pg_class where oid='public.hof_brokerage_form_sources'::regclass")).rows);
 const before=await snapshot();
 await assert.rejects(()=>admin.query("insert into public.hof_brokerage_form_sources values('TXR-2008')"),e=>e.code==='23514');checks++;
 await admin.query(sql('20261021113432_allow_rental_disclosure_sources_for_qa.sql'));
 check(before===await snapshot(),'Source table grants and RLS unchanged');
 for(const code of ['TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TXR-1101','TXR-1102','TXR-1406','TXR-1418','TXR-2008','TXR-2015','TREC-55-1','TREC-61-0','TREC-62-0','TREC-38-8','TREC-39-11']){
  await admin.query('insert into public.hof_brokerage_form_sources values($1)',[code]);checks++;
 }
 await assert.rejects(()=>admin.query("insert into public.hof_brokerage_form_sources values('TXR-injected')"),e=>e.code==='23514');checks++;
 const service=await connect('service_role'),anonymous=await connect('anon'),actor=await connect('authenticated');
 check((await probe(service)).ready,'All 22 source codes are ready');
 for(const client of [anonymous,actor]){
  await denied(()=>probe(client));await denied(()=>client.query('select * from public.hof_brokerage_form_sources'));
 }
 const fn=(await admin.query("select prosecdef,proconfig from pg_proc where oid='public.hof_rental_source_schema_readiness()'::regprocedure")).rows[0];
 check(!fn.prosecdef&&fn.proconfig.includes('search_path=pg_catalog'),'Invoker-only RPC, fixed search path');
 const definition=(await admin.query("select pg_get_constraintdef(oid) as value from pg_constraint where conname='hof_brokerage_form_sources_form_code_check'")).rows[0].value;
 await admin.query('alter table public.hof_brokerage_form_sources drop constraint hof_brokerage_form_sources_form_code_check');
 check(!(await probe(service)).ready,'Missing constraint fails readiness');
 await admin.query('alter table public.hof_brokerage_form_sources add constraint hof_brokerage_form_sources_form_code_check '+definition+' not valid');
 check(!(await probe(service)).ready,'Unvalidated constraint fails readiness');
 await admin.query('alter table public.hof_brokerage_form_sources validate constraint hof_brokerage_form_sources_form_code_check');
 check((await probe(service)).ready,'Validated complete catalog restores readiness');
 check(before===await snapshot(),'Final source privileges unchanged');
 console.log(JSON.stringify({ok:true,assertions:checks,network:'none',provider_sends:0}));
}finally{
 await Promise.allSettled(clients.map(c=>c.end()));
 if(server&&server.exitCode===null){server.kill('SIGTERM');await new Promise(r=>server.once('exit',r));}
 fs.rmSync(temp,{recursive:true,force:true});
}})().catch(error=>{console.error(error);process.exitCode=1;});

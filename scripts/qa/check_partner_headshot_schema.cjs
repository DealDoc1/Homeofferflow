// Isolated real PostgreSQL; no TCP/cloud account or production writes.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawn,execFileSync}=require('node:child_process');
const modules=process.env.HOF_PG_QA_MODULES;
if(!modules||!path.isAbsolute(modules))throw Error('Set the pinned absolute PostgreSQL QA runtime.');
const {Client}=require(path.join(modules,'pg')),bin=path.join(modules,'@embedded-postgres/darwin-arm64/native/bin');
const temp=fs.mkdtempSync('/private/tmp/hof-partner-headshot-'),clients=[];
let server,checks=0,logs='';
const check=(ok,message)=>{assert.ok(ok,message);checks++;};
async function connect(role){
 const client=new Client({host:temp,port:55476,user:'hof_qa',database:'postgres',connectionTimeoutMillis:1000,query_timeout:10000});
 await client.connect();clients.push(client);await client.query("set statement_timeout='8s'");
 if(role)await client.query('set role '+role);return client;
}
(async()=>{try{
 execFileSync(path.join(bin,'initdb'),['-D',path.join(temp,'data'),'-U','hof_qa','--auth-local=trust','--auth-host=reject','--no-locale','-E','UTF8','--no-sync'],{stdio:'pipe'});
 server=spawn(path.join(bin,'postgres'),['-D',path.join(temp,'data'),'-k',temp,'-p','55476','-c','listen_addresses=','-c','unix_socket_permissions=0700','-c','shared_buffers=16MB'],{stdio:['ignore','pipe','pipe']});
 server.stdout.on('data',v=>logs+=v);server.stderr.on('data',v=>logs+=v);
 let admin;for(let n=0;n<60;n++){try{admin=await connect();break;}catch(e){if(server.exitCode!==null)throw Error(logs.slice(-500));await new Promise(r=>setTimeout(r,100));}}
 if(!admin)throw Error('Isolated database did not start.');
 check((await admin.query('show listen_addresses')).rows[0].listen_addresses==='','No TCP listener');
 await admin.query(`create role anon;create role authenticated;create role service_role bypassrls;
 grant usage on schema public to anon,authenticated,service_role;
 create table public.hof_partner_leads(id int primary key,company_name text,partner_program text,payment_status text);
 alter table public.hof_partner_leads enable row level security;
 grant all on public.hof_partner_leads to service_role;
 insert into public.hof_partner_leads values(1,'Existing Beta','beta','not_started');`);
 const snapshot=async()=>JSON.stringify((await admin.query("select relacl,relrowsecurity from pg_class where oid='public.hof_partner_leads'::regclass")).rows);
 const before=await snapshot();
 const migration=fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/20261021202420_partner_public_headshot.sql'),'utf8');
 await admin.query(migration);
 check(before===await snapshot(),'Existing table grants and RLS unchanged');
 const row=(await admin.query('select * from public.hof_partner_leads where id=1')).rows[0];
 check(row.onboarding_public_headshot_url===null,'Existing partner has no inferred headshot');
 check(row.partner_program==='beta'&&row.payment_status==='not_started','No commercial change');
 const service=await connect('service_role');
 for(const value of [null,'https://example.com/photo.jpg','https://example.com/写真.webp']){
  await service.query('update public.hof_partner_leads set onboarding_public_headshot_url=$1 where id=1',[value]);checks++;
 }
 for(const value of ['', 'http://example.com/a.jpg','javascript:evil','data:image/png,AAA',
     'https://example.com/a b.jpg','https://example.com/a\n.jpg','https://example.com/<x>.jpg','https://example.com/'+'a'.repeat(501)]){
  await assert.rejects(()=>service.query('update public.hof_partner_leads set onboarding_public_headshot_url=$1 where id=1',[value]),e=>e.code==='23514');checks++;
 }
 await service.query('update public.hof_partner_leads set onboarding_public_headshot_url=null where id=1');
 check((await service.query('select onboarding_public_headshot_url from public.hof_partner_leads where id=1')).rows[0].onboarding_public_headshot_url===null,'Explicit removal works');
 for(const role of ['anon','authenticated']){
  const actor=await connect(role);
  await assert.rejects(()=>actor.query('select * from public.hof_partner_leads'),e=>e.code==='42501');checks++;
  await assert.rejects(()=>actor.query("update public.hof_partner_leads set onboarding_public_headshot_url='https://example.com/x.jpg'"),e=>e.code==='42501');checks++;
 }
 check(before===await snapshot(),'Final privileges remain identical');
 console.log(JSON.stringify({ok:true,assertions:checks,network:'none',provider_sends:0}));
}finally{
 await Promise.allSettled(clients.map(c=>c.end()));
 if(server&&server.exitCode===null){server.kill('SIGTERM');await new Promise(r=>server.once('exit',r));}
 fs.rmSync(temp,{recursive:true,force:true});
}})().catch(error=>{console.error(error);process.exitCode=1;});

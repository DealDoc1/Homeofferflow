// Real PostgreSQL multi-connection tests. Never accepts a database URL.
// Requires pinned local test dependencies; see postgres-runtime/README.md.
const fs = require('node:fs');
const path = require('node:path');
const {spawn, execFileSync} = require('node:child_process');
const {randomUUID} = require('node:crypto');
const assert = require('node:assert/strict');
const modules = process.env.HOF_PG_QA_MODULES;
if (!modules || !path.isAbsolute(modules)) throw Error('Set HOF_PG_QA_MODULES to an absolute local node_modules directory.');
const {Client} = require(path.join(modules, 'pg'));
const binaries = path.join(modules, '@embedded-postgres/darwin-arm64/native/bin');
const temp = fs.mkdtempSync('/private/tmp/hof-pg-usage-');
const data = path.join(temp,'data');
const config = {host:temp,port:55472,user:'hof_qa',password:'local-only',database:'postgres',
  connectionTimeoutMillis:1500,query_timeout:15000};
const pause = ms=>new Promise(resolve=>setTimeout(resolve,ms));
const clients=[];
let server, admin, checks=0, serverLog='';
const check=(condition,message)=>{assert.ok(condition,message);checks++;};
async function connect(role){
  const client=new Client(config);
  await client.connect(); clients.push(client);
  await client.query("set statement_timeout='10s'");
  if(role) await client.query('set role '+role);
  client.pid=(await client.query('select pg_backend_pid() as pid')).rows[0].pid;
  return client;
}
const value=async(client,sql,args=[])=>(await client.query(sql,args)).rows[0].result;
const claim=(client,user,offer,hash,token)=>value(client,
  'select public.hof_claim_packet_generation($1,$2,$3,$4) as result',[user,offer,hash,token]);
const complete=(client,user,key,token)=>value(client,
  'select public.hof_complete_packet_generation($1,$2,$3) as result',[user,key,token]);
const release=(client,user,key,token)=>value(client,
  'select public.hof_release_unrendered_packet($1,$2,$3) as result',[user,key,token]);
const summary=(client,user)=>value(client,'select public.hof_packet_usage_summary($1) as result',[user]);
async function fixture(){
  const user=randomUUID(),offer=randomUUID();
  await admin.query("insert into public.hof_subscriptions(user_id,status,packet_limit) values($1,'active',1)",[user]);
  await admin.query('insert into public.hof_offers(id,user_id) values($1,$2)',[offer,user]);
  return {user,offer};
}
async function waitForBlocked(pids){
  for(let i=0;i<100;i++){
    const rows=(await admin.query("select pid from pg_stat_activity where pid=any($1::int[]) and wait_event_type='Lock'",[pids])).rows;
    if(rows.length===pids.length){checks++;return;}
    await pause(20);
  }
  throw Error('Expected independent backend lock contention was not observed.');
}
async function main(){
  try {
    execFileSync(path.join(binaries,'initdb'),['-D',data,'-U','hof_qa','--auth-local=trust',
      '--auth-host=reject','--no-locale','-E','UTF8','--no-sync'],{stdio:'pipe'});
    server=spawn(path.join(binaries,'postgres'),['-D',data,'-k',temp,'-p','55472',
      '-c','listen_addresses=','-c','unix_socket_permissions=0700',
      '-c','shared_buffers=16MB','-c','max_connections=20'],{stdio:['ignore','pipe','pipe']});
    server.stdout.on('data',data=>{serverLog+=data;});
    server.stderr.on('data',data=>{serverLog+=data;});
    server.on('error',error=>{serverLog+=error.message;});
    for(let i=0;i<80;i++){
      try {admin=await connect();break;}catch(error){
        if(server.exitCode!==null)throw Error('Local PostgreSQL stopped: '+serverLog.slice(-1000));
        await pause(100);
      }
    }
    if(!admin)throw Error('Local PostgreSQL did not become ready.');
    check((await admin.query('show listen_addresses')).rows[0].listen_addresses==='', 'No TCP listener');
    const version=(await admin.query('show server_version')).rows[0].server_version;
    await admin.query(`create role anon; create role authenticated; create role service_role bypassrls;
      grant usage on schema public to anon,authenticated,service_role;
      create table public.hof_subscriptions(id uuid primary key default gen_random_uuid(),
        user_id uuid unique not null,status text not null,packet_limit integer);
      create table public.hof_offers(id uuid primary key,user_id uuid not null);
      create table public.hof_usage_events(id uuid primary key default gen_random_uuid(),user_id uuid not null,
        offer_id uuid,event_type text not null,quantity integer not null default 1,
        billing_month text not null,metadata jsonb not null default '{}',created_at timestamptz default now());
      grant select,insert,update on public.hof_subscriptions,public.hof_offers,public.hof_usage_events to service_role;`);
    await admin.query(fs.readFileSync(path.resolve(__dirname,
      '../../supabase/migrations/20260915193756_server_owned_packet_usage.sql'),'utf8'));
    const workers=await Promise.all(Array.from({length:8},()=>connect('service_role')));
    check(new Set(workers.map(w=>w.pid)).size===8,'Eight independent PostgreSQL backend processes');

    // Queue all contenders behind the same actual row lock, then let them race.
    for(let round=0;round<5;round++){
      const {user,offer}=await fixture();
      await admin.query('begin');
      await admin.query('select 1 from public.hof_subscriptions where user_id=$1 for update',[user]);
      const tokens=workers.map(()=>randomUUID());
      const pending=workers.map((worker,i)=>claim(worker,user,offer,String(i).repeat(64),tokens[i]));
      await waitForBlocked(workers.map(w=>w.pid));
      await admin.query('commit');
      const outcomes=await Promise.all(pending);
      check(outcomes.filter(v=>v.outcome==='reserved').length===1,'Exactly one contender reserves the last slot');
      check(outcomes.filter(v=>v.outcome==='limit_reached').length===7,'Seven competing new packets rejected at quota');
      const winner=outcomes.findIndex(v=>v.outcome==='reserved');
      const key=outcomes[winner].generation_key;
      const receipts=await Promise.all(workers.map(w=>complete(w,user,key,tokens[winner])));
      check(receipts.every(r=>r.outcome==='completed'),'Concurrent completion retries all recover confirmed result');
      check(new Set(receipts.map(r=>r.usage_event_id)).size===1,'Concurrent completion creates one usage event');
      const totals=await summary(admin,user);
      check(totals.used===1 && totals.reserved===0,'Final summary is one used and zero reserved');
    }

    const same=await fixture(), hash='e'.repeat(64);
    await admin.query('begin');
    await admin.query('select 1 from public.hof_subscriptions where user_id=$1 for update',[same.user]);
    const tokens=workers.map(()=>randomUUID());
    const pending=workers.map((w,i)=>claim(w,same.user,same.offer,hash,tokens[i]));
    await waitForBlocked(workers.map(w=>w.pid));
    await admin.query('commit');
    const outcomes=await Promise.all(pending);
    const winningIndex=outcomes.findIndex(r=>r.outcome==='reserved');
    check(winningIndex>=0 && outcomes.filter(r=>r.outcome==='busy').length===7,
      'Same-packet race admits one worker and marks seven busy');
    const key=outcomes[winningIndex].generation_key, oldToken=tokens[winningIndex], newToken=randomUUID();
    await admin.query("update public.hof_packet_generations set lease_until=now()-interval '1 minute' where generation_key=$1",[key]);
    await admin.query('begin');
    check((await claim(admin,same.user,same.offer,hash,newToken)).outcome==='reserved','Expired worker is replaced');
    const staleComplete=complete(workers[0],same.user,key,oldToken);
    const staleRelease=release(workers[1],same.user,key,oldToken);
    await waitForBlocked([workers[0].pid,workers[1].pid]);
    await admin.query('commit');
    check((await staleComplete).outcome==='stale_attempt','Stale completion is fenced after waiting on recovery');
    check(await staleRelease===false,'Stale release cannot free the recovered slot');

    // Readers see either side of the commit, never a mixed double count.
    await admin.query('begin');
    await complete(admin,same.user,key,newToken);
    const before=await summary(workers[2],same.user);
    check(before.used===0 && before.reserved===1,'Uncommitted completion remains one reservation to other sessions');
    await admin.query('commit');
    const after=await summary(workers[2],same.user);
    check(after.used===1 && after.reserved===0,'Committed completion moves the unit exactly once');

    // One account's slow transaction must not block another account.
    const a=await fixture(),b=await fixture();
    await admin.query('begin');
    await admin.query('select 1 from public.hof_subscriptions where user_id=$1 for update',[a.user]);
    const held=claim(workers[0],a.user,a.offer,hash,randomUUID());
    await waitForBlocked([workers[0].pid]);
    check((await claim(workers[1],b.user,b.offer,hash,randomUUID())).outcome==='reserved',
      'Unrelated account can reserve while another subscription is locked');
    await admin.query('commit');await held;

    const failed=await fixture(), failedToken=randomUUID();
    const reserved=await claim(workers[0],failed.user,failed.offer,hash,failedToken);
    await admin.query('begin');
    check(await release(admin,failed.user,reserved.generation_key,failedToken),'Definite failure releases the reservation');
    const replacement=claim(workers[1],failed.user,failed.offer,'f'.repeat(64),randomUUID());
    await waitForBlocked([workers[1].pid]);await admin.query('commit');
    check((await replacement).outcome==='reserved','Waiting replacement receives exactly the released slot');
    const result=await summary(admin,failed.user);
    check(result.used===0 && result.reserved===1,'Failure plus replacement does not create usage');

    // A disconnected transaction must not leave a partial completion behind.
    const disconnected=await fixture(), disconnectToken=randomUUID();
    const original=await claim(workers[0],disconnected.user,disconnected.offer,hash,disconnectToken);
    const temporary=await connect('service_role');
    await temporary.query('begin');
    await complete(temporary,disconnected.user,original.generation_key,disconnectToken);
    await temporary.end();
    const afterDisconnect=await summary(admin,disconnected.user);
    check(afterDisconnect.used===0 && afterDisconnect.reserved===1,'Disconnect rolls back both completion changes atomically');
    check((await complete(workers[1],disconnected.user,original.generation_key,disconnectToken)).outcome==='completed',
      'A disconnected completion can be retried without another reservation');

    const canceled=await fixture();
    await admin.query('begin');
    await admin.query("update public.hof_subscriptions set status='past_due' where user_id=$1",[canceled.user]);
    const queued=claim(workers[0],canceled.user,canceled.offer,hash,randomUUID());
    await waitForBlocked([workers[0].pid]);await admin.query('commit');
    check((await queued).outcome==='inactive','Queued generation sees committed billing cancellation');

    for(const role of ['anon','authenticated']){
      const client=await connect(role);
      await assert.rejects(summary(client,failed.user),{code:'42501'});checks++;
      await assert.rejects(claim(client,failed.user,failed.offer,hash,randomUUID()),{code:'42501'});checks++;
    }
    console.log(JSON.stringify({engine:'PostgreSQL '+version,checks,passed:true,
      independentWorkers:8,lastSlotRaceRounds:5,transport:'private Unix socket',
      limitation:'Isolated schema fixtures, not full Supabase/PostgREST or production.'}));
  } finally {
    if(admin)try{await admin.query('rollback');}catch{}
    await Promise.allSettled(clients.map(client=>client.end()));
    if(server && server.exitCode===null){
      execFileSync(path.join(binaries,'pg_ctl'),['-D',data,'-m','fast','-w','stop'],{stdio:'pipe',timeout:10000});
    }
    console.log(JSON.stringify({localDatabaseStopped:!fs.existsSync(path.join(data,'postmaster.pid')),fixtureDirectory:temp}));
  }
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});

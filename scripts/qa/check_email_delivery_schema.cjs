// Use HOF_PG_QA_MODULES for the existing pinned embedded PostgreSQL runtime,
// or HOF_PGLITE_MODULE for an already installed PGlite. No hosted URL is read.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

async function openDatabase() {
  if (!process.env.HOF_PG_QA_MODULES) {
    const { PGlite } = require(process.env.HOF_PGLITE_MODULE || '@electric-sql/pglite');
    return {db:new PGlite(), engine:'isolated PGlite/PostgreSQL'};
  }
  const modules=process.env.HOF_PG_QA_MODULES;
  assert.ok(path.isAbsolute(modules),'Use an absolute local node_modules directory');
  const {Client}=require(path.join(modules,'pg'));
  const {spawn,execFileSync}=require('node:child_process');
  const {randomInt}=require('node:crypto');
  const temp=fs.mkdtempSync('/private/tmp/hof-email-schema-');
  const data=path.join(temp,'data'), bin=path.join(modules,'@embedded-postgres/darwin-arm64/native/bin');
  const port=randomInt(55100,55999);
  let server,client;
  const close=async()=>{
    if(client) await client.end();
    if(server && server.exitCode===null) {
      execFileSync(path.join(bin,'pg_ctl'),['-D',data,'-m','fast','-w','stop'],{stdio:'pipe',timeout:10000});
      await new Promise(resolve=>server.exitCode!==null?resolve():server.once('exit',resolve));
    }
    assert.equal(fs.existsSync(path.join(data,'postmaster.pid')),false,'QA database is stopped');
  };
  try {
    execFileSync(path.join(bin,'initdb'),['-D',data,'-U','hof_qa','--auth-local=trust','--auth-host=reject','--no-locale','-E','UTF8','--no-sync'],{stdio:'pipe'});
    server=spawn(path.join(bin,'postgres'),['-D',data,'-k',temp,'-p',String(port),'-c','listen_addresses=','-c','unix_socket_permissions=0700','-c','shared_buffers=16MB'],{stdio:'ignore'});
    for(let attempt=0;attempt<80;attempt++) {
      const candidate=new Client({host:temp,port,user:'hof_qa',database:'postgres',connectionTimeoutMillis:1000,query_timeout:8000});
      try {await candidate.connect();client=candidate;break;}
      catch(error) {await candidate.end().catch(()=>{});if(server.exitCode!==null)throw Error('Isolated QA database stopped');await new Promise(r=>setTimeout(r,100));}
    }
    if(!client)throw Error('Isolated QA database did not start');
    assert.equal((await client.query('show listen_addresses')).rows[0].listen_addresses,'','No TCP listener');
    await client.query("set statement_timeout='8s'");
    return {db:{query:(...args)=>client.query(...args),exec:sql=>client.query(sql),close},engine:'isolated PostgreSQL 17 (private Unix socket)'};
  } catch(error) {await close();throw error;}
}

(async () => {
  const {db,engine} = await openDatabase();
  let checks = 0;
  const check = (value, message) => { assert.ok(value, message); checks++; };
  const reject = async (sql, params = []) => {
    await assert.rejects(db.query(sql, params)); checks++;
  };
  try {
    await db.exec('create role anon; create role authenticated; create role service_role bypassrls; grant usage on schema public to anon, authenticated, service_role;');
    const migration = path.resolve(__dirname, '../../supabase/migrations/20260915185113_durable_checkout_email_delivery.sql');
    await db.exec(fs.readFileSync(migration, 'utf8'));
    const table = 'public.hof_email_deliveries';
    const key = 'hof-email-v1-' + 'a'.repeat(64), hash = 'b'.repeat(64);
    const body = JSON.stringify({to: ['qa@example.test'], html: 'Controlled QA'});
    const rls = await db.query(`select relrowsecurity from pg_class where oid = '${table}'::regclass`);
    check(rls.rows[0].relrowsecurity, 'RLS must be enabled');
    const fn = await db.query("select prosecdef, proconfig from pg_proc where oid = 'public.hof_preserve_email_delivery()'::regprocedure");
    check(fn.rows[0].prosecdef === false, 'Trigger must not run as a privileged definer');
    check(fn.rows[0].proconfig.includes('search_path=pg_catalog'), 'Trigger uses a fixed search path');
    for (const role of ['anon', 'authenticated']) {
      const grants = await db.query("select has_function_privilege($1, 'public.hof_preserve_email_delivery()', 'EXECUTE') as allowed", [role]);
      check(grants.rows[0].allowed === false, 'Trigger function is not a public RPC');
    }
    for (const role of ['anon', 'authenticated']) {
      await db.exec(`set role ${role}`);
      await reject(`select * from ${table}`);
      await reject(`insert into ${table}(delivery_key,payload,payload_fingerprint) values ($1,$2,$3)`, [key,body,hash]);
      await db.exec('reset role');
    }
    await db.exec('set role service_role');
    await reject(`insert into ${table}(delivery_key,payload,payload_fingerprint,status,provider_id,first_attempt_at)
      values ($1,null,$2,'accepted','fake-receipt',1000)`, [key,hash]);
    await db.query(`insert into ${table}(delivery_key,payload,payload_fingerprint) values ($1,$2,$3)`, [key,body,hash]);
    const duplicate = await db.query(`insert into ${table}(delivery_key,payload,payload_fingerprint) values ($1,'{}',$2)
      on conflict(delivery_key) do nothing returning delivery_key`, [key,hash]);
    check(duplicate.rows.length === 0, 'A replay must not overwrite the first body');
    await reject(`update ${table} set payload='{}' where delivery_key=$1`, [key]);
    await reject(`update ${table} set payload_fingerprint=$2 where delivery_key=$1`, [key,'c'.repeat(64)]);
    await reject(`update ${table} set delivery_key=$2 where delivery_key=$1`, [key,'hof-email-v1-'+'d'.repeat(64)]);
    await reject(`update ${table} set status='accepted',payload=null,provider_id='email-1' where delivery_key=$1`, [key]);
    await reject(`update ${table} set first_attempt_at='NaN' where delivery_key=$1`, [key]);
    const claimed = await db.query(`update ${table} set first_attempt_at=1000 where delivery_key=$1 and first_attempt_at is null returning *`, [key]);
    check(claimed.rows.length === 1, 'First attempt is persisted');
    const raced = await db.query(`update ${table} set first_attempt_at=1001 where delivery_key=$1 and first_attempt_at is null returning *`, [key]);
    check(raced.rows.length === 0, 'Only one timestamp claim wins');
    await reject(`update ${table} set first_attempt_at=1001 where delivery_key=$1`, [key]);
    await reject(`update ${table} set first_attempt_at=null where delivery_key=$1`, [key]);
    const accepted = await db.query(`update ${table} set status='accepted',payload=null,provider_id='email-1'
      where delivery_key=$1 and status='pending' and first_attempt_at=1000 returning *`, [key]);
    check(accepted.rows.length === 1 && accepted.rows[0].payload === null, 'Acceptance clears private body');
    await reject(`update ${table} set status='pending',payload='{}',provider_id=null where delivery_key=$1`, [key]);
    await reject(`update ${table} set provider_id='different' where delivery_key=$1`, [key]);
    await reject(`delete from ${table} where delivery_key=$1`, [key]);
    // Reproduce REST float8 output with production's precision setting. The
    // first timestamp is immutable, but its JSON decimal need not round-trip.
    const fractionalKey = 'hof-email-v1-' + 'c'.repeat(64);
    await db.query(`insert into ${table}(delivery_key,payload,payload_fingerprint) values ($1,$2,$3)`, [fractionalKey, body, hash]);
    await db.query(`update ${table} set first_attempt_at=$2 where delivery_key=$1 and first_attempt_at is null`, [fractionalKey, 1700000000.1234567]);
    await db.exec('set extra_float_digits=0');
    const wire = await db.query(`select first_attempt_at::text as attempt_text from ${table} where delivery_key=$1`, [fractionalKey]);
    const rounded = wire.rows[0].attempt_text;
    const missed = await db.query(`update ${table} set status='accepted',payload=null,provider_id='fractional-email'
      where delivery_key=$1 and payload_fingerprint=$2 and status='pending'
      and first_attempt_at=$3::double precision returning delivery_key`, [fractionalKey, hash, rounded]);
    check(missed.rows.length === 0, 'Rounded REST timestamp reproduces zero-row acceptance');
    await reject(`update ${table} set first_attempt_at=1001 where delivery_key=$1`, [fractionalKey]);
    const fractionalAccepted = await db.query(`update ${table} set status='accepted',payload=null,provider_id='fractional-email'
      where delivery_key=$1 and payload_fingerprint=$2 and status='pending'
      and first_attempt_at is not null returning delivery_key,payload`, [fractionalKey, hash]);
    check(fractionalAccepted.rows.length === 1 && fractionalAccepted.rows[0].payload === null, 'Immutable attempted identity accepts without lossy timestamp equality');
    await reject(`update ${table} set provider_id='different' where delivery_key=$1`, [fractionalKey]);
    await db.exec('reset role');
    // Defense in depth: even an accidental read grant must not bypass RLS.
    await db.exec(`grant select on ${table} to anon, authenticated`);
    for (const role of ['anon', 'authenticated']) {
      await db.exec(`set role ${role}`);
      check((await db.query(`select * from ${table}`)).rows.length === 0, 'RLS denies all client rows');
      await db.exec('reset role');
    }
    console.log(JSON.stringify({engine, checks, passed: true}));
  } finally {
    await db.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });

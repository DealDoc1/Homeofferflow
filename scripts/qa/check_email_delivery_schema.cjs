// Run with HOF_PGLITE_MODULE pointing to an explicitly installed, pinned
// @electric-sql/pglite package. No production connection is used.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { PGlite } = require(process.env.HOF_PGLITE_MODULE || '@electric-sql/pglite');

(async () => {
  const db = new PGlite();
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
    await db.exec('reset role');
    // Defense in depth: even an accidental read grant must not bypass RLS.
    await db.exec(`grant select on ${table} to anon, authenticated`);
    for (const role of ['anon', 'authenticated']) {
      await db.exec(`set role ${role}`);
      check((await db.query(`select * from ${table}`)).rows.length === 0, 'RLS denies all client rows');
      await db.exec('reset role');
    }
    console.log(JSON.stringify({engine: 'isolated PGlite/PostgreSQL', checks, passed: true}));
  } finally {
    await db.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });

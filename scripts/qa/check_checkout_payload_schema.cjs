// Isolated PostgreSQL semantics QA. No hosted database or account credentials.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {PGlite} = require(process.env.HOF_PGLITE_MODULE || '@electric-sql/pglite');
(async()=>{
  const db = new PGlite(); let checks = 0;
  const check = (value,message)=>{assert.ok(value,message);checks++;};
  const reject = async (sql,params=[])=>{await assert.rejects(db.query(sql,params));checks++;};
  const table = 'public.hof_checkout_payloads';
  const id = '11111111-1111-4111-8111-111111111111', hash = 'a'.repeat(64);
  try {
    await db.exec('create role anon; create role authenticated; create role service_role bypassrls; grant usage on schema public to anon, authenticated, service_role;');
    await db.exec(fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/20260915233303_private_buyer_checkout_payloads.sql'),'utf8'));
    check((await db.query(`select relrowsecurity from pg_class where oid='${table}'::regclass`)).rows[0].relrowsecurity,'RLS enabled');
    const fn = (await db.query("select prosecdef,proconfig from pg_proc where oid='public.hof_preserve_checkout_payload()'::regprocedure")).rows[0];
    check(!fn.prosecdef && fn.proconfig.includes('search_path=pg_catalog'),'Trigger is invoker with fixed path');
    for(const role of ['anon','authenticated']) {
      check(!(await db.query("select has_function_privilege($1,'public.hof_preserve_checkout_payload()','EXECUTE') allowed",[role])).rows[0].allowed,'No client RPC');
      await db.exec(`set role ${role}`);
      await reject(`select * from ${table}`);
      await reject(`insert into ${table}(id,payload_text,payload_sha256) values($1,'{}',$2)`,[id,hash]);
      await reject(`update ${table} set stripe_session_id='cs_stolen' where id=$1`,[id]);
      await reject(`delete from ${table} where id=$1`,[id]);
      await db.exec('reset role');
    }
    await db.exec('set role service_role');
    await reject(`insert into ${table}(id,payload_text,payload_sha256,stripe_session_id) values($1,'{}',$2,'cs_premature')`,[id,hash]);
    const body=JSON.stringify({docs:Buffer.alloc(2.5*1024*1024).toString('base64'),text:'José 🏡\u2028李\u2029'});
    await db.query(`insert into ${table}(id,payload_text,payload_sha256) values($1,$2,$3)`,[id,body,hash]);
    check((await db.query(`select payload_text from ${table} where id=$1`,[id])).rows[0].payload_text===body,'Full upload-size payload round trip');
    await reject(`insert into ${table}(id,payload_text,payload_sha256) values($1,'{}',$2)`,[id,hash]);
    await reject(`update ${table} set payload_text='{}' where id=$1`,[id]);
    await reject(`update ${table} set payload_sha256=$2 where id=$1`,[id,'b'.repeat(64)]);
    check((await db.query(`update ${table} set stripe_session_id='cs_first' where id=$1 and stripe_session_id is null returning id`,[id])).rows.length===1,'First binding succeeds');
    check((await db.query(`update ${table} set stripe_session_id='cs_second' where id=$1 and stripe_session_id is null returning id`,[id])).rows.length===0,'Second binding cannot win');
    await reject(`update ${table} set stripe_session_id='cs_second' where id=$1`,[id]);
    await reject(`update ${table} set stripe_session_id=null where id=$1`,[id]);
    await reject(`delete from ${table} where id=$1`,[id]);
    await reject(`insert into ${table}(id,payload_text,payload_sha256) values('22222222-2222-4222-8222-222222222222',$1,$2)`,['x'.repeat(4194305),hash]);
    await db.exec('reset role');
    await db.exec(`grant select on ${table} to anon,authenticated`);
    for(const role of ['anon','authenticated']){
      await db.exec(`set role ${role}`);
      check((await db.query(`select * from ${table}`)).rows.length===0,'RLS protects even with accidental select grant');
      await db.exec('reset role');
    }
    await db.exec(fs.readFileSync(path.resolve(__dirname,'../../supabase/migrations/20260915234223_expired_checkout_payload_cleanup.sql'),'utf8'));
    for(const role of ['anon','authenticated']) {
      check(!(await db.query(`select has_table_privilege($1,'${table}','DELETE') allowed`,[role])).rows[0].allowed,'Cleanup grant excludes browser roles');
    }
    await db.exec('set role service_role');
    const remove = async (target, fingerprint, session)=>db.query(`delete from ${table}
      where id=$1 and payload_sha256=$2 and (stripe_session_id=$3 or stripe_session_id is null) returning id`,[target,fingerprint,session]);
    check((await remove(id,'b'.repeat(64),'cs_first')).rows.length===0,'Wrong hash cannot delete');
    check((await remove(id,hash,'cs_other')).rows.length===0,'Other bound session cannot delete');
    check((await remove(id,hash,'cs_first')).rows.length===1,'Exact cleanup removes abandoned staging copy');
    check((await remove(id,hash,'cs_first')).rows.length===0,'Cleanup retry is idempotent');
    await db.query(`insert into ${table}(id,payload_text,payload_sha256) values($1,'{}',$2)`,[id,hash]);
    check((await remove(id,hash,'cs_unbound')).rows.length===1,'Expired creation with lost binding can be cleaned');
    await db.exec('reset role');
    console.log(JSON.stringify({engine:'isolated PGlite/PostgreSQL',checks,passed:true}));
  } finally {await db.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});

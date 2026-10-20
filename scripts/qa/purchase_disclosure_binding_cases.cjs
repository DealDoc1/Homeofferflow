// Extends the existing isolated PostgreSQL runner; no new server or credentials.
const fs=require('node:fs'),path=require('node:path'),{randomUUID}=require('node:crypto');
module.exports=async function run(ctx) {
  const {admin,service,actor,a,b,owner,render,createDraft,createLink,attest,cache,row,blocked,check,reject}=ctx;
  await admin.query(`create table public.hof_offers (
    id uuid primary key,user_id uuid not null,status text not null default 'Draft',
    offer_data jsonb not null default '{}',signwell_document_id text,signwell_status text,
    generated_at timestamptz,deleted_at timestamptz,last_updated timestamptz default now(),updated_at timestamptz default now());
    alter table public.hof_offers enable row level security;
    create policy own on public.hof_offers for all to authenticated using(user_id='${owner}') with check(user_id='${owner}');
    grant select,insert,update on public.hof_offers to authenticated;
    grant all on public.hof_offers to service_role;`);
  const baseline=(await admin.query("select md5(pg_get_functiondef('public.hof_release_schema_readiness()'::regprocedure)) as hash")).rows[0].hash;
  await admin.query(fs.readFileSync(path.join(__dirname,'../../supabase/migrations/20260915203004_protect_offer_packet_autosave.sql'),'utf8'));
  await admin.query(fs.readFileSync(path.join(__dirname,'../../supabase/migrations/20261020140935_bind_reviewed_disclosure_to_purchase.sql'),'utf8'));
  check((await admin.query("select md5(pg_get_functiondef('public.hof_release_schema_readiness()'::regprocedure)) as hash")).rows[0].hash===baseline,'Existing readiness function unchanged');
  for(const name of ['hof_guard_purchase_disclosure_recipe','hof_keep_purchase_disclosure','hof_keep_purchase_disclosure_review','hof_bind_purchase_disclosure','hof_purchase_disclosure_schema_readiness']) {
    const fn=(await admin.query('select prosecdef,proconfig from pg_proc where oid=$1::regprocedure',['public.'+name+'()'])).rows[0];
    check(!fn.prosecdef && fn.proconfig.includes('search_path=pg_catalog'),'Invoker-only fixed search path');
    for(const role of ['anon','authenticated'])
      check(!(await admin.query('select has_function_privilege($1,$2,\'execute\') as ok',[role,'public.'+name+'()'])).rows[0].ok,'No public RPC grants');
  }
  const readiness=(await service.query('select public.hof_purchase_disclosure_schema_readiness() as result')).rows[0].result;
  check(readiness.ready && readiness.contract==='homeofferflow-purchase-disclosure-v1','Additive private readiness includes current disclosure baseline');
  await admin.query('alter table public.hof_offers disable trigger hof_purchase_disclosure_signature_guard');
  check(!(await service.query('select public.hof_purchase_disclosure_schema_readiness() as result')).rows[0].result.ready,'Disabled send guard cannot report ready');
  await admin.query('alter table public.hof_offers enable trigger hof_purchase_disclosure_signature_guard');
  const forged=randomUUID();
  await actor.query(`insert into public.hof_offers(id,user_id,offer_data) values($1,$2,'{"purchaseDisclosurePacket":{"included":true},"address":"QA address"}')`,[forged,owner]);
  check(!(await admin.query('select offer_data from public.hof_offers where id=$1',[forged])).rows[0].offer_data.purchaseDisclosurePacket,'Client cannot forge server inclusion recipe on insert');
  await actor.query(`update public.hof_offers set offer_data='{"purchaseDisclosurePacket":{"included":true},"address":"Updated QA address"}' where id=$1`,[forged]);
  check(!(await admin.query('select offer_data from public.hof_offers where id=$1',[forged])).rows[0].offer_data.purchaseDisclosurePacket,'Client cannot forge recipe on draft update');
  const ready=async(sellers=['QA Seller One'])=>{
    const draft=await createDraft(sellers),links=[];
    for(let i=1;i<=sellers.length;i++) {
      const id=await createLink(draft,i,`seller-${i}@example.test`);
      await attest(service,id,sellers[i-1]);links.push(id);
    }
    await cache(service,draft);return {...await row(draft.id),links};
  };
  const offer=async(draft,{two=false,reverse=false,user=owner}={})=>{
    const id=randomUUID(),names=reverse?[...draft.seller_names].reverse():draft.seller_names;
    const data={buyer1:'QA Buyer One',buyerEmail:'buyer-one@example.test',seller:names[0],seller2Name:names[1]||'',
      address:draft.property_address,purchaseSellerDisclosureId:draft.id};
    if(two)Object.assign(data,{buyer2:'QA Buyer Two',buyer2Email:'buyer-two@example.test'});
    await service.query('insert into public.hof_offers(id,user_id,status,offer_data) values($1,$2,\'Generated\',$3)',[id,user,data]);
    return {id,user,data,two,reverse};
  };
  const body=(saved,draft,mutation={})=>{
    const recipients=[{id:'1',name:'QA Buyer One',email:'buyer-one@example.test'}];
    if(saved.two)recipients.push({id:'2',name:'QA Buyer Two',email:'buyer-two@example.test'});
    const names=saved.reverse?[...draft.seller_names].reverse():draft.seller_names;
    names.forEach((name,i)=>recipients.push({id:String(i+3),name,email:`seller-${draft.seller_names.indexOf(name)+1}@example.test`}));
    return {...saved.data,_hof_signature_delivery:{version:1,document_id:'fictional-provider-'+saved.id,phase:'prepared',recipients,
      seller_disclosure:{id:draft.id,revision:draft.review_content_revision,render_revision:render,
        user_id:saved.user,offer_id:saved.id,fingerprint:'c'.repeat(64),...mutation}}};
  };
  const bind=(client,saved,draft,mutation={},transform=v=>v)=>client.query(
    'update public.hof_offers set signwell_document_id=$2,offer_data=$3 where id=$1 returning id',
    [saved.id,'fictional-provider-'+saved.id,transform(body(saved,draft,mutation))]);
  const d=await ready(['QA Seller One','QA Seller Two']),o=await offer(d,{two:true,reverse:true});
  await reject(()=>bind(service,o,d,{revision:randomUUID()}),'55000');
  await reject(()=>bind(service,o,d,{render_revision:'old'}),'55000');
  check((await row(d.id)).signature_offer_id===null,'Stale review cannot claim disclosure');
  await reject(()=>bind(service,o,d,{},v=>({...v,address:'Different property'})),'55000');
  await reject(()=>bind(service,o,d,{},v=>{v._hof_signature_delivery.recipients[2].email='unknown@example.test';return v;}),'55000');
  await reject(()=>bind(service,o,d,{},v=>{v._hof_signature_delivery.recipients[0].id='9';return v;}),'55000');
  await reject(()=>service.query('update public.hof_seller_disclosure_drafts set signature_offer_id=$2 where id=$1',[d.id,o.id]),'42501');
  await bind(service,o,d);
  check((await row(d.id)).signature_offer_id===o.id,'Checkpoint atomically binds both reversed sellers and two buyers');
  await bind(service,o,d);
  check((await row(d.id)).signature_offer_id===o.id,'Same journal checkpoint replay keeps one association');
  const competing=await offer(d);
  await reject(()=>bind(service,competing,d),'55000');
  check((await admin.query('select signwell_document_id from public.hof_offers where id=$1',[competing.id])).rows[0].signwell_document_id===null,'Losing offer checkpoint rolls back');
  await reject(()=>service.query("update public.hof_seller_disclosure_drafts set response_data='{\"notes\":\"changed\"}' where id=$1",[d.id]),'55000');
  await reject(()=>service.query('update public.hof_seller_disclosure_drafts set signature_offer_id=null where id=$1',[d.id]),'55000');
  await reject(()=>service.query('delete from public.hof_seller_disclosure_drafts where id=$1',[d.id]),'55000');
  await reject(()=>admin.query('update public.hof_seller_disclosure_review_links set revoked_at=now() where id=$1',[d.links[0]]),'55000');
  await reject(()=>admin.query('delete from public.hof_seller_disclosure_review_links where id=$1',[d.links[0]]),'55000');
  await reject(()=>service.query("update public.hof_offers set offer_data=offer_data #- '{_hof_signature_delivery,seller_disclosure}' where id=$1",[o.id]),'55000');
  await reject(()=>service.query('update public.hof_offers set signwell_document_id=\'replacement\' where id=$1',[o.id]),'55000');
  await actor.query("update public.hof_offers set status='Deleted',deleted_at=now() where id=$1",[o.id]);
  check((await row(d.id)).signature_offer_id===o.id,'Normal dashboard soft-delete retains association');
  const foreign=await ready(),f=await offer(foreign,{user:randomUUID()});
  await reject(()=>bind(service,f,foreign),'55000');
  check((await row(foreign.id)).signature_offer_id===null,'Cross-account offer cannot bind private disclosure');
  const own=await ready(),ownOffer=await offer(own);
  await reject(()=>bind(actor,ownOffer,own),'55000');
  const unicode=await ready(['Élodie QA 李']),unicodeOffer=await offer(unicode);
  await bind(service,unicodeOffer,unicode);
  check((await row(unicode.id)).signature_offer_id===unicodeOffer.id,'Unicode seller works without a brokerage seat check');
  // Exercise compatibility with the separate, unapplied listing association.
  await admin.query('alter table public.hof_seller_disclosure_drafts add column signature_packet_id uuid');
  await reject(()=>admin.query('update public.hof_seller_disclosure_drafts set signature_packet_id=$2 where id=$1',[d.id,randomUUID()]),'55000');
  const listed=await ready(),listedOffer=await offer(listed);
  await admin.query('update public.hof_seller_disclosure_drafts set signature_packet_id=$2 where id=$1',[listed.id,randomUUID()]);
  await reject(()=>bind(service,listedOffer,listed),'55000');

  // Actual independent connection waits establish both race orderings.
  const editFirst=await ready(),editOffer=await offer(editFirst);
  await a.query('begin');await a.query("update public.hof_seller_disclosure_drafts set response_data='{\"notes\":\"changed first\"}' where id=$1",[editFirst.id]);
  const lateBind=bind(b,editOffer,editFirst).then(()=>null,e=>e);
  await blocked(b);await a.query('commit');check((await lateBind)?.code==='55000','Edit-first race rejects old version after lock wait');
  const sendFirst=await ready(),sendOffer=await offer(sendFirst);
  await a.query('begin');await bind(a,sendOffer,sendFirst);
  const lateEdit=b.query("update public.hof_seller_disclosure_drafts set response_data='{\"notes\":\"changed late\"}' where id=$1",[sendFirst.id]).then(()=>null,e=>e);
  await blocked(b);await a.query('commit');check((await lateEdit)?.code==='55000','Send-first race preserves reviewed content');
  const race=await ready(),winner=await offer(race),loser=await offer(race);
  await a.query('begin');await bind(a,winner,race);
  const losingBind=bind(b,loser,race).then(()=>null,e=>e);
  await blocked(b);await a.query('commit');check((await losingBind)?.code==='55000','Competing offers cannot both claim the same disclosure');
  const retiring=await ready(),retireOffer=await offer(retiring);
  await a.query('begin');await a.query('update public.hof_seller_disclosure_review_links set revoked_at=now() where id=$1',[retiring.links[0]]);
  const retiredBind=bind(b,retireOffer,retiring).then(()=>null,e=>e);
  await blocked(b);await a.query('commit');check((await retiredBind)?.code==='55000','Retired proof cannot authorize waiting send');
  const protectedProof=await ready(),protectedOffer=await offer(protectedProof);
  await a.query('begin');await bind(a,protectedOffer,protectedProof);
  const lateRetirement=b.query('update public.hof_seller_disclosure_review_links set revoked_at=now() where id=$1',[protectedProof.links[0]]).then(()=>null,e=>e);
  await blocked(b);await a.query('commit');check((await lateRetirement)?.code==='55000','Send-first proof remains attached after concurrent retirement');
};

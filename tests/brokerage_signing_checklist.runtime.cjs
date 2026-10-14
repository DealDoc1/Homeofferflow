const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const start=html.indexOf('  root.renderBrokerageFoundationPanel = async function renderBrokerageFoundationPanel()');
const end=html.indexOf('  root.retryBrokerageWorkspace =',start);
assert(start>=0&&end>start);
async function render(metrics){
  const panel={innerHTML:''},dashboard={innerHTML:''};
  const context=vm.createContext({
    document:{getElementById:id=>id==='brokerageFoundationPanel'?panel:id==='brokerSafeDashboard'?dashboard:null},
    safe:value=>String(value||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
    brokerSummary:async()=>({metrics,agents:[],pendingInvites:[],sourceReadiness:[],teamCohorts:[]}),
    hofAuth:{session:{user:{id:'fictional-broker'}},authoritativeProfile:{role:'brokerage_admin'}},
    hofPlatform:{brokerage:{name:'QA Brokerage',brand_color:'#173f35',default_title_company:'QA Title Company'},brokerageMembership:{role:'broker_admin',status:'active'}},
    renderBrokerageBrandPreview(){},
  });
  context.root=context;context.window=context;
  vm.runInContext(html.slice(start,end),context);
  await context.renderBrokerageFoundationPanel();
  return dashboard.innerHTML;
}
module.exports={render};
if(require.main===module){
  const {test}=require('node:test');
  for(const [name,metrics,done] of [
    ['sent but not complete',{offerCount:1,signingStartedCount:1,signedCount:0},true],
    ['draft not sent',{offerCount:1,signingStartedCount:0,signedCount:0},false],
    ['completed offer',{offerCount:1,signingStartedCount:1,signedCount:1},true],
    ['unknown missing metric',{offerCount:1,signedCount:0},false],
  ])test(`actual broker checklist: ${name}`,async()=>{
    const output=await render(metrics);
    const row=output.match(/<li class="([^"]*)">[^]*?Send the first offer for signing<\/span><\/li>/g)?.at(-1);
    assert(row,'Signing milestone must render');
    const correct=output.match(/<li class="([^"]*)"><span class="activation-mark">[^<]*<\/span><span>Send the first offer for signing<\/span><\/li>/);
    assert(correct);assert.equal(correct[1]==='is-complete',done);
    assert(output.includes('Buyer names, property addresses, offer terms, and document contents are not included.'));
  });
}

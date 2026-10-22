const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script id="hof-standalone-agreement-signing-v1">([\s\S]*?)<\/script>/)?.[1];
assert.ok(script);
const root={setTimeout(){}};
const document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(script.replace('  const previous = root.renderAccountDashboard;',
  '  root.formatListingPacket = listingPacketSummary;\n  const previous = root.renderAccountDashboard;'),{window:root,document,console});

test('shows actual included documents separately from pending seller disclosure without a sending gate',()=>{
  const view=root.formatListingPacket({pageCount:11,included:['Sale listing agreement','Information About Brokerage Services'],pending:['Seller’s Disclosure Notice']});
  assert.match(view,/Your packet · 11 pages/);
  assert.match(view,/<strong>Included:<\/strong> Sale listing agreement · Information About Brokerage Services/);
  assert.match(view,/<strong>Still to prepare:<\/strong> Seller’s Disclosure Notice/);
  assert.match(view,/You can send the prepared documents now/);
});
test('unknown legacy packets render no invented summary and complete packets have no pending warning',()=>{
  assert.equal(root.formatListingPacket(null),'');
  assert.equal(root.formatListingPacket({included:['A']}),'');
  const view=root.formatListingPacket({pageCount:10,included:['Sale listing agreement'],pending:[]});
  assert.doesNotMatch(view,/Still to prepare|complete the remaining items/);
});
test('lease packet lists actual IABS and pending rental disclosures without blocking prepared documents',()=>{
  const view=root.formatListingPacket({pageCount:12,included:['Lease listing agreement','Information About Brokerage Services'],
    pending:['Rental flood disclosure — Landlord completion to follow.','Lead-based paint disclosure for a lease — Confirm the home’s age.']});
  assert.match(view,/<strong>Included:<\/strong> Lease listing agreement · Information About Brokerage Services/);
  assert.match(view,/<strong>Still to prepare:<\/strong> Rental flood disclosure/);
  assert.match(view,/You can send the prepared documents now/);
  assert.doesNotMatch(view,/Seller’s Disclosure Notice|Sale listing agreement/);
});
test('document labels and additional notes are escaped, never injected as markup',()=>{
  const view=root.formatListingPacket({pageCount:11,included:['<img src=x onerror=alert(1)>'],pending:['<script>bad()</script>'],otherDocuments:'<iframe>private</iframe>'});
  assert.doesNotMatch(view,/<img|<script|<iframe/);
  assert.match(view,/&lt;img/);assert.match(view,/&lt;iframe/);
});
test('included rental disclosures still show tenant receipt and pamphlet follow-up without a send gate',()=>{
  const view=root.formatListingPacket({pageCount:14,included:['Lease listing agreement','Rental flood disclosure','Lead-based paint disclosure for a lease'],pending:[],
    followUp:['Tenant receipt and signature remain to be completed.','Provide the lead pamphlet.','<img src=x onerror=attack()>']});
  assert.match(view,/Before the lease is signed/);assert.match(view,/Tenant receipt and signature/);
  assert.match(view,/Provide the lead pamphlet/);assert.match(view,/&lt;img/);
  assert.doesNotMatch(view,/<img|disabled|approval required|Still to prepare/);
});
test('send confirmation uses the server delivery state rather than claiming every retry sent invitations',()=>{
  const expression=script.match(/status\.textContent = (result\.signwell\?\.message[^;]+);/)?.[1];
  assert.ok(expression);
  for(const message of ['Signature request sent.',
    'This document is already fully signed. No new invitation was sent.',
    'This signing request has ended. No new invitation was sent.']){
    assert.equal(vm.runInNewContext(expression,{result:{status:'ok',signwell:{message}}}),message);
  }
  assert.equal(vm.runInNewContext(expression,{result:{message:'Legacy confirmation'}}),'Legacy confirmation');
  assert.equal(vm.runInNewContext(expression,{result:{}}),'Signature request sent.');
});

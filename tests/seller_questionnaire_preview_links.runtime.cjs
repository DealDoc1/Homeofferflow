const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const nodes=Object.fromEntries(['preview','openPreview','downloadPreview'].map(id=>[id,{
 attributes:{},setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this.attributes[k];}
}]));
const context={window:{},document:{getElementById:id=>nodes[id]}};
const script=fs.readFileSync(path.join(root,'assets/seller-disclosure-questionnaire.js'),'utf8');
vm.runInNewContext(script,context);
const set=context.window.hofSellerQuestionnaire.setPreviewSource;
for(const url of ['blob:fictional-pdf','/api/admin-dashboard?seller_review_pdf=fictional-session']){
 set(url);assert.equal(nodes.preview.attributes.src,url);assert.equal(nodes.openPreview.attributes.href,url);assert.equal(nodes.downloadPreview.attributes.href,url);
 set('');assert.deepEqual(nodes.preview.attributes,{});assert.deepEqual(nodes.openPreview.attributes,{});assert.deepEqual(nodes.downloadPreview.attributes,{});
}
const html=fs.readFileSync(path.join(root,'seller-review.html'),'utf8');
assert.match(html,/id="openPreview" target="_blank" rel="noopener noreferrer"/);
assert.match(html,/id="downloadPreview" download="Seller_Disclosure.pdf"/);
assert.match(html,/hofSellerQuestionnaire\.setPreviewSource\('\/api\/admin-dashboard\?seller_review_pdf='/);
assert.match(script,/function invalidatePreview\(\)[\s\S]*?setPreviewSource\(''\)/);
assert.match(script,/URL\.revokeObjectURL\(previewUrl\); previewUrl=''/);
console.log('PDF open/download links share the verified preview; edits remove all stale sources.');

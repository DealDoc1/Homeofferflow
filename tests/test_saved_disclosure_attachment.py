from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SavedDisclosureAttachmentTests(unittest.TestCase):
    def test_selection_helper_cache_bust_reaches_installed_shell(self):
        html=(ROOT/'index.html').read_text()
        worker=(ROOT/'service-worker.js').read_text()
        asset='/assets/saved-disclosure-attachment.js?v=20261022-summary1'
        self.assertIn(asset,html)
        self.assertIn("'"+asset+"'",worker)
        self.assertIn("homeofferflow-shell-v129",worker)

    def test_selected_reviewed_disclosure_shows_bound_parties_without_exposing_email(self):
        script = r'''
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
function element(){return {children:[],hidden:true,style:{},dataset:{},replaceChildren(){this.children=[]},appendChild(child){this.children.push(child);return child},addEventListener(){},setAttribute(){}}}
const boxes=new Map([['purchaseDisclosureSelection',element()],['purchaseDisclosureReview',element()]]);
const state={data:{_hofOfferId:'offer',address:'123 QA Road',city:'Dallas',state:'TX',zip:'75201',purchaseSellerDisclosureId:'draft',purchaseSellerDisclosureFingerprint:'a'.repeat(64),purchaseSellerDisclosureSummary:{ownerId:'owner',propertyAddress:'123 QA Road, Dallas, TX 75201',recipients:[{role:'Seller',name:'<img src=x>',email:'seller@example.test'},{role:'Buyer',name:'QA Buyer',email:'buyer@example.test'}]}}};
const window={hofAuth:{session:{user:{id:'owner'}}}};
const document={getElementById:id=>boxes.get(id),createElement:tag=>({...element(),tag})};
const context={window,document,state};vm.runInNewContext(fs.readFileSync('assets/saved-disclosure-attachment.js','utf8'),context);
window.hofRenderPurchaseDisclosureSelection();
for(const box of boxes.values()){
  assert.equal(box.hidden,false);
  const paragraphs=box.children.filter(child=>child.tag==='p');
  assert.equal(paragraphs.length,2);
  assert.match(paragraphs[0].textContent,/123 QA Road, Dallas, TX 75201/);
  assert.match(paragraphs[1].textContent,/<img src=x>/);
  assert.match(paragraphs[1].textContent,/Buyer receipt acknowledgment: QA Buyer/);
  assert.doesNotMatch(paragraphs.map(child=>child.textContent).join(' '),/@example\.test/);
  assert.equal(paragraphs[0].innerHTML,undefined,'untrusted summary text is assigned as text, never markup');
}
state.data.purchaseSellerDisclosureSummary.ownerId='another-owner';
window.hofRenderPurchaseDisclosureSelection();
for(const box of boxes.values()){assert.equal(box.hidden,true);assert.equal(box.children.length,0)}
'''
        result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_reviewed_choice_and_preview_contract_never_imply_signature_completion(self):
        script = r'''
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict'),ctx={window:{}};
vm.runInNewContext(fs.readFileSync('assets/saved-disclosure-attachment.js','utf8'),ctx);
const {eligible,validatePreview}=ctx.window.hofSavedDisclosureAttachment;
const property={address:'123 QA Road',city:'Dallas',state:'TX',zip:'75201'};
const reviewed={id:'draft',property_address:'123 QA Road, Dallas, TX 75201',status:'draft',buyer_names:[],seller_review_attested:true};
assert.equal(eligible(reviewed,property),true);
for(const change of [{seller_review_attested:false},{signature_offer_id:'other'},{signature_packet_id:'other'},{buyer_names:['buyer']},{signwell_document_id:'sent'},{property_address:'123 QA Road Apt 2, Dallas, TX 75201'}])assert.equal(eligible({...reviewed,...change},property),false);
assert.equal(eligible({...reviewed,status:'signed',signwell_document_id:'signed'},property),true);
const preview={previewOnly:true,signatureRequestCreated:false,disclosureId:'draft',contentFingerprint:'a'.repeat(64),reviewRevision:'version',pdfBase64:'JVBERg==',recipients:[{role:'Buyer'},{role:'Seller'}]};
validatePreview(preview,'draft');
for(const change of [{previewOnly:false},{signatureRequestCreated:true},{disclosureId:'other'},{contentFingerprint:'bad'},{pdfBase64:''},{recipients:[{role:'Buyer'}]}])assert.throws(()=>validatePreview({...preview,...change},'draft'),/could not be confirmed/);
'''
        result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_address_duplicates_and_existing_upload_limits_use_real_helpers(self):
        script = r'''
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const context={window:{}};
vm.runInNewContext(fs.readFileSync('assets/saved-disclosure-attachment.js','utf8'),context);
const {matches,validateAddition}=context.window.hofSavedDisclosureAttachment;
const property={address:'123 QA Road',city:'Dallas',state:'TX',zip:'75201'};
assert.equal(matches('123 QA Road, Dallas, TX 75201',property),true);
assert.equal(matches('123 QA Road Apt 2, Dallas, TX 75201',property),false);
const doc={name:'disclosure.pdf',size:1024,base64:'JVBERg==',type:'seller_disclosure',homeOfferFlowDisclosureReceipt:{sourceDisclosureId:'one'}};
validateAddition([],doc);
assert.throws(()=>validateAddition([doc],doc),/already included/);
assert.throws(()=>validateAddition([{type:'seller_disclosure',name:'other.pdf'}],doc),/already includes/);
assert.throws(()=>validateAddition(Array.from({length:5},(_,i)=>({name:String(i)})),doc),/limit/);
assert.throws(()=>validateAddition([],{...doc,size:3*1024*1024}),/limit/);
assert.throws(()=>validateAddition([{size:2.5*1024*1024}],doc),/limit/);
assert.throws(()=>validateAddition([],{...doc,base64:''}),/could not/);
'''
        result = subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_receipt_metadata_survives_both_generation_paths_and_checkout_snapshot(self):
        html=(ROOT/'index.html').read_text()
        self.assertEqual(html.count('homeOfferFlowDisclosureReceipt:d.homeOfferFlowDisclosureReceipt'),2)
        self.assertIn('/assets/saved-disclosure-attachment.js',html)
        self.assertIn('Use a saved seller disclosure',html)
        placement=(ROOT/'assets/uploaded-pdf-signing-placement.js').read_text()
        self.assertIn('homeOfferFlowDisclosureReceipt:source.homeOfferFlowDisclosureReceipt',placement)
        self.assertIn('Buyer acknowledgments included automatically',placement)

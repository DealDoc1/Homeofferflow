"""Execute the actual draft writer with server-state and race doubles."""
import json
from pathlib import Path
import subprocess
import unittest

HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
SOURCE = HTML[HTML.index('  function cleanOfferDraftData('):HTML.index('  function setFeedbackStatus(')]


class OfferAutosaveRuntimeTests(unittest.TestCase):
    def run_save(self, row=None, race=False, new=False, error=None):
        config = dict(row=row or {'id': 'offer', 'status': 'Draft', 'last_updated': 'version-1'},
                      race=race, new=new, error=error)
        script = 'const config=' + json.dumps(config) + ';\n' + r'''
        const assert = require('node:assert/strict');
        const calls = [], notices=[];
        const state = {data:{userType:'agent',address:'QA property',buyer1:'QA buyer',price:400000,
          _hofOfferId:config.new ? null : 'offer',_hof_signature_delivery:{private:'must not copy'},
          signwell:{document_id:'old-document'},generatedAt:'old-date'}};
        const hofAuth = {session:{user:{id:'owner'},access_token:'test-token'}};
        let __hofCloudDraftSaveNeedsCopy = false;
        const collectAllData=()=>{}, getVal=()=>'', getRadio=()=>'', moneyNumber=v=>Number(v)||0;
        const updateSaveStatus=text=>notices.push(text);
        const console={warn:()=>{}};
        const window={hofSaveAgentOfferDraft:async(offerId,offer)=>{
          calls.push({offerId,offer});
          if(config.error){const error=new Error('save failed');error.code=config.error;throw error;}
          if(config.race)throw new Error('concurrent update');
          const row=config.row||{}, data=row.offer_data||{};
          const status=String(row.status||'Draft').toLowerCase();
          const prepared=!!(row.generated_at||row.signwell_document_id||data.generatedAt||data.generated_at||
            data.signwellDocumentId||data.signwell_document_id||data.signwell?.document_id||data.signwell?.response?.id||
            Object.prototype.hasOwnProperty.call(data,'_hof_signature_delivery')||!['draft','generation failed'].includes(status));
          if(prepared)return {id:offerId,saved:false,copyRequired:true};
          return {id:offerId||'new-offer',saved:true,created:!offerId};
        }};
        ''' + SOURCE + r'''
        (async()=>{
          const saved=await saveOfferDraftToSupabase();
          const cleaned=cleanOfferDraftData({...state.data,repairsText:'Keep agreed repairs',
             signwellRecipientStatuses:['signed'],packetGenerationError:'old'});
          assert.equal(cleaned.repairsText,'Keep agreed repairs');
          for(const key of ['_hof_signature_delivery','signwell','generatedAt','signwellRecipientStatuses','packetGenerationError'])
            assert.equal(key in cleaned,false,key);
          process.stdout.write(JSON.stringify({calls,notices,saved,copy:__hofCloudDraftSaveNeedsCopy}));
        })();
        '''
        return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)

    def test_draft_update_never_writes_signing_state_and_is_version_checked(self):
        result = self.run_save()
        update = result['calls'][0]
        self.assertEqual(update['offerId'], 'offer')
        self.assertNotIn('user_id', update['offer'])
        self.assertNotIn('last_updated', update['offer'])
        for key in ('status', 'signwell_document_id', 'signwell_status', 'generated_at'):
            self.assertNotIn(key, update['offer'])
        self.assertNotIn('_hof_signature_delivery', update['offer']['offer_data'])
        self.assertTrue(result['saved'])

    def test_server_signed_packet_wins_over_stale_draft_tab(self):
        for row in ({'status': 'Buyer Signed'}, {'status': 'Generated'},
                    {'status': 'Draft', 'signwell_document_id': 'doc'},
                    {'status': 'Draft', 'offer_data': {'signwell': {'response': {'id': 'doc'}}}},
                    {'status': 'Draft', 'offer_data': {'_hof_signature_delivery': {}}}):
            with self.subTest(row=row):
                result = self.run_save(row)
                self.assertEqual(len(result['calls']), 1)
                self.assertTrue(result['copy'])
                self.assertIsNone(result['saved'])
                self.assertEqual(result['notices'], [])

    def test_write_race_never_reports_saved(self):
        result = self.run_save(race=True)
        self.assertIsNone(result['saved'])
        self.assertEqual(result['notices'], [])

    def test_new_draft_does_not_inherit_receipts(self):
        call = self.run_save(new=True)['calls'][0]
        self.assertIsNone(call['offerId'])
        self.assertNotIn('_hof_signature_delivery', call['offer']['offer_data'])

    def test_database_packet_protection_has_specific_recovery(self):
        self.assertTrue(self.run_save(error='55000')['copy'])

    def test_resuming_signed_offer_opens_one_new_clean_editable_copy(self):
        helpers = SOURCE[:SOURCE.index('  async function saveOfferDraftToSupabase(')]
        flows = HTML[HTML.index('  function beginOfferOpenRequest('):HTML.index('  async function reuseOfferTerms(')]
        script = r'''
        const assert=require('node:assert/strict');
        const state={data:{_hof_signature_delivery:{stale:true},generatedAt:'stale'}};
        const hofAuth={session:{user:{id:'owner'}},role:'agent'};
        const source={id:'signed',status:'Buyer Signed',role:'agent',property_address:'QA',
          offer_data:{price:400000,repairsText:'Agreed repairs',_hof_signature_delivery:{receipt:'keep original'},
            signwellDocumentId:'original',generatedAt:'yesterday',uploadedDisclosureDocs:['private attachment']}};
        const original=JSON.stringify(source); const copies=[];
        const copy={id:'copy',status:'Draft',role:'agent',property_address:'QA',
          offer_data:{price:400000,repairsText:'Agreed repairs',_hofOfferId:'copy'}};
        const getOfferById=async id=>id==='signed'?source:copy;
        const resetUploadedDisclosureDraftForOffer=()=>{},setAudience=()=>{},closeAccountDashboard=()=>{},
          openWizard=()=>{},openSavedOfferInterview=()=>{},setTimeout=()=>{},logOfferEvent=async()=>{},loadMyOffers=async()=>{};
        const window={confirm:()=>{throw Error('No confirmation required');},
          hofDuplicateAgentOffer:async id=>{copies.push(id);return {id:'copy',copiedFromOfferId:id};}};
        ''' + helpers + flows + r'''
        (async()=>{
          await resumeOffer('signed');
          assert.deepEqual(copies,['signed']);
          assert.equal(JSON.stringify(source),original);
          assert.equal(state.data.repairsText,'Agreed repairs');
          assert.equal(state.data._hofOfferId,'copy');
          assert.equal('_hof_signature_delivery' in state.data,false);
        })().catch(e=>{console.error(e);process.exitCode=1;});
        '''
        subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)

    def test_recovery_keeps_edits_and_does_not_start_overlapping_saves(self):
        helpers = SOURCE[:SOURCE.index('  async function saveOfferDraftToSupabase(')]
        flows = HTML[HTML.index('  function showCloudSaveFailure()'):HTML.index('  function getDraftSnapshot()')]
        script = r'''
        const assert=require('node:assert/strict'); const window={};
        const hofAuth={session:{user:{id:'owner'}}};
        const state={data:{address:'QA property',_hofOfferId:'signed',repairsText:'Revised terms',
          _hof_signature_delivery:{receipt:'original'},signwellDocumentId:'original'}};
        let __hofCloudDraftSaveNeedsCopy=true,__hofCloudDraftSaveInFlight=false,
          __hofCloudDraftSaveQueued=false,__hofSaveTimer=null,release;
        const element={innerHTML:'',classList:{add:()=>{}}};
        const document={getElementById:()=>element}; const clearTimeout=()=>{},setTimeout=()=>0,
          updateSaveStatus=()=>{},logOfferEvent=()=>{},getVal=()=>'',moneyNumber=()=>0;
        const writes=[];
        const saveOfferDraftToSupabase=async()=>{
          writes.push({...state.data}); await new Promise(resolve=>{release=resolve;});
          return {id:'new'};
        };
        ''' + helpers + flows + r'''
        (async()=>{
          showCloudSaveFailure(); assert.ok(element.innerHTML.includes('Save changes as a new draft'));
          const pending=window.saveOfferChangesAsNewDraft();
          await window.retryCloudDraftSave();
          assert.equal(writes.length,1);
          assert.equal(writes[0]._hofOfferId,null);
          assert.equal(writes[0].repairsText,'Revised terms');
          assert.equal('_hof_signature_delivery' in writes[0],false);
          assert.equal('signwellDocumentId' in writes[0],false);
          release(); await pending; assert.equal(__hofCloudDraftSaveInFlight,false);
        })().catch(e=>{console.error(e);process.exitCode=1;});
        '''
        subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()

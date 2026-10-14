import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from lib import amendment_signing_qa as qa, trec_39_11

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tests/fixtures/trec_39_11_source.pdf'


class AmendmentSigningQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_bytes()
        cls.packet, cls.fields, cls.manifest = qa.build_packet(cls.source)

    def test_all_signer_counts_and_every_amendment_choice_are_covered(self):
        cases = list(qa.cases())
        self.assertEqual({(len(d['buyer_names']), len(d['seller_names'])) for _, d in cases},
                         {(1, 1), (1, 2), (2, 1), (2, 2)})
        self.assertEqual(set().union(*(set(d['changes']) for _, d in cases)), set(trec_39_11.CHANGE_MARKS))
        self.assertTrue(all(not {'option_extension', 'option_waiver'} <= set(d['changes']) for _, d in cases))
        for _, data in cases:
            for key in ('repairs_text', 'other_modifications'):
                self.assertLessEqual(len(data.get(key, '')), 3000)

    def test_every_box_matches_the_current_production_map_with_only_qa_remapping(self):
        for (name, data), manifest in zip(qa.cases(), self.manifest):
            original = trec_39_11.build_signwell_fields_trec3911(data)[0]
            actual = [f for f in self.fields[0] if f['api_id'].startswith(name + '_')]
            expected = [{**f, 'api_id': name + '_' + f['api_id'],
                         'page': f['page'] + manifest['output_pages'][0] - 1,
                         'recipient_id': 'qa_b' if f['recipient_id'] in {'2', '4'} else 'qa_a'} for f in original]
            self.assertEqual(actual, expected)
        self.assertEqual(len({f['api_id'] for f in self.fields[0]}), len(self.fields[0]))

    def test_long_unicode_has_continuation_initials_for_all_selected_parties(self):
        case = self.manifest[-1]
        self.assertGreater(len(case['output_pages']), 1)
        initials = [f for f in self.fields[0] if f['type'] == 'initials']
        self.assertEqual({f['page'] for f in initials}, set(case['output_pages'][1:]))
        self.assertEqual(len(initials), 4 * (len(case['output_pages']) - 1))
        text = ' '.join(p.extract_text() or '' for p in PdfReader(BytesIO(self.packet)).pages)
        for phrase in ('Élodie Hernández', 'Zoë O’Connell', 'José Muñoz', 'façade'):
            self.assertIn(phrase, text)

    def test_signed_copy_is_static_source_is_unchanged_and_fields_are_bounded(self):
        reader = PdfReader(BytesIO(self.packet))
        self.assertFalse(reader.get_fields())
        self.assertTrue(all(not any(a.get_object().get('/Subtype') == '/Widget' for a in p.get('/Annots', [])) for p in reader.pages))
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), qa.SOURCE_SHA256)
        for field in self.fields[0]:
            self.assertTrue(field['required'])
            self.assertGreaterEqual(field['x'], 0); self.assertGreaterEqual(field['y'], 0)
            self.assertLessEqual(field['x'] + field['width'], 816)
            self.assertLessEqual(field['y'] + field['height'], 1056)
            self.assertIn(field['page'], range(1, len(reader.pages) + 1))

    def test_payload_is_fixed_parallel_nonbinding_and_rejects_map_revision_changes(self):
        payload = qa.build_payload(self.packet, self.fields, qa.REVIEWED_SOURCE_COMMIT)
        self.assertTrue(payload['test_mode']); self.assertFalse(payload['apply_signing_order'])
        self.assertFalse(payload['reminders']); self.assertFalse(payload['with_signature_page'])
        self.assertEqual({r['email'] for r in payload['recipients']}, {'andrewchri@gmail.com', 'brewbqinfo@gmail.com'})
        self.assertEqual(base64.b64decode(payload['files'][0]['file_base64']), self.packet)
        changed = json.loads(json.dumps(self.fields)); changed[0][0]['x'] += 1
        with self.assertRaises(ValueError): qa.build_payload(self.packet, changed, qa.REVIEWED_SOURCE_COMMIT)
        with self.assertRaises(ValueError): qa.build_payload(self.packet, self.fields, '0' * 40)
        with self.assertRaises(ValueError): qa.build_packet(b'%PDF wrong source')
        with patch.object(trec_39_11, 'RENDER_REVISION', 'future-unreviewed'):
            with self.assertRaises(ValueError): qa.build_packet(self.source)

    def test_owner_only_ui_and_request_shape_are_preserved(self):
        html = (ROOT / 'index.html').read_text()
        admin = (ROOT / 'api/admin-dashboard.py').read_text()
        start = admin.index('if data.get("action") in {"send_amendment_signing_test", "check_amendment_signing_test"}')
        self.assertLess(admin.index('if not asyncio.run(_is_platform_admin(user)):', admin.index('def do_POST')), start)
        self.assertIn('if set(data) != {"action"}', admin[start:start + 550])
        self.assertIn("onclick=\"runPurchaseSigningTest(true, this, 'amendment')\"", html)
        self.assertIn('adminAmendmentSigningTestStatus', html)
        owner_start = html.index("${['andrewchri@gmail.com', 'andrew@ondemanddfw.com'].includes")
        self.assertGreater(html.index('<summary>Amendment signing test</summary>'), owner_start)

    def test_actual_admin_ui_routes_each_scope_and_keeps_recorded_attempts_disabled(self):
        result = subprocess.run(['node', '-e', r'''
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
const start=html.indexOf('  async function runPurchaseSigningTest(');
const source=html.slice(start,html.indexOf('  async function loadAdminDashboard(',start));
(async()=>{
 for(const scope of ['purchase','showing','amendment']){
  const prefix=scope[0].toUpperCase()+scope.slice(1);
  for(const phase of ['not_started','started','created','unconfirmed']){
   const send={disabled:false,textContent:'Send'}, status={textContent:''}, check={disabled:false,textContent:'Check'};
   let action;
   const c={hofAuth:{session:{access_token:'FICTIONAL'}}, document:{getElementById:id=>id.endsWith('Send')?send:status},
     fetch:async(url,options)=>{assert.equal(url,'/api/admin-dashboard'); action=JSON.parse(options.body);
       return {ok:true,json:async()=>({signingTest:{phase,message:'Safe status'}})};}};
   vm.createContext(c);vm.runInContext(source,c);
   await c.runPurchaseSigningTest(false,check,scope);
   assert.deepEqual(Object.keys(action),['action']);assert.equal(action.action,`check_${scope}_signing_test`);
   assert.equal(send.disabled,phase!=='not_started');assert.equal(check.disabled,false);
   await c.runPurchaseSigningTest(true,send,scope);
   assert.equal(action.action,`send_${scope}_signing_test`);assert.equal(send.disabled,phase!=='not_started');
  }
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
'''], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

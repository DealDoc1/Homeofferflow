from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PlatformSourceUploadButtonRuntimeTests(unittest.TestCase):
    def test_success_failure_and_double_click_release_the_correct_ui_state(self):
        script = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
const section=html.split('<script id="hof-platform-source-intake-v1">')[1];
const start=section.indexOf('  async function upload()');
const end=section.indexOf('  const priorDashboard',start);
assert.ok(start>=0 && end>start && end-start<8000,'bounded upload handler');
const source=section.slice(start,end);
async function check(ok){
 const button={disabled:false,textContent:'Save library revision',attrs:{},setAttribute(k,v){this.attrs[k]=v}};
 const file={name:'TXR1101.pdf',type:'application/pdf',size:10,arrayBuffer:async()=>new Uint8Array([37,80,68,70]).buffer};
 const fields={'#platformSourceStatus':{},'#platformSourceUploadButton':button,'#platformSourceFile':{files:[file],value:'selected'},
   '#platformSourceBrokerage':{value:'fictional-host'},'#platformSourceForm':{value:'TXR-1101'},
   '#platformSourceRevision':{value:'06-15-26'},'#platformSourceAttestation':{checked:true}};
 const card={querySelector:s=>fields[s]};let calls=0;
 const context={root:{hofAuth:{session:{access_token:'fictional'}}},window:{},document:{getElementById:()=>card},
   BUCKET_LIMIT:100,sourceFingerprint:async()=>'a'.repeat(64),toBase64:()=>'JVBERg==',
   console:{error(){}},fetch:async(url,init)=>{calls++;assert.equal(url,'/api/admin-dashboard');
     assert.equal(JSON.parse(init.body).action,'upload_platform_form_source');return {ok,json:async()=>ok?{source:{formCode:'TXR-1101',sourceRevision:'06-15-26',workflowActivated:false}}:{error:'fixture failure'}};}};
 vm.runInNewContext(source+';root.upload=upload;',context);
 const pending=context.root.upload();await context.root.upload();await pending;
 assert.equal(calls,1);assert.equal(button.disabled,false);assert.equal(button.attrs['aria-busy'],'false');
 assert.equal(button.textContent,'Save library revision');
 if(ok){assert.match(fields['#platformSourceStatus'].textContent,/saved privately/);assert.equal(fields['#platformSourceFile'].value,'');assert.equal(fields['#platformSourceAttestation'].checked,false);}
 else {assert.equal(fields['#platformSourceStatus'].textContent,'We couldn’t save that form-library revision. Please try again.');assert.equal(fields['#platformSourceFile'].value,'selected');assert.equal(fields['#platformSourceAttestation'].checked,true);}
}
(async()=>{await check(true);await check(false)})().catch(e=>{console.error(e);process.exitCode=1});
'''
        result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr[-2500:])

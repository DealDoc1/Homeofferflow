"""Execute the actual recovery actions; no database/provider/browser network."""
import json
from pathlib import Path
import subprocess
import unittest

HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
START = HTML.index('  function packetGenerationFailureDetails(err)')
END = HTML.index('  window.hofUploadedDisclosureDocs', START)


class PacketUsageRecoveryUiTests(unittest.TestCase):
    def run_recovery(self, code):
        script = '''
const elements = Object.fromEntries(['packetGenerationRecoveryNotice', 'packetGenerationRecoveryMessage',
 'packetGenerationRetryButton'].map(id=>[id,{style:{},textContent:'',scrollIntoView:()=>{}}]));
const document={getElementById:id=>elements[id]};
const calls=[];
const openAccountDashboard=async options=>calls.push(options.tab);
const logOfferEvent=async()=>{};
const generateSubscribedPacket=async()=>calls.push('generate');
const state={data:{}}; const hofAuth={};
'''
        script += HTML[START:END]
        script += '\nconst failure=packetGenerationFailureDetails({code:' + json.dumps(code) + ',message:"Unconfirmed request"});'
        script += '''
showPacketGenerationRecoveryNotice(failure);
elements.packetGenerationRetryButton.onclick().then(()=>process.stdout.write(JSON.stringify({
 calls, text:elements.packetGenerationRecoveryMessage.textContent,
 button:elements.packetGenerationRetryButton.textContent, category:failure.category})));
'''
        return json.loads(subprocess.run(['node','-e',script],capture_output=True,text=True,check=True).stdout)

    def test_uncertain_or_busy_packet_opens_saved_offers_instead_of_generating_again(self):
        for code in ('packet_generation_busy','packet_generation_unconfirmed'):
            result=self.run_recovery(code)
            self.assertEqual(result['calls'], ['offers'])
            self.assertEqual(result['button'], 'View My Offers')
            self.assertNotIn('No packet credit', result['text'])

    def test_allowance_issue_opens_account_without_starting_a_purchase(self):
        result=self.run_recovery('packet_allowance_unavailable')
        self.assertEqual(result['calls'], ['dashboard'])
        self.assertEqual(result['button'], 'Open Account')

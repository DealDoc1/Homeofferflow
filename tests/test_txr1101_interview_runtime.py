from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Txr1101InterviewRuntimeTests(unittest.TestCase):
    def test_actual_answer_mapper_and_async_opening_guards(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('txr1101_interview.runtime.cjs'))],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_private_document_viewer_account_isolation(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('standalone_document_viewer.runtime.cjs'))],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_asset_and_saved_queue_are_connected_to_the_sale_path(self):
        html = (ROOT / 'index.html').read_text()
        self.assertIn('src="/assets/txr1101-interview.js"', html)
        self.assertIn('href="/assets/txr1101-interview.css"', html)
        start = html.index('      sale_listing: {', html.index('    const packages = {'))
        end = html.index('      lease_representation:', start)
        self.assertIn("openRelationshipDraft('hofOpenTxr1101Draft'", html[start:end])
        self.assertIn('data-edit-listing=', html)
        self.assertIn("['draft', 'failed'].includes(agreement.status)", html)
        self.assertIn('!agreement.signwell_document_id', html)
        self.assertIn("window.startListingAgreement = async", html)

    def test_answer_limits_match_the_server_contract(self):
        from lib.txr_1101 import TEXT_LIMITS
        result = subprocess.run(['node', '-e', 'console.log(JSON.stringify(require("./assets/txr1101-interview.js").textLimits))'],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        import json
        self.assertEqual(json.loads(result.stdout), TEXT_LIMITS)

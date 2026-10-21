"""New page markup must not depend on unversioned, browser-cached partner code."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='?v=20261021-portrait1'


class PartnerAssetVersionsTests(unittest.TestCase):
    def test_both_pages_version_the_shared_helper_and_stylesheet(self):
        for page in ('index.html','directory.html'):
            html=(ROOT/page).read_text()
            for asset in ('partner-profile.js','partner-profile.css'):
                self.assertIn('/assets/'+asset+VERSION+'"',html)
                self.assertNotIn('/assets/'+asset+'"',html)
        html=(ROOT/'index.html').read_text()
        for asset in ('inspection-partners.js','insurance-partners.js'):
            self.assertIn('/assets/'+asset+VERSION+'"',html)

    def test_installed_shell_prewarms_the_same_versioned_partner_assets(self):
        worker=(ROOT/'service-worker.js').read_text()
        for asset in ('partner-profile.js','partner-profile.css','inspection-partners.js','insurance-partners.js'):
            self.assertIn("'/assets/"+asset+VERSION+"'",worker)
            self.assertNotIn("'/assets/"+asset+"'",worker)

    def test_cost_saving_asset_cache_policy_remains_unchanged(self):
        settings=json.loads((ROOT/'vercel.json').read_text())
        group=next(rule for rule in settings['headers'] if rule['source']=='/assets/(.*)')
        self.assertEqual(group['headers'],[{'key':'Cache-Control','value':'public, max-age=900, s-maxage=86400, stale-while-revalidate=604800'}])

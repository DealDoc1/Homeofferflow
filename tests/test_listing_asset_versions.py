"""Interview HTML and the installed shell load the exact reviewed asset bytes."""
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ('txr1101-interview.css', 'txr1102-interview.js', 'txr1101-interview.js')


def versioned_url(name):
    digest = hashlib.sha256((ROOT / 'assets' / name).read_bytes()).hexdigest()[:16]
    return '/assets/' + name + '?v=' + digest


class ListingAssetVersionsTests(unittest.TestCase):
    def test_page_versions_are_bound_to_actual_asset_content(self):
        html = (ROOT / 'index.html').read_text()
        for name in ASSETS:
            with self.subTest(asset=name):
                self.assertTrue('"' + versioned_url(name) + '"' in html,
                                'Page must load content-versioned ' + name)
                self.assertFalse('"/assets/' + name + '"' in html,
                                 'Page must not load unversioned ' + name)

    def test_offline_shell_prewarms_the_identical_versioned_urls(self):
        worker = (ROOT / 'service-worker.js').read_text()
        for name in ASSETS:
            with self.subTest(asset=name):
                self.assertTrue("'" + versioned_url(name) + "'" in worker,
                                'Worker must prewarm content-versioned ' + name)
                self.assertFalse("'/assets/" + name + "'" in worker,
                                 'Worker must not prewarm unversioned ' + name)

    def test_deferred_lease_model_still_precedes_shared_interview_engine(self):
        html = (ROOT / 'index.html').read_text()
        references = re.findall(r'<script defer src="([^"]+)"', html)
        for name in ASSETS[1:]:
            self.assertTrue(versioned_url(name) in references, 'Missing versioned script ' + name)
        self.assertLess(references.index(versioned_url('txr1102-interview.js')),
                        references.index(versioned_url('txr1101-interview.js')))

    def test_local_fixture_uses_the_same_real_asset_urls(self):
        with tempfile.TemporaryDirectory(prefix='hof-listing-asset-qa-') as folder:
            result = subprocess.run(['node', str(ROOT / 'scripts/qa/txr1101_interview_fixture.cjs'), folder],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            fixture = (Path(folder) / 'index.html').read_text()
            for name in ASSETS:
                self.assertTrue('"' + versioned_url(name) + '"' in fixture,
                                'Local fixture must use actual versioned ' + name)

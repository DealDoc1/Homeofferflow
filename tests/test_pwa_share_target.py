import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'manifest.webmanifest').read_text(encoding='utf-8'))
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
SHARE = (ROOT / 'assets' / 'pwa-share-target.js').read_text(encoding='utf-8')


class PwaShareTargetTests(unittest.TestCase):
    def test_manifest_declares_a_get_share_target_without_extra_services(self):
        target = MANIFEST['share_target']
        self.assertEqual(target['action'], '/?pwa_share=1')
        self.assertEqual(target['method'], 'GET')
        self.assertEqual(target['params'], {'title': 'title', 'text': 'text', 'url': 'url'})

    def test_share_context_is_loaded_as_escaped_dom_text_and_external_links_are_safe(self):
        self.assertIn('/assets/pwa-share-target.js', INDEX)
        self.assertIn("params.get('pwa_share') !== '1'", SHARE)
        self.assertIn('textContent', SHARE)
        self.assertIn("/^https?:\\/\\//i.test(sharedUrl)", SHARE)
        self.assertIn("rel = 'noopener noreferrer'", SHARE)
        self.assertIn('document.body', SHARE)


if __name__ == '__main__':
    unittest.main()

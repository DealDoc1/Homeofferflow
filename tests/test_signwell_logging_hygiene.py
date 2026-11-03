import unittest
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SIGNWELL_ROUTES = (
    ROOT / "api" / "fill-pdf.py",
    ROOT / "api" / "fill_pdf_20_19_staging.py",
)


class SignWellLoggingHygieneTests(unittest.TestCase):
    def test_verbose_signwell_diagnostics_are_explicitly_opt_in(self):
        for route in SIGNWELL_ROUTES:
            source = route.read_text(encoding="utf-8")
            self.assertIn('SIGNWELL_DEBUG_LOGS = os.environ.get("SIGNWELL_DEBUG_LOGS", "false")', source)
            self.assertIn("def signwell_debug(label, payload, limit=3000):", source)
            self.assertNotIn('print("SIGNWELL DEBUG', source)
            self.assertNotIn('print("SIGNWELL RESPONSE BODY:', source)

    def test_failure_log_does_not_dump_signwell_response_body(self):
        for route in SIGNWELL_ROUTES:
            source = route.read_text(encoding="utf-8")
            self.assertNotIn('print("SIGNWELL RESPONSE STATUS:", r.status_code)', source)
            self.assertNotIn('print("SIGNWELL RESPONSE BODY:', source)
        # The production adapter no longer logs response bodies or requires
        # the removed create-and-send helper's particular log statement.
        adapter = (ROOT / 'lib/offer_signwell_delivery.py').read_text()
        self.assertNotIn('response.text', adapter)

    def test_rejected_create_logs_only_bounded_value_free_diagnostic(self):
        from lib.offer_signwell_delivery import deliver_offer_document
        from lib.signwell_rejections import SigningCreateRejected
        private = 'PRIVATE buyer@example.test https://private.test/key'
        response = SimpleNamespace(status_code=422, content=b'{}', json=lambda: {
            'errors': {'fields': [[{'height': [private]}]], private: private},
            'message': private,
        })
        with patch('lib.offer_signwell_delivery.httpx.post', return_value=response) as post, \
             patch('lib.offer_signwell_delivery.httpx.patch') as write, \
             patch('lib.offer_signwell_delivery.httpx.get') as read, \
             patch('builtins.print') as log:
            with self.assertRaises(SigningCreateRejected):
                deliver_offer_document(
                    {'id': 'qa-offer', 'user_id': 'qa-owner', 'offer_data': {}},
                    {'fields': [], 'recipients': [], 'metadata': {}}, {},
                    user_id='qa-owner', supabase_url='https://qa.example.test',
                    supabase_key=private, signwell_key=private)
        post.assert_called_once()
        self.assertTrue(post.call_args.kwargs['json']['draft'])
        write.assert_not_called()
        read.assert_not_called()
        log.assert_called_once()
        diagnostic = json.loads(log.call_args.args[0])
        self.assertEqual(diagnostic, {'event': 'signwell_create_rejected',
            'http_status': 422, 'category': 'signature_fields',
            'fields': ['fields.0.0.height']})
        self.assertNotIn('PRIVATE', log.call_args.args[0])


if __name__ == "__main__":
    unittest.main()

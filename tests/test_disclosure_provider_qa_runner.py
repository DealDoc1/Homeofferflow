"""Synthetic runner tests: no account credentials, email or network."""
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pypdf import PdfWriter, PdfReader
from scripts.qa import prepare_disclosure_provider_test as qa


class DisclosureProviderQARunnerTests(unittest.TestCase):
    def test_runner_binds_to_exact_reviewed_renderer_bytes(self):
        qa.validate_renderer()
        with patch.object(qa, 'REVIEWED_RENDER_FILES', {'lib/trec_seller_disclosure.py': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'renderer changed'):
                qa.validate_renderer()

    def specimens(self, root):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.add_blank_page(width=612, height=792)
        stream = BytesIO(); writer.write(stream); packet = stream.getvalue()
        rows = []
        for name in ['one-seller', 'two-sellers-water', 'unicode-overflow', 'unknown-responses']:
            (root / (name + '.pdf')).write_bytes(packet)
            rows.append({'case': name, 'pages': 2, 'packet_sha256': hashlib.sha256(packet).hexdigest(),
                         'fields': [{'api_id': 'same_original_id', 'page': 2, 'x': 80, 'y': 749,
                                     'width': 250, 'height': 26, 'type': 'signature',
                                     'required': True, 'recipient_id': '2' if name == 'unicode-overflow' else '1'}]})
        (root / 'manifest.json').write_text(json.dumps({'cases': rows}))

    def test_compact_packet_preserves_rectangles_remaps_pages_and_only_approved_recipients(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.specimens(root)
            packet, fields, cases = qa.build_packet(root)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 4)
        self.assertEqual([f['page'] for f in fields[0]], [1, 2, 3, 4])
        self.assertEqual([c['source_pages'] for c in cases], [[2]] * 4)
        self.assertEqual({f['recipient_id'] for f in fields[0]}, {'qa_a', 'qa_b'})
        self.assertEqual(len({f['api_id'] for f in fields[0]}), 4)
        for field in fields[0]:
            self.assertEqual([field[k] for k in ['x', 'y', 'width', 'height']], [80, 749, 250, 26])
            self.assertTrue(field['required'])

    def test_manifest_byte_mismatch_cannot_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.specimens(root)
            (root / 'one-seller.pdf').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                qa.build_packet(root)

    def test_payload_is_nonbinding_draft_parallel_fixed_inboxes_and_one_field_array(self):
        payload = qa.payload_for(b'fictional', [[]])
        self.assertTrue(payload['test_mode']); self.assertTrue(payload['draft'])
        self.assertFalse(payload['apply_signing_order']); self.assertFalse(payload['reminders'])
        self.assertFalse(payload['with_signature_page'])
        self.assertEqual({r['email'] for r in payload['recipients']},
                         {'andrewchri@gmail.com', 'brewbqinfo@gmail.com'})
        self.assertEqual(len(payload['files']), len(payload['fields']))
        self.assertEqual(base64.b64decode(payload['files'][0]['file_base64']), b'fictional')

    def test_existing_reservation_never_opens_provider_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'receipt.json').write_text('{}')
            with patch.object(qa.httpx, 'Client', side_effect=AssertionError('No network')):
                with self.assertRaises(FileExistsError):
                    qa.send_once(root, b'fictional', [[]], [], root / 'missing-key')

    def test_create_timeout_retains_reservation_and_deletes_only_temporary_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); key = root / 'existing-key'; key.write_text('fictional')
            with patch.object(qa.httpx, 'Client') as client:
                client.return_value.__enter__.return_value.post.side_effect = TimeoutError('fictional')
                with self.assertRaises(TimeoutError):
                    qa.send_once(root, b'fictional', [[]], [], key)
            self.assertFalse(key.exists())
            receipt = json.loads((root / 'receipt.json').read_text())
            self.assertEqual(receipt['phase'], 'create_requested')
            self.assertEqual(receipt['error_type'], 'TimeoutError')

    def test_provider_field_mismatch_keeps_draft_and_cannot_send(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); key = root / 'existing-key'; key.write_text('fictional')
            document = {'id': 'fictional-doc', 'test_mode': True,
                        'name': qa.payload_for(b'', [[]])['name'],
                        'metadata': {'qa_revision': qa.REVISION}, 'fields': [[]], 'recipients': []}
            with patch.object(qa.httpx, 'Client') as client:
                active = client.return_value.__enter__.return_value
                active.post.return_value.status_code = 201
                active.post.return_value.json.return_value = document
                active.get.return_value.status_code = 200
                active.get.return_value.json.return_value = document
                result = qa.send_once(root, b'fictional', [[]], [], key)
                active.post.assert_called_once()
            self.assertEqual(result['phase'], 'field_readback_mismatch')
            self.assertEqual(result['document_id'], 'fictional-doc')
            self.assertFalse(key.exists())

    def test_initial_send_uses_documented_route_after_exact_field_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); key = root / 'existing-key'; key.write_text('fictional')
            payload = qa.payload_for(b'fictional', [[]])
            document = {'id': 'fictional-doc', 'test_mode': True, 'status': 'Created',
                        'name': payload['name'], 'metadata': payload['metadata'],
                        'fields': payload['fields'], 'recipients': payload['recipients']}
            with patch.object(qa.httpx, 'Client') as client:
                active = client.return_value.__enter__.return_value
                active.post.return_value.status_code = 201
                active.post.return_value.json.return_value = document
                active.get.return_value.status_code = 200
                active.get.return_value.json.return_value = document
                result = qa.send_once(root, b'fictional', [[]], [], key)
                self.assertEqual(active.post.call_count, 2)
                self.assertEqual(active.post.call_args.args[0], qa.BASE_URL + 'fictional-doc/send')
                self.assertTrue(active.post.call_args.kwargs['json']['test_mode'])
            self.assertTrue(result['fields_verified']); self.assertEqual(result['phase'], 'sent')
            self.assertFalse(key.exists())

    def test_recovery_refuses_a_document_that_is_already_sent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); key = root / 'existing-key'; key.write_text('fictional')
            (root / 'receipt.json').write_text(json.dumps({'phase': 'sent', 'qa_revision': qa.REVISION}))
            with patch.object(qa.httpx, 'Client', side_effect=AssertionError('No network')):
                with self.assertRaisesRegex(ValueError, 'recorded rejected'):
                    qa.resume_existing(root, key)
            self.assertFalse(key.exists())

    def test_verified_rejected_draft_recovers_only_same_id_and_preserves_validation_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); key = root / 'existing-key'; key.write_text('fictional')
            packet, fields = b'fictional', [[]]
            (root / 'QA_ONLY_disclosure_execution.pdf').write_bytes(packet)
            (root / 'fields.json').write_text(json.dumps(fields))
            (root / 'receipt.json').write_text(json.dumps({
                'phase': 'send_unconfirmed', 'send_http_status': 422, 'qa_revision': qa.REVISION,
                'document_id': 'same-fictional-draft', 'packet_sha256': hashlib.sha256(packet).hexdigest(),
                'fields_sha256': hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()}))
            payload = qa.payload_for(packet, fields)
            document = {'id': 'same-fictional-draft', 'status': 'created', 'test_mode': True,
                        'name': payload['name'], 'metadata': payload['metadata'],
                        'fields': fields, 'recipients': payload['recipients']}
            with patch.object(qa.httpx, 'Client') as client:
                active = client.return_value.__enter__.return_value
                active.get.return_value.status_code = 200
                active.get.return_value.json.return_value = document
                active.post.return_value.status_code = 422
                active.post.return_value.json.return_value = {'errors': ['Fictional validation']}
                result = qa.resume_existing(root, key)
                active.post.assert_called_once()
                self.assertEqual(active.post.call_args.args[0], qa.BASE_URL + 'same-fictional-draft/send')
                self.assertTrue(active.post.call_args.kwargs['json']['test_mode'])
            self.assertEqual(result['phase'], 'send_rejected')
            self.assertIn('Fictional validation', result['validation']['errors'])
            self.assertTrue(result['resume_attempted'])
            self.assertFalse(key.exists())


if __name__ == '__main__':
    unittest.main()

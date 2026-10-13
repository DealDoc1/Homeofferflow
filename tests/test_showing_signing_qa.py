import hashlib
from io import BytesIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from lib import showing_signing_qa as qa
from lib.txr_1508 import build_signwell_fields_txr1508


class ShowingSigningQATests(unittest.TestCase):
    def setUp(self):
        output = BytesIO()
        c = Canvas(output, pagesize=(612, 792)); c.showPage(); c.save()
        self.source = output.getvalue()
        patched = patch.object(qa, 'SOURCE_SHA256', hashlib.sha256(self.source).hexdigest())
        patched.start(); self.addCleanup(patched.stop)

    def test_three_fixed_cases_use_only_two_inboxes_without_changing_geometry(self):
        packet, fields, cases = qa.build_packet(self.source)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 4)
        self.assertEqual(len(fields[0]), 21)
        self.assertEqual({f['recipient_id'] for f in fields[0]}, {'qa_a', 'qa_b'})
        self.assertEqual(len({f['api_id'] for f in fields[0]}), 21)
        for (name, data), manifest in zip(qa.cases(), cases):
            original = build_signwell_fields_txr1508(data, client_count=2, page_count=len(manifest['source_pages']))[0]
            output_fields = [f for f in fields[0] if f['api_id'].startswith(name + '_')]
            for a, b in zip(original, output_fields):
                self.assertEqual({k: v for k, v in a.items() if k not in {'api_id', 'recipient_id', 'page'}},
                                 {k: v for k, v in b.items() if k not in {'api_id', 'recipient_id', 'page'}})
                self.assertEqual(b['page'], a['page'] + manifest['output_pages'][0] - 1)
                self.assertEqual(b['recipient_id'], 'qa_b' if a['recipient_id'] == '2' else 'qa_a')

    def test_payload_is_nonbinding_parallel_and_has_no_added_signature_or_reminders(self):
        packet, fields, _ = qa.build_packet(self.source)
        payload = qa.build_payload(packet, fields, qa.REVIEWED_SOURCE_COMMIT)
        self.assertTrue(payload['test_mode']); self.assertFalse(payload['draft'])
        self.assertFalse(payload['apply_signing_order']); self.assertFalse(payload['reminders'])
        self.assertFalse(payload['with_signature_page'])
        self.assertNotIn('embedded_signing', payload)
        self.assertEqual({r['email'] for r in payload['recipients']}, {'andrewchri@gmail.com', 'brewbqinfo@gmail.com'})
        self.assertTrue(payload['name'].startswith(qa.DOCUMENT_PREFIX))
        self.assertEqual(hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest(), qa.FIELDS_SHA256)

    def test_source_and_changed_map_reject_before_any_send(self):
        with self.assertRaises(ValueError): qa.build_packet(b'not the reviewed source')
        packet, fields, _ = qa.build_packet(self.source)
        fields[0][0]['y'] += 1
        with self.assertRaises(ValueError): qa.build_payload(packet, fields, qa.REVIEWED_SOURCE_COMMIT)

    def test_fictional_answers_keep_each_representation_choice_explicit(self):
        cases = dict(qa.cases())
        self.assertEqual(cases['two_customer_broker']['other_broker_agreement'], ['no', 'no'])
        self.assertEqual(cases['two_customer_associate_mixed']['other_broker_agreement'], ['yes', 'no'])
        self.assertEqual(cases['two_customer_associate_mixed']['signer_plan'], 'associate_and_clients')
        self.assertEqual(cases['unicode_continuation']['signer_plan'], 'broker_and_clients')

    def test_unicode_names_are_lossless_and_source_bytes_are_not_modified(self):
        before = hashlib.sha256(self.source).hexdigest()
        packet, _, _ = qa.build_packet(self.source)
        text = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(packet)).pages)
        self.assertIn('Élodie Hernández', text); self.assertIn("Zoë O'Connell", text)
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), before)
        self.assertEqual(sum(a.get_object().get('/Subtype') == '/Widget' for p in PdfReader(BytesIO(packet)).pages for a in p.get('/Annots', [])), 0)

    def test_runtime_fixture_has_no_test_suite_import_or_key_input(self):
        source = Path('lib/showing_signing_qa.py').read_text()
        self.assertNotIn('from tests', source); self.assertNotIn('getpass', source)

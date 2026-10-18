from copy import deepcopy
from io import BytesIO
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from lib import listing_lead_signing_qa as qa


class ListingLeadSigningQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.packet,cls.fields,cls.cases=qa.build_packet()

    def test_actual_fixed_packet_contains_all_cases_and_only_two_test_recipients(self):
        self.assertEqual(len(PdfReader(BytesIO(self.packet)).pages),7)
        self.assertEqual([item['field_count'] for item in self.cases],[12,15,6,9])
        self.assertEqual(len({item['api_id'] for item in self.fields[0]}),42)
        self.assertEqual({item['recipient_id'] for item in self.fields[0]},{'qa_a','qa_b'})
        self.assertFalse(any('buyer' in item['api_id'].lower() for item in self.fields[0]))
        payload=qa.build_payload(self.packet,self.fields,qa.REVIEWED_SOURCE_COMMIT)
        self.assertIs(payload['draft'],True);self.assertIs(payload['test_mode'],True)
        for key in ('apply_signing_order','with_signature_page','reminders'):self.assertIs(payload[key],False)
        self.assertEqual({item['email'] for item in payload['recipients']},{'andrewchri@gmail.com','brewbqinfo@gmail.com'})

    def test_every_group_rule_and_explanation_is_bound_to_a_present_qa_field(self):
        fields={item['api_id']:item for item in self.fields[0]};groups,rules=qa.completion_controls()
        self.assertEqual(len(groups),4);self.assertEqual(len(rules),4)
        for group in groups:
            self.assertEqual(group['exact_value'],1);self.assertIs(group['required'],True)
            for key in group['checkbox_ids']:
                self.assertEqual(fields[key]['type'],'checkbox');self.assertEqual(fields[key]['recipient_id'],'qa_a')
                self.assertIs(fields[key]['required'],False);self.assertNotIn('value',fields[key])
        for rule in rules:
            self.assertIn(rule['target_id'],fields)
            for key in rule['action_field_ids']:
                self.assertEqual(fields[key]['type'],'text');self.assertIs(fields[key]['fixed_width'],True)
                self.assertEqual(fields[key]['recipient_id'],'qa_a')

    def test_changed_geometry_or_source_revision_cannot_create_payload(self):
        changed=deepcopy(self.fields);changed[0][0]['x']+=2
        with self.assertRaises(ValueError):qa.build_payload(self.packet,changed,qa.REVIEWED_SOURCE_COMMIT)
        with self.assertRaises(ValueError):qa.build_payload(self.packet,self.fields,'a'*40)
        with patch.object(qa,'LAYOUT_SHA256',''):
            with self.assertRaises(ValueError):qa.build_payload(self.packet,self.fields,qa.REVIEWED_SOURCE_COMMIT)

    def test_changed_printed_content_cannot_reuse_the_reviewed_fingerprint(self):
        from pypdf import PdfWriter
        from reportlab.pdfgen.canvas import Canvas
        overlay=BytesIO();canvas=Canvas(overlay,pagesize=(612,792))
        canvas.drawString(50,700,'Different fictional facts');canvas.showPage();canvas.save()
        writer=PdfWriter();writer.append(PdfReader(BytesIO(self.packet)))
        writer.pages[0].merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
        changed=BytesIO();writer.write(changed)
        with self.assertRaises(ValueError):qa.build_payload(changed.getvalue(),self.fields,qa.REVIEWED_SOURCE_COMMIT)

    def test_builder_uses_no_customer_records_or_test_imports(self):
        from pathlib import Path
        text=Path(qa.__file__).read_text()
        for value in ('from tests','import httpx','SIGNWELL_API_KEY','SUPABASE_SECRET_KEY'):self.assertNotIn(value,text)
        self.assertEqual(qa.layout_fingerprint(self.fields,self.cases),qa.LAYOUT_SHA256)

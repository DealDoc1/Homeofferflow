"""Showing-only answers follow the short form's explicit paragraphs 6-8 exclusion."""
from io import BytesIO
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from lib import txr_1507
from tests.test_standalone_agreement_foundation import MODULE, valid_payload
from tests.test_txr_1507_renderer import blank_two_page_pdf, sample_data


class Txr1507ServiceTermsTests(unittest.TestCase):
    def test_showing_only_needs_its_fee_not_full_service_answers(self):
        data = valid_payload()
        data.update(serviceLevel='showing_services', showingFee='150.25')
        data.pop('compensation')
        data.pop('intermediary')
        parsed = MODULE._parse_txr_1507_draft(data)['agreement_data']
        self.assertEqual(parsed['showing_fee'], '150.25')
        self.assertEqual(parsed['intermediary'], '')
        self.assertNotIn('purchase_percentage', parsed)

    def test_showing_only_does_not_validate_or_save_hidden_full_service_values(self):
        data = valid_payload()
        data.update(serviceLevel='showing_services', showingFee='0',
                    compensation={'purchaseFlatFee': 'stale invalid value'}, intermediary='stale')
        parsed = MODULE._parse_txr_1507_draft(data)['agreement_data']
        self.assertEqual(parsed['showing_fee'], '0')
        self.assertEqual(parsed['intermediary'], '')
        self.assertNotIn('purchase_flat_fee', parsed)

    def test_full_services_does_not_validate_or_save_hidden_showing_fee(self):
        data = valid_payload()
        data['showingFee'] = 'stale invalid value'
        parsed = MODULE._parse_txr_1507_draft(data)['agreement_data']
        self.assertEqual(parsed['showing_fee'], '')
        self.assertEqual(parsed['purchase_percentage'], '3')
        self.assertEqual(parsed['intermediary'], 'authorized')

    def test_applicable_questions_are_still_required(self):
        for update, error in [({'compensation': {}}, 'at least one'),
                              ({'intermediary': ''}, 'intermediary'),
                              ({'serviceLevel': 'showing_services', 'showingFee': ''}, 'requires the execution fee'),
                              ({'serviceLevel': 'showing_services', 'showingFee': 'invalid'}, 'dollar amount')]:
            with self.subTest(update=update), self.assertRaisesRegex(ValueError, error):
                MODULE._parse_txr_1507_draft({**valid_payload(), **update})

    def test_legacy_showing_draft_omits_inapplicable_amounts_and_intermediary_marks(self):
        data = {**sample_data(), 'service_level': 'showing_services', 'showing_fee': '157.29',
                'intermediary': 'authorized',
                'compensation': {'purchase_flat_fee': '999999.99', 'lease_flat_fee': '87654.32'}}
        with patch.object(txr_1507, '_draw_check', wraps=txr_1507._draw_check) as check:
            raw = txr_1507.render_txr_1507(blank_two_page_pdf(), data, {}, {})
        text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(raw)).pages)
        self.assertIn('157.29', text)
        self.assertNotIn('999999.99', text)
        self.assertNotIn('87654.32', text)
        self.assertEqual([call.args[1:] for call in check.call_args_list], [(55, 427)])

    def test_parsed_showing_answers_reach_renderer_without_missing_field_errors(self):
        payload = {**valid_payload(), 'serviceLevel': 'showing_services', 'showingFee': '157.29',
                   'intermediary': '', 'compensation': {}}
        parsed = MODULE._parse_txr_1507_draft(payload)
        data = {**parsed['agreement_data'], 'client_names': parsed['client_names'], 'compensation': {}}
        raw = txr_1507.render_txr_1507(blank_two_page_pdf(), data, {'name': 'QA Brokerage'}, {})
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages), 2)
        fields = txr_1507.build_signwell_fields_txr1507(data, client_count=1)[0]
        self.assertEqual({f['recipient_id'] for f in fields}, {'1', 'associate'})


if __name__ == '__main__':
    unittest.main()

"""Combined purchase packets must preserve appraisal answers and page offsets."""
from io import BytesIO
from pathlib import Path
import hashlib
import unittest
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from lib import production_adapter as adapter, txr_1948 as form
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64
from tests.test_txr1948_answer_bounds import appearance_pdf
from tests.test_seller_temporary_lease_production_signwell import load_offer_api


def offer_sample(**overrides):
    return minimal_offer(**{
        'financing': 'conventional', 'loanAmount': '400000', 'loanTerm': '30',
        'interestRate': '6.5', 'appraisalAddendum': 'additionalRight',
        'appraisalTerminateValue': '475000', 'appraisalTerminateDays': '7',
        'buyer1': 'José 李', 'buyer2': 'Second Buyer', 'buyer2Email': 'second@example.com',
        **overrides,
    })


class PurchaseAppraisalLayoutTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()

    def test_all_choices_keep_canonical_values_and_actual_appearances(self):
        for choice in ('waiver', 'partialWaiver', 'additionalRight'):
            with self.subTest(choice=choice):
                offer = offer_sample(appraisalAddendum=choice, appraisalMinimum='475000',
                                     address='100 José 李 Street')
                raw = adapter.fill_and_merge_20_19(offer)
                reader = PdfReader(BytesIO(raw))
                data = adapter.verified.appraisal_render_data(offer)
                expected = form._editable_values(PdfReader(adapter.verified.APPRAISAL_PDF), data)
                fields = reader.get_fields()
                self.assertEqual(len(reader.pages), 15)
                for ref in reader.pages[14]['/Annots']:
                    widget = ref.get_object()
                    name = widget['/T']
                    if name not in expected:
                        continue
                    self.assertEqual(fields['hof_appraisal.' + name]['/V'], expected[name])
                    self.assertEqual(widget['/V'], expected[name])
                    self.assertTrue(widget['/AP']['/N'])
                    if widget['/FT'] == '/Tx':
                        visible = PdfReader(BytesIO(appearance_pdf(widget))).pages[0].extract_text().strip()
                        self.assertEqual(visible, expected[name])
                    else:
                        self.assertEqual(widget['/AS'], expected[name])
                source = Path(adapter.verified.APPRAISAL_PDF).read_bytes()
                self.assertIn(hashlib.sha256(source).hexdigest(), offer['_signing_source_hashes'])
                self.assertEqual(offer['_signing_render_revisions']['TXR-1948'], form.RENDER_REVISION)

    def test_one_or_two_buyer_signatures_share_standalone_boxes_without_extra_dates(self):
        for buyers in (1, 2):
            with self.subTest(buyers=buyers):
                offer = offer_sample(buyer2Email='second@example.com' if buyers == 2 else '')
                raw = adapter.fill_and_merge_20_19(offer)
                fields = adapter.build_signwell_fields_20_19(offer, raw)[0]
                app = [f for f in fields if 'appraisal' in f['api_id']]
                self.assertEqual(len(app), buyers)
                for index, field in enumerate(app):
                    self.assertEqual(field['type'], 'signature')
                    self.assertEqual(field['recipient_id'], str(index + 1))
                    self.assertEqual(field['page'], 15)
                    self.assertEqual(tuple(field[k] for k in ('x', 'y', 'width', 'height')),
                                     form.BUYER_SIGNATURE_BOXES[index])

    def test_long_answers_shift_following_addenda_and_initial_each_appraisal_page(self):
        for buyers in (1, 2):
            with self.subTest(buyers=buyers):
                offer = offer_sample(address='A' * 400,
                    buyer1='José 李 <b>Buyer</b> & ' + 'B' * 160,
                    buyer2Email='second@example.com' if buyers == 2 else '',
                    hoa='yes', hoaDelivery='seller', hoaDeliveryDays='7', hoaName='Example HOA',
                    nonRealtyItems='yes', nonRealtyItemsText='Refrigerator', nonRealtyItemsAmount='750',
                    uploadedDisclosureDocs=[{'name': 'Disclosure.pdf', 'base64': one_page_pdf_base64()}])
                raw = adapter.fill_and_merge_20_19(offer)
                reader = PdfReader(BytesIO(raw))
                answers = form.answer_layout(adapter.verified.appraisal_render_data(offer))
                continuation_count = len(PdfReader(BytesIO(answers.continuation())).pages)
                financing_answers = adapter.verified.financing_addendum_layout.answer_layout(
                    offer, adapter.verified.normalize_financing(offer['financing']))
                financing_count = len(PdfReader(BytesIO(financing_answers.continuation())).pages)
                appraisal_page = 15 + financing_count
                self.assertGreater(continuation_count, 0)
                text = ''.join(p.extract_text() for p in reader.pages[
                    appraisal_page:appraisal_page + continuation_count])
                self.assertIn('Appraisal Addendum Continuation', text)
                self.assertIn('Seller: Controlled Launch Seller', text)
                self.assertIn('A' * 400, ''.join(text.split()))
                fields = adapter.build_signwell_fields_20_19(offer, raw)[0]
                by_id = {f['api_id']: f for f in fields}
                self.assertEqual(len(by_id), len(fields))
                self.assertEqual(by_id['buyer1_non_realty_items_addendum_signature']['page'],
                                 appraisal_page + 1 + continuation_count)
                self.assertEqual(by_id['buyer1_hoa_addendum_signature']['page'],
                                 appraisal_page + 2 + continuation_count)
                for page in range(appraisal_page + 1, appraisal_page + 1 + continuation_count):
                    initials = [f for f in fields if f['page'] == page and f['api_id'].startswith('appraisal_continuation_')]
                    self.assertEqual({f['recipient_id'] for f in initials}, {str(i + 1) for i in range(buyers)})
                    self.assertTrue(all(f['type'] == 'initials' and f['required'] for f in initials))
                self.assertTrue(all(f['page'] <= len(reader.pages) for f in fields))
                self.assertFalse(any(f['page'] == len(reader.pages) for f in fields))

    def test_appraisal_not_added_for_cash_fha_va_or_none(self):
        for financing, choice, pages in [('cash', 'waiver', 12), ('fha', 'waiver', 14),
                                        ('va', 'waiver', 14), ('conventional', 'none', 14)]:
            offer = offer_sample(financing=financing, appraisalAddendum=choice)
            raw = adapter.verified.fill_and_merge(offer)
            self.assertEqual(len(PdfReader(BytesIO(raw)).pages), pages)
            self.assertFalse(any('appraisal' in f['api_id'] for f in adapter.verified.build_signwell_fields(offer, raw)[0]))

    def test_selected_missing_source_cannot_silently_omit_addendum(self):
        with patch.object(adapter.verified, 'APPRAISAL_PDF', '/nonexistent/appraisal.pdf'), \
             patch.object(adapter.verified, 'APPRAISAL_PDF_ALT', '/nonexistent/appraisal.pdf'):
            with self.assertRaisesRegex(ValueError, 'appraisal addendum source'):
                adapter.fill_and_merge_20_19(offer_sample())

    def test_missing_continuation_is_rejected_by_signing_map(self):
        offer = offer_sample(address='A' * 400)
        financing_answers = adapter.verified.financing_addendum_layout.answer_layout(
            offer, adapter.verified.normalize_financing(offer['financing']))
        financing_count = len(PdfReader(BytesIO(financing_answers.continuation())).pages)
        writer = PdfWriter()
        # Main contract, two financing pages, its complete continuation, and
        # the appraisal base page are present. Only appraisal continuation is absent.
        for _ in range(15 + financing_count):
            writer.add_blank_page(612, 792)
        out = BytesIO()
        writer.write(out)
        with self.assertRaisesRegex(ValueError, 'appraisal continuation'):
            adapter.verified.build_signwell_fields(offer, out.getvalue())

    def test_real_packet_send_payload_keeps_parallel_buyers_and_matching_fields(self):
        api = load_offer_api()
        for buyers in (1, 2):
            for long in (False, True):
                with self.subTest(buyers=buyers, long=long):
                    offer = offer_sample(userType='agent',
                        buyer2Email='second@example.com' if buyers == 2 else '',
                        address='A' * 400 if long else '100 Example Street')
                    raw = adapter.fill_and_merge_20_19(offer)
                    captured = {}
                    def deliver(record, payload, answers, **options):
                        captured.update(payload)
                        return {'document_id': 'offline-appraisal', 'document': {'id': 'offline-appraisal', 'status': 'sent'},
                                'state': 'sent', 'message': 'Signature request sent.', 'recovered': False}
                    with patch.object(api, 'SIGNWELL_ENABLED', True), \
                         patch.object(api, 'SIGNWELL_API_KEY', 'offline-only'), \
                         patch.object(api, 'deliver_offer_document', side_effect=deliver) as delivery:
                        self.assertTrue(api.create_signwell_signature_request(offer, raw)['ok'])
                    delivery.assert_called_once()
                    self.assertFalse(captured['apply_signing_order'])
                    self.assertEqual({r['id'] for r in captured['recipients']}, {str(i + 1) for i in range(buyers)})
                    self.assertEqual(captured['fields'], adapter.build_signwell_fields_20_19(offer, raw))
                    self.assertEqual(len(captured['files']), 1)


if __name__ == '__main__':
    unittest.main()

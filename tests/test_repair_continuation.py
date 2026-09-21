"""Verify lossless terms and field/page ownership through the real adapter."""
from io import BytesIO
import re
import unittest

from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from lib.repair_continuation import (
    REFERENCE, TITLE, inline_entries, render_repair_continuation,
)
from tests.test_controlled_launch import (
    adapter, configure_local_forms, minimal_offer, one_page_pdf_base64,
    residential_lease_offer,
)


def long_terms(count=18):
    return "\n".join(
        f"Repair {number:03d}: Replace the damaged fixture in room {number:03d} before closing."
        for number in range(1, count + 1)
    ) + "\nFINAL REQUIREMENT: Remove all packaging from the property."


class RepairContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def packet(self, **kwargs):
        offer = minimal_offer(asIs='repairs', repairsText=long_terms(), **kwargs)
        pdf = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, pdf)[0]
        return offer, PdfReader(BytesIO(pdf)), fields

    def test_short_terms_stay_complete_on_original_blanks(self):
        text = 'Replace the cracked kitchen window before closing.'
        entries = inline_entries(text)
        self.assertEqual(' '.join(e[2] for e in entries).strip(), text)
        for entry, width in zip(entries, (246, 463)):
            self.assertLessEqual(stringWidth(entry[2], 'Helvetica', entry[3]), width)
        offer = minimal_offer(asIs='repairs', repairsText=text)
        self.assertIsNone(render_repair_continuation(offer))
        self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages), 12)

    def test_all_terms_and_last_requirement_reach_packet_without_ellipsis(self):
        offer, reader, fields = self.packet()
        self.assertIn(REFERENCE, reader.pages[4].extract_text())
        terms = ' '.join(page.extract_text() for page in reader.pages[12:])
        for line in offer['repairsText'].splitlines():
            self.assertIn(line, terms)
        self.assertNotIn('...', terms)
        self.assertIn(TITLE, terms)
        self.assertEqual({f['recipient_id'] for f in fields}, {'1'})
        self.assertEqual(next(f['page'] for f in fields if f['api_id']=='buyer1_main_contract_signature'), 10)

    def test_multi_page_terms_keep_every_number_and_buyer_initials_on_every_page(self):
        offer = minimal_offer(asIs='repairs', repairsText=long_terms(150),
                              buyer2='Second Buyer', buyer2Email='second@example.com')
        pdf = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(pdf))
        fields = adapter.build_signwell_fields_20_19(offer, pdf)[0]
        self.assertGreater(len(reader.pages), 14)
        text = ' '.join(p.extract_text() for p in reader.pages[12:])
        for number in range(1, 151):
            self.assertEqual(text.count(f'Repair {number:03d}:'), 1)
        self.assertIn('FINAL REQUIREMENT', text)
        for page in range(13, len(reader.pages) + 1):
            page_text = reader.pages[page-1].extract_text()
            self.assertIn(TITLE, page_text)
            self.assertIn(offer['address'], page_text)
            marks = [f for f in fields if f['page']==page]
            self.assertEqual({f['recipient_id'] for f in marks}, {'1', '2'})
            self.assertTrue(all(f['type']=='initials' and f['required'] for f in marks))
            for f in marks:
                self.assertGreaterEqual(f['y']*.75, 706)
                self.assertLessEqual((f['y']+f['height'])*.75, 724)
                self.assertLessEqual(f['width']*.75, 50)

    def test_stale_terms_with_explicit_as_is_do_not_create_continuation(self):
        for choice in ('yes', True, '1'):
            offer = minimal_offer(asIs=choice, repairsText=long_terms(100))
            self.assertIsNone(render_repair_continuation(offer))
            pdf = adapter.fill_and_merge_20_19(offer)
            self.assertEqual(len(PdfReader(BytesIO(pdf)).pages), 12)
            self.assertFalse(any(f['api_id'].startswith('repair_continuation_')
                                 for f in adapter.build_signwell_fields_20_19(offer, pdf)[0]))

    def test_legacy_text_only_offer_keeps_continuation(self):
        offer = minimal_offer(repairsText=long_terms())
        offer.pop('asIs')
        self.assertIsNotNone(render_repair_continuation(offer))
        pdf = adapter.fill_and_merge_20_19(offer)
        self.assertIn(REFERENCE, PdfReader(BytesIO(pdf)).pages[4].extract_text())

    def test_existing_addendum_signature_pages_do_not_move(self):
        extra = dict(financing='conventional', loanAmount='400000', hoa='yes',
                     saleContingency='yes', backupOffer='yes')
        original = minimal_offer(**extra)
        old_pdf = adapter.fill_and_merge_20_19(original)
        old_fields = adapter.build_signwell_fields_20_19(original, old_pdf)[0]
        changed = dict(original, asIs='repairs', repairsText=long_terms())
        new_pdf = adapter.fill_and_merge_20_19(changed)
        new_fields = adapter.build_signwell_fields_20_19(changed, new_pdf)[0]
        self.assertEqual(old_fields, [f for f in new_fields if not f['api_id'].startswith('repair_continuation_')])
        base_count = len(PdfReader(BytesIO(old_pdf)).pages)
        self.assertTrue(all(f['page'] > base_count for f in new_fields if f['api_id'].startswith('repair_continuation_')))

    def test_existing_seller_recipient_gets_initials_without_changing_party_ids(self):
        offer = residential_lease_offer(asIs='repairs', repairsText=long_terms())
        pdf = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, pdf)[0]
        continuation = [f for f in fields if f['api_id'].startswith('repair_continuation_')]
        self.assertEqual({f['recipient_id'] for f in continuation}, {'1', '3'})
        reader = PdfReader(BytesIO(pdf))
        self.assertEqual({f['page'] for f in continuation}, {len(reader.pages)-1})

    def test_literal_markup_and_long_unbroken_words_are_not_discarded(self):
        text = long_terms() + '\nKeep <b>wood</b> & metal. ' + 'X'*900 + ' END_MARKER'
        pdf = render_repair_continuation(minimal_offer(asIs='repairs', repairsText=text))
        extracted = ''.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
        self.assertIn('<b>wood</b> & metal.', extracted)
        self.assertEqual(sum(len(run) for run in re.findall(r'X{2,}', extracted)), 900)
        self.assertIn('END_MARKER', extracted)

    def test_uploaded_document_keeps_its_own_signature_page_after_continuation(self):
        _, reader, fields = self.packet(uploadedDisclosureDocs=[{
            'name': 'Example disclosure.pdf', 'base64': one_page_pdf_base64(),
            'signaturePlacements': [{'type': 'buyer1_signature', 'page': 1,
                                    'signwellX': 100, 'signwellY': 200}],
        }])
        uploaded = [f for f in fields if f['api_id'].startswith('uploaded_')]
        self.assertEqual(len(uploaded), 1)
        self.assertEqual(uploaded[0]['page'], len(reader.pages))
        self.assertEqual(uploaded[0]['type'], 'signature')
        self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('repair_continuation_')},
                         {len(reader.pages)-1})


if __name__ == '__main__':
    unittest.main()

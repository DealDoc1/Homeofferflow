"""Real packet checks for complete TREC 20-19 Paragraph 8/11 answers."""
from io import BytesIO
import re
import unittest

from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from lib.contract_terms_continuation import (
    LABELS, REFERENCE, TITLE, inline_entries, render_continuation, terms, text_entries,
)
from tests.test_controlled_launch import (
    adapter, configure_local_forms, minimal_offer, one_page_pdf_base64, residential_lease_offer,
)


def long_answer(prefix="Information", count=30):
    return "\n".join(f"{prefix} {i:03d}: This is a synthetic informational item for layout review."
                     for i in range(1, count + 1)) + f"\n{prefix} FINAL ITEM."


class ContractTermsContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def packet(self, **values):
        offer = minimal_offer(**values)
        pdf = adapter.fill_and_merge_20_19(offer)
        return offer, PdfReader(BytesIO(pdf)), adapter.build_signwell_fields_20_19(offer, pdf)[0]

    def test_blank_and_short_answers_do_not_add_pages(self):
        for values in ({}, dict(brokerDisclosure="Example disclosure.", specialProvisions="Example instructions.")):
            offer, reader, fields = self.packet(**values)
            self.assertEqual(len(reader.pages), 12)
            self.assertIsNone(render_continuation(offer))
            for text in values.values():
                self.assertIn(text, reader.pages[5].extract_text())
            self.assertFalse(any(f['api_id'].startswith('contract_terms_') for f in fields))

    def test_inline_text_fits_independently_measured_source_blanks(self):
        # Separate measured bounds, not the implementation's BLANKS constant.
        source = {
            "broker": [(481.70, 558.00, 76.73), (61.34, 557.38, 88.99), (61.34, 557.38, 101.35)],
            "special": [(349.20, 554.40, 554.40), (59.88, 554.40, 565.44), (59.88, 554.40, 576.48)],
        }
        for section, rules in source.items():
            for sample in ("Example item. " * 15, long_answer()):
                for x, y, text, size in text_entries(sample, section):
                    left, right, rule = min(rules, key=lambda r: abs(r[2] - (792-y)))
                    self.assertGreaterEqual(x, left)
                    self.assertLessEqual(x + stringWidth(text, 'Helvetica', size), right)
                    self.assertLess(792-y + 1.66, rule)
            # A word too wide for the first blank can use the next full line.
            value = 'W' * 30
            entries = inline_entries(value, section)
            self.assertEqual(' '.join(e[2] for e in entries), value)

    def test_each_overflow_section_is_referenced_and_copied_completely(self):
        for key, section in (("brokerDisclosure", "broker"), ("specialProvisions", "special")):
            value = long_answer()
            _, reader, fields = self.packet(**{key: value})
            self.assertIn(REFERENCE, reader.pages[5].extract_text())
            appended = '\n'.join(p.extract_text() for p in reader.pages[12:])
            self.assertIn(LABELS[section], appended)
            for line in value.splitlines():
                self.assertIn(line, appended)
            self.assertNotIn('...', appended)
            self.assertEqual({f['recipient_id'] for f in fields}, {'1'})

    def test_both_sections_and_multiple_pages_preserve_every_item(self):
        _, reader, fields = self.packet(brokerDisclosure=long_answer('Disclosure', 80),
            specialProvisions=long_answer('Instructions', 80), buyer2='Second QA Buyer', buyer2Email='second@example.com')
        self.assertGreater(len(reader.pages), 14)
        appended = '\n'.join(p.extract_text() for p in reader.pages[12:])
        for prefix in ('Disclosure', 'Instructions'):
            for i in range(1, 81):
                self.assertEqual(appended.count(f'{prefix} {i:03d}:'), 1)
            self.assertIn(prefix+' FINAL ITEM.', appended)
        for page in range(13, len(reader.pages)+1):
            self.assertIn(TITLE, reader.pages[page-1].extract_text())
            marks = [f for f in fields if f['page']==page]
            self.assertEqual({f['recipient_id'] for f in marks}, {'1','2'})
            self.assertTrue(all(f['type']=='initials' and f['required'] for f in marks))

    def test_special_provisions_alias_precedence(self):
        self.assertEqual(terms({'specialProvisions':'Primary', 'specialProvisionsText':'Legacy'}, 'special'), 'Primary')
        self.assertEqual(terms({'specialProvisions':'', 'specialProvisionsText':'Legacy'}, 'special'), 'Legacy')
        _, reader, _ = self.packet(specialProvisionsText=long_answer('Legacy'))
        self.assertIn('Legacy FINAL ITEM.', '\n'.join(p.extract_text() for p in reader.pages[12:]))

    def test_literal_markup_and_unbroken_text_are_preserved(self):
        value = '<b>Literal</b> & information. ' + 'X'*900 + ' END_MARKER'
        reader = PdfReader(BytesIO(render_continuation(minimal_offer(brokerDisclosure=value))))
        text = '\n'.join(p.extract_text() for p in reader.pages)
        self.assertIn('<b>Literal</b> & information.', text)
        self.assertEqual(sum(len(run) for run in re.findall('X{2,}', text)), 900)
        self.assertIn('END_MARKER', text)

    def test_existing_packet_fields_unchanged_and_continuations_ordered(self):
        extra = dict(financing='conventional', loanAmount='400000', hoa='yes',
            saleContingency='yes', backupOffer='yes', asIs='repairs', repairsText=long_answer('Repair'),
            nonRealtyItems='yes', nonRealtyDescription=long_answer('Inventory'),
            possession='temporaryLease', buyerTemporaryLease='yes', buyerTemporaryLeaseSpecialProvisions=long_answer('Lease'))
        _, original, old_fields = self.packet(**extra)
        _, changed, new_fields = self.packet(**extra, brokerDisclosure=long_answer())
        self.assertEqual(old_fields, [f for f in new_fields if not f['api_id'].startswith('contract_terms_')])
        self.assertGreater(len(changed.pages), len(original.pages))
        self.assertTrue(all(f['page']>len(original.pages) for f in new_fields if f['api_id'].startswith('contract_terms_')))

    def test_existing_seller_can_initial_but_no_new_recipient_is_added(self):
        offer = residential_lease_offer(brokerDisclosure=long_answer())
        pdf = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, pdf)[0]
        marks = [f for f in fields if f['api_id'].startswith('contract_terms_')]
        self.assertEqual({f['recipient_id'] for f in marks}, {'1','3'})
        self.assertEqual({f['recipient_id'] for f in fields}, {'1','3'})

    def test_uploaded_signature_stays_with_its_document(self):
        _, reader, fields = self.packet(brokerDisclosure=long_answer(), uploadedDisclosureDocs=[{
            'name':'Example disclosure.pdf', 'base64':one_page_pdf_base64(),
            'signaturePlacements':[{'type':'buyer1_signature','page':1,'signwellX':100,'signwellY':200}],
        }])
        upload = [f for f in fields if f['api_id'].startswith('uploaded_')]
        self.assertEqual(len(upload), 1)
        self.assertEqual(upload[0]['page'], len(reader.pages))
        self.assertTrue(all(f['page']<len(reader.pages) for f in fields if f['api_id'].startswith('contract_terms_')))


if __name__ == '__main__':
    unittest.main()

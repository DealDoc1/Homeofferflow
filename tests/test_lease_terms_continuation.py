"""Real packet checks for temporary-lease special-provision completeness."""
from io import BytesIO
import re
import unittest

from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from lib import lease_terms_continuation as lease
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer, one_page_pdf_base64, residential_lease_offer
from tests.test_nonrealty_continuation import item_list
from tests.test_repair_continuation import long_terms as repair_terms


def long_terms(count=60):
    return '\n'.join(f'Term {n:03d}: Preserve this complete example lease provision, reference LT-{n:03d}.'
                     for n in range(1, count + 1)) + '\nFINAL TERM: Return every supplied key.'


def lease_answers(kind):
    return {'possession': 'temporaryLease' if kind == 'buyer' else 'sellerTemporaryLease',
            kind+'TemporaryLease': 'yes', 'sellerEmail':'seller@example.com'}


class LeaseTermsContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def packet(self, kind, text, **overrides):
        values = {**lease_answers(kind), kind + 'TemporaryLeaseSpecialProvisions': text}
        values.update(overrides)
        offer = minimal_offer(**values)
        pdf = adapter.fill_and_merge_20_19(offer)
        return offer, PdfReader(BytesIO(pdf)), adapter.build_signwell_fields_20_19(offer, pdf)[0]

    def test_short_terms_remain_on_existing_blanks_without_extra_pages(self):
        text = 'Return the supplied keys and garage door controls.'
        for kind in ('buyer', 'seller'):
            with self.subTest(kind=kind):
                entries = lease.inline_entries(text, kind)
                self.assertEqual(' '.join(e[2] for e in entries), text)
                self.assertLessEqual(stringWidth(entries[0][2], 'Helvetica', 8), lease.BLANKS[kind][0][2])
                _, reader, fields = self.packet(kind, text)
                self.assertEqual(len(reader.pages), 14)
                self.assertIn(text, reader.pages[12].extract_text())
                self.assertFalse(any(f['api_id'].startswith('lease_continuation_') for f in fields))

    def test_both_lease_types_preserve_all_terms_across_multiple_pages(self):
        for kind in ('buyer', 'seller'):
            with self.subTest(kind=kind):
                _, reader, fields = self.packet(kind, long_terms(100), buyer2='Second QA Buyer', buyer2Email='second@example.com')
                self.assertIn(lease.REFERENCE, reader.pages[12].extract_text())
                self.assertNotIn('LT-001', reader.pages[12].extract_text())
                text = ' '.join(p.extract_text() for p in reader.pages[14:])
                for n in range(1,101): self.assertEqual(text.count(f'LT-{n:03d}.'), 1)
                self.assertIn('FINAL TERM: Return every supplied key.', text)
                self.assertNotIn('...', text)
                for page in range(15, len(reader.pages) + 1):
                    self.assertIn(kind.capitalize() + "'s Temporary Residential Lease", reader.pages[page-1].extract_text())
                    marks = [f for f in fields if f['page'] == page]
                    self.assertEqual({f['recipient_id'] for f in marks}, {'1', '2', '3'} if kind=='seller' else {'1', '2'})
                    self.assertTrue(all(f['type']=='initials' and f['required'] for f in marks))

    def test_unbroken_tokens_and_literal_markup_are_not_dropped(self):
        for kind in ('buyer','seller'):
            text = 'Z'*800 + '\nLiteral <oak> & pine. FINAL-EXAMPLE.'
            with self.subTest(kind=kind):
                self.assertIsNone(lease.inline_entries(text, kind))
                _, reader, _ = self.packet(kind,text)
                result = '\n'.join(p.extract_text() for p in reader.pages[14:])
                self.assertEqual(sum(len(run) for run in re.findall('Z{2,}', result)), 800)
                self.assertIn('Literal <oak> & pine. FINAL-EXAMPLE.', result)

    def test_deselected_lease_cannot_append_stale_special_provisions(self):
        offer = minimal_offer(possession='funding', buyerTemporaryLeaseSpecialProvisions=long_terms(),
                              sellerTemporaryLeaseSpecialProvisions=long_terms())
        self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages), 12)
        for kind in ('buyer', 'seller'):
            _, reader, _ = self.packet(kind, '')
            self.assertEqual(len(reader.pages), 14)

    def test_legacy_aliases_keep_the_same_terms(self):
        for kind in ('buyer', 'seller'):
            for key in (kind+'TempLeaseSpecialProvisions', 'temporaryLeaseSpecialProvisions'):
                with self.subTest(kind=kind,key=key):
                    _, reader, _ = self.packet(kind, '', **{key:long_terms()})
                    self.assertIn('FINAL TERM: Return every supplied key.', reader.pages[-1].extract_text())

    def test_all_continuation_types_keep_original_signatures_and_upload_last(self):
        for kind in ('buyer','seller'):
            with self.subTest(kind=kind):
                base = dict(financing='conventional', loanAmount='400000', hoa='yes',
                            nonRealtyItems='yes', nonRealtyDescription=item_list(1))
                _, short, old_fields = self.packet(kind, 'Return keys.', **base)
                base.update(nonRealtyDescription=item_list(70), asIs='repairs', repairsText=repair_terms(70),
                    uploadedDisclosureDocs=[{'name':'Example.pdf','base64':one_page_pdf_base64(),
                        'signaturePlacements':[{'type':'buyer1_signature','page':1,'signwellX':100,'signwellY':200}]}])
                _, reader, fields = self.packet(kind, long_terms(), **base)
                prefixes = ('repair_continuation_', 'nonrealty_continuation_', 'lease_continuation_', 'uploaded_')
                self.assertEqual([f for f in fields if not f['api_id'].startswith(prefixes)], old_fields)
                page_sets = [{f['page'] for f in fields if f['api_id'].startswith(prefix)} for prefix in prefixes]
                self.assertEqual(min(page_sets[0]), len(short.pages)+1)
                for left,right in zip(page_sets,page_sets[1:]): self.assertLess(max(left),min(right))
                self.assertEqual(page_sets[-1], {len(reader.pages)})
                self.assertEqual(len({f['api_id'] for f in fields}), len(fields))

    def test_existing_seller_recipients_receive_initials_without_new_recipients(self):
        for kind in ('buyer','seller'):
            offer = residential_lease_offer(**lease_answers(kind),
                **{kind+'TemporaryLeaseSpecialProvisions':long_terms()})
            pdf = adapter.fill_and_merge_20_19(offer)
            fields = adapter.build_signwell_fields_20_19(offer, pdf)[0]
            marks = [f for f in fields if f['api_id'].startswith('lease_continuation_')]
            self.assertEqual({f['recipient_id'] for f in marks}, {'1','3'})
            for page in {f['page'] for f in marks}:
                self.assertEqual({f['recipient_id'] for f in marks if f['page']==page}, {'1','3'})

    def test_selected_lease_ignores_other_lease_stale_terms(self):
        for kind,other in (('buyer','seller'),('seller','buyer')):
            _,reader,_ = self.packet(kind,'Return keys.', **{other+'TemporaryLeaseSpecialProvisions':long_terms()})
            self.assertEqual(len(reader.pages),14)
            self.assertNotIn('LT-001',' '.join(p.extract_text() for p in reader.pages))


if __name__ == '__main__': unittest.main()

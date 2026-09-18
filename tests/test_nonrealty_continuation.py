"""Full item inventories must survive packet generation and page placement."""
from io import BytesIO
import re
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from lib import nonrealty_continuation as inventory
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer, one_page_pdf_base64, residential_lease_offer
from tests.test_repair_continuation import long_terms


def item_list(count):
    return '\n'.join(f'Item {n:03d}: Example appliance, model QA-{n:03d}, serial SN-{n:03d}.'
                     for n in range(1, count+1))


class NonRealtyContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def packet(self, text, **kwargs):
        offer = minimal_offer(nonRealtyItems='yes', nonRealtyDescription=text, **kwargs)
        pdf = adapter.fill_and_merge_20_19(offer)
        return offer, PdfReader(BytesIO(pdf)), adapter.build_signwell_fields_20_19(offer,pdf)[0]

    def test_all_eleven_measured_blanks_are_used_without_dropping_last_item(self):
        text = item_list(11)
        entries = inventory.inline_entries(text)
        self.assertEqual(len(entries), 11)
        # Independently measured rule boundaries from TREC 57-0 rectangles.
        rules = (248.72,267.56,286.41,305.25,324.09,342.94,361.78,380.63,399.47,418.31,436.69)
        for (x,y,line,size), rule in zip(entries,rules):
            self.assertGreaterEqual(x,64.5)
            self.assertLessEqual(x+stringWidth(line,'Helvetica',size),567)
            self.assertLess(792-y+2,rule)
        _,reader,fields = self.packet(text)
        self.assertEqual(len(reader.pages),13)
        page = reader.pages[12].extract_text()
        for line in text.splitlines(): self.assertIn(line,page)
        self.assertFalse(any(f['api_id'].startswith('nonrealty_continuation_') for f in fields))

    def test_twelve_items_move_whole_inventory_to_continuation_not_partial_list(self):
        text = item_list(12)
        _,reader,fields = self.packet(text)
        self.assertEqual(len(reader.pages),14)
        self.assertIn(inventory.REFERENCE,reader.pages[12].extract_text())
        self.assertNotIn('Item 001:',reader.pages[12].extract_text())
        for line in text.splitlines(): self.assertIn(line,reader.pages[13].extract_text())
        self.assertEqual({f['recipient_id'] for f in fields},{'1'})

    def test_multi_page_inventory_has_every_serial_and_buyer_initials(self):
        _,reader,fields = self.packet(item_list(120),buyer2='Second Buyer',buyer2Email='second@example.com')
        self.assertGreater(len(reader.pages),15)
        text=' '.join(p.extract_text() for p in reader.pages[13:])
        for n in range(1,121): self.assertEqual(text.count(f'serial SN-{n:03d}.'),1)
        for page in range(14,len(reader.pages)+1):
            self.assertIn(inventory.TITLE,reader.pages[page-1].extract_text())
            marks=[f for f in fields if f['page']==page]
            self.assertEqual({f['recipient_id'] for f in marks},{'1','2'})
            self.assertTrue(all(f['type']=='initials' and f['required'] for f in marks))
            for f in marks: self.assertLessEqual((f['y']+f['height'])*.75,724)

    def test_long_word_does_not_run_outside_original_form_or_disappear(self):
        token='W'*700
        self.assertIsNone(inventory.inline_entries(token))
        _,reader,_=self.packet(token)
        text=''.join(p.extract_text() for p in reader.pages[13:])
        self.assertEqual(sum(len(run) for run in re.findall('W{2,}',text)),700)

    def test_literal_markup_and_final_terms_survive(self):
        text=item_list(12)+'\nFinal item: <oak> table & chairs, model LAST-123.'
        _,reader,_=self.packet(text)
        self.assertIn('Final item: <oak> table & chairs, model LAST-123.',reader.pages[13].extract_text())

    def test_deselection_and_empty_inventory_cannot_append_stale_pages(self):
        for choice in ('no','',False):
            offer=minimal_offer(nonRealtyItems=choice,nonRealtyDescription=item_list(40))
            self.assertIsNone(inventory.render_nonrealty_continuation(offer))
            self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages),12)
        self.assertIsNone(inventory.render_nonrealty_continuation(minimal_offer(nonRealtyItems='yes',nonRealtyDescription='')))

    def test_legacy_description_aliases_are_kept(self):
        for key in ('nonRealtyItemsDescription','nonRealtyItemsText','personalPropertyDescription'):
            offer=minimal_offer(nonRealtyItems='yes',**{key:item_list(12)})
            pdf=adapter.fill_and_merge_20_19(offer)
            self.assertIn('serial SN-012.',PdfReader(BytesIO(pdf)).pages[-1].extract_text())

    def test_repair_and_inventory_continuations_keep_upload_and_addendum_fields_separate(self):
        base=dict(financing='conventional',loanAmount='400000',hoa='yes',buyer2='Buyer Two',buyer2Email='two@example.com')
        _,short,old_fields=self.packet(item_list(1),**base)
        _,reader,fields=self.packet(item_list(70),asIs='repairs',repairsText=long_terms(70),
            uploadedDisclosureDocs=[{'name':'Example.pdf','base64':one_page_pdf_base64(),
                'signaturePlacements':[{'type':'buyer1_signature','page':1,'signwellX':100,'signwellY':200}]}],**base)
        stable=[f for f in fields if not f['api_id'].startswith(('repair_continuation_','nonrealty_continuation_','uploaded_'))]
        self.assertEqual(stable,old_fields)
        repairs={f['page'] for f in fields if f['api_id'].startswith('repair_continuation_')}
        items={f['page'] for f in fields if f['api_id'].startswith('nonrealty_continuation_')}
        self.assertEqual(min(repairs),len(short.pages)+1)
        self.assertLess(max(repairs),min(items))
        self.assertLess(max(items),len(reader.pages))
        self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('uploaded_')},{len(reader.pages)})
        self.assertEqual(len({f['api_id'] for f in fields}),len(fields))

    def test_existing_seller_signer_can_initial_without_new_recipients(self):
        offer=residential_lease_offer(nonRealtyItems='yes',nonRealtyDescription=item_list(12),
                                     asIs='repairs',repairsText=long_terms())
        pdf=adapter.fill_and_merge_20_19(offer)
        fields=adapter.build_signwell_fields_20_19(offer,pdf)[0]
        for prefix in ('repair_continuation_','nonrealty_continuation_'):
            marks=[f for f in fields if f['api_id'].startswith(prefix)]
            self.assertEqual({f['recipient_id'] for f in marks},{'1','3'})
            self.assertEqual(len({f['page'] for f in marks}),1)

    def test_continuation_cannot_be_sent_without_its_underlying_addendum(self):
        with patch.object(adapter.verified,'NON_REALTY_PDF','/nonexistent/form.pdf'), patch.object(adapter.verified,'NON_REALTY_PDF_ALT','/nonexistent/form.pdf'):
            for count in (1,12):
                with self.subTest(count=count), self.assertRaisesRegex(ValueError,'addendum source is unavailable'):
                    self.packet(item_list(count))

    def test_explicit_zero_amount_is_not_dropped_or_replaced_by_a_default(self):
        for amount,expected in [(0,'0'),('0','0'),('',''),(None,'')]:
            with patch.object(adapter.verified,'stamp_pdf',wraps=adapter.verified.stamp_pdf) as stamp:
                self.packet(item_list(1),nonRealtyAmount=amount)
            call=next(c for c in stamp.call_args_list if c.args[0]==adapter.verified.NON_REALTY_PDF)
            entry=next(e for e in call.args[1][0] if e[:2]==(220,614))
            self.assertEqual(entry[2],expected)


if __name__=='__main__': unittest.main()

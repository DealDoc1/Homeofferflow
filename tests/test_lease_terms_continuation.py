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


def answer_key(kind, section):
    suffix = 'UtilitiesPaidBy' + ('Seller' if kind == 'buyer' else 'Buyer') if section == 'utilities' else 'PetsAllowed'
    return kind + 'TemporaryLease' + suffix


def long_answer(section, count=12):
    return '\n'.join(f'{section.upper()}-{n:03d}: Preserve this complete example answer without shortening any detail.'
                     for n in range(1, count+1))


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
                base.update({answer_key(kind,section):long_answer(section) for section in ('utilities','pets')})
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

    def test_short_utility_and_pet_answers_remain_in_their_blanks(self):
        for kind in ('buyer','seller'):
            values = {answer_key(kind,'utilities'):'Water and trash', answer_key(kind,'pets'):'One dog'}
            _,reader,fields = self.packet(kind,'Return keys.',**values)
            self.assertEqual(len(reader.pages),14)
            for text in values.values(): self.assertIn(text,reader.pages[12].extract_text())
            self.assertFalse(any(f['api_id'].startswith('lease_continuation_') for f in fields))

    def test_each_utility_and_pet_answer_is_preserved_in_a_labeled_continuation(self):
        for kind in ('buyer','seller'):
            for section in ('utilities','pets'):
                with self.subTest(kind=kind,section=section):
                    value=long_answer(section)
                    _,reader,fields=self.packet(kind,'Return keys.',**{answer_key(kind,section):value})
                    self.assertIn(lease.SHORT_REFERENCE,reader.pages[12].extract_text())
                    result='\n'.join(p.extract_text() for p in reader.pages[14:])
                    self.assertIn(lease.LABELS[section],result)
                    self.assertNotIn(lease.LABELS['special'],result)
                    for n in range(1,13): self.assertEqual(result.count(f'{section.upper()}-{n:03d}:'),1)
                    self.assertNotIn('...',result)
                    self.assertTrue(any(f['api_id'].startswith('lease_continuation_') for f in fields))
                    x,y,reference,size=lease.text_entries(value,kind,section)[0]
                    self.assertLessEqual(stringWidth(reference,'Helvetica',size),lease.section_blanks(kind,section)[0][2])

    def test_combined_sections_preserve_original_order_and_terms_once(self):
        for kind in ('buyer','seller'):
            values={answer_key(kind,section):long_answer(section,30) for section in ('utilities','pets')}
            _,reader,fields=self.packet(kind,long_terms(),**values)
            result='\n'.join(p.extract_text() for p in reader.pages[14:])
            self.assertLess(result.index(lease.LABELS['utilities']),result.index(lease.LABELS['pets']))
            self.assertLess(result.index(lease.LABELS['pets']),result.index(lease.LABELS['special']))
            for section in ('utilities','pets'):
                for n in range(1,31): self.assertEqual(result.count(f'{section.upper()}-{n:03d}:'),1)
            self.assertEqual(result.count('FINAL TERM:'),1)
            marks=[f for f in fields if f['api_id'].startswith('lease_continuation_')]
            for page in range(15,len(reader.pages)+1):
                self.assertEqual({f['recipient_id'] for f in marks if f['page']==page}, {'1','3'} if kind=='seller' else {'1'})

    def test_utility_and_pet_aliases_preserve_long_answers(self):
        for kind in ('buyer','seller'):
            for section,suffix in (('utilities','Utilities'),('pets','Pets')):
                for key in (kind+'TempLease'+suffix,'temporaryLease'+suffix):
                    with self.subTest(kind=kind,key=key):
                        _,reader,_=self.packet(kind,'',**{key:long_answer(section)})
                        self.assertIn(f'{section.upper()}-012:',reader.pages[-1].extract_text())

    def test_unbroken_pet_and_utility_tokens_survive_instead_of_disappearing(self):
        for kind in ('buyer','seller'):
            for section in ('utilities','pets'):
                with self.subTest(kind=kind,section=section):
                    value='Z'*800 + '\nLiteral <oak> & pine. FINAL-ANSWER.'
                    _,reader,_=self.packet(kind,'',**{answer_key(kind,section):value})
                    result='\n'.join(p.extract_text() for p in reader.pages[14:])
                    self.assertEqual(sum(len(run) for run in re.findall('Z{2,}',result)),800)
                    self.assertIn('Literal <oak> & pine. FINAL-ANSWER.',result)

    def test_deselected_lease_and_other_lease_answers_do_not_leak(self):
        stale={answer_key(kind,section):long_answer(section) for kind in ('buyer','seller') for section in ('utilities','pets')}
        offer=minimal_offer(**stale)
        self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages),12)
        for kind,other in (('buyer','seller'),('seller','buyer')):
            _,reader,_=self.packet(kind,'',**{answer_key(other,section):long_answer(section) for section in ('utilities','pets')})
            self.assertEqual(len(reader.pages),14)

    def test_notice_addresses_fit_independently_measured_source_rules(self):
        rules = {
            ('buyer','landlord_mail'): [(134.98,298.8,465.55),(51.75,298.8,485.14),(51.75,298.8,504.64)],
            ('buyer','tenant_mail'): [(382.94,573.94,465.55),(307.8,573.94,485.14),(307.8,573.94,504.64)],
            ('seller','landlord_mail'): [(127.42,305.4,465.48),(52.28,305.4,484.43),(52.28,305.4,503.38)],
            ('seller','tenant_mail'): [(391.91,574.88,465.48),(324.07,574.88,484.43),(324.07,574.88,503.38)],
        }
        for (kind,section),bounds in rules.items():
            with self.subTest(kind=kind,section=section):
                value=' '.join(['WWW']*20)
                entries=lease.inline_entries(value,kind,section)
                self.assertIsNotNone(entries)
                self.assertEqual(' '.join(e[2] for e in entries),value)
                for (x,y,text,size),(left,right,top) in zip(entries,bounds):
                    self.assertEqual(size,7.5)
                    self.assertGreaterEqual(x,left)
                    self.assertLessEqual(x+stringWidth(text,'Helvetica',size),right)
                    self.assertLess(792-y+size*.207,top)

    def test_notice_addresses_follow_landlord_and_tenant_roles_in_actual_pdf(self):
        values={'buyerMailAddr':'222 Example Buyer Road', 'sellerMailAddr':'111 Example Seller Road'}
        for kind in ('buyer','seller'):
            _,reader,_=self.packet(kind,'',**values)
            self.assertEqual(len(reader.pages),14)
            spans=[]
            reader.pages[13].extract_text(visitor_text=lambda t,cm,tm,font,size:spans.append((t.strip(),tm[4],tm[5])))
            for section,party in [('landlord_mail','seller' if kind=='buyer' else 'buyer'),
                                  ('tenant_mail','buyer' if kind=='buyer' else 'seller')]:
                found=[s for s in spans if s[0]==values[party+'MailAddr']]
                self.assertEqual(len(found),1)
                self.assertEqual(found[0][1:],lease.section_blanks(kind,section)[0][:2])

    def test_long_notice_addresses_survive_with_correct_paragraph_and_role(self):
        buyer='\n'.join(f'BUYER-ADDR-{n:03d}: Example care-of office and building detail.' for n in range(1,21))+'\nExample City, TX 75001'
        seller='\n'.join(f'SELLER-ADDR-{n:03d}: Example care-of office and building detail.' for n in range(1,21))+'\nExample City, TX 75002'
        for kind in ('buyer','seller'):
            _,reader,fields=self.packet(kind,'',buyerMailAddr=buyer,sellerMailAddr=seller)
            self.assertEqual(reader.pages[13].extract_text().count(lease.SHORT_REFERENCE),2)
            result='\n'.join(p.extract_text() for p in reader.pages[14:])
            for prefix in ('BUYER','SELLER'):
                for n in range(1,21): self.assertEqual(result.count(f'{prefix}-ADDR-{n:03d}:'),1)
            left=result.index(lease.LABELS['landlord_mail'])
            right=result.index(lease.LABELS['tenant_mail'])
            self.assertLess(left,right)
            expected_left='SELLER' if kind=='buyer' else 'BUYER'
            expected_right='BUYER' if kind=='buyer' else 'SELLER'
            self.assertIn(expected_left+'-ADDR-001:',result[left:right])
            self.assertIn(expected_right+'-ADDR-001:',result[right:])
            for page in range(15,len(reader.pages)+1):
                marks=[f for f in fields if f['page']==page]
                self.assertEqual({f['recipient_id'] for f in marks},{'1','3'} if kind=='seller' else {'1'})

    def test_notice_address_aliases_do_not_override_current_party_address(self):
        for kind in ('buyer','seller'):
            for section,role in [('landlord_mail','landlord'),('tenant_mail','tenant')]:
                party='seller' if (kind=='buyer')==(role=='landlord') else 'buyer'
                self.assertEqual(lease.terms({role+'MailAddr':'Alias Address'},kind,section),'Alias Address')
                self.assertEqual(lease.terms({party+'MailAddr':'Current Address',role+'MailAddr':'Old Address'},kind,section),'Current Address')

    def test_unbroken_notice_tokens_are_preserved_without_crossing_columns(self):
        for kind in ('buyer','seller'):
            _,reader,_=self.packet(kind,'',buyerMailAddr='Z'*800+' END-ADDRESS')
            result='\n'.join(p.extract_text() for p in reader.pages[14:])
            self.assertEqual(sum(len(run) for run in re.findall('Z{2,}',result)),800)
            self.assertIn('END-ADDRESS',result)


if __name__ == '__main__': unittest.main()

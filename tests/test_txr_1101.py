"""Sale-listing contract and geometry checks; never send a customer packet."""
from copy import deepcopy
from io import BytesIO
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from pypdf import PdfReader

from lib import txr_1101 as form
from lib.pdf_text import text_width


BROKER = {'legal_name':'QA Realty', 'license_number':'9000000',
          'address':'10 Example Lane', 'city_state_zip':'Dallas, TX 75201',
          'phone':'214-555-0100', 'email':'broker@example.com'}
ASSOCIATE = {'agent_name':'QA Associate', 'license_number':'0000001'}


def sample_answers(**updates):
    result = {
        'client_names':['QA Seller One','QA Seller Two'],
        'client_address':'100 Fictional Lane', 'client_city_state_zip':'Frisco, TX 75033',
        'client_phone':'214-555-0101', 'client_email':'seller@example.com',
        'client_email_2':'seller2@example.com', 'property_address':'200 Example Street, Frisco, TX 75033',
        'lot':'12', 'block':'A', 'subdivision':'Example Estates', 'city':'Frisco', 'county':'Collin',
        'listing_price':'625000', 'term_start':'2026-10-17', 'term_end':'2027-04-17',
        'hoa':'yes', 'fee_basis':'percentage', 'fee_amount':'2.5',
        'additional_fee_basis':'none', 'disclose_buyer_expenses':'yes',
        'protection_days':'30', 'payment_county':'Collin', 'mls_filing':'standard',
        'internet_display':'full', 'scheduling_companies':'Example Showing Service',
        'keybox':'yes', 'intermediary':'authorized', 'foreign_person':'unanswered',
        'financing':['conventional','va','fha','cash'], 'addenda':['A','B'],
        'signer_plan':'clients_and_associate',
    }
    result.update(updates)
    return result


def qa_cases():
    return {
        'standard-two':sample_answers(),
        'flat-one':sample_answers(client_names=['QA Single Seller'], fee_basis='flat',fee_amount='12000'),
        'broker-two':sample_answers(signer_plan='clients_and_broker',intermediary='not_authorized',
                                  hoa='no',keybox='no',disclose_buyer_expenses='no',foreign_person='no'),
        'delayed-two':sample_answers(mls_filing='delayed',mls_delay_days='7',
                                    mls_delay_purpose='Complete property photographs before marketing.',
                                    internet_display='hide_address'),
        'offmls-one':sample_answers(client_names=['QA Seller'],mls_filing='none',
                                  internet_display='not_applicable',foreign_person='yes'),
        'extra-fee-two':sample_answers(additional_fee_basis='percentage',additional_fee_amount='1',
                                    other_compensation='Seller-approved additional service fee of $100.',
                                    other_fees='Seller-approved photography expense of $250.',
                                    financial_exceptions='QA mortgage payment exception supplied by Seller.',
                                    liens='QA recorded lien identified by Seller.',
                                    relocation_entity='QA Relocation Company',
                                    districts='QA municipal utility district supplied by Seller.',
                                    special_provisions='QA entered provision for placement review only.',
                                    internet_display='hide_listing',financing=list(form.FINANCING),
                                    addenda=list('ABCDEFGHIJKLMNOP'),other_documents='QA other document'),
        'unicode-two':sample_answers(client_names=['QA José Núñez','QA 李华'],
                                   exclusions='Seller retains the bibliothèque and 茶桌.',
                                   liens='QA recorded document — lender release pending.',
                                   districts='QA district information supplied by Seller.'),
        'overflow-one':sample_answers(client_names=['QA Seller ' + 'Long legal name '*15],
                                    exclusions='QA retained item ' * 75,
                                    other_compensation='QA seller-approved term ' * 60,
                                    special_provisions='QA entered text; no inferred terms. '*100,
                                    other_documents='QA document ' * 120),
    }


class Txr1101AnswerTests(unittest.TestCase):
    def test_all_interview_branches_validate_without_mutating_answers(self):
        for label,data in qa_cases().items():
            with self.subTest(label=label):
                before = deepcopy(data)
                self.assertEqual(form.validate_answers(data)['client_names'],
                                 [' '.join(name.split()) for name in data['client_names']])
                self.assertEqual(data,before)

    def test_no_inferred_fee_or_disclosure_choices(self):
        for key in ('fee_basis','disclose_buyer_expenses','intermediary','foreign_person','hoa','keybox'):
            data=sample_answers(); data.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError): form.validate_answers(data)
        self.assertEqual(form.validate_answers(sample_answers())['foreign_person'],'unanswered')

    def test_zero_compensation_is_explicit_and_valid(self):
        self.assertEqual(form.validate_answers(sample_answers(fee_amount='0'))['fee_amount'],'0')
        with self.assertRaises(ValueError):
            form.validate_answers(sample_answers(fee_basis='none',fee_amount=''))

    def test_amounts_do_not_round_or_accept_nonfinite_values(self):
        for key,value in [('fee_amount','NaN'),('fee_amount','101'),('fee_amount',True),
                          ('listing_price','0'),('listing_price','1e6'),('listing_price','500.001'),
                          ('listing_price',-1),('fee_amount','2.12345')]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                form.validate_answers(sample_answers(**{key:value}))

    def test_inactive_compensation_and_mls_branches_do_not_drop_hidden_terms(self):
        for values in [dict(additional_fee_amount='100'),dict(mls_delay_days='7'),
                       dict(mls_delay_purpose='Stale hidden text'),
                       dict(mls_filing='none'),dict(internet_display='not_applicable'),
                       dict(mls_filing='delayed'),dict(mls_filing='delayed',mls_delay_days='0')]:
            with self.subTest(values=values),self.assertRaises(ValueError):
                form.validate_answers(sample_answers(**values))

    def test_dates_and_seller_counts(self):
        for values in [dict(term_start='2026-02-30'),dict(term_start='20261017'),
                       dict(term_end='2025-01-01'),dict(client_names=[]),
                       dict(client_names=['One','Two','Three']),dict(client_names=[''])]:
            with self.subTest(values=values),self.assertRaises(ValueError):
                form.validate_answers(sample_answers(**values))

    def test_unsupported_or_oversized_answers_fail_instead_of_disappearing(self):
        for values in [dict(unknown_term='Never drop me'),dict(exclusions='x'*2001),
                       dict(addenda=['Q']),dict(addenda=['A','A']),dict(financing=['imagined']),
                       dict(financing=['cash','cash']),dict(client_email='not-an-email')]:
            with self.subTest(values=values),self.assertRaises(ValueError):
                form.validate_answers(sample_answers(**values))

    def test_layout_has_source_anchors_and_current_ondemand_license(self):
        pages,overflow=form.answer_layout(sample_answers(),{'name':'OnDemand Realty'},ASSOCIATE)
        self.assertFalse(overflow)
        self.assertIn((478,108,'625000',8),pages[1])
        self.assertIn((184,717,'10/17/2026',8),pages[2])
        self.assertIn((230,610,'9010832',8),pages[10])
        self.assertIn((29,517,'QA Associate',8),pages[10])
        self.assertIn((326,610,'QA Seller One',8),pages[10])

    def test_every_inline_value_fits_a_measured_blank_and_long_answers_survive(self):
        for label,data in qa_cases().items():
            with self.subTest(label=label):
                pages,overflow=form.answer_layout(data,BROKER,ASSOCIATE)
                for page in pages.values():
                    for x,y,text,size in page:
                        self.assertTrue(0<=x<612 and 0<=y<792)
                        self.assertLessEqual(text_width(text,'Helvetica',size),576-x+1)
                if label=='overflow-one':
                    self.assertEqual(overflow['Exclusions'],data['exclusions'].strip())
                    self.assertEqual(overflow['Special Provisions'],data['special_provisions'].strip())
                    self.assertTrue(any('continuation' in entry[2] for entry in pages[8]))

    def test_only_explicit_checkbox_choices_are_marked(self):
        with patch.object(form,'_mark') as mark:
            form._overlay(sample_answers(),BROKER,ASSOCIATE)
        cells=[call.args[1:] for call in mark.call_args_list]
        self.assertIn((56,283),cells)  # MLS parent plus standard child.
        self.assertIn((74,266),cells)
        self.assertIn((28,548),cells)  # Associate execution.
        self.assertNotIn((28,558),cells)
        self.assertNotIn((528,142),cells)  # Unanswered foreign-person status.
        self.assertNotIn((74,126),cells)
        self.assertNotIn((55,607),cells)  # No hidden-Internet restriction.

    def test_source_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'reviewed June'):
            form.render_txr_1101(b'wrong source',sample_answers(),BROKER,ASSOCIATE)


class Txr1101SigningTests(unittest.TestCase):
    def test_one_two_seller_and_professional_role_matrix(self):
        for count in (1,2):
            for role in ('associate','broker'):
                data=sample_answers(client_names=['QA Seller One','QA Seller Two'][:count],
                                    signer_plan='clients_and_'+role)
                fields=form.build_signwell_fields_txr1101(data,client_count=count,page_count=12)[0]
                recipients={'1',role}|({'2'} if count==2 else set())
                self.assertEqual({f['recipient_id'] for f in fields},recipients)
                self.assertEqual(len(fields),13*(count+1))  # 9 source initials, 2 execution, 2 continuation.
                self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
                for field in fields:
                    self.assertTrue(field['required'])
                    self.assertGreaterEqual(field['x'],0);self.assertGreaterEqual(field['y'],0)
                    self.assertLessEqual(field['x']+field['width'],816)
                    self.assertLessEqual(field['y']+field['height'],1056)
                    if field['type']=='date':
                        self.assertTrue(field['lock_sign_date'])
                        self.assertEqual(field['date_format'],'MM/DD/YYYY')
                # No sign-order metadata: existing send path supplies simultaneous invitations.
                self.assertFalse(any('order' in f for f in fields))

    def test_footer_fields_stay_inside_the_source_underscore_blanks(self):
        fields=form.build_signwell_fields_txr1101(sample_answers(),client_count=2)[0]
        blanks={'1':(406.51,444.02),'2':(446.55,481.52),'associate':(325.98,361.06)}
        for f in fields:
            if f['page']>=10:continue
            lo,hi=blanks[f['recipient_id']]
            self.assertGreaterEqual(f['x']*.75,lo)
            self.assertLessEqual((f['x']+f['width'])*.75,hi)

    def test_signature_and_date_rectangles_use_signature_not_printed_name_rows(self):
        fields=form.build_signwell_fields_txr1101(sample_answers(),client_count=2)[0]
        for f in fields:
            if f['page']!=10:continue
            bottom=792-(f['y']+f['height'])*.75
            top=792-f['y']*.75
            rule=473.1 if f['recipient_id']=='2' else 566.3
            name_rule=514.5 if f['recipient_id']=='2' else 607.7
            self.assertGreater(bottom,rule)
            self.assertLess(top,name_rule-5)
            if f['type']=='date': self.assertGreaterEqual(f['width']*.75,54)

    def test_wrong_counts_or_page_counts_are_rejected(self):
        for kwargs in [dict(client_count=True),dict(client_count=1),dict(client_count=3),
                       dict(client_count=2,page_count=9),dict(client_count=2,page_count=True),
                       dict(client_count=2,page_count=101)]:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                form.build_signwell_fields_txr1101(sample_answers(),**kwargs)


@unittest.skipUnless(os.environ.get('HOF_TXR1101_SOURCE'),'Private exact-source QA is opt-in.')
class Txr1101PrivateSourceTests(unittest.TestCase):
    def test_exact_source_matrix_roundtrip_preserves_boilerplate_and_removes_supplier_footer(self):
        source=Path(os.environ['HOF_TXR1101_SOURCE']).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),form.SOURCE_SHA256)
        originals=PdfReader(BytesIO(source))
        for label,data in qa_cases().items():
            with self.subTest(label=label):
                result=form.render_txr_1101(source,data,BROKER,ASSOCIATE)
                reader=PdfReader(BytesIO(result))
                self.assertGreaterEqual(len(reader.pages),10)
                text='\n'.join(p.extract_text() or '' for p in reader.pages)
                self.assertNotIn('Andrew Christian',text)
                self.assertNotIn('Greenville',text)
                self.assertIn('EXCLUSIVE RIGHT TO SELL',text)
                self.assertIn('CONFIDENTIAL INFORMATION',text)
                self.assertIn('CONSULT AN ATTORNEY',text)
                self.assertIn('QA Realty',text)
                for i,p in enumerate(reader.pages[:10]):
                    self.assertIn('06-15-26',p.extract_text() or '')
                    # Every original clause/header/copyright remains intact;
                    # only the source supplier's final two imprint lines go.
                    original_lines=[line for line in (originals.pages[i].extract_text() or '').splitlines()
                                    if line.strip()]
                    original_form=' '.join(' '.join(original_lines[:-2]).split())
                    actual=' '.join((p.extract_text() or '').split())
                    self.assertTrue(actual.startswith(original_form),f'{label}, page {i+1}')
                fields=form.build_signwell_fields_txr1101(data,
                    client_count=len(data['client_names']),page_count=len(reader.pages))[0]
                self.assertEqual(max(f['page'] for f in fields),len(reader.pages))
                if label=='overflow-one':
                    self.assertGreater(len(reader.pages),10)
                    self.assertIn('Paragraph 19Q - Other documents',text)


if __name__=='__main__':unittest.main()

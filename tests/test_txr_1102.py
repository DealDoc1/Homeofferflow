"""Pure lease-listing contract and exact private-source opt-in checks; no sends."""
from copy import deepcopy
from io import BytesIO
import os
from pathlib import Path
import unittest

from pypdf import PdfReader

from lib import txr_1102 as form

BROKER={'name':'OnDemand Realty','license_number':'','address':'10 Fictional Plaza',
        'city_state_zip':'Dallas, TX 75201','phone':'214-555-0100','email':'broker@example.test'}
ASSOCIATE={'agent_name':'QA Associate','license_number':'000001'}


def sample(**changes):
    data={'client_names':['QA Landlord One','QA Landlord Two'],'property_address':'100 Fictional QA Lane, Dallas, TX 75201',
        'client_address':'200 Fictional Client Lane','client_city_state_zip':'Plano, TX 75024',
        'client_phone':'214-555-0123','client_email':'landlord-one@example.test','client_email_2':'landlord-two@example.test',
        'lot':'12','block':'B','subdivision':'Fictional QA Addition','city':'Dallas','county':'Dallas',
        'non_real_estate_items':'Refrigerator and washer','exclusions':'Garage shelving',
        'listing_price':'2500.00','lease_min_months':'12','lease_max_months':'24',
        'term_start':'2026-11-01','term_end':'2027-03-01','hoa':'yes',
        'fee_scope':'with_other_broker','fee_basis':'month_percentage','fee_amount':'100',
        'cobroker_basis':'month_percentage','cobroker_amount':'50',
        'renewal_basis':'total_percentage','renewal_amount':'2.5','sale_fee_basis':'percentage','sale_fee_amount':'3',
        'protection_days':'90','payment_county':'Dallas','mls_filing':'standard','internet_display':'full',
        'keybox':'yes','intermediary':'authorized','make_ready':'not_authorized',
        'signer_plan':'clients_and_associate','addenda':['A','B','C','K'],'built_before_1978':'yes',
        'reimbursable_expenses':'Landlord-approved advertising expense only',
        'financial_exceptions':'None reported for this fictional test','liens':'Fictional mortgage lien',
        'common_area_fees':'Optional fictional gym fee','health_safety_conditions':'Fictional repair note',
        'special_provisions':'Fictional QA instructions only. Not for a real transaction.'}
    data.update(changes);return data


def with_preferences(**changes):
    data=sample(include_rental_preferences=True,rent_due='first',late_after_days='3',
        initial_late_basis='flat',initial_late_amount='50',daily_late_amount='10',animals='permitted',
        animal_restrictions='Two household animals; see agreed terms',animal_deposit='300',animal_monthly_rent='25',
        animal_one_time_fee='100',animal_violation_initial='100',animal_violation_daily='10',
        security_deposit='2500',utilities_exceptions='Landlord pays fictional waste service',guests_days='10',vehicle_count='3',
        trip_charge='50',keybox_last_days='30',keybox_withdrawal_fee='100',inventory_days='5',yard='tenant',pool='landlord',
        repair_phone='214-555-0199',unrepaired_items='Fictional decorative light',liability_insurance='100000',
        tenant_replacement_basis='flat',tenant_replacement_amount='500',landlord_replacement_basis='percentage',
        landlord_replacement_amount='25',lease_special_provisions='Fictional preference note.',lease_other='Fictional other note.')
    data.update(changes);return data


class LeaseListingTests(unittest.TestCase):
    def test_roundtrip_is_lossless_idempotent_and_never_mutates_inputs(self):
        for original in (sample(),with_preferences()):
            before=deepcopy(original);result=form.validate_answers(original)
            self.assertEqual(original,before);self.assertEqual(result,form.validate_answers(result))
            self.assertEqual(result['fee_amount'],'100');self.assertEqual(result['sale_fee_amount'],'3')

    def test_core_choices_dates_terms_and_property_cannot_be_inferred(self):
        cases=[{'client_names':[]},{'client_names':['A','B','C']},{'client_names':['']},{'property_address':''},
            {'term_start':'11/01/2026'},{'term_end':'2026-02-30'},{'term_end':'2026-01-01'},
            {'listing_price':0},{'lease_min_months':0},{'lease_min_months':'24','lease_max_months':'12'},
            {'lease_max_months':True},{'hoa':'unknown'},{'fee_basis':None},{'arbitrary_recipient':'injected'}]
        for values in cases:
            with self.subTest(values=values),self.assertRaises(ValueError):form.validate_answers(sample(**values))

    def test_money_never_rounds_exponents_booleans_nan_or_extra_precision(self):
        for key in ('listing_price','fee_amount','cobroker_amount','renewal_amount','sale_fee_amount'):
            for value in (True,'NaN','1e2','-1','1.00001'):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):form.validate_answers(sample(**{key:value}))
        result=form.validate_answers(sample(fee_amount='150',cobroker_amount='125'))
        self.assertEqual(result['fee_amount'],'150')  # Negotiated month-based fees are not capped at one month.
        with self.assertRaises(ValueError):form.validate_answers(sample(cobroker_amount='101'))

    def test_fee_scope_other_terms_and_zero_are_explicit(self):
        result=form.validate_answers(sample(fee_scope='broker_only',cobroker_basis='',cobroker_amount='',
            fee_basis='other',fee_amount='',fee_other='No fee for this fictional demonstration',
            renewal_basis='other',renewal_amount='',renewal_other='No renewal fee',sale_fee_basis='other',sale_fee_amount='',sale_fee_other='No sale fee'))
        self.assertEqual(result['fee_amount'],'');self.assertEqual(result['fee_scope'],'broker_only')
        for values in ({'fee_scope':'broker_only'},{'fee_basis':'other'},{'fee_other':'Conflicting fee'},
                       {'cobroker_basis':'flat','cobroker_amount':''}):
            with self.subTest(values=values),self.assertRaises(ValueError):form.validate_answers(sample(**values))
        self.assertEqual(form.validate_answers(sample(fee_amount='0',cobroker_amount='0'))['fee_amount'],'0')

    def test_make_ready_and_mls_branch_values_are_not_silently_dropped(self):
        for values in ({'mls_filing':'delayed'},{'mls_filing':'none'},{'mls_delay_days':'5'},
                       {'make_ready_limit':'100'},{'make_ready':'landlord_pays','make_ready_limit':'100'}):
            with self.subTest(values=values),self.assertRaises(ValueError):form.validate_answers(sample(**values))
        result=form.validate_answers(sample(mls_filing='delayed',mls_delay_days='5',mls_delay_purpose='Landlord preparation',
            make_ready='broker_reimbursed',make_ready_limit='250',make_ready_service_fee='0'))
        self.assertEqual(result['make_ready_service_fee'],'0')
        self.assertEqual(form.validate_answers(sample(mls_filing='none',internet_display='not_applicable'))['mls_filing'],'none')

    def test_rental_preferences_are_optional_and_never_default_to_no_or_zero(self):
        result=form.validate_answers(sample())
        self.assertFalse(result['include_rental_preferences']);self.assertEqual(result['animals'],'unspecified')
        self.assertEqual(result['security_deposit'],'')
        for values in ({'security_deposit':'0'},{'animals':'not_permitted'},{'include_rental_preferences':'yes'}):
            with self.subTest(values=values),self.assertRaises(ValueError):form.validate_answers(sample(**values))
        self.assertEqual(form.validate_answers(with_preferences(security_deposit='0'))['security_deposit'],'0')

    def test_conditional_rental_preferences_reject_stale_or_incomplete_values(self):
        for values in ({'rent_due':'other'},{'rent_due_other':'10th'},{'animals':'not_permitted'},
                       {'yard':'named_contractor'},{'pool':'other'},{'tenant_replacement_basis':'unspecified'},
                       {'initial_late_basis':'percentage','initial_late_amount':'101'}):
            with self.subTest(values=values),self.assertRaises(ValueError):form.validate_answers(with_preferences(**values))
        result=form.validate_answers(with_preferences(rent_due='other',rent_due_other='10th of each month',
            yard='named_contractor',yard_contractor='Fictional Yard Co',pool='other',pool_other='No pool at property'))
        self.assertEqual(result['pool_other'],'No pool at property')

    def test_selected_related_documents_are_requests_not_fake_attachments(self):
        self.assertEqual(form.validate_answers(sample(addenda=[]))['addenda'],['B','C'])
        self.assertEqual(form.validate_answers(sample(built_before_1978='unanswered',addenda=[]))['addenda'],['B','C'])
        self.assertEqual(form.validate_answers(sample(built_before_1978='no',addenda=[]))['addenda'],['B'])
        self.assertEqual(form.validate_answers(sample(built_before_1978='no',addenda=['C']))['addenda'],['B'])
        self.assertEqual(form.validate_answers(sample(built_before_1978='no',addenda=[],other_documents='Fictional notice'))['addenda'],['B','L'])
        for selected in (['A','A'],['M'],['L'],[{}],'ABC'):
            with self.subTest(selected=selected),self.assertRaises(ValueError):form.validate_answers(sample(addenda=selected))

    def test_field_plan_has_explicit_roles_locked_dates_and_no_signing_order(self):
        for count in (1,2):
            for role in ('clients_and_broker','clients_and_associate'):
                data=sample(client_names=['QA One','QA Two'][:count],signer_plan=role)
                fields=form.build_signwell_fields_txr1102(data,client_count=count,page_count=13)[0]
                self.assertEqual({f['recipient_id'] for f in fields},{*map(str,range(1,count+1)),'broker' if role.endswith('_broker') else 'associate'})
                self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
                for f in fields:
                    self.assertTrue(0<=f['x']<816 and 0<=f['y']<1056)
                    self.assertLessEqual(f['x']+f['width'],816);self.assertLessEqual(f['y']+f['height'],1056)
                    self.assertIn(f['page'],range(1,14))
                    if f['type']=='date':self.assertTrue(f['lock_sign_date']);self.assertEqual(f['date_format'],'MM/DD/YYYY')
                self.assertEqual({f['page'] for f in fields if f['type']=='signature'},{11})
                self.assertEqual({f['page'] for f in fields if f['type']=='initials'},set(range(1,14)))
        for count,pages in ((True,11),(1,10),(1,True),(2,101)):
            with self.subTest(count=count,pages=pages),self.assertRaises(ValueError):form.build_signwell_fields_txr1102(sample(),client_count=count,page_count=pages)

    def test_long_unicode_answers_keep_complete_values_in_a_referenced_exhibit(self):
        data=sample(client_names=['Élodie QA 李'],special_provisions='Fictional Büro 李 '*150)
        pages,overflow=form.answer_layout(data,BROKER,ASSOCIATE)
        self.assertEqual(overflow[form.LABELS['special_provisions']],data['special_provisions'].strip())
        self.assertTrue(any('continuation' in value.lower() for x,y,value,size in pages[9]))
        self.assertTrue(any(value=='9010832' for x,y,value,size in pages[11]))

    def test_replacement_percentage_stays_inside_its_actual_narrow_source_blank(self):
        pages,overflow=form.answer_layout(with_preferences(),BROKER,ASSOCIATE)
        replacement=[entry for entry in pages[10] if entry[1]==487]
        self.assertEqual(len(replacement),1)
        self.assertEqual(replacement[0][0],318)
        self.assertLessEqual(replacement[0][3],7)
        self.assertNotIn(form.LABELS['landlord_replacement_amount'],overflow)
        _,overflow=form.answer_layout(with_preferences(landlord_replacement_amount='25.1234'),BROKER,ASSOCIATE)
        self.assertEqual(overflow[form.LABELS['landlord_replacement_amount']],'25.1234')

    def test_arbitrary_source_is_rejected_before_reading_or_rendering(self):
        with self.assertRaises(ValueError):form.render_txr_1102(b'%PDF-unapproved',sample(),BROKER,ASSOCIATE)

    def test_broker_execution_does_not_fill_an_unused_associate_identity(self):
        pages,_=form.answer_layout(sample(signer_plan='clients_and_broker'),BROKER,ASSOCIATE)
        self.assertFalse(any(value==ASSOCIATE['agent_name'] or value==ASSOCIATE['license_number'] for x,y,value,size in pages[11]))

    def test_other_documents_are_preserved_once_when_a_continuation_is_needed(self):
        text='Fictional related notice Büro 李 '*25
        _,overflow=form.answer_layout(sample(other_documents=text),BROKER,ASSOCIATE)
        self.assertEqual(list(overflow.values()).count(text.strip()),1)
        self.assertEqual(overflow['Paragraph 19L - Other documents'],text.strip())

    @unittest.skipUnless(os.environ.get('HOF_TXR1102_SOURCE'),'Exact private lease source opt-in')
    def test_actual_complete_source_is_preserved_without_source_host_imprints(self):
        source=Path(os.environ['HOF_TXR1102_SOURCE']).read_bytes()
        for data in (sample(),with_preferences(),sample(client_names=['QA 李'],special_provisions='Fictional Büro 李 '*150)):
            result=PdfReader(BytesIO(form.render_txr_1102(source,data,BROKER,ASSOCIATE)))
            self.assertGreaterEqual(len(result.pages),11)
            for page in result.pages[:11]:
                text=page.extract_text()
                self.assertIn('TXR-1102',text.replace(' ',''));self.assertNotIn('Andrew Christian',text);self.assertNotIn('12225 Greenville',text)
            self.assertIn('9010832',result.pages[10].extract_text())

    @unittest.skipUnless(os.environ.get('HOF_TXR1102_SOURCE'),'Exact private lease source opt-in')
    def test_execution_rectangles_do_not_overlap_any_printed_source_label(self):
        import pdfplumber
        with pdfplumber.open(os.environ['HOF_TXR1102_SOURCE']) as source:
            chars=[c for c in source.pages[10].chars if c['text'].strip() and c['text']!='_']
            for field in form.build_signwell_fields_txr1102(sample(),client_count=2)[0]:
                if field['type'] not in ('signature','date'):continue
                left=field['x']*.75;right=left+field['width']*.75
                bottom=792-(field['y']+field['height'])*.75;top=bottom+field['height']*.75
                overlap=[c['text'] for c in chars if min(right,c['x1'])>max(left,c['x0']) and min(top,c['y1'])>max(bottom,c['y0'])]
                self.assertEqual(overlap,[],field['api_id'])


if __name__=='__main__':unittest.main()

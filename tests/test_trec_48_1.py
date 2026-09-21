from io import BytesIO
import unittest

from pypdf import PdfReader
from lib.trec_48_1 import (ADDRESS_FIELD, AMOUNT_FIELD, RISK_FIELDS, SOURCE_PATH,
    render_trec_48_1, validate_hydrostatic_terms, verified_source, build_signwell_fields_trec48_1)


class HydrostaticFormTests(unittest.TestCase):
    def data(self, risk='buyer_capped', amount='2,500.00'):
        return {'property_address':'123 Example Lane, Frisco', 'risk_allocation':risk,
                'buyer_liability_limit':amount}

    def test_all_risk_choices_update_canonical_values_and_widget_appearances(self):
        for risk in RISK_FIELDS:
            with self.subTest(risk=risk):
                reader = PdfReader(BytesIO(render_trec_48_1(self.data(risk))))
                fields = reader.get_fields()
                expected = {ADDRESS_FIELD:'123 Example Lane, Frisco',
                            AMOUNT_FIELD:'2,500.00' if risk == 'buyer_capped' else ''}
                expected.update({name:'/On' if key == risk else '/Off' for key,name in RISK_FIELDS.items()})
                for name,value in expected.items():
                    self.assertEqual(fields[name].get('/V'), value)
                canonical_ids = {ref.idnum for ref in reader.trailer['/Root']['/AcroForm']['/Fields']}
                for reference in reader.pages[0]['/Annots']:
                    widget = reference.get_object()
                    self.assertIn(reference.idnum, canonical_ids)
                    if widget['/T'] in expected:
                        self.assertEqual(widget.get('/V'),expected[widget['/T']])
                        self.assertTrue(widget.get('/AP').get('/N'))
                        if widget['/FT'] == '/Btn':
                            self.assertEqual(widget.get('/AS'),expected[widget['/T']])
                self.assertEqual(len(reader.pages),1)

    def test_no_risk_choice_is_assumed(self):
        for risk in ('',None,'both','unknown',[],{}):
            with self.assertRaises(ValueError):
                render_trec_48_1(self.data(risk))

    def test_capped_liability_requires_exact_valid_money(self):
        for value in ('',None,'NaN','Infinity','-1','1e4','2,00','100.001',True,'1000000000'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_hydrostatic_terms(self.data(amount=value))
        self.assertEqual(validate_hydrostatic_terms(self.data(amount=0))['buyer_liability_limit'],'0.00')

    def test_uncapped_choice_clears_stale_amount(self):
        self.assertEqual(validate_hydrostatic_terms(self.data('seller'))['buyer_liability_limit'],'')
        self.assertEqual(validate_hydrostatic_terms(self.data('buyer'))['buyer_liability_limit'],'')

    def test_missing_and_overlong_address_do_not_truncate(self):
        for address in ('','W' * 200, None, {}, []):
            with self.assertRaises(ValueError):
                render_trec_48_1({**self.data(),'property_address':address})

    def test_wrong_source_is_rejected(self):
        verified_source()
        with self.assertRaises(ValueError):
            verified_source(SOURCE_PATH.read_bytes() + b' changed')

    def test_all_four_party_count_combinations_use_source_signature_rectangles(self):
        for buyers in (1,2):
            for sellers in (1,2):
                fields = build_signwell_fields_trec48_1(buyer_count=buyers,seller_count=sellers,page=16)[0]
                self.assertEqual(len(fields),buyers+sellers)
                self.assertEqual({f['recipient_id'] for f in fields},
                                 {'1','3'} | ({'2'} if buyers==2 else set()) | ({'4'} if sellers==2 else set()))
                self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
                for field in fields:
                    self.assertEqual(field['page'],16)
                    self.assertEqual(field['type'],'signature')
                    self.assertGreater(field['x'],0)
                    self.assertLess(field['x']+field['width'],816)
                    self.assertGreater(field['y'],0)
                    self.assertLess(field['y']+field['height'],1056)

    def test_invalid_party_counts_and_page_are_rejected(self):
        for buyers,sellers,page in ((0,1,1),(1,3,1),(True,1,1),(1,1,0),(1,1,True)):
            with self.assertRaises(ValueError):
                build_signwell_fields_trec48_1(buyer_count=buyers,seller_count=sellers,page=page)


if __name__ == '__main__':
    unittest.main()

from io import BytesIO
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from lib import trec_seller_disclosure as m
from lib.seller_disclosure_draft import parse_seller_disclosure_draft

class SellerDisclosureLayoutRoundtripTests(unittest.TestCase):
    def render(self, code, values):
        stream=BytesIO(); c=Canvas(stream,pagesize=(612,792))
        for _ in range(4 if code=='TREC-55-1' else 2):c.showPage()
        c.save()
        with patch.object(m,'validate_source_bytes'):
            return PdfReader(BytesIO(m.render_unsigned_preview(stream.getvalue(),code,values,qa_mode=True)))

    def test_false_and_canonical_no_do_not_become_yes_marks(self):
        for code,key,expected in [('TREC-55-1','working_smoke_detectors','smoke_detectors_no'),
            ('TREC-55-1','property_needs_repair','repair_condition_no'),('TREC-61-0','water_wells_known','water_well_no')]:
            a=m.source_contract(code)['field_map'][expected]
            with patch.object(m,'_check') as mark:self.render(code,{key:False})
            self.assertEqual([call.args[1:] for call in mark.call_args_list],[(a['x'],a['y'])])
        with patch.object(m,'_check') as mark:self.render('TREC-55-1',{'working_smoke_detectors':'N','smoke_detectors_yes':True})
        self.assertEqual(mark.call_count,1)

    def test_scalar_answers_and_zero_counts_survive_real_rendering(self):
        main=self.render('TREC-55-1',{'seller_occupancy_duration':'2 years','roof_type':'Metal','roof_age':'8 years',
            'other_structural_description':'Detached support beams'})
        for value in ('2 years','Metal','8 years','Detached support beams'):
            self.assertIn(value,' '.join(p.extract_text() for p in main.pages))
        water=self.render('TREC-61-0',{'water_well_count_total':3,'water_well_count_in_use':'2','water_well_count_capped':0})
        self.assertEqual(water.pages[0].extract_text().split(),['3','2','0'])

    def test_flood_extent_never_marks_stale_yes_after_no(self):
        with patch.object(m,'_check') as mark:
            self.render('TREC-55-1',{'in_100_year_floodplain':'Y','in_100_year_floodplain_extent':'partly',
                'in_reservoir':'N','in_reservoir_extent':'wholly'})
        self.assertEqual([call.args[1:] for call in mark.call_args_list],[(168.13,581.16)])

    def test_water_initials_fit_printed_footer_for_all_parties_and_packet_offsets(self):
        for sellers in (1,2):
            for buyers in (0,1,2):
                for offset in (0,4):
                    fields=[f for f in m.build_signwell_fields('TREC-61-0',{'seller_names':['QA']*sellers,'buyer_names':['QA']*buyers},page_offset=offset)[0] if f['type']=='initials']
                    self.assertEqual(len(fields),sellers+buyers)
                    self.assertEqual({f['recipient_id'] for f in fields},{str(i+1) for i in range(sellers+buyers)})
                    for f in fields:
                        self.assertEqual(f['page'],offset+1)
                        self.assertGreater(792-(f['y']+f['height'])*.75,22.32);self.assertLess(792-f['y']*.75,35.52)
                        if '_seller' in f['api_id']:left,right=(313.32,342.24) if '_seller1_' in f['api_id'] else (351.24,378.24)
                        else:left,right=(193.08,216.24) if '_buyer1_' in f['api_id'] else (225.24,252.24)
                        self.assertGreater(f['x']*.75,left);self.assertLessEqual((f['x']+f['width'])*.75,right)

    def test_addresses_repeat_and_long_values_are_not_lost(self):
        for code,count in [('TREC-55-1',4),('TREC-61-0',2)]:
            reader=self.render(code,{'propertyAddress':'100 Fictional QA Lane'})
            for page in reader.pages:self.assertIn('100 Fictional QA Lane',page.extract_text())
            address='Fictional long property address. '*10;reader=self.render(code,{'propertyAddress':address})
            self.assertGreater(len(reader.pages),count)
            self.assertIn(' '.join(address.split()),' '.join(' '.join(p.extract_text() for p in reader.pages[count:]).split()))

    def test_new_values_validate_without_attestation_and_invalid_counts_do_not(self):
        data={'formCode':'TREC-55-1','disclosureSourceId':'11111111-1111-4111-8111-111111111111',
            'propertyAddress':'100 Fictional QA Lane','sellerNames':['QA Seller'],
            'responseData':{'seller_occupancy':'N','roof_type':'Metal','fuel_gas_piping':'N','in_floodway_extent':'wholly'},
            'waterRightsData':{'water_well_count_total':0,'well_ownership':'seller_only'}}
        self.assertFalse(parse_seller_disclosure_draft(data)['seller_review_attested'])
        for bad in (-1,True,'-1','x',10000):
            with self.assertRaises(ValueError):parse_seller_disclosure_draft({**data,'waterRightsData':{'water_well_count_total':bad}})

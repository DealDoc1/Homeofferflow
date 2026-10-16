"""Independent 05-04-2026 source bounds, not copies of draft anchors."""
import unittest
from lib import trec_seller_disclosure as m

class TrecSellerDisclosureMapTests(unittest.TestCase):
    def check_row(self, rows, key, left, right, rule):
        x,y={k:(x,y) for k,x,y in rows}[key]
        self.assertGreater(x,left);self.assertLess(x+6,right)
        self.assertGreaterEqual(y-rule,2);self.assertLessEqual(y-rule,3)

    def test_all_item_answers_fit_source_rules_including_two_line_fireplaces(self):
        # Source rule coordinates measured before changing the renderer.
        rows=[(('range','oven','microwave'),566.68),(('dishwasher','trash_compactor','disposal'),548.68),
            (('washer_dryer_hookups','window_screens','rain_gutters'),530.68),
            (('security_system','fire_detection_equipment','intercom_system'),512.68),
            (('smoke_detector',),494.68),(('smoke_detector_hearing_impaired',),476.68),
            (('carbon_monoxide_alarm',),458.68),(('emergency_escape_ladders',),440.68),
            (('tv_antenna','cable_tv_wiring','satellite_dish'),422.68),(('ceiling_fans','attic_fans','exhaust_fans'),404.68),
            (('central_ac','central_heating','wall_window_ac'),386.68),(('plumbing_system','septic_system','public_sewer_system'),368.68),
            (('patio_decking','outdoor_grill','fences'),350.68),(('pool','sauna','spa'),332.68),
            (('pool_equipment','pool_heater','automatic_lawn_sprinkler_system'),314.68),
            (('fireplace_wood_burning','fireplace_mock'),291.68),(('natural_gas_lines','gas_fixtures'),273.68),
            (('liquid_propane_gas',),255.68),(('fuel_gas_piping',),236.69)]
        rules={key:rule for names,rule in rows for key in names}
        self.assertEqual({k for k,_,_ in m.TREC_55_1_ITEM_ROWS},set(rules))
        for key,x,y in m.TREC_55_1_ITEM_ROWS:
            left={74:63.6,227:216.6,407:396.6}[x]
            self.check_row(m.TREC_55_1_ITEM_ROWS,key,left,left+27,rules[key])

    def test_every_defect_maps_to_its_own_question(self):
        groups=[(('defect_interior_walls','defect_ceilings','defect_floors'),494.16),
            (('defect_exterior_walls','defect_doors','defect_windows'),476.16),
            (('defect_roof','defect_foundation_slabs','defect_sidewalks'),458.16),
            (('defect_walls_fences','defect_driveways','defect_intercom'),440.16),
            (('defect_plumbing_sewers_septics','defect_electrical_systems','defect_lighting_fixtures'),422.16)]
        for names,rule in groups:
            for key,left in zip(names,(55,235,406)):self.check_row(m.TREC_55_1_CONDITION_ROWS,key,left,left+29,rule)
        self.check_row(m.TREC_55_1_CONDITION_ROWS,'defect_other_structural_components',55,83.7,404.16)

    def test_flood_and_wrapped_additional_answers_fit_source_rules(self):
        for rows,rules in ((m.TREC_55_1_FLOOD_ROWS,(647.16,629.16,611.16,575.16,557.16,539.16,521.16,503.16)),
            (m.TREC_55_1_ADDITIONAL_ROWS,(705.16,687.96,664.96,642.17,623.76,605.76,582.76,564.96,546.96,514.55,496.55,477.95,459.94,436.94,413.77))):
            self.assertEqual(len(rows),len(rules))
            for (key,_,_),rule in zip(rows,rules):self.check_row(rows,key,54.5,82.3,rule)

    def test_main_choice_marks_fit_inside_actual_ten_point_squares(self):
        boxes={'seller_occupancy_yes':(76.13,607.17),'seller_occupancy_no':(100.30,607.17),
            'repair_awareness_yes':(130.13,102.34),'repair_awareness_no':(166.13,102.34),'repair_awareness_unknown':(202.13,102.34),
            'smoke_detectors_yes':(193.13,723.66),'smoke_detectors_no':(229.13,723.66),'smoke_detectors_unknown':(265.13,723.66),
            'repair_condition_yes':(482.93,734.46),'repair_condition_no':(58.13,723.66),
            'flood_claim_yes':(202.14,166.48),'flood_claim_no':(238.14,166.48),'fema_yes':(103.14,58.48),'fema_no':(139.14,58.48)}
        for key,(left,bottom) in boxes.items():
            a=m.TREC_55_1_MAP[key]
            self.assertGreaterEqual(a['x'],left+1);self.assertLessEqual(a['x']+6,left+9)
            self.assertGreaterEqual(a['y'],bottom+1);self.assertLessEqual(a['y']+6,bottom+9)

    def test_source_contract_and_unapproved_bytes_stay_protected(self):
        for code,pages in (('TREC-55-1',4),('TREC-61-0',2)):
            self.assertEqual(m.source_contract(code)['page_count'],pages)
            self.assertEqual(m.source_contract(code)['activation_status'],'pending_visual_qa')
            with self.assertRaisesRegex(ValueError,'fingerprint'):m.validate_source_bytes(code,b'not-source')
        with self.assertRaisesRegex(ValueError,'qa_mode'):m.render_unsigned_preview(b'not-source','TREC-55-1',{},qa_mode=False)
        with self.assertRaises(ValueError):m.source_contract('TREC-56-0')

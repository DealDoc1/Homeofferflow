"""Independent bounds measured on TXR-1507 06-15-26, not copied from widgets."""
import unittest
from unittest.mock import patch
from lib import txr_1507
from tests.test_txr_1507_renderer import sample_data


class Txr1507ExecutionBoundsTests(unittest.TestCase):
    def test_showing_fee_is_on_the_amount_blank_not_the_previous_sentence(self):
        with patch.object(txr_1507, '_draw', wraps=txr_1507._draw) as draw:
            txr_1507._overlay({**sample_data(),'service_level':'showing_services','showing_fee':'150'},{},{})
        amount=next(call for call in draw.call_args_list if call.args[1]=='150')
        self.assertEqual(amount.args[2:4],(325,414))
        from reportlab.pdfbase.pdfmetrics import stringWidth
        self.assertLessEqual(325+stringWidth('150',txr_1507.FONT,8),387.67)
        self.assertLess(792-414,379.25)

    def test_entire_execution_rectangles_clear_printed_rules_and_labels(self):
        for role in ('broker', 'associate'):
            for count in (1, 2):
                fields = txr_1507.build_signwell_fields_txr1507(
                    {'signer_plan': 'clients_and_' + role}, client_count=count)[0]
                for f in fields:
                    if f['page'] != 2:
                        continue
                    with self.subTest(role=role, count=count, field=f['api_id']):
                        left, top = f['x']*.75, f['y']*.75
                        right, bottom = left+f['width']*.75, top+f['height']*.75
                        second = f['recipient_id'] == '2'
                        self.assertGreaterEqual(top, 590 if second else 513)
                        self.assertLessEqual(bottom, 616.78 if second else 533.95)
                        self.assertGreaterEqual(left, 324 if f['recipient_id'] in ('1','2') else 36)
                        self.assertLessEqual(right, 576.10 if f['recipient_id'] in ('1','2') else 288.05)
                        if f['type'] == 'date':
                            self.assertGreaterEqual(f['width']*.75, 53)
                            signature = next(s for s in fields if s['type']=='signature' and s['recipient_id']==f['recipient_id'])
                            self.assertLess(signature['x']+signature['width'], f['x'])

    def test_initials_fit_each_printed_footer_blank(self):
        ranges = {'associate': (325.98,361.06), '1': (406.52,444.03), '2': (446.55,481.53)}
        for f in txr_1507.build_signwell_fields_txr1507({'signer_plan':'clients_and_associate'}, client_count=2)[0]:
            if f['type']=='initials':
                low, high = ranges[f['recipient_id']]
                self.assertGreaterEqual(f['x']*.75, low)
                self.assertLessEqual((f['x']+f['width'])*.75, high)
                self.assertLessEqual((f['y']+f['height'])*.75, 744)

    def test_selected_x_strokes_including_line_width_stay_inside_source_cells(self):
        cells = {
            'full_services':(54,325.35,63.84,336.39),
            'showing_services':(54,356.67,63.84,367.71),
            'authorized':(176.06,145.82,188.57,159.86),
            'not_authorized':(232.01,145.82,244.52,159.86),
            'associate':(36,546.60,44.02,555.60),
            'broker':(36,536.15,44.02,545.15),
        }
        class Canvas:
            def __init__(self): self.lines=[];self.width=0
            def setLineWidth(self,width): self.width=width
            def line(self,*values): self.lines.append(values)
        for role in ('broker','associate'):
            for service, intermediary in [('full_services','authorized'),('showing_services','not_authorized')]:
                with patch.object(txr_1507,'_draw_check',wraps=txr_1507._draw_check) as check, patch.object(txr_1507,'_draw_signing_role_check',wraps=txr_1507._draw_signing_role_check) as role_check:
                    txr_1507._overlay({**sample_data(),'signer_plan':'clients_and_'+role,'service_level':service,'intermediary':intermediary},{},{})
                self.assertEqual(len(check.call_args_list),2)
                self.assertEqual(len(role_check.call_args_list),1)
                for calls, draw, keys in [(check.call_args_list,txr_1507._draw_check,[service,intermediary]),(role_check.call_args_list,txr_1507._draw_signing_role_check,[role])]:
                    for call,key in zip(calls,keys):
                        x,y=call.args[1:];bounds=cells[key];c=Canvas();draw(c,x,y)
                        for x1,y1,x2,y2 in c.lines:
                            for px,py in [(x1,y1),(x2,y2)]:
                                self.assertGreaterEqual(px-c.width/2,bounds[0])
                                self.assertLessEqual(px+c.width/2,bounds[2])
                                self.assertGreaterEqual(792-py-c.width/2,bounds[1])
                                self.assertLessEqual(792-py+c.width/2,bounds[3])

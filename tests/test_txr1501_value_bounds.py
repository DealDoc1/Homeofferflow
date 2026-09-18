"""Rendered values must fit independently measured 06-15-26 source blanks."""
from io import BytesIO
import unittest
from unittest.mock import patch
import pdfplumber
from lib import txr_1501


class Txr1501ValueBoundsTests(unittest.TestCase):
    def test_all_supported_value_areas_fit_source_blanks(self):
        data={'client_names':['QA First Client','QA Second Client'],
              'client_address':'100 QA Street','client_city_state_zip':'Frisco, TX 75034',
              'client_phone':'2145550100','client_email':'client@example.test',
              'term_start':'2026-09-18','term_end':'2027-09-17',
              'compensation':{'purchase_percentage':'99.875','purchase_flat_fee':'100000.55',
                              'lease_one_month_percentage':'88.125','lease_total_rents_percentage':'77.625',
                              'lease_flat_fee':'200000.66'},
              'retainer_amount':'300000.77','protection_days':'365','payment_county':'Collin'}
        broker={'legal_name':'QA Brokerage','address':'200 QA Avenue',
                'city_state_zip':'Dallas, TX 75201','phone':'2145550101','email':'broker@example.test'}
        # page, value, left, right, top, bottom: 72-DPI source measurements.
        blanks=[
            (1,'QA First Client, QA Second Client',108.02,576.09,166,179.66),
            (1,'100 QA Street',127.46,576.09,193.10,204.98),
            (1,'Frisco, TX 75034',159.26,576.09,205.82,217.58),
            (1,'2145550100',118.94,324.04,218.42,230.30),
            (1,'client@example.test',114.62,324.04,231.14,242.90),
            (1,'QA Brokerage',108.02,576.09,247,261.29),
            (1,'200 QA Avenue',124.46,576.09,274.85,286.61),
            (1,'Dallas, TX 75201',156.26,576.09,287.45,299.33),
            (1,'2145550101',115.94,324.04,300.17,311.93),
            (1,'broker@example.test',111.62,324.04,312.77,324.53),
            (1,'2026-09-18',234.17,324.05,613.578,623.50),
            (1,'2027-09-17',457.99,531.694,613.578,623.50),
            (2,'99.875',174.02,216.04,307.73,318.77),
            (2,'100000.55',403.15,504.09,307.73,318.77),
            (2,'88.125',155.66,216.04,326.45,337.49),
            (2,'77.625',348.67,396.07,326.45,337.49),
            (2,'200000.66',279.89,360.07,339.05,350.09),
            (2,'300000.77',140.629,207.719,371.488,382.528),
            (3,'365',108.02,175.359,297.208,308.248),
            (3,'Collin',379.27,495.69,472.51,483.55),
        ]
        with pdfplumber.open(BytesIO(txr_1501._overlay(data,broker,{}))) as pdf:
            for number,value,left,right,top,bottom in blanks:
                chars=pdf.pages[number-1].chars
                text=''.join(c['text'] for c in chars)
                start=text.index(value)
                selected=chars[start:start+len(value)]
                with self.subTest(value=value):
                    self.assertGreaterEqual(min(c['x0'] for c in selected),left)
                    self.assertLessEqual(max(c['x1'] for c in selected),right)
                    self.assertGreaterEqual(min(c['top'] for c in selected),top)
                    self.assertLessEqual(max(c['bottom'] for c in selected),bottom)

    def test_both_intermediary_marks_including_strokes_fit_source_cells(self):
        class Canvas:
            def __init__(self):self.lines=[];self.width=0
            def setLineWidth(self,width):self.width=width
            def line(self,*line):self.lines.append(line)
        for choice,top,bottom in [('authorized',76.683,87.723),('not_authorized',328.353,339.393)]:
            with patch.object(txr_1501,'_check') as mark:
                txr_1501._overlay({'intermediary':choice},{},{})
            self.assertEqual(len(mark.call_args_list),1)
            c=Canvas()
            txr_1501._check(c,*mark.call_args.args[1:])
            for x1,y1,x2,y2 in c.lines:
                for x,y in [(x1,y1),(x2,y2)]:
                    with self.subTest(choice=choice):
                        self.assertGreaterEqual(x-c.width/2,45)
                        self.assertLessEqual(x+c.width/2,54.837)
                        self.assertGreaterEqual(792-y-c.width/2,top)
                        self.assertLessEqual(792-y+c.width/2,bottom)


if __name__=='__main__':unittest.main()

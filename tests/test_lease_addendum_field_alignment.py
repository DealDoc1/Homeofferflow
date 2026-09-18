"""Source-calibrated overlay positions; these do not certify signed PDFs."""
from io import BytesIO
import unittest
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from pypdf import PdfReader
from lib.txr_1953 import render_txr_1953
from lib.txr_1954 import render_txr_1954
from lib.signwell_delivery import request_fingerprint
from lib.offer_signwell_delivery import offer_answers


def overlays(render, data):
    blank = BytesIO()
    canvas = Canvas(blank, pagesize=(612, 792))
    canvas.showPage(); canvas.save()
    page = PdfReader(BytesIO(render(blank.getvalue(), data))).pages[0]
    values = []
    size = 0
    def operand(op, args, cm, tm):
        nonlocal size
        if op == b'Tf':
            size = float(args[1])
        elif op == b'Tj':
            text = args[0].decode('latin1') if isinstance(args[0], bytes) else str(args[0])
            if text.strip():
                values.append((text.strip(), tm[4], tm[5], size))
    # Inspect each actual draw operation, not pypdf's delayed text-line flush.
    page.extract_text(visitor_operand_before=operand)
    return values


class LeaseFieldAlignmentTests(unittest.TestCase):
    def assert_marks(self, render, data, centers):
        marks = [value for value in overlays(render, data) if value[0] == 'X']
        self.assertEqual(len(marks), len(centers))
        for (_, x, y, size), (cx, cy) in zip(marks, centers):
            self.assertEqual(size, 6)
            self.assertAlmostEqual(x + stringWidth('X', 'Helvetica-Bold', size) / 2, cx, places=2)
            self.assertAlmostEqual(y + 2.15, cy, places=2)

    def test_residential_status_and_delivery_boxes(self):
        self.assert_marks(render_txr_1953, {'lease_status':'termination'}, [(34.77,612.24)])
        for choice, point in [('received',(75.27,523.80)), ('not_received',(75.27,512.16)), ('oral_notice',(75.27,474.06))]:
            with self.subTest(choice=choice):
                self.assert_marks(render_txr_1953, {'lease_status':'assignment','delivery_choice':choice}, [(34.77,557.70),point])

    def test_fixture_inventory_and_assumption_boxes(self):
        choices = ['solar_panels','propane_tanks','water_softener','security_system','other']
        self.assert_marks(render_txr_1954, {'leased_fixture_types':choices,'assumed_fixture_leases':choices},
            [(x,595.98) for x in (81.46,165.82,263.56,362.50,465.58)] +
            [(x,549.48) for x in (89.44,201.76,325.78,456.10)] + [(89.44,535.08)])

    def test_fixture_removal_and_delivery_boxes(self):
        for key, value, point in [
            ('removal_choice','will',(210.82,477.84)),
            ('removal_choice','will_not',(256.54,477.84)),
            ('delivery_choice','received',(53.68,409.92)),
            ('delivery_choice','not_received',(53.68,395.46)),
            ('delivery_choice','oral_notice',(53.56,348.96)),
        ]:
            with self.subTest(value=value):
                self.assert_marks(render_txr_1954, {key:value}, [point])

    def test_residential_days_land_in_blank_not_printed_sentence(self):
        values = overlays(render_txr_1953, {'lease_status':'assignment','delivery_choice':'not_received','delivery_days':'5'})
        self.assertIn(('5',103.0,489.5,8.0), values)

    def test_residential_narrative_sits_above_its_rules(self):
        values = overlays(render_txr_1953, {'lease_status':'assignment','delivery_choice':'oral_notice','oral_lease_notice':'QA notice','explanation':'QA explanation'})
        self.assertIn(('QA notice',103.0,458.0,8.0), values)
        self.assertIn(('QA explanation',480.0,318.0,8.0), values)

    def test_fixture_address_clears_underline(self):
        self.assertIn(('QA property',243.0,664.0,8.0), overlays(render_txr_1954, {'property_address':'QA property'}))

    def test_render_revision_change_invalidates_saved_offer_fingerprint(self):
        first = {'_signing_render_revisions': {'TXR-1953':'v1'}}
        second = {'_signing_render_revisions': {'TXR-1953':'v2'}}
        self.assertNotEqual(request_fingerprint({}, offer_answers(first)), request_fingerprint({}, offer_answers(second)))

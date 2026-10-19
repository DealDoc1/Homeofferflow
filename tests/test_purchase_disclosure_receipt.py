import hashlib
import base64
from contextlib import redirect_stdout
from io import BytesIO, StringIO
import unittest
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms, minimal_offer
from lib.purchase_disclosure_receipt import address_matches, receipt_fields
from lib.seller_disclosure_explanations import RENDER_REVISION


class PurchaseDisclosureReceiptTests(unittest.TestCase):
    def doc(self, water=False):
        raw = b'%PDF-fictional-signed-disclosure'
        return {'type': 'seller_disclosure', 'raw': raw, 'page_count': 7 if water else 5,
                'homeOfferFlowDisclosureReceipt': {
                    'sourceRevision': '05-04-2026', 'renderRevision': RENDER_REVISION,
                    'propertyAddress': '123 QA Road, Dallas, TX 75201',
                    'sha256': hashlib.sha256(raw).hexdigest(), 'hasWaterRights': water}}

    def offer(self, second=False):
        return {'address': '123 QA Road', 'city': 'Dallas', 'state': 'TX', 'zip': '75201',
                'buyer2Email': 'second@example.com' if second else ''}

    def test_no_disclosure_does_not_stop_other_documents(self):
        self.assertEqual(receipt_fields({}, {}), [])

    def test_main_receipt_reuses_calibrated_buyer_geometry_only(self):
        fields = receipt_fields(self.doc(), self.offer(), page_offset=11)
        self.assertEqual(len(fields), 2)
        self.assertEqual({f['page'] for f in fields}, {15})
        self.assertEqual({f['recipient_id'] for f in fields}, {'1'})
        self.assertEqual(fields[0]['y'], 877)
        self.assertEqual((fields[1]['width'], fields[1]['height']), (96, 18))
        self.assertTrue(all('_buyer' in f['api_id'] for f in fields))

    def test_two_buyers_water_and_audit_pages_do_not_shift_receipt(self):
        fields = receipt_fields(self.doc(True), self.offer(True), page_offset=20)
        self.assertEqual(len(fields), 10)
        self.assertEqual({f['recipient_id'] for f in fields}, {'1', '2'})
        self.assertEqual({f['page'] for f in fields if 'trec551' in f['api_id']}, {24})
        self.assertEqual({f['page'] for f in fields if 'trec610' in f['api_id']}, {25, 26})
        self.assertFalse(any(f['page'] == 27 for f in fields))

    def test_modified_pdf_wrong_property_revision_type_or_missing_pages_reject(self):
        for mutation in ('bytes', 'address', 'revision', 'type', 'pages'):
            with self.subTest(mutation=mutation):
                doc = self.doc()
                if mutation == 'bytes': doc['raw'] += b'changed'
                if mutation == 'address': doc['homeOfferFlowDisclosureReceipt']['propertyAddress'] = '124 QA Road, Dallas, TX 75201'
                if mutation == 'revision': doc['homeOfferFlowDisclosureReceipt']['renderRevision'] = 'old'
                if mutation == 'type': doc['type'] = 'other'
                if mutation == 'pages': doc['page_count'] = 3
                with self.assertRaises(ValueError): receipt_fields(doc, self.offer())

    def test_units_are_not_discarded_and_punctuation_is_not_significant(self):
        self.assertTrue(address_matches('123 QA Road, Dallas, TX 75201', self.offer()))
        self.assertFalse(address_matches('123 QA Road Apt 2, Dallas, TX 75201', self.offer()))
        self.assertFalse(address_matches('', self.offer()))

    def test_real_packet_appends_every_page_and_offsets_only_buyer_receipts(self):
        configure_local_forms()
        stream=BytesIO()
        c=canvas.Canvas(stream,pagesize=(612,792))
        for n in range(5):
            c.drawString(50,500,f'FICTIONAL DISCLOSURE PAGE {n+1}')
            c.showPage()
        c.save()
        raw=stream.getvalue()
        doc=self.doc()
        doc.update(name='signed-disclosure.pdf',base64=base64.b64encode(raw).decode())
        doc['homeOfferFlowDisclosureReceipt']['sha256']=hashlib.sha256(raw).hexdigest()
        survey=PdfWriter();survey.add_blank_page(width=612,height=792)
        survey_bytes=BytesIO();survey.write(survey_bytes)
        preceding={'name':'survey.pdf','type':'survey','base64':base64.b64encode(survey_bytes.getvalue()).decode()}
        offer=minimal_offer(**self.offer(True),financing='conventional',loanAmount='200000',uploadedDisclosureDocs=[preceding,doc])
        with redirect_stdout(StringIO()):
            pdf=adapter.fill_and_merge_20_19(offer)
            fields=adapter.build_signwell_fields_20_19(offer,pdf)[0]
        reader=PdfReader(BytesIO(pdf))
        self.assertTrue(all(f'FICTIONAL DISCLOSURE PAGE {n+1}' in reader.pages[-5+n].extract_text() for n in range(5)))
        receipt=[f for f in fields if f['api_id'].startswith('saved_disclosure_')]
        self.assertEqual(len(receipt),4)
        self.assertEqual({f['page'] for f in receipt},{len(reader.pages)-1})
        self.assertEqual({f['recipient_id'] for f in receipt},{'1','2'})
        self.assertFalse(any('_seller' in f['api_id'] for f in receipt))

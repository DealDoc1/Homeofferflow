"""Appraisal answers must agree with visible editable appearances and maps."""
import base64
import copy
from io import BytesIO
from pathlib import Path
import unittest

import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, IndirectObject
from lib import txr_1948 as FORM
from tests.test_txr_1948_renderer import blank_one_page_pdf
from tests.test_txr_render_send_snapshot import RenderSendFixture, USER
from tests.test_txr_signing_request_path import MODULE


SOURCE = (Path(__file__).resolve().parents[1] / 'appraisal_addendum.pdf').read_bytes()


def sample(*, long=False, buyers=2, sellers=2):
    data = {'property_address': '100 José 李 Street, Frisco',
            'buyer_names': ['José 李', 'BuyerTwo'][:buyers],
            'seller_names': ['Ana Gómez', 'SellerTwo'][:sellers],
            'appraisal_choice': 'additional_right', 'partial_value': '400000.50',
            'additional_days': '365', 'additional_value': '500000.25'}
    if long:
        data['property_address'] = 'A' * 400
        data['buyer_names'] = [(f'José 李 <b>Buyer{i}</b> & ' + 'B' * 180)[:180] for i in range(buyers)]
        data['seller_names'] = [(f'Gómez <i>Seller{i}</i> & ' + 'S' * 180)[:180] for i in range(sellers)]
    return data


def appearance_pdf(widget):
    """Read the actual widget appearance as a page, not its canonical value."""
    ap = widget['/AP']['/N']
    writer = PdfWriter()
    page = writer.add_blank_page(float(ap['/BBox'][2]), float(ap['/BBox'][3]))
    page[NameObject('/Resources')] = ap['/Resources'].clone(writer)
    page.replace_contents(ap.clone(writer))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class AppraisalAnswerBoundsTests(unittest.TestCase):
    def test_canonical_values_widgets_and_visible_unicode_appearances_agree(self):
        for choice in FORM.CHOICE_FIELDS:
            data = {**sample(), 'appraisal_choice': choice, '_for_signing': True}
            raw = FORM.render_txr_1948(SOURCE, data)
            reader = PdfReader(BytesIO(raw))
            expected = FORM._editable_values(PdfReader(BytesIO(SOURCE)), data)
            fields = reader.get_fields()
            self.assertEqual(len(fields), 11)
            self.assertEqual(len(reader.pages), 1)
            root_ids = {ref.idnum for ref in reader.trailer['/Root']['/AcroForm']['/Fields']}
            widget_ids = {ref.idnum for ref in reader.pages[0]['/Annots']}
            self.assertEqual(root_ids, widget_ids)
            for ref in reader.pages[0]['/Annots']:
                widget = ref.get_object()
                name = widget['/T']
                if name not in expected:
                    continue
                with self.subTest(choice=choice, name=name):
                    self.assertEqual(fields[name]['/V'], expected[name])
                    self.assertEqual(widget['/V'], fields[name]['/V'])
                    self.assertTrue(widget['/AP']['/N'])
                    if widget['/FT'] == '/Btn':
                        self.assertEqual(widget['/AS'], expected[name])
                        continue
                    self.assertIsInstance(widget['/AP'].raw_get('/N'), IndirectObject)
                    ap_pdf = appearance_pdf(widget)
                    visible = PdfReader(BytesIO(ap_pdf)).pages[0].extract_text().strip()
                    self.assertEqual(visible, expected[name])
                    with pdfplumber.open(BytesIO(ap_pdf)) as pdf:
                        page = pdf.pages[0]
                        for char in page.chars:
                            self.assertGreaterEqual(char['x0'], 0)
                            self.assertLessEqual(char['x1'], page.width)
                            self.assertGreaterEqual(char['top'], 0)
                            self.assertLessEqual(char['bottom'], page.height)

    def test_source_measured_blanks_and_preview_names_fit_without_intersections(self):
        data = {**sample(), 'property_address': 'Property',
                'buyer_names': ['BuyerOne', 'BuyerTwo'], 'seller_names': ['SellerOne', 'SellerTwo']}
        regions = {'Property': (223.32, 576, 140.64), '365': (65.424, 109.91832, 474.09172),
                   '500000.25': (124.68, 219.84, 506.13172),
                   'BuyerOne': (43.08, 294.84, 602.52), 'BuyerTwo': (43.08, 294.84, 668.52),
                   'SellerOne': (317.88, 556.44, 602.52), 'SellerTwo': (317.88, 556.44, 668.52)}
        with pdfplumber.open(BytesIO(FORM.render_txr_1948(blank_one_page_pdf(), data))) as pdf:
            words = pdf.pages[0].extract_words()
            for value, (left, right, rule) in regions.items():
                with self.subTest(value=value):
                    word = next(w for w in words if w['text'] == value)
                    self.assertGreaterEqual(word['x0'], left)
                    self.assertLessEqual(word['x1'], right)
                    self.assertGreaterEqual(word['top'], rule - 12)
                    self.assertLess(word['bottom'], rule)

    def test_long_values_survive_in_full_with_identical_preview_and_signing_pagination(self):
        for source in (SOURCE, blank_one_page_pdf()):
            data = sample(long=True)
            original = copy.deepcopy(data)
            draft = FORM.render_txr_1948(source, data)
            signed = FORM.render_txr_1948(source, {**data, '_for_signing': True})
            self.assertEqual(len(PdfReader(BytesIO(draft)).pages), len(PdfReader(BytesIO(signed)).pages))
            with pdfplumber.open(BytesIO(signed)) as pdf:
                self.assertGreater(len(pdf.pages), 1)
                body = ''.join(''.join((p.crop((48,140,564,682)).extract_text() or '').split()) for p in pdf.pages[1:])
                for value in FORM.answer_layout(data).overflow.values():
                    self.assertIn(''.join(value.split()), body)
                for page in pdf.pages[1:]:
                    for char in page.chars:
                        self.assertGreaterEqual(char['x0'], 47.9)
                        self.assertLessEqual(char['x1'], 564.1)
                        self.assertGreaterEqual(char['top'], 40)
                        self.assertLessEqual(char['bottom'], 755)
            if source == SOURCE:
                fields = PdfReader(BytesIO(signed)).get_fields()
                self.assertEqual(fields[FORM.ADDRESS_FIELD]['/V'], 'Exhibit')
            self.assertEqual(data, original)

    def test_actual_offline_send_keeps_all_continuations_initialed_and_invitations_parallel(self):
        for buyers, sellers in ((1, 1), (1, 2), (2, 1), (2, 2)):
            for long in (False, True):
                with self.subTest(buyers=buyers, sellers=sellers, long=long):
                    f = RenderSendFixture(self)
                    data = sample(long=long, buyers=buyers, sellers=sellers)
                    data['signing_map_revision'] = MODULE.TXR_SIGNING_MAP_REVISIONS['TXR-1948']
                    f.row.update(form_code='TXR-1948', agreement_data=data,
                                 client_names=data['buyer_names'] + data['seller_names'])
                    f.source_bytes = SOURCE
                    f.emails = [f'party{i}@example.test' for i in range(buyers+sellers)]
                    f.recipients = MODULE._txr_signwell_recipients(f.row, f.emails, f.broker,
                        {'email': USER['email'], 'name': f.profile['agent_name']})
                    self.assertTrue(f.run()['ok'])
                    raw = base64.b64decode(f.document['files'][0]['file_base64'])
                    reader = PdfReader(BytesIO(raw))
                    fields = f.document['fields'][0]
                    self.assertEqual(len(reader.pages) > 1, long)
                    self.assertEqual(max(v['page'] for v in fields), len(reader.pages))
                    self.assertEqual(len({v['api_id'] for v in fields}), len(fields))
                    self.assertEqual(f.document['recipients'], f.recipients)
                    for page in range(2, len(reader.pages)+1):
                        extra = [v for v in fields if v['page'] == page]
                        self.assertEqual({v['recipient_id'] for v in extra}, {str(i) for i in range(1,buyers+sellers+1)})
                        self.assertTrue(all(v['required'] and v['type'] == 'initials' for v in extra))
                    self.assertFalse(f.document['apply_signing_order'])
                    self.assertEqual(f.downloads, 1)
                    self.assertEqual(f.sends, 1)
        self.assertEqual(MODULE.TXR_RENDER_REVISIONS['TXR-1948'], FORM.RENDER_REVISION)

    def test_deselection_clears_the_old_value_and_appearance(self):
        partial = FORM.render_txr_1948(SOURCE, {**sample(), 'appraisal_choice': 'partial_waiver'})
        waiver = PdfReader(BytesIO(FORM.render_txr_1948(partial, {**sample(), 'appraisal_choice': 'waiver'})))
        for ref in waiver.pages[0]['/Annots']:
            widget = ref.get_object()
            if widget.get('/T') in FORM.TERM_FIELDS.values():
                self.assertEqual(widget['/V'], '')
                self.assertEqual(PdfReader(BytesIO(appearance_pdf(widget))).pages[0].extract_text().strip(), '')


if __name__ == '__main__':
    unittest.main()

"""Signing copies must not print draft party names underneath SignWell ink."""
import importlib
from io import BytesIO
from pathlib import Path
import unittest

import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
from reportlab.pdfgen.canvas import Canvas


CASES = ((1905, 1), (1914, 2), (1917, 1), (1919, 2), (1948, 1))


def blank_source(pages):
    output = BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(pages):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample(buyers=2, sellers=2):
    return {'property_address': '100 QA Street, Frisco',
            'buyer_names': ['AlphaBuyer', 'BetaBuyer'][:buyers],
            'seller_names': ['GammaSeller', 'DeltaSeller'][:sellers],
            'reservation_choice': 'all', 'surface_rights': 'waived',
            'review_types': ['environmental'], 'termination_days': '10',
            'appraisal_choice': 'partial_waiver', 'partial_value': '450000',
            'credit_days': '7', 'credit_documents': ['credit_report'],
            'variance': {'adjustment': 'cash', 'termination_threshold': '1000'}}


class TxrExecutionNameClearanceTests(unittest.TestCase):
    def test_appraisal_rejects_ambiguous_fields_or_an_executed_source(self):
        module = importlib.import_module('lib.txr_1948')
        source = (Path(__file__).resolve().parents[1] / 'appraisal_addendum.pdf').read_bytes()
        for defect in ('missing_field', 'signed'):
            with self.subTest(defect=defect):
                writer = PdfWriter()
                writer.clone_document_from_reader(PdfReader(BytesIO(source)))
                if defect == 'missing_field':
                    writer.root_object['/AcroForm']['/Fields'].pop()
                else:
                    signature = next(ref.get_object() for ref in writer.pages[0]['/Annots']
                                     if ref.get_object().get('/T') == 'Signature1')
                    signature[NameObject('/V')] = TextStringObject('Synthetic signed-source marker')
                output = BytesIO()
                writer.write(output)
                with self.assertRaises(ValueError):
                    module.render_txr_1948(output.getvalue(), sample())

    def test_appraisal_deselection_clears_previous_editable_answers(self):
        module = importlib.import_module('lib.txr_1948')
        source = (Path(__file__).resolve().parents[1] / 'appraisal_addendum.pdf').read_bytes()
        data = {**sample(), '_for_signing': True}
        partial = module.render_txr_1948(source, data)
        waiver = module.render_txr_1948(partial, {**data, 'appraisal_choice': 'waiver'})
        fields = PdfReader(BytesIO(waiver)).get_fields()
        self.assertEqual(fields[module.CHOICE_FIELDS['waiver']]['/V'], '/On')
        self.assertEqual(fields[module.CHOICE_FIELDS['partial_waiver']]['/V'], '/Off')
        self.assertTrue(all(fields[name]['/V'] == '' for name in module.TERM_FIELDS.values()))

    def test_environmental_marks_and_terms_fit_measured_source_blanks(self):
        module = importlib.import_module('lib.txr_1917')
        raw = module.render_txr_1917(blank_source(1), {
            **sample(), '_for_signing': True, 'termination_days': '365',
            'review_types': ['environmental', 'species', 'wetlands']})
        with pdfplumber.open(BytesIO(raw)) as pdf:
            marks = [char for char in pdf.pages[0].chars if char['text'] == 'X']
            self.assertEqual(len(marks), 3)
            for mark, (top, bottom) in zip(marks, [(242.64, 254.64), (280.32, 292.32), (345.90, 357.90)]):
                self.assertGreaterEqual(mark['x0'], 58.02)
                self.assertLessEqual(mark['x1'], 68.712)
                self.assertGreaterEqual(mark['top'], top)
                self.assertLessEqual(mark['bottom'], bottom)
            words = pdf.pages[0].extract_words()
            days = next(word for word in words if word['text'] == '365')
            self.assertGreaterEqual(days['x0'], 90.30)
            self.assertLessEqual(days['x1'], 120.66)
            self.assertLessEqual(days['bottom'], 417.42)
            address = [char for char in pdf.pages[0].chars if char['top'] < 200]
            self.assertLessEqual(max(char['bottom'] for char in address), 190.38)

    def test_appraisal_fillable_fields_and_widget_appearances_agree(self):
        module = importlib.import_module('lib.txr_1948')
        source = (Path(__file__).resolve().parents[1] / 'appraisal_addendum.pdf').read_bytes()
        for choice in ('waiver', 'partial_waiver', 'additional_right'):
            with self.subTest(choice=choice):
                data = {**sample(), '_for_signing': True, 'appraisal_choice': choice,
                        'additional_days': '7', 'additional_value': '400000'}
                rendered = PdfReader(BytesIO(module.render_txr_1948(source, data)))
                expected = module._editable_values(PdfReader(BytesIO(source)), data)
                fields = rendered.get_fields()
                self.assertEqual(len(fields), 11)
                for name, value in expected.items():
                    self.assertEqual(fields[name]['/V'], value)
                root_ids = {ref.idnum for ref in rendered.trailer['/Root']['/AcroForm']['/Fields']}
                widget_ids = {ref.idnum for ref in rendered.pages[0]['/Annots']}
                self.assertEqual(root_ids, widget_ids)
                for ref in rendered.pages[0]['/Annots']:
                    widget = ref.get_object()
                    if widget['/T'] in expected:
                        self.assertEqual(widget['/V'], fields[widget['/T']]['/V'])
                        self.assertTrue(widget['/AP']['/N'])
                self.assertNotIn('AlphaBuyer', rendered.pages[0].extract_text())

    def test_signing_copy_clears_names_but_keeps_every_non_name_term(self):
        for code, pages in CASES:
            module = importlib.import_module(f'lib.txr_{code}')
            render = getattr(module, f'render_txr_{code}')
            for buyers in (1, 2):
                for sellers in (1, 2):
                    with self.subTest(code=code, buyers=buyers, sellers=sellers):
                        data = sample(buyers, sellers)
                        source = blank_source(pages)
                        draft = PdfReader(BytesIO(render(source, data)))
                        signing = PdfReader(BytesIO(render(source, {**data, '_for_signing': True})))
                        self.assertEqual(len(signing.pages), pages)
                        names = data['buyer_names'] + data['seller_names']
                        draft_text = '\n'.join(page.extract_text() or '' for page in draft.pages)
                        signing_text = '\n'.join(page.extract_text() or '' for page in signing.pages)
                        for name in names:
                            self.assertIn(name, draft_text)
                            self.assertNotIn(name, signing_text)
                            draft_text = draft_text.replace(name, '')
                        self.assertEqual(' '.join(draft_text.split()), ' '.join(signing_text.split()))
                        self.assertIn(data['property_address'], signing_text)
                        field_builder = getattr(module, f'build_signwell_fields_txr{code}')
                        self.assertEqual(field_builder(data), field_builder({**data, '_for_signing': True}))

    def test_signing_overlay_text_does_not_intersect_any_signature_rectangle(self):
        for code, pages in CASES:
            module = importlib.import_module(f'lib.txr_{code}')
            data = {**sample(), '_for_signing': True}
            raw = getattr(module, f'render_txr_{code}')(blank_source(pages), data)
            fields = getattr(module, f'build_signwell_fields_txr{code}')(data)[0]
            with pdfplumber.open(BytesIO(raw)) as pdf:
                for field in fields:
                    with self.subTest(code=code, field=field['api_id']):
                        left, top = field['x'] * .75, field['y'] * .75
                        right = left + field['width'] * .75
                        bottom = top + field['height'] * .75
                        overlaps = [char['text'] for char in pdf.pages[field['page'] - 1].chars
                                    if char['x0'] < right and char['x1'] > left
                                    and char['top'] < bottom and char['bottom'] > top]
                        self.assertEqual(overlaps, [])


if __name__ == '__main__':
    unittest.main()

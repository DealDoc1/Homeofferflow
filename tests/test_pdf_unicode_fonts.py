"""Real rendering, embedded resources, measured widths, and deployment assets."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import unittest

from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas

from lib.pdf_text import draw_text, font_runs, text_width, paragraph_markup
from lib import contract_terms_continuation, lease_terms_continuation, nonrealty_continuation
from scripts.qa.pdf_unicode_audit import CASES, canonical
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer


class PdfUnicodeFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_audit_cases_survive_main_contract_and_continuation(self):
        for key, value in CASES.items():
            with self.subTest(case=key):
                offer = minimal_offer(buyer1=value, asIs='repairs',
                    repairsText='Keep this complete instruction. '*40+'\nFinal text: '+value)
                before = deepcopy(offer)
                reader = PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer)))
                self.assertIn(canonical(value), canonical(reader.pages[0].extract_text()))
                self.assertIn(canonical('Final text: '+value), canonical(reader.pages[-1].extract_text()))
                # The existing adapter appends render metadata. It must not
                # normalize or otherwise rewrite any original answer.
                self.assertEqual({key: offer[key] for key in before}, before)

    def test_ascii_keeps_original_font_and_exact_width(self):
        for text in ['Example Buyer', '123 Example Street', 'See continuation.', '<oak> & pine']:
            self.assertEqual(font_runs(text), [('Helvetica', text)])
            for size in [7.5, 8, 9.5, 10.5]:
                self.assertEqual(text_width(text, 'Helvetica', size), pdfmetrics.stringWidth(text, 'Helvetica', size))

    def test_canonically_equivalent_accents_have_identical_geometry(self):
        composed='Jos\u00e9 Garc\u00eda'; decomposed='Jose\u0301 Garci\u0301a'
        self.assertEqual(font_runs(composed), font_runs(decomposed))
        self.assertEqual(text_width(composed,'Helvetica',8),text_width(decomposed,'Helvetica',8))

    def test_overlay_uses_embedded_fonts_and_preserves_mixed_font_word(self):
        raw=BytesIO(); c=Canvas(raw,pagesize=(612,792))
        value='Example \u0141ukasz Nguy\u1ec5n \u738b\u5c0f\u660e'
        draw_text(c,value,50,700,10); c.save()
        page=PdfReader(BytesIO(raw.getvalue())).pages[0]
        self.assertIn(value,page.extract_text())
        embedded=[]
        for ref in page['/Resources']['/Font'].values():
            font=ref.get_object()
            descriptor=font.get('/FontDescriptor')
            if descriptor and '/FontFile2' in descriptor.get_object():
                embedded.append(font)
                self.assertIn('/ToUnicode',font)
        self.assertEqual(len(embedded),2)
        # Each packet embeds subsets, not the entire 10 MB CJK asset.
        self.assertLess(len(raw.getvalue()),150_000)

    def test_paragraph_markup_escapes_input_before_font_wrapping(self):
        value='<font name="Fake">\u738b</font> & \u0141\nNext'
        markup=paragraph_markup(value)
        self.assertIn('&lt;font name="Fake"&gt;',markup)
        self.assertNotIn('<font name="Fake">',markup)
        self.assertIn('&amp;',markup)
        self.assertIn('<br/>',markup)
        self.assertIn('<font name="HOFUnicodeSC">',markup)

    def test_unsupported_glyph_is_not_silently_replaced(self):
        with self.assertRaisesRegex(ValueError,'cannot display correctly'):
            font_runs('Example \U0010ffff')

    def test_all_shared_continuation_types_preserve_unicode(self):
        value='Example \u0141ukasz Nguy\u1ec5n \u738b\u5c0f\u660e'
        long_text=('Keep complete information. '*60)+'\nFinal text: '+value
        cases=[
            (contract_terms_continuation.render_continuation, minimal_offer(brokerDisclosure=long_text)),
            (nonrealty_continuation.render_nonrealty_continuation, minimal_offer(nonRealtyItems='yes',nonRealtyDescription=long_text)),
            (lambda o:lease_terms_continuation.render_continuation(o,'buyer'),minimal_offer(buyerTemporaryLeaseSpecialProvisions=long_text)),
            (lambda o:lease_terms_continuation.render_continuation(o,'seller'),minimal_offer(sellerTemporaryLeaseSpecialProvisions=long_text)),
        ]
        for render,offer in cases:
            reader=PdfReader(BytesIO(render(offer)))
            text=canonical(' '.join(p.extract_text() for p in reader.pages))
            self.assertIn('Final text: '+value,text)

    def test_inline_fit_uses_same_fallback_metrics_as_drawing(self):
        text='\u0141ukasz \u738b\u5c0f\u660e '*9
        for section in ('broker','special'):
            entries=contract_terms_continuation.inline_entries(text,section)
            self.assertIsNotNone(entries)
            for x,y,line,size in entries:
                width=next(w for bx,by,w in contract_terms_continuation.BLANKS[section] if bx==x and by==y)
                independent=sum(pdfmetrics.stringWidth(run,font,size) for font,run in font_runs(line))
                self.assertLessEqual(independent,width)

    def test_fonts_packaged_only_for_pdf_rendering_functions(self):
        root=Path(__file__).resolve().parents[1]
        functions=json.loads((root/'vercel.json').read_text())['functions']
        renderers={'api/fill-pdf.py','api/admin-dashboard.py'}
        for name,config in functions.items():
            if name in renderers:
                self.assertIn('lib/fonts/**',config['includeFiles'],name)
                self.assertNotIn('lib/fonts/**',config['excludeFiles'],name)
            else:
                self.assertIn('lib/fonts/**',config['excludeFiles'],name)
        for name in ['NotoSans-Regular.ttf','HOFUnicodeSC-Regular.ttf','OFL-NotoSans.txt','OFL-NotoSansCJK.txt']:
            self.assertTrue((root/'lib/fonts'/name).is_file())


if __name__=='__main__': unittest.main()

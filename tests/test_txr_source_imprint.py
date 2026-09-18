"""A precise source-imprint removal must not become a general text scrubber."""
import copy
import hashlib
from io import BytesIO
import unittest
from unittest.mock import patch
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, ArrayObject, TextStringObject, NumberObject
from lib import txr_source_imprint as MODULE


def fixture():
    writer = PdfWriter()
    content = (b'BT /F1 10 Tf 40 700 Td [(Legal terms and copyright; Sample Person)] TJ ET\n'
               b'BT 34 25 Td [(Sample Office)] TJ ET\nBT 34 17 Td [(Sample Person)] TJ ET\n'
               b'0 0 m 20 20 l S\n')
    for _ in range(2):
        page = writer.add_blank_page(612, 792)
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({
            NameObject('/F1'): DictionaryObject({NameObject('/Type'): NameObject('/Font'),
              NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})})})
        stream = DecodedStreamObject()
        stream.set_data(content)
        page.replace_contents(stream)
        page[NameObject('/Annots')] = ArrayObject([DictionaryObject({NameObject('/Subtype'): NameObject('/Text'),
                                                                  NameObject('/Contents'): TextStringObject('Keep annotation')})])
    data = BytesIO()
    writer.write(data)
    raw = data.getvalue()
    lines = tuple((hashlib.sha256(text.encode()).hexdigest(), position) for text, position in
                  [('Sample Office', (34, 25)), ('Sample Person', (34, 17))])
    source = PdfReader(BytesIO(raw))
    clone = PdfWriter()
    for page in source.pages:
        clone.add_page(page)
    indices = tuple(tuple(i for i, (args, op) in enumerate(page.get_contents().operations)
                          if op == b'TJ' and str(args[0][0]) in ('Sample Office', 'Sample Person')) for page in clone.pages)
    spec = {'TXR-TEST': (hashlib.sha256(raw).hexdigest(), indices)}
    return raw, source, clone, spec, lines


class SourceImprintTests(unittest.TestCase):
    def test_only_the_two_reviewed_operations_are_removed_and_source_is_untouched(self):
        raw, source, writer, spec, lines = fixture()
        before = [copy.deepcopy(page.get_contents().operations) for page in writer.pages]
        with patch.object(MODULE, 'SOURCE_IMPRINTS', spec), patch.object(MODULE, 'IMPRINT_LINES', lines):
            self.assertEqual(MODULE.remove_known_source_imprint(writer, raw, 'TXR-TEST'), 4)
        for index, page in enumerate(writer.pages):
            self.assertEqual(page.get_contents().operations,
                             [entry for i, entry in enumerate(before[index]) if i not in spec['TXR-TEST'][1][index]])
            self.assertEqual(source.pages[index].get_contents().operations, before[index])
            self.assertEqual(page['/Annots'][0]['/Contents'], 'Keep annotation')
        output = BytesIO()
        writer.write(output)
        for page in PdfReader(output).pages:
            text = page.extract_text()
            self.assertIn('Legal terms and copyright; Sample Person', text)
            self.assertNotIn('Sample Office', text)
            self.assertEqual(text.count('Sample Person'), 1)

    def test_unknown_form_or_changed_source_is_untouched(self):
        for code, suffix in [('OTHER', b''), ('TXR-TEST', b'\nchanged')]:
            raw, _, writer, spec, lines = fixture()
            before = [page.get_contents().get_data() for page in writer.pages]
            with patch.object(MODULE, 'SOURCE_IMPRINTS', spec), patch.object(MODULE, 'IMPRINT_LINES', lines):
                self.assertEqual(MODULE.remove_known_source_imprint(writer, raw + suffix, code), 0)
            self.assertEqual([page.get_contents().get_data() for page in writer.pages], before)

    def test_structure_position_or_text_mismatch_never_partially_edits(self):
        for defect in ('text', 'position', 'operator', 'isolation', 'pages'):
            raw, _, writer, spec, lines = fixture()
            content = writer.pages[1].get_contents()
            index = spec['TXR-TEST'][1][1][0]
            operations = copy.deepcopy(content.operations)
            if defect == 'text':
                operations[index][0][0][0] = TextStringObject('Not the imprint')
            elif defect == 'position':
                operations[index - 1] = ([NumberObject(34), NumberObject(600)], b'Td')
            elif defect == 'operator':
                operations[index] = ([], b'S')
            elif defect == 'isolation':
                operations[index + 1] = ([], b'T*')
            else:
                writer.add_blank_page(612, 792)
            content.operations = operations
            writer.pages[1].replace_contents(content)
            before = [page.get_contents().get_data() if page.get_contents() else b'' for page in writer.pages]
            with self.subTest(defect=defect), patch.object(MODULE, 'SOURCE_IMPRINTS', spec), \
                 patch.object(MODULE, 'IMPRINT_LINES', lines), self.assertRaises(ValueError):
                MODULE.remove_known_source_imprint(writer, raw, 'TXR-TEST')
            self.assertEqual([page.get_contents().get_data() if page.get_contents() else b'' for page in writer.pages], before)

    def test_known_source_manifest_has_only_the_reviewed_form_pages(self):
        self.assertEqual({code: len(plan) for code, (_, plan) in MODULE.SOURCE_IMPRINTS.items()},
                         {'TXR-1501': 6, 'TXR-1506': 6, 'TXR-1507': 2, 'TXR-1508': 1})
        self.assertTrue(all(len(digest) == 64 for digest, _ in MODULE.SOURCE_IMPRINTS.values()))


if __name__ == '__main__':
    unittest.main()

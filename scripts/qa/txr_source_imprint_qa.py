"""Offline before/after imprint QA. Requires private blank sources and Poppler."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import subprocess
from unittest.mock import patch

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter
from lib.txr_source_imprint import SOURCE_IMPRINTS, remove_known_source_imprint
from scripts.run_private_txr_draft_qa import _data, _renderers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_dir', type=Path)
    parser.add_argument('output_dir', type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pages_checked = 0
    for code, (_, renderer, expected_pages) in _renderers().items():
        form_code = code.replace('TXR', 'TXR-')
        source = args.source_dir / f'{code}.pdf'
        raw = source.read_bytes()
        digest, indices = SOURCE_IMPRINTS[form_code]
        assert hashlib.sha256(raw).hexdigest() == digest, f'{code}: unreviewed source'
        original = PdfReader(BytesIO(raw))
        writer = PdfWriter()
        for page in original.pages:
            writer.add_page(page)
        expected = [[entry for i, entry in enumerate(page.get_contents().operations) if i not in indices[n]]
                    for n, page in enumerate(original.pages)]
        imprint_lines = [[str(page.get_contents().operations[i][0][0][0]) for i in indices[n]]
                         for n, page in enumerate(original.pages)]
        assert remove_known_source_imprint(writer, raw, form_code) == 2 * expected_pages
        for number, page in enumerate(writer.pages):
            assert page.get_contents().operations == expected[number], f'{code}: non-imprint operations changed'
        with patch(f'lib.txr_{code[3:]}.remove_known_source_imprint', return_value=0):
            before = renderer(raw, _data()[code])
        after = renderer(raw, _data()[code])
        assert len(PdfReader(BytesIO(after)).pages) == expected_pages
        for label, content in [('before', before), ('after', after)]:
            target = args.output_dir / f'{code}-{label}.pdf'
            target.write_bytes(content)
            subprocess.run(['pdftoppm', '-r', '100', '-png', str(target), str(target.with_suffix(''))], check=True)
        for number in range(1, expected_pages + 1):
            before_image = Image.open(args.output_dir / f'{code}-before-{number}.png').convert('RGB')
            after_image = Image.open(args.output_dir / f'{code}-after-{number}.png').convert('RGB')
            assert before_image.size == after_image.size
            diff = ImageChops.difference(before_image, after_image).getbbox()
            assert diff is not None, f'{code} p{number}: imprint still visible'
            # Original imprint baselines are 17/26pt from the bottom; no
            # difference is permitted outside that measured bottom 34pt band.
            assert diff[1] >= after_image.height - 34 * 100 / 72, (code, number, diff)
            text = PdfReader(BytesIO(after)).pages[number - 1].extract_text()
            assert all(''.join(line.split()) not in ''.join(text.split()) for line in imprint_lines[number - 1])
            # pypdf 4 inserts a space before the source's hyphen; this is an
            # extraction difference, not a visible form-code change.
            assert form_code in ''.join(text.split())
            assert f'Page {number} of {expected_pages}' in ' '.join(text.split())
            pages_checked += 1
        assert source.read_bytes() == raw, f'{code}: source file changed'
        print(f'{code}: {expected_pages} pages; only two footer operations removed per page; all pixels above footer unchanged')
    print(f'PASS: {pages_checked} pages, source files preserved, no network/provider/database activity.')


if __name__ == '__main__':
    main()

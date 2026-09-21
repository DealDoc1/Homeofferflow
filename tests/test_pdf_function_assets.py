"""Offline asset-packaging regression, not a Vercel build or signing QA.

Run real representation renderers in a fresh interpreter with a filtered copy
of lib/. The normal checkout and previously registered ReportLab fonts must not
be available to conceal a missing deployment asset. Sources are blank synthetic
pages and answers are fake; no source PDFs, credentials or network are needed.
"""
from fnmatch import fnmatchcase
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import pypdf
from scripts.run_private_txr_draft_qa import _data


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'vercel.json').read_text())
FONT_FILES = ('NotoSans-Regular.ttf', 'HOFUnicodeSC-Regular.ttf',
              'OFL-NotoSans.txt', 'OFL-NotoSansCJK.txt')


def excluded(path, pattern):
    # The project's current excludes are simple flat brace alternatives.
    # This is intentionally not a general-purpose Vercel/glob implementation.
    patterns = pattern[1:-1].split(',') if pattern.startswith('{') and pattern.endswith('}') else [pattern]
    if any(any(char in part for char in '{}![]') for part in patterns):
        raise ValueError('Unsupported exclusion syntax in the offline asset check')
    return any(fnmatchcase(path, part) for part in patterns)


RENDER = r'''
import importlib
from io import BytesIO
import json
from pathlib import Path
import socket
import sys
from unittest.mock import patch

root = Path(sys.argv[1]).resolve()
# Carry over only the installed PDF dependency location, not the checkout or
# its PYTHONPATH. This also exercises a pinned dependency installed with -t.
sys.path.insert(0, sys.argv[2])
sys.path.insert(0, str(root))
import pypdf
assert pypdf.__version__ == sys.argv[3]
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from lib import pdf_text
assert Path(pdf_text.__file__).resolve().is_relative_to(root)
assert 'HOFUnicode' not in pdfmetrics.getRegisteredFontNames()
assert 'HOFUnicodeSC' not in pdfmetrics.getRegisteredFontNames()
forms = json.load(sys.stdin)
value = 'QA Łukasz Nguyễn 王小明'
brokerage = {'legal_name': 'QA Brokerage', 'license_number': '0000000'}
associate = {'name': 'QA Associate', 'license_number': '0000000'}
results = []
with patch.object(socket.socket, 'connect', side_effect=AssertionError('Network forbidden')):
    for code, base_pages in [('1501', 6), ('1506', 6), ('1507', 2), ('1508', 1)]:
        module = importlib.import_module('lib.txr_' + code)
        render = getattr(module, 'render_txr_' + code)
        source = BytesIO()
        writer = PdfWriter()
        for _ in range(base_pages):
            writer.add_blank_page(width=612, height=792)
        writer.write(source)
        for long in (False, True):
            data = dict(forms['TXR' + code])
            data['client_names'] = [value]
            data['_for_signing'] = True
            if long:
                key = {'1501':'market_area', '1506':'additional_notice',
                       '1507':'market_area', '1508':'property_address'}[code]
                data[key] = ('QA description. ' * 45) + 'End: ' + value
            args = [source.getvalue(), data, brokerage]
            if code != '1506':
                args.append(associate)
            packet = render(*args)
            reader = PdfReader(BytesIO(packet))
            text = ' '.join(page.extract_text() or '' for page in reader.pages)
            assert value in text, (code, long, 'name was lost')
            if long:
                assert len(reader.pages) > base_pages, (code, 'missing continuation')
                assert 'End: ' + value in text, (code, 'last answer was lost')
            else:
                assert len(reader.pages) == base_pages, (code, 'unexpected continuation')
            results.append({'form': code, 'long': long, 'pages': len(reader.pages)})
print(json.dumps(results))
'''


class PdfFunctionAssetsTests(unittest.TestCase):
    def stage(self, target, function, *, omit_fonts=False):
        pattern = CONFIG['functions'][function]['excludeFiles']
        for source in (ROOT / 'lib').rglob('*'):
            if not source.is_file():
                continue
            relative = source.relative_to(ROOT).as_posix()
            if excluded(relative, pattern) or (omit_fonts and relative.startswith('lib/fonts/')):
                continue
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

    def run_renderer(self, root):
        # -I discards inherited PYTHONPATH and the checkout's working directory;
        # only the copied runtime and the interpreter's installed deps remain.
        return subprocess.run([sys.executable, '-I', '-c', RENDER, str(root),
            str(Path(pypdf.__file__).resolve().parents[1]), pypdf.__version__],
            cwd=root, input=json.dumps(_data()), text=True, capture_output=True, timeout=45)

    def test_both_pdf_functions_keep_fonts_and_licenses(self):
        for function in ('api/admin-dashboard.py', 'api/fill-pdf.py'):
            with self.subTest(function=function), tempfile.TemporaryDirectory(prefix='hof-assets-') as tmp:
                root = Path(tmp)
                self.stage(root, function)
                for filename in FONT_FILES:
                    self.assertTrue((root / 'lib/fonts' / filename).is_file(), filename)

    def test_standalone_forms_render_with_configured_assets_in_fresh_process(self):
        with tempfile.TemporaryDirectory(prefix='hof-assets-') as tmp:
            root = Path(tmp)
            self.stage(root, 'api/admin-dashboard.py')
            result = self.run_renderer(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)), 8)

    def test_missing_fonts_reproduce_the_original_failure_not_a_cached_success(self):
        with tempfile.TemporaryDirectory(prefix='hof-assets-missing-') as tmp:
            root = Path(tmp)
            self.stage(root, 'api/admin-dashboard.py', omit_fonts=True)
            result = self.run_renderer(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('NotoSans-Regular.ttf', result.stderr)

    def test_non_pdf_services_still_exclude_the_large_font_assets(self):
        for function, config in CONFIG['functions'].items():
            if function in {'api/admin-dashboard.py', 'api/fill-pdf.py'}:
                continue
            with self.subTest(function=function):
                for filename in FONT_FILES:
                    self.assertTrue(excluded('lib/fonts/' + filename, config['excludeFiles']))


if __name__ == '__main__':
    unittest.main()

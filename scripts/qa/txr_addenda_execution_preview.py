"""Local synthetic render + field outlines; not a provider-completed specimen."""
import argparse
import importlib
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from scripts.render_txr_signwell_map_review import _overlay
from tests.test_txr_execution_name_clearance import CASES, sample
from tests.test_txr_1914_renderer import sample_data as financing_sample


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = {**financing_sample(), **sample(), '_for_signing': True}
    for code, pages in CASES:
        module = importlib.import_module(f'lib.txr_{code}')
        source_bytes = (args.source_dir / f'TXR{code}.pdf').read_bytes()
        source = PdfReader(BytesIO(source_bytes))
        widgets = [annotation.get_object() for page in source.pages
                   for annotation in page.get('/Annots', [])
                   if annotation.get_object().get('/Subtype') == '/Widget']
        if (source.get_fields() or widgets) and code != 1948:
            raise ValueError(f'TXR-{code}: inspect interactive source before using this static-overlay QA helper')
        render = getattr(module, f'render_txr_{code}')
        rendered = PdfReader(BytesIO(render(source_bytes, data)))
        assert len(rendered.pages) == pages
        if code == 1948:
            canonical = rendered.get_fields() or {}
            expected = module._editable_values(source, data)
            assert expected is not None
            for name, value in expected.items():
                assert canonical[name].get('/V') == value, name
            for annotation in rendered.pages[0].get('/Annots', []):
                widget = annotation.get_object()
                if widget.get('/T') in expected:
                    assert widget.get('/V') == canonical[widget['/T']].get('/V')
                    assert widget['/AP']['/N']
        fields = getattr(module, f'build_signwell_fields_txr{code}')(data)[0]
        writer = PdfWriter()
        writer.clone_document_from_reader(rendered)
        for number, page in enumerate(writer.pages, 1):
            if any(field['page'] == number for field in fields):
                page.merge_page(PdfReader(BytesIO(_overlay(number, fields))).pages[0])
        writer.add_metadata({'/Title': f'QA ONLY TXR-{code} execution field outlines - not signed'})
        output = args.output_dir / f'txr{code}-qa-field-outlines.pdf'
        writer.write(output)
        print(f'{output}: {pages} pages; {len(fields)} field outlines; {len(widgets)} source widgets checked')


if __name__ == '__main__':
    main()

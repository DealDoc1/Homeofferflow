#!/usr/bin/env python3
"""Offline, fixed fictional buyer-package specimens. No delivery capability.

Private input directory: TXR1507.pdf, TXR1506.pdf, IABS.pdf. The caller must
pin the saved-profile IABS hash. Outputs contain private licensed source PDFs
and must stay outside repositories. Review guides are NOT completed signatures.
"""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from scripts.render_txr_signwell_map_review import _overlay

from lib.buyer_representation_signing_qa import (
    SOURCE_HASHES, CASES, load_sources, case_data, build_case,
)


def field_guide(package):
    writer = PdfWriter()
    for number, page in enumerate(PdfReader(BytesIO(package.pdf)).pages, 1):
        writer.add_page(page)
        if any(field['page'] == number for field in package.fields[0]):
            writer.pages[-1].merge_page(PdfReader(BytesIO(_overlay(number, package.fields[0]))).pages[0])
        stamp = BytesIO()
        canvas = Canvas(stamp, pagesize=(float(page.mediabox.width), float(page.mediabox.height)))
        canvas.setFillColorRGB(.7, .1, .1)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawCentredString(float(page.mediabox.width) / 2, 779,
                                 'FICTIONAL QA FIELD GUIDE - NOT SIGNED - DO NOT SEND')
        canvas.save()
        writer.pages[-1].merge_page(PdfReader(BytesIO(stamp.getvalue())).pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def run(source_dir, output_dir, iabs_sha256):
    # Refuse repository output before creating any artifacts.
    resolved = output_dir.resolve()
    if any((parent / '.git').exists() for parent in (resolved, *resolved.parents)):
        raise ValueError('Private QA outputs must be outside a Git checkout.')
    sources = load_sources(source_dir, iabs_sha256)
    packages = {case: build_case(sources, case) for case in CASES}
    guides = {case: field_guide(package) for case, package in packages.items()}
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest = {'provider_sends': 0, 'source_sha256': {
        code: sha256(value).hexdigest() for code, value in sources.items()}, 'cases': {}}
    for case, package in packages.items():
        files = {}
        for suffix, value in [('unsigned', package.pdf), ('field-guide', guides[case])]:
            path = output_dir / f'{case}-{suffix}.pdf'
            with path.open('xb') as stream:
                path.chmod(0o600)
                stream.write(value)
            files[path.name] = sha256(value).hexdigest()
        manifest['cases'][case] = {'manifest': package.manifest, 'fields': package.fields,
            'layout_sha256': sha256(json.dumps(package.fields, sort_keys=True).encode()).hexdigest(),
            'files': files}
    path = output_dir / 'manifest.json'
    with path.open('x') as stream:
        path.chmod(0o600)
        json.dump(manifest, stream, indent=2)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_dir', type=Path)
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--iabs-sha256', required=True)
    args = parser.parse_args()
    result = run(args.source_dir, args.output_dir, args.iabs_sha256)
    print(json.dumps({'case_count': len(result['cases']), 'provider_sends': 0}))

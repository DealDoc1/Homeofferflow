"""Read-only geometry audit of three recovered completed-provider components.

This does not create/edit PDFs, send invitations, or prove the full transaction
matrix. Measured bitmaps come from the immutable completed provider output.
"""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.trec_48_1 import build_signwell_fields_trec48_1, SOURCE_PATH
from lib.txr_1953 import build_signwell_fields_txr1953
from lib.txr_1954 import build_signwell_fields_txr1954
from scripts.qa.audit_txr1506_completed import match_marks, PROVIDER_SCALE

COMPLETED_SHA256 = 'd5dd3d701b06cff87934235680dbee1d40e56fe99d827b34f260849208c95f28'
SOURCE_PINS = {
    'TREC-48-1': '3eb6e7ced0723ceaab6bef2645fcd7868ee3c2cd2734a6a5f03dbe049bd5df6a',
    'TXR-1953': '00075ab42b6d7f234c5e70197f02fadb736b2ff3ee02a0dc1f5499535b045fc3',
    'TXR-1954': 'e96fe7d35245aee60920ba264ef870542199fa201e49382a6eac27718fabdc28',
}
COMPONENT_PAGES = {'TREC-48-1': 21, 'TXR-1953': 31, 'TXR-1954': 32}
# Observed printed-source logos and provider TEST MODE watermarks; these are
# not signatures. Exclude only these measured boxes, never an arbitrary size.
BACKGROUNDS = {
    'TREC-48-1': [(40.922, 37.995, 62.156, 51.315),
                  (32.143, 698.206, 59.336, 48.986)],
    'TXR-1953': [(40.8, 37.68, 62.4, 51.84), (31.92, 697.92, 59.76, 49.44)],
    'TXR-1954': [(40.8, 37.68, 62.4, 51.84), (31.92, 697.92, 59.76, 49.44)],
}
WATERMARKS = [(225, 560.09009, 154, 31.90991), (225, 260.09009, 154, 31.90991)]
MARK_KEYS = ('x0', 'top', 'width', 'height')


def current_fields(form):
    parties = {'buyer_names': ['QA Buyer A', 'QA Buyer B'],
               'seller_names': ['QA Seller A', 'QA Seller B']}
    if form == 'TREC-48-1':
        return build_signwell_fields_trec48_1(buyer_count=2, seller_count=2)[0]
    if form == 'TXR-1953':
        return build_signwell_fields_txr1953(parties)[0]
    if form == 'TXR-1954':
        return build_signwell_fields_txr1954(parties)[0]
    raise ValueError('Unknown reviewed component.')


def component_marks(form, images):
    """Keep every bitmap except four uniquely observed background boxes."""
    remaining = list(images)
    for rectangle in BACKGROUNDS[form] + WATERMARKS:
        found = [m for m in remaining if all(
            abs(float(m[key]) - expected) < .02
            for key, expected in zip(MARK_KEYS, rectangle))]
        if len(found) != 1:
            raise ValueError('The recovered component background identity changed.')
        remaining.remove(found[0])
    return [{'page': 1, **{key: float(m[key]) for key in MARK_KEYS}}
            for m in remaining]


def audit(source_paths, completed_path):
    import pdfplumber
    from pypdf import PdfReader

    raw = completed_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != COMPLETED_SHA256:
        raise ValueError('The recovered completed-provider identity changed.')
    completed = PdfReader(BytesIO(raw))
    if len(completed.pages) != 32 or completed.get_fields() or any(
        a.get_object().get('/Subtype') == '/Widget'
        for p in completed.pages for a in p.get('/Annots', [])):
        raise ValueError('The completed provider page/field structure changed.')
    for form, pin in SOURCE_PINS.items():
        source = source_paths[form].read_bytes()
        if hashlib.sha256(source).hexdigest() != pin:
            raise ValueError('The approved source identity changed: ' + form)
        reader = PdfReader(BytesIO(source))
        if len(reader.pages) != 1 or tuple(reader.pages[0].mediabox) != (0, 0, 612, 792):
            raise ValueError('The approved source page shape changed: ' + form)
    cases = []
    with pdfplumber.open(completed_path) as pdf:
        for form, number in COMPONENT_PAGES.items():
            measured = match_marks(current_fields(form), component_marks(form, pdf.pages[number - 1].images))
            cases.append({'form': form, 'case': 'ordinary_two_buyers_two_sellers',
                          'composite_page': number, 'source_sha256': SOURCE_PINS[form],
                          'measured_marks': measured, 'signatures_count': len(measured),
                          'all_form_cases_passed': False,
                          'combined_packet_assembly_verified': False})
    return {'completed_sha256': COMPLETED_SHA256, 'provider_scale': PROVIDER_SCALE,
            'provider_document_id': '13f7fe33-3620-4b61-b66e-4c96b5792c1f',
            'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--completed', type=Path, required=True)
    parser.add_argument('--txr1953-source', type=Path, required=True)
    parser.add_argument('--txr1954-source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit({'TREC-48-1': SOURCE_PATH, 'TXR-1953': args.txr1953_source,
                           'TXR-1954': args.txr1954_source}, args.completed), indent=2))


if __name__ == '__main__':
    main()

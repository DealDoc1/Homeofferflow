"""Read-only audit of the recovered ordinary two-consumer TXR-1506 test.

No PDFs are created, edited, uploaded or sent. Bitmap origins are measured
from the immutable completed provider PDF, independently of requested maps.
This verifies one case; dates additionally require the recorded visual review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.txr_1506 import build_signwell_fields_txr1506

SOURCE_SHA256 = 'df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4'
COMPLETED_SHA256 = 'd5dd3d701b06cff87934235680dbee1d40e56fe99d827b34f260849208c95f28'
# Independent provider bitmap calibration, not the local PDF-outline scale.
PROVIDER_SCALE = 0.7528125
TOLERANCE = 0.02


def match_marks(fields, marks):
    """Require each actual bitmap to match exactly one current field origin."""
    expected = [f for f in fields if f['type'] in {'initials', 'signature'}]
    if len(marks) != len(expected):
        raise ValueError('Completed bitmap count does not match the current map.')
    unused = list(marks)
    results = []
    for field in expected:
        x = (field['x'] + 1) * PROVIDER_SCALE
        top = (field['y'] - 1) * PROVIDER_SCALE
        height = field['height'] * PROVIDER_SCALE
        matches = [m for m in unused if m['page'] == field['page']
                   and abs(m['x0'] - x) <= TOLERANCE
                   and abs(m['top'] - top) <= TOLERANCE
                   and abs(m['height'] - height) <= TOLERANCE
                   and 0 < m['width'] <= field['width'] * PROVIDER_SCALE + TOLERANCE]
        if len(matches) != 1:
            raise ValueError('Completed origin does not uniquely match ' + field['api_id'])
        mark = matches[0]
        unused.remove(mark)
        results.append({'field': field['api_id'], 'type': field['type'],
                        'page': field['page'], 'x0': mark['x0'], 'top': mark['top'],
                        'width': mark['width'], 'height': mark['height']})
    if unused:
        raise ValueError('Unexpected completed marks remain.')
    return results


def audit(source_path, completed_path):
    import pdfplumber
    from pypdf import PdfReader

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('The approved TXR-1506 source identity changed.')
    if hashlib.sha256(completed_path.read_bytes()).hexdigest() != COMPLETED_SHA256:
        raise ValueError('This is not the independently recovered completed test.')
    source = PdfReader(source_path)
    completed = PdfReader(completed_path)
    if len(source.pages) != 6 or len(completed.pages) != 32:
        raise ValueError('The reviewed source/composite page shape changed.')
    if completed.get_fields() or any(
        annotation.get_object().get('/Subtype') == '/Widget'
        for page in completed.pages for annotation in page.get('/Annots', [])):
        raise ValueError('The recovered completed test unexpectedly has editable fields.')
    marks = []
    with pdfplumber.open(completed_path) as pdf:
        for index in range(22, 28):
            # Printed source logo and two large TEST MODE watermarks are not
            # initials/signatures. Audit only the known execution-page regions.
            cutoff = 730 if index < 27 else 595
            for bitmap in pdf.pages[index].images:
                if bitmap['top'] < cutoff:
                    continue
                marks.append({'page': index - 21, **{key: float(bitmap[key])
                              for key in ('x0', 'top', 'width', 'height')}})
    fields = build_signwell_fields_txr1506(
        {'signer_plan': 'consumers_and_associate'}, client_count=2, page_count=6)[0]
    measured = match_marks(fields, marks)
    return {'case': 'ordinary_two_consumers_and_associate',
            'source_sha256': SOURCE_SHA256, 'completed_sha256': COMPLETED_SHA256,
            'composite_pages': [23, 24, 25, 26, 27, 28],
            'provider_scale': PROVIDER_SCALE, 'measured_marks': measured,
            'initials_count': sum(f['type'] == 'initials' for f in measured),
            'signature_count': sum(f['type'] == 'signature' for f in measured),
            'date_fields_requiring_visual_review': [f['api_id'] for f in fields if f['type'] == 'date'],
            'all_form_cases_passed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--completed', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.source, args.completed), indent=2))


if __name__ == '__main__':
    main()

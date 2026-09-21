"""Read-only measurements for the one-client/associate nonbinding TXR-1507 test.

This does not validate legal execution, edit a PDF, or approve untested signer
variants. Visual inspection of the completed pages is still required.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pdfplumber


REGIONS = {
    # left, right, top, bottom in 72-DPI, top-origin PDF coordinates.
    'associate_initials': (325.98, 361.06, 730, 745.266),
    'client_initials': (406.52, 444.03, 730, 745.266),
    'associate_signature': (36, 216, 513, 533.95),
    'client_signature': (324, 504, 513, 533.95),
    'associate_date': (234, 288.05, 519, 533.95),
    'client_date': (522, 576.10, 519, 533.95),
}


def contained(box, region):
    left, right, top, bottom = region
    return (left <= box['x0'] < box['x1'] <= right and
            top <= box['top'] < box['bottom'] <= bottom)


def validate_measurements(measurements):
    if set(measurements) != set(REGIONS):
        raise ValueError('Expected exactly the six tested signature/date/initial regions')
    for name, bounds in REGIONS.items():
        if not contained(measurements[name], bounds):
            raise ValueError(name + ' extends beyond its measured source region')
    return True


def _bounds(items):
    return {'x0': min(i['x0'] for i in items), 'x1': max(i['x1'] for i in items),
            'top': min(i['top'] for i in items), 'bottom': max(i['bottom'] for i in items)}


def inspect(path):
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 2:
            raise ValueError('This verifier covers only the two-page nonbinding test download')
        text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
        for required in ('NOT LEGALLY VALID (TEST MODE)', 'QA Placement Client',
                         'QA Placement Associate', 'QA ONLY - NOT A REAL TRANSACTION'):
            if ''.join(required.split()) not in ''.join(text.split()):
                raise ValueError('Not the expected nonbinding QA specimen')
        measured = {}
        for name, region in REGIONS.items():
            page = pdf.pages[0 if 'initials' in name else 1]
            left, right, top, bottom = region
            if 'date' in name:
                # A broad capture catches artwork crossing a source line.
                chars = [c for c in page.chars if c['text'] in '0123456789/'
                         and left - 10 < c['x0'] < right + 10
                         and top - 8 < c['top'] < bottom + 18]
                if ''.join(c['text'] for c in chars) != '09/18/2026':
                    raise ValueError(name + ' does not contain the expected complete date')
                measured[name] = _bounds(chars)
            else:
                artwork = [i for i in page.images if left - 10 < i['x0'] < right
                           and top - 8 < i['top'] < bottom + 18]
                if len(artwork) != 1:
                    raise ValueError(name + ' needs one identifiable provider-rendered image')
                measured[name] = _bounds(artwork)
        validate_measurements(measured)
    return {'scope': 'TXR1507 one client and associate; nonbinding test only',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'pages': 2,
            'measurements': measured, 'measured_regions_pass': True,
            'audit_page_included': False, 'visual_review_required': True,
            'does_not_cover': ['second client', 'broker signer', 'other service/intermediary elections']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.pdf), indent=2))


if __name__ == '__main__':
    main()

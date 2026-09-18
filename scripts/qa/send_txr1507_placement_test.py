"""Send one nonbinding candidate-map test to the owner's two QA addresses.

No production configuration, existing document, or real client is changed.
The API key is read from the terminal without echo and never written to disk.
"""
import argparse
import base64
import getpass
import json
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfReader
from lib.txr_1507 import render_txr_1507, build_signwell_fields_txr1507
from scripts.render_txr_signwell_map_review import txr1507_value_overlay_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--send', action='store_true')
    args = parser.parse_args()
    receipt = args.output_dir / 'receipt.json'
    if receipt.exists():
        raise SystemExit('Receipt already exists; inspect it before creating another test.')
    data, brokerage, associate = txr1507_value_overlay_data()
    data['client_names'] = ['QA Placement Client']
    data['market_area'] = 'QA ONLY - NOT A REAL TRANSACTION'
    data['term_start'] = '2026-09-18'
    data['term_end'] = '2026-09-19'
    associate['name'] = 'QA Placement Associate'
    raw = render_txr_1507(args.source.read_bytes(), data, brokerage, associate)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'unsigned.pdf').write_bytes(raw)
    payload = {
        'test_mode': True, 'draft': False, 'apply_signing_order': False,
        'name': 'QA ONLY - TXR1507 placement correction - 2026-09-18',
        'subject': 'TEST ONLY: corrected TXR1507 signature placement',
        'message': 'Nonbinding placement test, not a client agreement. Please complete the test signature and initials so the final PDF can be checked. Both test recipients may sign independently.',
        'files': [{'name': 'QA_TXR1507_placement.pdf', 'file_base64': base64.b64encode(raw).decode('ascii')}],
        'recipients': [
            {'id': '1', 'name': 'QA Placement Client', 'email': 'brewbqinfo@gmail.com'},
            {'id': 'associate', 'name': 'QA Placement Associate', 'email': 'andrewchri@gmail.com'},
        ],
        'fields': build_signwell_fields_txr1507(data, client_count=1, page_count=len(PdfReader(BytesIO(raw)).pages)),
        'reminders': False,
    }
    if not args.send:
        print('Unsigned test prepared; nothing sent.')
        return
    key = getpass.getpass('Existing SignWell API key (hidden): ')
    if not key.strip():
        raise SystemExit('No key supplied; nothing sent.')
    # No automatic retry: a network timeout can occur after document creation.
    result = httpx.post('https://www.signwell.com/api/v1/documents/',
        headers={'X-Api-Key': key.strip()}, json=payload, timeout=60)
    if result.status_code != 201:
        print('SignWell response:', result.status_code)
        raise SystemExit('Test creation not confirmed. Inspect provider before retrying.')
    response = result.json()
    metadata = {k: response.get(k) for k in ('id', 'name', 'status', 'test_mode', 'created_at')}
    metadata['recipients'] = [
        {k: recipient.get(k) for k in ('id', 'name', 'email', 'status')}
        for recipient in response.get('recipients', [])
    ]
    receipt.write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()

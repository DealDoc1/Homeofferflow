"""One fixed nonbinding disclosure placement test; never a customer workflow.

Default is offline. --send uses a temporary existing-key file, removed after
use, and exclusively reserves receipt.json before any provider side effect.
An interrupted/unconfirmed attempt is not automatically retried or replaced.
This tests provider geometry, not authenticated Seller review or live schema.
"""
import argparse
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys

import httpx
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.purchase_signing_qa import QA_RECIPIENTS
from lib.seller_disclosure_explanations import RENDER_REVISION
from lib.signwell_request import document_matches_signing_request, send_options
from lib.signwell_delivery import document_state

REVISION = 'seller-disclosure-provider-2026-10-16-date-fit-v2'
REVIEWED_RENDER_FILES = {
    'lib/trec_seller_disclosure.py': 'f377e0b319adf570fd6cd4b2c7cb095abb3c782e14511540c642daca641b565c',
    'lib/seller_disclosure_explanations.py': 'a0923b472611c0823abab43b7d0799c8b1c8dcc988889b3c78483ce3c507fa51',
}
BASE_URL = 'https://www.signwell.com/api/v1/documents/'


def validate_renderer():
    for name, digest in REVIEWED_RENDER_FILES.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Reviewed disclosure renderer changed; inspect it before another QA attempt.')


def build_packet(specimen_dir):
    manifest = json.loads((specimen_dir / 'manifest.json').read_text())
    writer, fields, cases = PdfWriter(), [], []
    expected_cases = ['one-seller', 'two-sellers-water', 'unicode-overflow', 'unknown-responses']
    if [c['case'] for c in manifest['cases']] != expected_cases:
        raise ValueError('Unexpected fictional specimen matrix.')
    for case in manifest['cases']:
        packet = (specimen_dir / (case['case'] + '.pdf')).read_bytes()
        if hashlib.sha256(packet).hexdigest() != case['packet_sha256']:
            raise ValueError('Fictional specimen bytes differ from their manifest.')
        reader = PdfReader(BytesIO(packet))
        if len(reader.pages) != case['pages']:
            raise ValueError('Fictional specimen page count changed.')
        # Keep every execution/initials/continuation page, without changing any
        # source content or field rectangle. This reduces repetitive QA pages.
        selected = sorted({f['page'] for f in case['fields']})
        remap = {}
        for number in selected:
            remap[number] = len(writer.pages) + 1
            writer.add_page(reader.pages[number - 1])
        for field in case['fields']:
            fields.append({**field, 'api_id': case['case'] + '_' + field['api_id'],
                           'page': remap[field['page']],
                           'recipient_id': 'qa_b' if field['recipient_id'] in {'2', '4'} else 'qa_a'})
        cases.append({'case': case['case'], 'source_pages': selected,
                      'output_pages': list(remap.values()), 'field_count': len(case['fields'])})
    if len({f['api_id'] for f in fields}) != len(fields):
        raise ValueError('Duplicate QA field identifiers.')
    writer.add_metadata({'/Title': 'QA ONLY - seller disclosure placement',
                         '/Subject': 'Fictional nonbinding provider geometry test'})
    output = BytesIO(); writer.write(output)
    return output.getvalue(), [fields], cases


def payload_for(packet, fields):
    return {'test_mode': True, 'draft': True, 'reminders': False,
            'apply_signing_order': False, 'embedded_signing': False,
            'with_signature_page': False, 'custom_requester_name': 'HomeOfferFlow',
            'name': 'QA ONLY - seller disclosure date fit - v4',
            'subject': 'TEST ONLY: HomeOfferFlow seller disclosure placement',
            'message': 'Fictional, nonbinding placement test only. Main disclosure, water rights and attached details cover one Seller, four parties, Unicode and Unknown answers. Both approved test recipients may sign independently. This is not a client agreement.',
            'recipients': [dict(r) for r in QA_RECIPIENTS],
            'files': [{'name': 'QA_ONLY_disclosure_execution.pdf',
                       'file_base64': base64.b64encode(packet).decode('ascii')}],
            'fields': fields, 'metadata': {'qa_revision': REVISION, 'render_revision': RENDER_REVISION,
                'reviewed_renderer_sha256': hashlib.sha256(json.dumps(REVIEWED_RENDER_FILES, sort_keys=True).encode()).hexdigest()}}


def persist(path, receipt):
    temp = path.with_suffix('.next.json')
    temp.write_text(json.dumps(receipt, indent=2) + '\n')
    temp.replace(path)


def validation_error(response):
    try:
        body = response.json()
    except ValueError:
        return {'http_status': response.status_code}
    # This fixed QA request has only fictional data. Never retain a full
    # provider response, credentials, URLs or recipient delivery links.
    return {key: str(body[key])[:600] for key in ('error', 'errors', 'message', 'error_message')
            if isinstance(body, dict) and key in body}


def resume_existing(output, key_path):
    """One explicit recovery of a verified 422 draft, never a second create."""
    receipt_path = output / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    try:
        if (receipt.get('phase') != 'send_unconfirmed' or receipt.get('send_http_status') != 422
                or receipt.get('resume_attempted') or receipt.get('qa_revision') != REVISION):
            raise ValueError('Only the recorded rejected draft can be recovered once.')
        packet = (output / 'QA_ONLY_disclosure_execution.pdf').read_bytes()
        fields = json.loads((output / 'fields.json').read_text())
        if (hashlib.sha256(packet).hexdigest() != receipt['packet_sha256']
                or hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest() != receipt['fields_sha256']):
            raise ValueError('Recorded packet or fields changed; nothing sent.')
        payload = payload_for(packet, fields)
        key = key_path.read_text().strip()
        if not key:
            raise ValueError('Existing provider credential is unavailable.')
        with httpx.Client(timeout=45, headers={'X-Api-Key': key, 'X-TestMode-Enabled': 'true'}) as client:
            url = BASE_URL + receipt['document_id']
            checked = client.get(url)
            if checked.status_code != 200:
                raise ValueError('Recorded draft cannot be checked; nothing sent.')
            document = checked.json()
            if (document.get('id') != receipt['document_id'] or document_state(document) != 'draft'
                    or document.get('test_mode') is not True or document.get('name') != payload['name']
                    or (document.get('metadata') or {}).get('qa_revision') != REVISION
                    or not document_matches_signing_request(document, fields, payload['recipients'])):
                raise ValueError('Recorded document is not the exact unsent test draft; nothing sent.')
            receipt.update(resume_attempted=True, phase='resume_send_requested')
            persist(receipt_path, receipt)
            response = client.post(url + '/send', json=send_options(payload))
            receipt['resume_send_http_status'] = response.status_code
            if response.status_code not in {200, 201, 202}:
                receipt.update(phase='send_rejected', validation=validation_error(response))
            else:
                receipt['phase'] = 'sent'
                result = client.get(url)
                if result.status_code == 200:
                    receipt['provider_status'] = result.json().get('status')
            return receipt
    finally:
        persist(receipt_path, receipt)
        key_path.unlink(missing_ok=True)


def send_once(output, packet, fields, cases, key_path):
    receipt_path = output / 'receipt.json'
    receipt = {'qa_revision': REVISION, 'render_revision': RENDER_REVISION,
               'phase': 'reserved', 'test_mode': True, 'cases': cases,
               'packet_sha256': hashlib.sha256(packet).hexdigest(),
               'fields_sha256': hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()}
    # Existing receipt always wins, even when its provider result is uncertain.
    with receipt_path.open('x') as file:
        file.write(json.dumps(receipt, indent=2) + '\n')
    try:
        key = key_path.read_text().strip()
        if not key:
            raise ValueError('Existing provider credential is unavailable.')
        headers = {'X-Api-Key': key, 'X-TestMode-Enabled': 'true'}
        payload = payload_for(packet, fields)
        with httpx.Client(timeout=45, headers=headers) as client:
            receipt['phase'] = 'create_requested'; persist(receipt_path, receipt)
            created = client.post(BASE_URL, json=payload)
            receipt['create_http_status'] = created.status_code
            if created.status_code != 201:
                receipt['phase'] = 'create_unconfirmed'; return receipt
            document = created.json()
            if document.get('id'):
                receipt['document_id'] = document['id']
            receipt['phase'] = 'draft_created'; persist(receipt_path, receipt)
            if not receipt.get('document_id') or document.get('test_mode') is not True:
                receipt['phase'] = 'identity_unconfirmed'; return receipt
            exact_url = BASE_URL + str(receipt['document_id']) + '/'
            checked = client.get(exact_url)
            if checked.status_code != 200:
                receipt['phase'] = 'readback_unconfirmed'; return receipt
            document = checked.json()
            if (document.get('id') != receipt['document_id'] or document.get('test_mode') is not True
                    or document.get('name') != payload['name']
                    or (document.get('metadata') or {}).get('qa_revision') != REVISION
                    or not document_matches_signing_request(document, fields, payload['recipients'])):
                receipt['phase'] = 'field_readback_mismatch'; return receipt
            receipt['fields_verified'] = True
            receipt['phase'] = 'send_requested'; persist(receipt_path, receipt)
            sent = client.post(exact_url + 'send/', json=send_options(payload))
            receipt['send_http_status'] = sent.status_code
            receipt['phase'] = 'sent' if sent.status_code in {200, 201, 202} else 'send_unconfirmed'
            if receipt['phase'] != 'sent':
                receipt['validation'] = validation_error(sent)
            if receipt['phase'] == 'sent':
                final = client.get(exact_url)
                if final.status_code == 200:
                    doc = final.json()
                    receipt['provider_status'] = doc.get('status')
                    receipt['recipient_statuses'] = [{'id': r.get('id'), 'status': r.get('status')}
                                                     for r in doc.get('recipients') or []]
        return receipt
    except Exception as error:
        receipt['error_type'] = type(error).__name__
        raise
    finally:
        persist(receipt_path, receipt)
        key_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--send', action='store_true')
    parser.add_argument('--resume-existing', action='store_true')
    parser.add_argument('--existing-key-file', type=Path)
    args = parser.parse_args()
    validate_renderer()
    if args.resume_existing:
        if args.send or not args.existing_key_file:
            raise SystemExit('Choose only explicit recovery and the existing temporary key file.')
        print(json.dumps(resume_existing(args.output_dir, args.existing_key_file))); return
    if (args.output_dir / 'receipt.json').exists():
        raise SystemExit('A provider attempt is already reserved. Inspect it; do not recreate or resend.')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    specimens = args.output_dir / 'specimens'
    subprocess.run([sys.executable, '-m', 'scripts.qa.check_seller_disclosure_explanations',
                    '--disclosure-source', str(args.source_dir / 'seller_disclosure_notice_55-1.pdf'),
                    '--water-source', str(args.source_dir / 'seller_water_disclosure_61-0.pdf'),
                    '--output-dir', str(specimens)], check=True, cwd=ROOT)
    packet, fields, cases = build_packet(specimens)
    (args.output_dir / 'QA_ONLY_disclosure_execution.pdf').write_bytes(packet)
    (args.output_dir / 'fields.json').write_text(json.dumps(fields, indent=2) + '\n')
    (args.output_dir / 'manifest.json').write_text(json.dumps({'cases': cases, 'render_revision': RENDER_REVISION,
        'packet_sha256': hashlib.sha256(packet).hexdigest(), 'nothing_sent': True}, indent=2) + '\n')
    if not args.send:
        print(json.dumps({'nothing_sent': True, 'cases': cases, 'fields': len(fields[0])})); return
    if not args.existing_key_file:
        raise SystemExit('An existing temporary provider credential is required; nothing sent.')
    result = send_once(args.output_dir, packet, fields, cases, args.existing_key_file)
    print(json.dumps(result))


if __name__ == '__main__':
    main()

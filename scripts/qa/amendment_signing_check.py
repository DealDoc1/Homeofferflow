"""Prepare the same fixed amendment matrix used by protected production QA.

Read the approved fixture, write only fictional review artifacts; never send.
"""
import argparse
import hashlib
import json
from pathlib import Path

from lib import amendment_signing_qa as qa
from scripts.qa.purchase_signing_check import layout_fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2] / 'tests/fixtures/trec_39_11_source.pdf'
    packet, fields, cases = qa.build_packet(source.read_bytes())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'unsigned.pdf').write_bytes(packet)
    record = {'source_sha256': qa.SOURCE_SHA256,
              'packet_sha256': hashlib.sha256(packet).hexdigest(),
              'fields_sha256': hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest(),
              'layout_sha256': layout_fingerprint(packet, fields, cases),
              'cases': cases, 'fields': fields, 'nothing_sent': True}
    (args.output_dir / 'manifest.json').write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: value for key, value in record.items() if key not in {'fields', 'cases'}}))
    print(f'Prepared {len(cases)} cases and {len(fields[0])} signing fields. Nothing sent.')


if __name__ == '__main__':
    main()

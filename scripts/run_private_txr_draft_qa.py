#!/usr/bin/env python3
"""Run local draft-render QA against privately supplied TXR source PDFs.

This command intentionally stops at unsigned draft output. It never uploads a
source, changes brokerage authorization, creates a SignWell document, or marks
an item released. The source directory and generated PDFs stay local.
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import sys

from pypdf import PdfReader

# Make `python scripts/run_private_txr_draft_qa.py ...` work from a clean
# checkout without requiring callers to set PYTHONPATH.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.txr_1501 import render_txr_1501
from lib.txr_1506 import render_txr_1506
from lib.txr_1507 import render_txr_1507
from lib.txr_1508 import render_txr_1508


BROKERAGE = {"legal_name": "Example Brokerage", "license_number": "0000000", "name": "Example Brokerage"}
ASSOCIATE = {"name": "Example Associate", "license_number": "0000000"}


def _data():
    clients = ["Draft Client One", "Draft Client Two"]
    return {
        "TXR1501": {
            "client_names": clients,
            "client_address": "100 Example Street",
            "client_city_state_zip": "Example, TX 75000",
            "client_phone": "0000000000",
            "client_email": "draft@example.invalid",
            "market_area": "Collin and Denton Counties, Texas",
            "term_start": "2026-08-01",
            "term_end": "2027-01-31",
            "compensation": {"purchase_percentage": "3"},
            "retainer_amount": "",
            "retainer_treatment": "",
            "protection_days": "30",
            "payment_county": "Collin",
            "intermediary": "authorized",
        },
        "TXR1506": {
            "client_names": clients,
            "additional_notice": "Please review and ask questions before signing.",
            "signer_plan": "consumers_and_associate",
        },
        "TXR1507": {
            "client_names": clients,
            "market_area": "Example Property, Example City, Example County, Texas 75000",
            "term_start": "2026-08-01",
            "term_end": "2027-01-31",
            "service_level": "full_services",
            "showing_fee": "",
            "compensation": {
                "purchase_percentage": "3",
                "purchase_flat_fee": "",
                "lease_one_month_percentage": "",
                "lease_total_rents_percentage": "",
                "lease_flat_fee": "",
            },
            "intermediary": "authorized",
            "signer_plan": "clients_and_associate",
        },
        "TXR1508": {
            "property_address": "Example Property, Example City, TX 75000",
            "client_names": ["Unrepresented Client One", "Unrepresented Client Two"],
            "other_broker_agreement": ["no", "no"],
            "signer_plan": "associate_and_clients",
        },
    }


def _renderers():
    return {
        "TXR1501": (render_txr_1501, lambda source, data: render_txr_1501(source, data, BROKERAGE, ASSOCIATE), 6),
        "TXR1506": (render_txr_1506, lambda source, data: render_txr_1506(source, data, BROKERAGE), 6),
        "TXR1507": (render_txr_1507, lambda source, data: render_txr_1507(source, data, BROKERAGE, ASSOCIATE), 2),
        "TXR1508": (render_txr_1508, lambda source, data: render_txr_1508(source, data, BROKERAGE, ASSOCIATE), 1),
    }


def run(source_dir: Path, output_dir: Path) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for code, (_, renderer, expected_pages) in _renderers().items():
        source_path = source_dir / f"{code}.pdf"
        if not source_path.is_file():
            raise FileNotFoundError(f"Missing private source: {source_path}")
        rendered = renderer(source_path.read_bytes(), _data()[code])
        actual_pages = len(PdfReader(BytesIO(rendered)).pages)
        if actual_pages != expected_pages:
            raise ValueError(f"{code}: expected {expected_pages} pages, got {actual_pages}")
        output_path = output_dir / f"{code}_draft.pdf"
        output_path.write_bytes(rendered)
        results.append({"form": code, "pages": actual_pages, "output": str(output_path)})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="Private directory containing TXR1501.pdf, TXR1506.pdf, TXR1507.pdf, and TXR1508.pdf")
    parser.add_argument("output_dir", type=Path, help="Local directory for unsigned draft PDFs")
    args = parser.parse_args()
    print("Running local unsigned TXR draft QA; no source upload or signing will occur.")
    for result in run(args.source_dir, args.output_dir):
        print(f"{result['form']}: {result['pages']} pages -> {result['output']}")
    print("Draft QA passed. Restricted workflows remain gated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

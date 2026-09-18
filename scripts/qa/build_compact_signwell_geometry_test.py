#!/usr/bin/env python3
"""Build one nonbinding SignWell packet for all pending map corrections.

The production maps use several semantic recipient IDs. For provider-rendering
QA only, this helper remaps every field to one of the owner's two approved QA
addresses. Geometry, field type, required state, and page placement are left
unchanged. This reduces six separate provider documents to one signing session
without changing application behavior or production recipients.

Nothing is sent unless ``--send`` is provided. A successful provider response
is saved before the helper can create another test in the same output folder.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import importlib
import json
import sys
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfReader, PdfWriter

from scripts.render_txr_signwell_map_review import txr1507_value_overlay_data
from tests.test_txr_1501_renderer import sample_data as txr1501_sample
from tests.test_txr_1914_renderer import sample_data as txr1914_sample
from tests.test_txr_1919_renderer import sample_data as txr1919_sample


QA_RECIPIENTS = [
    {"id": "qa_a", "name": "QA Signer A", "email": "andrewchri@gmail.com"},
    {"id": "qa_b", "name": "QA Signer B", "email": "brewbqinfo@gmail.com"},
]
FORM_ORDER = ("1501", "1507", "1905", "1914", "1917", "1919")


def sample_for(code: str) -> tuple[dict, dict | None, dict | None]:
    brokerage = {
        "legal_name": "QA Review Brokerage",
        "license_number": "0000000",
        "address": "100 Review Lane",
        "city_state_zip": "Austin, TX 78701",
        "phone": "512-555-0100",
        "email": "qa-broker@example.test",
    }
    associate = {"name": "QA Review Associate", "license_number": "0000000"}
    if code == "1501":
        data = txr1501_sample()
        data.update(
            client_names=["QA Client One", "QA Client Two"],
            signer_plan="clients_and_associate",
            _for_signing=True,
        )
        return data, brokerage, associate
    if code == "1507":
        data, short_brokerage, short_associate = txr1507_value_overlay_data()
        data.update(
            client_names=["QA Client One", "QA Client Two"],
            market_area="QA ONLY - NOT A REAL TRANSACTION",
            signer_plan="clients_and_associate",
            _for_signing=True,
        )
        return data, short_brokerage, short_associate
    if code == "1905":
        return ({
            "property_address": "100 Review Lane, Austin, TX 78701",
            "buyer_names": ["QA Buyer One", "QA Buyer Two"],
            "seller_names": ["QA Seller One", "QA Seller Two"],
            "reservation_choice": "undivided_interest",
            "undivided_interest": "25",
            "surface_rights": "not_waived",
            "_for_signing": True,
        }, None, None)
    if code == "1914":
        return ({**txr1914_sample(), "_for_signing": True}, None, None)
    if code == "1917":
        return ({
            "property_address": "100 Review Lane, Austin, TX 78701",
            "review_types": ["environmental", "wetlands"],
            "termination_days": "10",
            "buyer_names": ["QA Buyer One", "QA Buyer Two"],
            "seller_names": ["QA Seller One", "QA Seller Two"],
            "_for_signing": True,
        }, None, None)
    if code == "1919":
        return ({**txr1919_sample(), "_for_signing": True}, None, None)
    raise ValueError(f"Unsupported compact QA form: TXR-{code}")


def qa_recipient(original_id: str) -> str:
    """Map every production role to one of two non-production QA signers."""
    return "qa_b" if str(original_id) in {"2", "4"} else "qa_a"


def render_form(source_bytes: bytes, code: str, data: dict,
                brokerage: dict | None, associate: dict | None) -> bytes:
    module = importlib.import_module(f"lib.txr_{code}")
    renderer = getattr(module, f"render_txr_{code}")
    if code in {"1501", "1507"}:
        return renderer(source_bytes, data, brokerage or {}, associate or {})
    return renderer(source_bytes, data)


def form_fields(code: str, data: dict, page_count: int) -> list[dict]:
    module = importlib.import_module(f"lib.txr_{code}")
    builder = getattr(module, f"build_signwell_fields_txr{code}")
    if code in {"1501", "1507"}:
        return builder(data, client_count=2, page_count=page_count)[0]
    return builder(data)[0]


def build_packet(source_dir: Path) -> tuple[bytes, list[list[dict]], list[dict]]:
    writer = PdfWriter()
    combined_fields: list[dict] = []
    manifest: list[dict] = []
    page_offset = 0

    for code in FORM_ORDER:
        source_path = source_dir / f"TXR{code}.pdf"
        if not source_path.is_file():
            raise FileNotFoundError(f"Missing private QA source: {source_path}")
        data, brokerage, associate = sample_for(code)
        rendered = render_form(source_path.read_bytes(), code, data, brokerage, associate)
        reader = PdfReader(BytesIO(rendered))
        local_fields = form_fields(code, data, len(reader.pages))
        shifted = []
        for field in local_fields:
            shifted_field = dict(field)
            shifted_field["page"] = int(field["page"]) + page_offset
            shifted_field["recipient_id"] = qa_recipient(str(field["recipient_id"]))
            shifted.append(shifted_field)
        for page in reader.pages:
            writer.add_page(page)
        combined_fields.extend(shifted)
        manifest.append({
            "form_code": f"TXR-{code}",
            "start_page": page_offset + 1,
            "end_page": page_offset + len(reader.pages),
            "field_count": len(shifted),
            "original_recipient_ids": sorted({str(f["recipient_id"]) for f in local_fields}),
        })
        page_offset += len(reader.pages)

    if len({field["api_id"] for field in combined_fields}) != len(combined_fields):
        raise ValueError("Compact QA packet contains duplicate SignWell field IDs.")
    if {field["recipient_id"] for field in combined_fields} != {"qa_a", "qa_b"}:
        raise ValueError("Compact QA packet must exercise both approved QA recipients.")

    writer.add_metadata({
        "/Title": "QA ONLY - HomeOfferFlow corrected signer geometry",
        "/Subject": "Nonbinding combined provider-rendering test",
    })
    output = BytesIO()
    writer.write(output)
    return output.getvalue(), [combined_fields], manifest


def build_payload(packet: bytes, fields: list[list[dict]]) -> dict:
    return {
        "test_mode": True,
        "draft": False,
        "apply_signing_order": False,
        "name": "QA ONLY - corrected HomeOfferFlow signer geometry",
        "subject": "TEST ONLY: HomeOfferFlow signature placement review",
        "message": (
            "Nonbinding placement test only. Please complete every highlighted "
            "signature, date, and initials field so the final provider PDF can "
            "be visually checked. Both QA signers may complete their fields independently."
        ),
        "files": [{
            "name": "QA_ONLY_HomeOfferFlow_signer_geometry.pdf",
            "file_base64": base64.b64encode(packet).decode("ascii"),
        }],
        "recipients": QA_RECIPIENTS,
        "fields": fields,
        "reminders": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    parser.add_argument(
        "--api-key-stdin",
        action="store_true",
        help="Read one API-key line from stdin without echoing or saving it.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = args.output_dir / "receipt.json"
    if receipt.exists():
        raise SystemExit("Receipt already exists; inspect the saved document instead of creating another.")

    packet, fields, manifest = build_packet(args.source_dir)
    packet_path = args.output_dir / "unsigned-compact-geometry-qa.pdf"
    packet_path.write_bytes(packet)
    (args.output_dir / "manifest.json").write_text(
        json.dumps({"forms": manifest, "total_fields": len(fields[0])}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Prepared {packet_path} with {len(manifest)} forms and {len(fields[0])} fields.")

    if not args.send:
        print("Nothing sent. Use --send only after reviewing the unsigned packet.")
        return 0

    key = (
        sys.stdin.readline().strip()
        if args.api_key_stdin
        else getpass.getpass("Existing SignWell API key (hidden): ").strip()
    )
    if not key:
        raise SystemExit("No key supplied; nothing sent.")
    response = httpx.post(
        "https://www.signwell.com/api/v1/documents/",
        headers={"X-Api-Key": key},
        json=build_payload(packet, fields),
        timeout=60,
    )
    if response.status_code != 201:
        print(f"SignWell response: {response.status_code}")
        raise SystemExit("Creation was not confirmed. Inspect SignWell before any retry.")
    provider = response.json()
    saved = {key: provider.get(key) for key in ("id", "name", "status", "test_mode", "created_at")}
    saved["recipients"] = [
        {key: recipient.get(key) for key in ("id", "name", "email", "status")}
        for recipient in provider.get("recipients", [])
    ]
    receipt.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(saved, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build one nonbinding provider test for every remaining release form scope.

The packet combines a maximum-coverage purchase offer with the standalone
forms that were not part of the first compact SignWell geometry test.  Every
production field keeps its type, page-relative rectangle, required state, and
party position.  For QA only, production recipients are remapped to the two
owner-approved test inboxes and API IDs are namespaced by packet component.

Nothing is sent unless ``--send`` is provided.  A successful provider response
is written to ``receipt.json`` before another request can be created from the
same output directory.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import importlib
import json
import sys
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import production_adapter as adapter
from scripts.check_golden_packet_rendering import _offer_scenarios
from tests.test_controlled_launch import configure_local_forms, minimal_offer
from tests.test_txr_1506_renderer import sample_data as txr1506_sample
from tests.test_txr_1508_renderer import sample_data as txr1508_sample


QA_RECIPIENTS = [
    {"id": "qa_a", "name": "QA Signer A", "email": "andrewchri@gmail.com"},
    {"id": "qa_b", "name": "QA Signer B", "email": "brewbqinfo@gmail.com"},
]
FORM_ORDER = ("1506", "1508", "1948", "1953", "1954")


def qa_recipient(original_id: str) -> str:
    """Preserve first/second signer separation using two approved QA inboxes."""
    return "qa_b" if str(original_id) in {"2", "4"} else "qa_a"


def purchase_offer(source_dir: Path) -> dict:
    """Return one valid offer exercising the released purchase addenda matrix."""
    overrides = dict(_offer_scenarios()["all_supported_addenda"])
    overrides.update({
        "buyer1": "QA Buyer One",
        "buyerEmail": "buyer1@example.test",
        "buyer2": "QA Buyer Two",
        "buyer2Email": "buyer2@example.test",
        "seller": "QA Seller One and QA Seller Two",
        "seller1Name": "QA Seller One",
        "seller1Email": "seller1@example.test",
        "seller2Name": "QA Seller Two",
        "seller2Email": "seller2@example.test",
        "hydrostaticTesting": "yes",
        "hydrostaticRiskAllocation": "buyer_capped",
        "hydrostaticBuyerLiabilityLimit": "2500.25",
        "yearBuilt": "1972",
        "leadBuiltBefore1978": "yes",
        "leadDisclosureStatus": "received",
        "uploadedDisclosureDocs": [{
            "name": "QA_ONLY_lead_disclosure.pdf",
            "type": "lead_based_paint",
            "base64": base64.b64encode(
                (source_dir / "lead_based_paint_56-0.pdf").read_bytes()
            ).decode("ascii"),
        }],
    })
    return minimal_offer(**overrides)


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
    if code == "1506":
        return ({**txr1506_sample(), "_for_signing": True}, brokerage, associate)
    if code == "1508":
        return ({**txr1508_sample(), "_for_signing": True}, brokerage, associate)
    parties = {
        "property_address": "100 Review Lane, Austin, TX 78701",
        "buyer_names": ["QA Buyer One", "QA Buyer Two"],
        "seller_names": ["QA Seller One", "QA Seller Two"],
        "_for_signing": True,
    }
    if code == "1948":
        return ({
            **parties,
            "appraisal_choice": "additional_right",
            "additional_days": "10",
            "additional_value": "350000",
        }, None, None)
    if code == "1953":
        return ({
            **parties,
            "lease_status": "assignment",
            "delivery_choice": "not_received",
            "delivery_days": "3",
            "explanation": "No tenant disputes reported for this nonbinding QA review.",
        }, None, None)
    if code == "1954":
        return ({
            **parties,
            "leased_fixture_types": ["solar_panels", "other"],
            "leased_fixtures_other": "Pool equipment",
            "assumed_fixture_leases": ["solar_panels"],
            "buyer_first_cost": "2500",
            "removal_choice": "will_not",
            "delivery_choice": "oral_notice",
            "oral_fixture_lease_notice": "Solar lease with monthly payment and remaining term.",
        }, None, None)
    raise ValueError(f"Unsupported remaining QA form: TXR-{code}")


def render_form(source_bytes: bytes, code: str, data: dict,
                brokerage: dict | None, associate: dict | None) -> bytes:
    module = importlib.import_module(f"lib.txr_{code}")
    renderer = getattr(module, f"render_txr_{code}")
    if code == "1506":
        return renderer(source_bytes, data, brokerage or {})
    if code == "1508":
        return renderer(source_bytes, data, brokerage or {}, associate or {})
    return renderer(source_bytes, data)


def form_fields(code: str, data: dict, page_count: int) -> list[dict]:
    module = importlib.import_module(f"lib.txr_{code}")
    builder = getattr(module, f"build_signwell_fields_txr{code}")
    if code in {"1506", "1508"}:
        return builder(data, client_count=2, page_count=page_count)[0]
    return builder(data)[0]


def append_component(writer: PdfWriter, combined_fields: list[dict], manifest: list[dict],
                     *, code: str, packet: bytes, local_fields: list[dict]) -> None:
    reader = PdfReader(BytesIO(packet))
    page_offset = len(writer.pages)
    for page in reader.pages:
        writer.add_page(page)
    shifted = []
    namespace = code.lower().replace("-", "_")
    for field in local_fields:
        shifted_field = dict(field)
        shifted_field["api_id"] = f"qa_{namespace}_{field['api_id']}"
        shifted_field["page"] = int(field["page"]) + page_offset
        shifted_field["recipient_id"] = qa_recipient(str(field["recipient_id"]))
        shifted.append(shifted_field)
    combined_fields.extend(shifted)
    manifest.append({
        "form_code": code,
        "start_page": page_offset + 1,
        "end_page": page_offset + len(reader.pages),
        "page_count": len(reader.pages),
        "field_count": len(shifted),
        "original_recipient_ids": sorted({str(field["recipient_id"]) for field in local_fields}),
    })


def build_packet(source_dir: Path) -> tuple[bytes, list[list[dict]], list[dict]]:
    configure_local_forms()
    writer = PdfWriter()
    combined_fields: list[dict] = []
    manifest: list[dict] = []

    offer = purchase_offer(source_dir)
    with redirect_stdout(StringIO()):
        purchase_packet = adapter.fill_and_merge_20_19(offer)
        purchase_fields = adapter.build_signwell_fields_20_19(offer, purchase_packet)[0]
    append_component(
        writer, combined_fields, manifest,
        code="PURCHASE-MAX-COVERAGE",
        packet=purchase_packet,
        local_fields=purchase_fields,
    )

    for code in FORM_ORDER:
        source_path = source_dir / f"TXR{code}.pdf"
        if not source_path.is_file():
            raise FileNotFoundError(f"Missing private QA source: {source_path}")
        data, brokerage, associate = sample_for(code)
        rendered = render_form(source_path.read_bytes(), code, data, brokerage, associate)
        local_fields = form_fields(code, data, len(PdfReader(BytesIO(rendered)).pages))
        append_component(
            writer, combined_fields, manifest,
            code=f"TXR-{code}",
            packet=rendered,
            local_fields=local_fields,
        )

    api_ids = [field["api_id"] for field in combined_fields]
    if len(set(api_ids)) != len(api_ids):
        raise ValueError("Remaining release QA packet contains duplicate SignWell field IDs.")
    if {field["recipient_id"] for field in combined_fields} != {"qa_a", "qa_b"}:
        raise ValueError("Remaining release QA packet must exercise both approved QA recipients.")

    writer.add_metadata({
        "/Title": "QA ONLY - HomeOfferFlow remaining release geometry",
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
        "name": "QA ONLY - remaining HomeOfferFlow release geometry",
        "subject": "TEST ONLY: final HomeOfferFlow release placement review",
        "message": (
            "Nonbinding placement test only. Please complete every highlighted "
            "signature, date, and initials field so the final provider PDF can "
            "be visually checked. Both QA signers may complete their fields independently."
        ),
        "files": [{
            "name": "QA_ONLY_remaining_HomeOfferFlow_release_geometry.pdf",
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
    packet_path = args.output_dir / "HomeOfferFlow_remaining_release_geometry_QA_unsigned.pdf"
    packet_path.write_bytes(packet)
    (args.output_dir / "manifest.json").write_text(
        json.dumps({
            "forms": manifest,
            "total_pages": len(PdfReader(BytesIO(packet)).pages),
            "total_fields": len(fields[0]),
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Prepared {packet_path} with {len(manifest)} components and {len(fields[0])} fields.")

    if not args.send:
        print("Nothing sent. Use --send only after reviewing every unsigned page.")
        return 0

    key = (
        sys.stdin.readline().strip()
        if args.api_key_stdin
        else getpass.getpass("Existing SignWell API key (hidden): ").strip()
    )
    if not key:
        raise SystemExit("No key supplied; nothing sent.")
    import httpx
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

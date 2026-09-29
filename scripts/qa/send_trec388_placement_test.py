"""Prepare or send one nonbinding TREC 38-8 Buyer-placement test through SignWell."""

import argparse
import base64
import json
import os
from pathlib import Path

import httpx

from lib.trec_38_8 import build_signwell_fields_trec388, render_trec_38_8


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--buyer-one-email", required=True)
    parser.add_argument("--buyer-two-email", required=True)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = args.output_dir / "receipt.json"
    if receipt.exists():
        raise SystemExit("Receipt already exists; inspect it before creating another test.")

    data = {
        "property_address": "QA ONLY - 1438 Whitaker Road, Van Alstyne, TX",
        "buyer_names": ["QA Buyer One", "QA Buyer Two"],
        "seller_names": ["QA Seller One", "QA Seller Two"],
        "termination_reasons": ["option_period", "other"],
        "other_termination_basis": "QA ONLY - Paragraph 22 and attached addendum.",
    }
    packet = render_trec_38_8(args.source.read_bytes(), data)
    (args.output_dir / "unsigned.pdf").write_bytes(packet)
    fields = build_signwell_fields_trec388(data)
    payload = {
        "test_mode": True,
        "draft": False,
        "apply_signing_order": False,
        "name": "QA ONLY - TREC 38-8 Buyer signature placement",
        "subject": "TEST ONLY: TREC 38-8 signature placement",
        "message": (
            "Nonbinding placement test only. Please complete the highlighted Buyer signature "
            "and date fields so the final PDF can be visually checked. Both recipients may sign independently."
        ),
        "files": [{
            "name": "QA_ONLY_TREC_38-8_Buyer_Termination_Notice.pdf",
            "file_base64": base64.b64encode(packet).decode("ascii"),
        }],
        "recipients": [
            {"id": "1", "name": "QA Buyer One", "email": args.buyer_one_email},
            {"id": "2", "name": "QA Buyer Two", "email": args.buyer_two_email},
        ],
        "fields": fields,
        "reminders": False,
    }
    if not args.send:
        print("Unsigned TREC 38-8 placement test prepared; nothing sent.")
        return
    api_key = os.environ.get("SIGNWELL_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("SIGNWELL_API_KEY is not available; nothing sent.")
    response = httpx.post(
        "https://www.signwell.com/api/v1/documents/",
        headers={"X-Api-Key": api_key},
        json=payload,
        timeout=60,
    )
    if response.status_code != 201:
        print("SignWell response:", response.status_code)
        raise SystemExit("Test creation was not confirmed. Inspect SignWell before retrying.")
    provider = response.json()
    saved = {key: provider.get(key) for key in ("id", "name", "status", "test_mode", "created_at")}
    saved["recipient_statuses"] = [
        {"id": recipient.get("id"), "status": recipient.get("status")}
        for recipient in provider.get("recipients", [])
    ]
    receipt.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(saved, indent=2))


if __name__ == "__main__":
    main()

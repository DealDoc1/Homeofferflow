"""Send one nonbinding TREC 62-0 Seller-placement test through SignWell."""

import argparse
import base64
import json
import os
from pathlib import Path

import httpx

from lib.trec_62_0 import build_signwell_fields_trec620, render_trec_62_0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seller-one-email", required=True)
    parser.add_argument("--seller-two-email", required=True)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = args.output_dir / "receipt.json"
    if receipt.exists():
        raise SystemExit("Receipt already exists; inspect it before creating another test.")

    data = {
        "property_address": "QA ONLY - 1438 Whitaker Road, Van Alstyne, TX",
        "buyer_names": ["QA Backup Buyer"],
        "seller_names": ["QA Seller One", "QA Seller Two"],
        "delivery_date": "09/22/2026",
    }
    packet = render_trec_62_0(args.source.read_bytes(), data)
    (args.output_dir / "unsigned.pdf").write_bytes(packet)
    fields = build_signwell_fields_trec620(data)
    payload = {
        "test_mode": True,
        "draft": False,
        "apply_signing_order": False,
        "name": "QA ONLY - TREC 62-0 Seller signature placement",
        "subject": "TEST ONLY: TREC 62-0 signature placement",
        "message": (
            "Nonbinding placement test only. Please complete the highlighted Seller signature "
            "and date fields so the final PDF can be visually checked. Both recipients may sign independently."
        ),
        "files": [{
            "name": "QA_ONLY_TREC_62-0_Seller_Notice.pdf",
            "file_base64": base64.b64encode(packet).decode("ascii"),
        }],
        "recipients": [
            {"id": "1", "name": "QA Seller One", "email": args.seller_one_email},
            {"id": "2", "name": "QA Seller Two", "email": args.seller_two_email},
        ],
        "fields": fields,
        "reminders": False,
    }
    if not args.send:
        print("Unsigned TREC 62-0 placement test prepared; nothing sent.")
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

"""Send one reviewed, nonbinding placement check; never a customer packet.

Only the established two QA inboxes may receive it. A receipt is reserved
before the provider call, and an ambiguous response is never retried here.
Credentials stay in the protected runner and are never logged or exported.
"""
import argparse
import base64
from contextlib import redirect_stdout
import hashlib
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import re
import subprocess

import httpx
import pdfplumber
from pypdf import PdfReader, PdfWriter
from reportlab import rl_config

from lib import production_adapter as adapter
from scripts.check_production_schema_readiness import parse_env_file
from scripts.qa.build_compact_signwell_geometry_test import QA_RECIPIENTS, qa_recipient
from tests.test_controlled_launch import configure_local_forms, minimal_offer


PRODUCT_FILES = (
    "lib", "api/fill-pdf.py", "api/fill_pdf_20_19_staging.py", "20-19_0.pdf",
    "buyer_temporary_residential_lease_16-7.pdf", "seller_temporary_residential_lease_15-7.pdf",
)
EXISTING_QA_DOCUMENT = "0093c1e0-8491-4a14-b659-dda35a8fbed4"


def build_packet():
    configure_local_forms()
    original_invariant = rl_config.invariant
    rl_config.invariant = 1
    try:
        return _build_packet()
    finally:
        rl_config.invariant = original_invariant


def _build_packet():
    common = dict(
        buyer1="QA Buyer One", seller="QA Seller One", address="100 QA Example Lane",
        city="Example City", county="Example County", zip="75001", userType="agent",
        hasBuyerAgent="yes", agentName="QA Associate", agentBrokerage="QA Review Brokerage",
        agentBrokerLicense="0000000", agentLicense="0000000", teamName="QA Team",
        agentEmail="qa-agent@example.test", agentPhone="9725550100",
        agentAddress="200 QA Office Lane, Example City, TX 75001",
        buyerMailAddr="300 QA Mailing Lane, Example City, TX 75001",
        buyerPhone="2145550100", buyerEmail="qa-buyer@example.test", closingDate="2026-12-01",
    )
    cases = {
        "single_buyer": {},
        "four_party_execution": dict(
            buyer2="QA Buyer Two", buyer2Email="qa-buyer-two@example.test",
            seller="QA Seller One and QA Seller Two", seller1Name="QA Seller One",
            seller1Email="qa-seller-one@example.test", seller2Name="QA Seller Two",
            seller2Email="qa-seller-two@example.test", possession="sellerTemporaryLease",
            sellerTemporaryLease="yes", sellerTemporaryLeaseTerminationDate="2026-12-10",
            sellerTemporaryLeaseRentPerDay="125", sellerTemporaryLeaseDeposit="1000",
            sellerTemporaryLeaseHoldoverPerDay="300",
        ),
        "unicode_continuation": dict(
            buyer2="QA Buyer Two", buyer2Email="qa-buyer-two@example.test",
            agentName="Élodie Hernández " * 65, agentEmail="long" * 70 + "@example.test",
        ),
    }
    writer, fields, manifest = PdfWriter(), [], []
    for case, overrides in cases.items():
        offer = minimal_offer(**{**common, **overrides})
        with redirect_stdout(StringIO()):
            packet = adapter.fill_and_merge_20_19(offer)
            original_fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        reader = PdfReader(BytesIO(packet))
        # Main footer variants, notices, execution, contacts, and any contact
        # overflow only. Unchanged temporary-lease pages are not added.
        selected = [1, 8, 10, 11]
        selected += sorted({f["page"] for f in original_fields
                            if f["api_id"].startswith("contacts_continuation_")})
        remap = {}
        content_hashes = []
        for source_page in selected:
            remap[source_page] = len(writer.pages) + 1
            page = reader.pages[source_page - 1]
            # Never add another merged overlay: source graphics state can
            # make that distort the page. Test mode supplies its own marking.
            content_hashes.append(hashlib.sha256(page.get_contents().get_data()).hexdigest())
            writer.add_page(page)
        shifted = []
        for field in original_fields:
            if field["page"] in remap:
                shifted.append({**field, "page": remap[field["page"]],
                                "recipient_id": qa_recipient(field["recipient_id"]),
                                "api_id": case + "_" + field["api_id"]})
        fields.extend(shifted)
        manifest.append({"case": case, "source_pages": selected,
                         "output_pages": list(remap.values()), "field_count": len(shifted),
                         "content_sha256": content_hashes})
    writer.add_metadata({"/Title": "QA ONLY - purchase contract placement",
                         "/Subject": "Nonbinding synthetic provider-rendering check"})
    output = BytesIO()
    writer.write(output)
    return output.getvalue(), [fields], manifest


def build_payload(packet, fields, release_sha):
    if not re.fullmatch(r"[0-9a-f]{40}", release_sha):
        raise ValueError("Choose the exact deployed release revision.")
    return {
        "test_mode": True, "draft": False, "apply_signing_order": False,
        "with_signature_page": False, "reminders": False,
        "name": "QA ONLY - purchase placement - " + release_sha[:12],
        "subject": "TEST ONLY: corrected HomeOfferFlow purchase-contract placement",
        "message": "Nonbinding placement check only, not a client agreement. Both test recipients may sign independently. Please complete the highlighted fields so the final PDF can be reviewed.",
        "recipients": [dict(r) for r in QA_RECIPIENTS],
        "files": [{"name": "QA_ONLY_purchase_placement.pdf", "file_base64": base64.b64encode(packet).decode("ascii")}],
        "fields": fields, "metadata": {"qa_kind": "purchase-placement", "release_sha": release_sha},
    }


def layout_fingerprint(packet, fields, cases):
    """Pin every visible glyph position and signing box, not serialization IDs."""
    pages = []
    with pdfplumber.open(BytesIO(packet)) as document:
        for page in document.pages:
            pages.append({
                "size": [page.width, page.height],
                "glyphs": [[c["text"], c["fontname"].split("+")[-1],
                            *[round(c[key], 3) for key in ("x0", "x1", "top", "bottom", "size")]]
                           for c in page.chars],
            })
    value = {"pages": pages, "fields": fields, "cases": cases}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def existing_key(env_file, *, trim=True):
    key = os.environ.get("SIGNWELL_API_KEY", "")
    if not key and env_file and env_file.is_file():
        for line in env_file.read_text().splitlines():
            name, separator, value = line.strip().partition("=")
            if separator and name.strip() == "SIGNWELL_API_KEY":
                value = value.strip()
                # Vercel's double-quoted serialization escapes control
                # characters. Decode that serialization, not the actual key.
                if value.startswith('"'):
                    key = json.loads(value)
                elif value.startswith("'") and value.endswith("'"):
                    key = value[1:-1]
                else:
                    key = value
                if not isinstance(key, str):
                    raise ValueError("The configured credential is not a string; nothing sent.")
                break
    if not key or not key.strip():
        raise ValueError("The existing SignWell credential is unavailable to this runner; nothing sent.")
    if key.strip().upper() in {"[REDACTED]", "[ENCRYPTED]", "[SENSITIVE]", "UNDEFINED", "NULL"} or re.fullmatch(r"\*+", key.strip()):
        raise ValueError("A protected-value placeholder is not a SignWell credential; nothing sent.")
    return key.strip() if trim else key


def diagnose_credential(env_file, *, get=httpx.get):
    """Read one existing QA document; never create, sign, or expose a key."""
    legacy = os.environ.get("SIGNWELL_API_KEY", "").strip()
    if not legacy and env_file and env_file.is_file():
        legacy = parse_env_file(env_file).get("SIGNWELL_API_KEY", "").strip()
    normalized = existing_key(env_file)
    runtime_value = existing_key(env_file, trim=False)
    result = {"read_only_qa_lookup": True, "decoding_changed": legacy != normalized,
              "runtime_trailing_whitespace": runtime_value != runtime_value.rstrip(),
              "runtime_transport_controls": "\r" in runtime_value or "\n" in runtime_value}
    seen = {}
    for label, key in (("legacy", legacy), ("normalized", normalized)):
        detail = {"length": len(key), "literal_control_escape": "\\n" in key or "\\r" in key}
        if key not in seen:
            try:
                response = get("https://www.signwell.com/api/v1/documents/" + EXISTING_QA_DOCUMENT,
                               headers={"X-Api-Key": key}, timeout=30)
                status_detail = {"http_status": response.status_code}
                if response.status_code == 200:
                    document = response.json()
                    status_detail["confirmed_qa_document"] = (
                        document.get("id") == EXISTING_QA_DOCUMENT
                        and str(document.get("name") or "").startswith("QA ONLY")
                    )
                seen[key] = status_detail
            except Exception as error:
                seen[key] = {"error_type": type(error).__name__}
        result[label] = {**detail, **seen[key]}
    return result


def send_once(packet, fields, release_sha, key, receipt, *, post=httpx.post):
    if receipt.exists():
        raise ValueError("A previous attempt is recorded; inspect it instead of sending another test.")
    payload = build_payload(packet, fields, release_sha)
    with receipt.open("x") as stream:
        stream.write(json.dumps({"status": "started", "release_sha": release_sha}) + "\n")
    try:
        response = post("https://www.signwell.com/api/v1/documents/",
                        headers={"X-Api-Key": key}, json=payload, timeout=60)
        if response.status_code != 201:
            result = {"status": "unconfirmed", "http_status": response.status_code}
        else:
            provider = response.json()
            if provider.get("test_mode") is not True or not provider.get("id"):
                result = {"status": "unconfirmed", "reason": "Provider test-mode confirmation missing"}
            else:
                result = {"status": "created", "document_id": provider["id"],
                          "provider_status": provider.get("status"), "test_mode": True}
    except Exception as error:
        # Exception messages or full provider bodies can contain credentials
        # and signing URLs. Save only the class, never the text or response.
        result = {"status": "unconfirmed", "error_type": type(error).__name__}
    result["release_sha"] = release_sha
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--release-sha", required=True)
    parser.add_argument("--expected-layout-sha256")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--check-key", action="store_true")
    parser.add_argument("--diagnose-credential", action="store_true")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.release_sha):
        raise ValueError("Choose the exact deployed release revision.")
    if args.send and not args.expected_layout_sha256:
        raise ValueError("A reviewed layout fingerprint is required; nothing sent.")
    if args.diagnose_credential:
        if args.send:
            raise ValueError("Credential diagnostics cannot send a document.")
        result = diagnose_credential(args.env_file)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "credential-check.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        return
    if args.check_key:
        existing_key(args.env_file)
        print("Existing SignWell credential is available; no value displayed.")
        return
    subprocess.run(["git", "diff", "--exit-code", args.release_sha, "--", *PRODUCT_FILES],
                   check=True, stdout=subprocess.DEVNULL)
    packet, fields, cases = build_packet()
    digest = hashlib.sha256(packet).hexdigest()
    layout_digest = layout_fingerprint(packet, fields, cases)
    if args.expected_layout_sha256 and layout_digest != args.expected_layout_sha256:
        raise ValueError("This packet differs from the visually reviewed specimen; nothing sent.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "unsigned.pdf").write_bytes(packet)
    (args.output_dir / "manifest.json").write_text(json.dumps({
        "release_sha": args.release_sha, "packet_sha256": digest, "layout_sha256": layout_digest, "cases": cases,
        "pages": len(PdfReader(BytesIO(packet)).pages), "fields": fields,
    }, indent=2) + "\n")
    print(f"Prepared {len(cases)} cases, {len(fields[0])} fields; layout SHA-256 {layout_digest}.")
    if args.send:
        result = send_once(packet, fields, args.release_sha, existing_key(args.env_file),
                           args.output_dir / "receipt.json")
        print(json.dumps(result))
        if result["status"] != "created":
            raise SystemExit("Creation unconfirmed. Inspect the saved receipt and SignWell; do not retry.")
    else:
        print("Nothing sent.")


if __name__ == "__main__":
    main()

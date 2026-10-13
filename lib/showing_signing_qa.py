"""Fixed nonbinding remaining TXR-1508 provider specimen; never client input."""
import base64
import hashlib
from io import BytesIO
import json
import re

from pypdf import PdfReader, PdfWriter
from lib.txr_1508 import render_txr_1508, build_signwell_fields_txr1508
from lib.purchase_signing_qa import QA_RECIPIENTS, QA_OPERATOR_EMAILS

QA_REVISION = "txr-1508-2026-10-13-provider-clearance-v2"
QA_SCENARIO = "txr1508-provider-placement-remaining"
REVIEWED_SOURCE_COMMIT = "30cf21f132f80bb9563356e568f6d62df12844f6"
SOURCE_SHA256 = "b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40"
FIELDS_SHA256 = "fb9a303670525c6719bd88e6283c99530910bd40a3d0c1eae70cc82a114233d7"
DOCUMENT_PREFIX = "QA ONLY - TXR-1508 placement - "
QA_TITLE = "TXR-1508 remaining provider placement"
TEST_LABEL = "showing-form signing"
QA_DESCRIPTION = "Synthetic two-customer broker/associate acknowledgements and Unicode continuation; completed PDF visual review required."
RENDER_REVISION = "txr-1508-2026-10-13-provider-clearance-v3"


def cases():
    base = {"property_address": "100 QA Example Lane, Example City, TX 75001",
            "client_names": ["QA Customer One", "QA Customer Two"],
            "other_broker_agreement": ["no", "no"],
            "signer_plan": "broker_and_clients", "_for_signing": True}
    return (
        ("two_customer_broker", dict(base)),
        ("two_customer_associate_mixed", {**base, "signer_plan": "associate_and_clients",
                                           "other_broker_agreement": ["yes", "no"]}),
        ("unicode_continuation", {**base, "client_names": ["Élodie Hernández " * 12, "Zoë O'Connell " * 12]}),
    )


def build_packet(source_bytes):
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError("The showing-form source changed; review the test layout before sending.")
    if len(PdfReader(BytesIO(source_bytes)).pages) != 1:
        raise ValueError("The showing-form source must contain one page.")
    brokerage = {"legal_name": "QA Review Brokerage", "license_number": "0000000"}
    associate = {"name": "QA Associate", "license_number": "0000000"}
    writer, fields, manifest = PdfWriter(), [], []
    for name, data in cases():
        rendered = render_txr_1508(source_bytes, data, brokerage, associate)
        reader = PdfReader(BytesIO(rendered))
        original_fields = build_signwell_fields_txr1508(data, client_count=2, page_count=len(reader.pages))[0]
        offset = len(writer.pages)
        hashes = []
        for page in reader.pages:
            hashes.append(hashlib.sha256(page.get_contents().get_data()).hexdigest())
            writer.add_page(page)
        # Logical role separation remains in the production map. Only this
        # explicitly fictional test shares QA A between professional/customer 1.
        fields.extend({**f, "api_id": name + "_" + f["api_id"], "page": f["page"] + offset,
                       "recipient_id": "qa_b" if f["recipient_id"] == "2" else "qa_a"}
                      for f in original_fields)
        manifest.append({"case": name, "source_pages": list(range(1, len(reader.pages) + 1)),
                         "output_pages": list(range(offset + 1, len(writer.pages) + 1)),
                         "field_count": len(original_fields), "content_sha256": hashes,
                         "signer_plan": data["signer_plan"],
                         "other_broker_agreement": data["other_broker_agreement"]})
    if len(writer.pages) != 4 or len(fields) != 21:
        raise ValueError("The showing-form test shape changed; review it before sending.")
    writer.add_metadata({"/Title": "QA ONLY - TXR-1508 remaining placement",
                         "/Subject": "Nonbinding synthetic two-customer acknowledgement review"})
    output = BytesIO()
    writer.write(output)
    return output.getvalue(), [fields], manifest


def build_payload(packet, fields, release_sha):
    if not re.fullmatch(r"[0-9a-f]{40}", release_sha):
        raise ValueError("Choose the exact reviewed release revision.")
    if not FIELDS_SHA256 or hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest() != FIELDS_SHA256:
        raise ValueError("The showing-form test placement has not matched its reviewed map.")
    return {"test_mode": True, "draft": False, "apply_signing_order": False,
            "with_signature_page": False, "reminders": False,
            "name": DOCUMENT_PREFIX + release_sha[:12],
            "subject": "TEST ONLY: two-customer showing-form placement",
            "message": "Nonbinding TXR-1508 placement check only, not a client agreement. Both test recipients may complete their fictional initials and dates independently.",
            "recipients": [dict(r) for r in QA_RECIPIENTS],
            "files": [{"name": "QA_ONLY_TXR1508_placement.pdf", "file_base64": base64.b64encode(packet).decode("ascii")}],
            "fields": fields, "metadata": {"qa_kind": "txr1508-placement", "release_sha": release_sha,
                                            "qa_revision": QA_REVISION}}

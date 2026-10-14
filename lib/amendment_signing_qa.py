"""Fixed fictional TREC-39-11 matrix for the existing protected QA sender."""
import base64
import hashlib
from io import BytesIO
import json
import re

from pypdf import PdfReader, PdfWriter
from lib import trec_39_11
from lib.purchase_signing_qa import QA_OPERATOR_EMAILS, QA_RECIPIENTS

QA_REVISION = "trec-39-11-placement-2026-10-14-static-source-v2"
QA_SCENARIO = "trec3911-provider-placement"
REVIEWED_SOURCE_COMMIT = "ee90d4d627b6ffd85bff673a4c52ab2a501ee6c8"
SOURCE_SHA256 = "d12909bcbd014080948eb6f9771231ba1b1d98c64eaf07e87ab0faa1118b8d36"
RENDER_REVISION = "trec-39-11-2026-10-11-static-source-v2"
FIELDS_SHA256 = "8b7e2fc87889ab1816e534be095edb0897d3ffc130d762025e70781f525ca6ee"
DOCUMENT_PREFIX = "QA ONLY - TREC-39-11 placement - "
QA_TITLE = "Amendment provider placement"
QA_DESCRIPTION = "All four Buyer/Seller counts, both option choices and Unicode continuations; completed PDF visual review required."
TEST_LABEL = "amendment signing"


def cases():
    base = {
        "property_address": "QA ONLY - 100 Example Lane, Example City, TX 75001",
        "buyer_names": ["QA Buyer One", "QA Buyer Two"],
        "seller_names": ["QA Seller One", "QA Seller Two"],
        "changes": ["sales_price", "repairs", "closing_date", "seller_expense",
                    "settlement_expenses", "lender_repairs", "option_extension",
                    "buyer_approval_date", "other"],
        "sales_price": {"cash": "125000", "financing": "375000", "total": "500000"},
        "repairs_text": "QA ONLY: repaint the detached storage building.",
        "closing_date": "12/01/2026", "seller_expense": "7500",
        "settlement_expenses": {"seller": {"type": "amount", "value": "5500"},
                                "buyer": {"type": "percent", "value": "1.25"}},
        "lender_repairs": {"seller": "2000", "buyer": "0"},
        "option_extension": {"fee": "250", "date": "11/01/2026", "credited": True},
        "buyer_approval_date": "11/15/2026",
        "other_modifications": "QA ONLY: the parties confirm the revised delivery date.",
    }
    return (
        ("two_buyers_two_sellers", dict(base)),
        ("one_buyer_one_seller_waiver", {**base, "buyer_names": ["QA Buyer One"],
          "seller_names": ["QA Seller One"], "changes": ["option_waiver"]}),
        ("one_buyer_two_sellers", {**base, "buyer_names": ["QA Buyer One"],
          "changes": ["closing_date"]}),
        ("two_buyers_one_seller", {**base, "seller_names": ["QA Seller One"],
          "changes": ["option_extension"],
          "option_extension": {"fee": "0", "date": "11/01/2026", "credited": False}}),
        ("unicode_continuation", {**base, "changes": ["repairs", "other"],
          "repairs_text": "QA ONLY - Élodie Hernández and Zoë O’Connell review the café finish. " * 35,
          "other_modifications": "QA ONLY - Confirm the façade color with José Muñoz; preserve these exact words. " * 35}),
    )


def build_packet(source_bytes):
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError("The amendment source changed; review it before sending.")
    if trec_39_11.RENDER_REVISION != RENDER_REVISION:
        raise ValueError("The amendment renderer changed; review it before sending.")
    writer, fields, manifest = PdfWriter(), [], []
    for name, data in cases():
        reader = PdfReader(BytesIO(trec_39_11.render_trec_39_11(source_bytes, data)))
        original = trec_39_11.build_signwell_fields_trec3911(data)[0]
        offset, hashes = len(writer.pages), []
        for page in reader.pages:
            hashes.append(hashlib.sha256(page.get_contents().get_data()).hexdigest())
            writer.add_page(page)
        # Only the fictional composite shares QA inboxes across party roles.
        # Keep every production field type, rectangle, required flag and page.
        fields.extend({**f, "api_id": name + "_" + f["api_id"],
                       "page": f["page"] + offset,
                       "recipient_id": "qa_b" if f["recipient_id"] in {"2", "4"} else "qa_a"}
                      for f in original)
        manifest.append({"case": name, "source_pages": list(range(1, len(reader.pages) + 1)),
                         "output_pages": list(range(offset + 1, len(writer.pages) + 1)),
                         "field_count": len(original), "content_sha256": hashes,
                         "buyer_count": len(data["buyer_names"]), "seller_count": len(data["seller_names"]),
                         "changes": data["changes"]})
    if len(writer.pages) != 7 or len(fields) != 24:
        raise ValueError("The amendment test shape changed; review it before sending.")
    if len({f["api_id"] for f in fields}) != len(fields):
        raise ValueError("Amendment test field IDs must be unique.")
    writer.add_metadata({"/Title": "QA ONLY - TREC-39-11 signing matrix",
                         "/Subject": "Nonbinding fictional placement review"})
    output = BytesIO(); writer.write(output)
    return output.getvalue(), [fields], manifest


def build_payload(packet, fields, release_sha):
    if release_sha != REVIEWED_SOURCE_COMMIT or not re.fullmatch(r"[0-9a-f]{40}", release_sha):
        raise ValueError("Choose the exact reviewed amendment revision.")
    if not FIELDS_SHA256 or hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest() != FIELDS_SHA256:
        raise ValueError("The amendment test placement differs from its reviewed map.")
    return {
        "test_mode": True, "draft": False, "apply_signing_order": False,
        "with_signature_page": False, "reminders": False,
        "name": DOCUMENT_PREFIX + release_sha[:12],
        "subject": "TEST ONLY: HomeOfferFlow amendment signing placement",
        "message": "One nonbinding fictional TREC-39-11 test covers all Buyer/Seller counts and long answers. This is not a client agreement. Both test recipients may sign independently.",
        "recipients": [dict(r) for r in QA_RECIPIENTS],
        "files": [{"name": "QA_ONLY_TREC3911_matrix.pdf", "file_base64": base64.b64encode(packet).decode("ascii")}],
        "fields": fields, "metadata": {"qa_kind": "trec3911-placement", "release_sha": release_sha,
                                       "qa_revision": QA_REVISION},
    }

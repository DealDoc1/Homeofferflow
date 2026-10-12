"""Fixed, fictional purchase specimen for operator-only provider QA.

No customer input, environment changes, or test-suite imports. The same
production renderer/map is used by the protected operator and local helper.
"""
import base64
from contextlib import redirect_stdout
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import re

from pypdf import PdfReader, PdfWriter
from lib import production_adapter as adapter


QA_REVISION = "purchase-placement-2026-10-11-contacts-execution-v1"
QA_SCENARIO = "purchase-provider-placement"
# Reviewed source/map tree; later QA-only releases do not change this layout.
REVIEWED_SOURCE_COMMIT = "ee90d4d627b6ffd85bff673a4c52ab2a501ee6c8"
QA_RECIPIENTS = (
    {"id": "qa_a", "name": "QA Signer A", "email": "andrewchri@gmail.com"},
    {"id": "qa_b", "name": "QA Signer B", "email": "brewbqinfo@gmail.com"},
)
QA_OPERATOR_EMAILS = {"andrewchri@gmail.com", "andrew@ondemanddfw.com"}


def qa_recipient(original_id):
    return "qa_b" if str(original_id) in {"2", "4"} else "qa_a"


def qa_offer(**overrides):
    offer = {
        "buyer1": "QA Buyer One", "buyerEmail": "qa-buyer@example.test",
        "seller": "QA Seller One", "address": "100 QA Example Lane",
        "city": "Example City", "county": "Example County", "zip": "75001",
        "lotNumber": "1", "blockNumber": "A", "price": "500000",
        "financing": "cash", "loanAmount": "0", "earnest": "5000",
        "optionFee": "250", "optionDays": "7", "escrowAgent": "Chicago Title DFW",
        "escrowAddress": "2770 Main Street, Frisco, TX 75033", "titleCompany": "Chicago Title DFW",
        "titlePayer": "buyer", "titleAmendment": "buyer", "survey": "buyerNew",
        "surveyDays": "7", "objectionDays": "5", "hoa": "no",
        "sellerDisclosure": "received", "sellerWaterDisclosure": "received", "asIs": "yes",
        "closingDate": "2026-12-01", "possession": "funding", "leases": "no",
        "saleContingency": "no", "backupOffer": "no", "appraisalAddendum": "none",
        "nonRealtyItems": "no", "leadBasedPaint": "no", "yearBuilt": "2005",
        "userType": "agent", "hasBuyerAgent": "yes", "agentName": "QA Associate",
        "agentBrokerage": "QA Review Brokerage", "agentBrokerLicense": "0000000",
        "agentLicense": "0000000", "teamName": "QA Team", "agentEmail": "qa-agent@example.test",
        "agentPhone": "9725550100", "agentAddress": "200 QA Office Lane, Example City, TX 75001",
        "buyerMailAddr": "300 QA Mailing Lane, Example City, TX 75001", "buyerPhone": "2145550100",
    }
    offer.update(overrides)
    return offer


def build_packet():
    from lib.trec_20_19_contacts import RENDER_REVISION
    if (RENDER_REVISION != "trec-20-19-2026-10-11-contacts-execution-v1"
            or hashlib.sha256(Path(adapter.verified.MAIN_PDF).read_bytes()).hexdigest()
            != "be3fa154f00476a674c73ba20f6c589111a905bc1e0894e0d5786b714f16f8d4"):
        raise ValueError("The purchase signing source changed; review it before sending.")
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
        offer = qa_offer(**overrides)
        with redirect_stdout(StringIO()):
            packet = adapter.fill_and_merge_20_19(offer)
            original_fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        reader = PdfReader(BytesIO(packet))
        selected = [1, 8, 10, 11]
        selected += sorted({f["page"] for f in original_fields
                            if f["api_id"].startswith("contacts_continuation_")})
        remap, content_hashes = {}, []
        for source_page in selected:
            remap[source_page] = len(writer.pages) + 1
            page = reader.pages[source_page - 1]
            content_hashes.append(hashlib.sha256(page.get_contents().get_data()).hexdigest())
            writer.add_page(page)
        shifted = [
            {**f, "page": remap[f["page"]], "recipient_id": qa_recipient(f["recipient_id"]),
             "api_id": case + "_" + f["api_id"]}
            for f in original_fields if f["page"] in remap
        ]
        fields.extend(shifted)
        manifest.append({"case": case, "source_pages": selected,
                         "output_pages": list(remap.values()), "field_count": len(shifted),
                         "content_sha256": content_hashes})
    writer.add_metadata({"/Title": "QA ONLY - purchase contract placement",
                         "/Subject": "Nonbinding synthetic provider-rendering check"})
    output = BytesIO()
    writer.write(output)
    if len(writer.pages) != 13 or len(fields) != 26:
        raise ValueError("The purchase signing specimen changed; review it before sending.")
    if hashlib.sha256(json.dumps([fields], sort_keys=True).encode()).hexdigest() != "9d4579cd2e2ece934aacdae185d462ac3528a45c6f831cb610bb575872a73691":
        raise ValueError("The purchase signing placement changed; review it before sending.")
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
        "fields": fields, "metadata": {"qa_kind": "purchase-placement", "release_sha": release_sha,
                                       "qa_revision": QA_REVISION},
    }

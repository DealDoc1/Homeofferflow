"""Production adapter for the visually verified TREC 20-19 buyer packet.

The coordinate and packet-assembly source of truth remains
``fill_pdf_20_19_staging.py`` (Release 18B). This adapter adds the production-only
uploaded-disclosure workflow and rejects paths that have not completed visual QA.
"""

import base64
from io import BytesIO

from pypdf import PdfReader, PdfWriter

from api import fill_pdf_20_19_staging as verified


class UnsupportedOfferPathError(ValueError):
    """Raised when an offer requests a path that is not production-verified."""

    def __init__(self, paths):
        self.paths = list(dict.fromkeys(paths))
        super().__init__(
            "This offer needs a dedicated Texas form packet before it can be "
            "generated: " + ", ".join(self.paths)
        )


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "required"}


def _normalized(value):
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def validate_supported_offer(offer):
    """Fail closed for buyer paths that have not passed rendered-PDF QA."""
    offer = offer or {}
    blocked = []

    financing = verified.normalize_financing(
        offer.get("financing") or offer.get("financingType") or ""
    )
    if financing not in {
        "cash", "conventional", "fha", "va", "usda",
        "seller_financing", "loan_assumption",
    }:
        blocked.append("unsupported financing type")

    leases = _normalized(offer.get("leases"))
    if leases in {
        "residential",
        "residential lease",
        "residentiallease",
        "fixture",
        "fixture lease",
        "fixturelease",
        "natural resource",
        "natural resource lease",
        "naturalresource",
        "naturalresourcelease",
    }:
        blocked.append("Paragraph 4 lease")

    lease_flags = {
        "leaseResidential": "residential lease",
        "leaseFixture": "fixture lease",
        "fixtureLease": "fixture lease",
        "leaseNaturalResource": "natural-resource lease",
        "naturalResourceLease": "natural-resource lease",
    }
    for key, label in lease_flags.items():
        if _truthy(offer.get(key)):
            blocked.append(label)

    possession = _normalized(offer.get("possession") or offer.get("possessionType"))
    buyer_temp_flag = _truthy(offer.get("buyerTemporaryLease"))
    buyer_temp_possession = possession in {"temporarylease", "temporary lease"}

    # TREC 16-7 Buyer Temporary Residential Lease completed rendered-PDF and
    # SignWell QA on the exact explicit production shape below. Keep compact or
    # ambiguous aliases fail-closed so this unlock does not broaden Paragraph 4
    # or Seller Temporary Residential Lease support.
    if buyer_temp_flag != buyer_temp_possession:
        blocked.append("Buyer Temporary Residential Lease configuration")
    if possession in {"lease", "buyerlease", "buyer lease"}:
        blocked.append("Buyer Temporary Residential Lease")
    if _truthy(offer.get("sellerTemporaryLease")):
        blocked.append("Seller Temporary Residential Lease")

    unsupported_flags = {
        "hydrostaticTesting": "Hydrostatic Testing Addendum",
        "hydrostaticAddendum": "Hydrostatic Testing Addendum",
        "leadBasedPaintAttached": "generated Lead-Based Paint Addendum",
        "attachLeadBasedPaintAddendum": "generated Lead-Based Paint Addendum",
        "sellerLeadDisclosureAttached": "generated Lead-Based Paint Addendum",
        "leadDisclosureAttached": "generated Lead-Based Paint Addendum",
    }
    for key, label in unsupported_flags.items():
        if _truthy(offer.get(key)):
            blocked.append(label)

    if blocked:
        raise UnsupportedOfferPathError(blocked)

    return True


def _uploaded_docs(offer):
    """Decode valid uploaded PDF disclosures using the existing production limits."""
    docs = (offer or {}).get("uploadedDisclosureDocs") or (offer or {}).get("uploadedDocs") or []
    if not isinstance(docs, list):
        return []

    decoded = []
    max_docs = 5
    max_bytes = 15 * 1024 * 1024

    for index, doc in enumerate(docs[:max_docs]):
        if not isinstance(doc, dict):
            continue
        name = str(doc.get("name") or f"uploaded_doc_{index + 1}.pdf")
        encoded = doc.get("base64") or doc.get("file_base64") or doc.get("data") or ""
        if not encoded:
            continue
        try:
            if isinstance(encoded, str) and encoded.strip().lower().startswith("data:") and "," in encoded:
                encoded = encoded.split(",", 1)[1]
            raw = base64.b64decode(str(encoded), validate=False)
            if not raw.startswith(b"%PDF") or len(raw) > max_bytes:
                continue
            reader = PdfReader(BytesIO(raw))
            if not reader.pages:
                continue
            copied = dict(doc)
            copied["name"] = name
            copied["raw"] = raw
            copied["page_count"] = len(reader.pages)
            decoded.append(copied)
        except Exception as exc:
            print("UPLOAD DOC SKIP:", name, str(exc))

    return decoded


def fill_and_merge_20_19(offer):
    """Generate the verified 20-19 packet, then preserve uploaded disclosures."""
    validate_supported_offer(offer)
    packet = verified.fill_and_merge(offer)
    docs = _uploaded_docs(offer)
    if not docs:
        return packet

    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(packet)))
    for doc in docs:
        writer.append(PdfReader(BytesIO(doc["raw"])))

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_20_19(offer, pdf_bytes):
    """Use verified 20-19 fields and append existing manual upload placements."""
    fields = verified.build_signwell_fields(offer, pdf_bytes)
    if not fields:
        fields = [[]]
    fields_for_file = fields[0]

    docs = _uploaded_docs(offer)
    if not docs:
        return fields

    try:
        page_count = len(PdfReader(BytesIO(pdf_bytes)).pages)
    except Exception:
        return fields

    uploaded_page_cursor = page_count - sum(doc["page_count"] for doc in docs) + 1
    has_buyer2 = bool(verified.first_present(offer.get("buyer2Email"), ""))

    placement_types = {
        "buyer1_signature": ("1", "signature", 145, 20, {}),
        "buyer1_date": ("1", "date", 66, 16, {"date_format": "MM/DD/YYYY", "lock_sign_date": True}),
        "buyer1_initials": ("1", "initials", 24, 10, {}),
        "buyer2_signature": ("2", "signature", 145, 20, {}),
        "buyer2_date": ("2", "date", 66, 16, {"date_format": "MM/DD/YYYY", "lock_sign_date": True}),
        "buyer2_initials": ("2", "initials", 24, 10, {}),
    }

    for doc_index, doc in enumerate(docs):
        placements = doc.get("signaturePlacements") or doc.get("placements") or []
        if isinstance(placements, list):
            for placement_index, placement in enumerate(placements):
                if not isinstance(placement, dict):
                    continue
                placement_type = str(placement.get("type") or placement.get("fieldType") or "").strip()
                spec = placement_types.get(placement_type)
                if not spec:
                    continue
                recipient_id, field_type, width, height, extra = spec
                if recipient_id == "2" and not has_buyer2:
                    continue

                try:
                    page_in_doc = max(1, min(doc["page_count"], int(float(placement.get("page") or 1))))
                except Exception:
                    page_in_doc = 1
                absolute_page = uploaded_page_cursor + page_in_doc - 1

                try:
                    x = float(placement.get("signwellX"))
                except Exception:
                    x = float(placement.get("xRatio") or 0) * 816
                try:
                    y = float(placement.get("signwellY"))
                except Exception:
                    y = float(placement.get("yRatio") or 0) * 1056

                safe_name = "".join(
                    character if character.isalnum() else "_"
                    for character in str(doc.get("name") or f"uploaded_doc_{doc_index + 1}")[:32]
                ).strip("_") or f"upoaded_doc_{doc_index + 1}"

                field = {
                    "api_id": f"uploaded_{doc_index + 1}_{safe_name}_p{page_in_doc}_{placement_type}_{placement_index + 1}",
                    "type": field_type,
                    "page": absolute_page,
                    "x": x,
                    "y": y,
                    "recipient_id": recipient_id,
                    "required": True,
                    "width": width,
                    "height": height,
                }
                field.update(extra)
                fields_for_file.append(field)
        uploaded_page_cursor += doc["page_count"]

    return fields

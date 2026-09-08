"""Production adapter for the visually verified TREC 20-19 buyer packet.

The coordinate and packet-assembly source of truth remains
``fill_pdf_20_19_staging.py`` (Release 18B). This adapter adds the production-only
uploaded-disclosure workflow and rejects paths that have not completed visual QA.
"""

import base64
import importlib.util
import sys
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from lib.txr_1953 import build_signwell_fields_txr1953, render_txr_1953
from lib.txr_1954 import build_signwell_fields_txr1954, render_txr_1954



def _load_verified_staging_module():
    """Load the verified adapter without relying on Vercel's ``api`` package.

    Vercel treats files under ``api/`` as serverless entrypoints rather than a
    normal Python package. A namespace import works locally but can fail in
    the deployed runtime, so production resolves the known source file
    explicitly while keeping the same verified implementation.
    """
    existing = sys.modules.get("api.fill_pdf_20_19_staging")
    if existing is not None:
        return existing
    source = Path(__file__).resolve().parent / "verified_20_19.py"
    spec = importlib.util.spec_from_file_location("_hof_verified_20_19_staging", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load verified 20-19 adapter from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Preserve compatibility with local tests and any code that imports the
    # verified adapter through its historical module name, without requiring
    # ``api/`` to become another Vercel function.
    sys.modules.setdefault("api.fill_pdf_20_19_staging", module)
    return module


verified = _load_verified_staging_module()


class UnsupportedOfferPathError(ValueError):
    """Raised when an offer requests a path that is not production-verified."""

    def __init__(self, paths):
        self.paths = list(dict.fromkeys(paths))
        super().__init__(
            "This offer uses options that are not yet available in the production "
            "TREC 20-19 packet: " + ", ".join(self.paths)
        )


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "required"}


def _normalized(value):
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def paragraph4_lease_kinds(offer):
    """Return the supported Paragraph 4 lease addenda selected by the interview."""
    offer = offer or {}
    leases = _normalized(offer.get("leases"))
    residential = _truthy(offer.get("leaseResidential")) or leases in {
        "residential", "residential lease", "residentiallease"
    }
    fixture = _truthy(offer.get("leaseFixture")) or _truthy(offer.get("fixtureLease")) or leases in {
        "fixture", "fixture lease", "fixturelease"
    }
    selected = []
    if residential:
        selected.append("TXR-1953")
    if fixture:
        selected.append("TXR-1954")
    return selected


def paragraph4_execution_parties(offer):
    """Return Seller recipients shared by the released Paragraph 4 addenda."""
    if not paragraph4_lease_kinds(offer):
        return []
    offer = offer or {}
    candidates = [
        (
            verified.first_present(
                offer.get("paragraph4Seller1Name"), offer.get("seller1Name"),
                offer.get("seller1"), offer.get("seller"),
            ),
            verified.first_present(
                offer.get("paragraph4Seller1Email"), offer.get("seller1Email"),
                offer.get("sellerEmail"),
            ),
        ),
        (
            verified.first_present(offer.get("paragraph4Seller2Name"), offer.get("seller2Name")),
            verified.first_present(offer.get("paragraph4Seller2Email"), offer.get("seller2Email")),
        ),
    ]
    buyer_emails = {
        str(value or "").strip().lower()
        for value in (offer.get("buyerEmail"), offer.get("buyer2Email"))
        if str(value or "").strip()
    }
    parties = []
    used_emails = set(buyer_emails)
    for index, (raw_name, raw_email) in enumerate(candidates, start=1):
        name = str(raw_name or "").strip()
        email = str(raw_email or "").strip().lower()
        if not name and not email:
            continue
        if not name or not email:
            raise UnsupportedOfferPathError([
                f"Paragraph 4 Seller {index} name and email"
            ])
        if email in used_emails:
            raise UnsupportedOfferPathError(["distinct Paragraph 4 signer emails"])
        used_emails.add(email)
        # Seller ids stay 3 and 4 even when there is one Buyer. This keeps the
        # same party id on a Paragraph 4 addendum and a Seller temporary lease.
        parties.append({"id": str(index + 2), "name": name, "email": email, "seller_index": index})
    if not parties:
        raise UnsupportedOfferPathError(["Paragraph 4 Seller signer"])
    return parties


def _paragraph4_render_data(offer, form_code):
    buyer_names = [str(offer.get("buyer1") or "").strip()]
    if str(offer.get("buyer2") or "").strip():
        buyer_names.append(str(offer.get("buyer2")).strip())
    seller_names = [party["name"] for party in paragraph4_execution_parties(offer)]
    property_address = ", ".join(
        part for part in (
            str(offer.get("address") or "").strip(),
            str(offer.get("city") or "").strip(),
            str(offer.get("state") or "TX").strip(),
            str(offer.get("zip") or "").strip(),
        ) if part
    )
    if form_code == "TXR-1953":
        return {
            "property_address": property_address,
            "buyer_names": buyer_names,
            "seller_names": seller_names,
            "lease_status": str(offer.get("residentialLeaseStatus") or "").strip(),
            "delivery_choice": str(offer.get("residentialLeaseDelivery") or "").strip(),
            "delivery_days": str(offer.get("residentialLeaseDeliveryDays") or "").strip(),
            "oral_lease_notice": str(offer.get("residentialLeaseOralNotice") or "").strip(),
            "explanation": str(offer.get("residentialLeaseExplanation") or "").strip(),
            "_for_signing": True,
        }
    return {
        "property_address": property_address,
        "buyer_names": buyer_names,
        "seller_names": seller_names,
        "leased_fixture_types": list(offer.get("leasedFixtureTypes") or []),
        "leased_fixtures_other": str(offer.get("leasedFixturesOther") or "").strip(),
        "assumed_fixture_leases": list(offer.get("assumedFixtureLeases") or []),
        "assumed_fixture_leases_other": str(offer.get("assumedFixtureLeasesOther") or "").strip(),
        "buyer_first_cost": str(offer.get("fixtureBuyerFirstCost") or "").strip(),
        "removal_choice": str(offer.get("fixtureRemovalChoice") or "").strip(),
        "delivery_choice": str(offer.get("fixtureLeaseDelivery") or "").strip(),
        "oral_fixture_lease_notice": str(offer.get("fixtureLeaseOralNotice") or "").strip(),
        "_for_signing": True,
    }


def _paragraph4_documents(offer):
    sources = (offer or {}).get("_paragraph4_source_pdf_bytes") or {}
    documents = []
    for form_code in paragraph4_lease_kinds(offer):
        source_bytes = sources.get(form_code) if isinstance(sources, dict) else None
        if not isinstance(source_bytes, (bytes, bytearray)) or not bytes(source_bytes).startswith(b"%PDF"):
            raise UnsupportedOfferPathError([f"available {form_code} source"])
        render_data = _paragraph4_render_data(offer, form_code)
        if form_code == "TXR-1953":
            rendered = render_txr_1953(bytes(source_bytes), render_data)
        else:
            rendered = render_txr_1954(bytes(source_bytes), render_data)
        documents.append({
            "form_code": form_code,
            "raw": rendered,
            "page_count": len(PdfReader(BytesIO(rendered)).pages),
            "render_data": render_data,
        })
    return documents


def seller_temporary_lease_execution_parties(offer):
    """Return production Seller/Tenant SignWell recipients for TREC 15-7.

    Buyers sign the lease as Landlords.  A Seller's Temporary Residential Lease
    is not complete unless the current Seller/Tenant signs too, so production
    refuses to generate a seller-lease packet without the actual Seller/Tenant
    contact details needed for those signature requests.
    """
    offer = offer or {}
    possession = _normalized(offer.get("possession") or offer.get("possessionType"))
    requested = _truthy(offer.get("sellerTemporaryLease")) or possession in {"seller temporary lease", "sellertemporarylease"}
    if not requested:
        return []

    candidates = [
        (
            verified.first_present(offer.get("seller1Name"), offer.get("seller1"), offer.get("seller")),
            verified.first_present(offer.get("seller1Email"), offer.get("sellerEmail"), offer.get("tenantEmail")),
        ),
        (offer.get("seller2Name"), offer.get("seller2Email")),
    ]
    buyer_emails = {
        str(value or "").strip().lower()
        for value in (offer.get("buyerEmail"), offer.get("buyer2Email"))
        if str(value or "").strip()
    }
    parties = []
    used_emails = set(buyer_emails)
    for index, (raw_name, raw_email) in enumerate(candidates, start=1):
        name = str(raw_name or "").strip()
        email = str(raw_email or "").strip().lower()
        if not name and not email:
            continue
        if not name or not email:
            raise UnsupportedOfferPathError([
                f"Seller Temporary Residential Lease Seller {index} name and email"
            ])
        if email in used_emails:
            raise UnsupportedOfferPathError([
                "distinct Seller Temporary Residential Lease signer emails"
            ])
        used_emails.add(email)
        parties.append({"id": str(index + 2), "name": name, "email": email, "seller_index": index})

    if not parties:
        raise UnsupportedOfferPathError([
            "Seller Temporary Residential Lease Seller/Tenant signer"
        ])
    return parties


def validate_supported_offer(offer):
    """Fail closed for buyer paths that have not passed rendered-PDF QA."""
    offer = offer or {}
    blocked = []

    financing = verified.normalize_financing(
        offer.get("financing") or offer.get("financingType") or ""
    )
    if financing not in {"cash", "conventional", "fha", "va", "usda"}:
        blocked.append("unsupported financing type")

    leases = _normalized(offer.get("leases"))
    if leases in {"natural resource", "natural resource lease", "naturalresource", "naturalresourcelease"}:
        blocked.append("natural-resource lease")
    if _truthy(offer.get("leaseNaturalResource")) or _truthy(offer.get("naturalResourceLease")):
        blocked.append("natural-resource lease")

    selected_leases = paragraph4_lease_kinds(offer)
    if leases in {"yes", "existing", "existing leases"} and not selected_leases:
        blocked.append("Paragraph 4 lease type")

    if "TXR-1953" in selected_leases:
        status = str(offer.get("residentialLeaseStatus") or "").strip()
        if status not in {"termination", "assignment"}:
            blocked.append("residential lease treatment")
        if status == "assignment":
            delivery = str(offer.get("residentialLeaseDelivery") or "").strip()
            if delivery not in {"received", "not_received", "oral_notice"}:
                blocked.append("residential lease delivery")
            if delivery == "not_received":
                days = str(offer.get("residentialLeaseDeliveryDays") or "").strip()
                if not days.isdigit() or int(days) < 1:
                    blocked.append("residential lease delivery days")
            if delivery == "oral_notice" and not str(offer.get("residentialLeaseOralNotice") or "").strip():
                blocked.append("oral residential lease notice")

    if "TXR-1954" in selected_leases:
        allowed_fixtures = {"solar_panels", "propane_tanks", "water_softener", "security_system", "other"}
        leased = offer.get("leasedFixtureTypes") or []
        assumed = offer.get("assumedFixtureLeases") or []
        if not isinstance(leased, list) or not leased or any(value not in allowed_fixtures for value in leased):
            blocked.append("leased fixture selection")
        if not isinstance(assumed, list) or not assumed or any(value not in allowed_fixtures for value in assumed):
            blocked.append("assumed fixture lease selection")
        if "other" in leased and not str(offer.get("leasedFixturesOther") or "").strip():
            blocked.append("other leased fixture description")
        if "other" in assumed and not str(offer.get("assumedFixtureLeasesOther") or "").strip():
            blocked.append("other assumed fixture lease description")
        if str(offer.get("fixtureRemovalChoice") or "").strip() not in {"will", "will_not"}:
            blocked.append("fixture removal choice")
        fixture_delivery = str(offer.get("fixtureLeaseDelivery") or "").strip()
        if fixture_delivery not in {"received", "not_received", "oral_notice"}:
            blocked.append("fixture lease delivery")
        if fixture_delivery == "oral_notice" and not str(offer.get("fixtureLeaseOralNotice") or "").strip():
            blocked.append("oral fixture lease notice")

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
    seller_temp_flag = _truthy(offer.get("sellerTemporaryLease"))
    seller_temp_possession = possession in {"seller temporary lease", "sellertemporarylease"}
    if seller_temp_flag != seller_temp_possession:
        blocked.append("Seller Temporary Residential Lease configuration")
    if _truthy(offer.get("sellerExecutionTestMode")):
        blocked.append("staging-only Seller Temporary Residential Lease test mode")

    unsupported_flags = {
        "sellerFinancing": "Seller Financing Addendum",
        "loanAssumption": "Loan Assumption Addendum",
        "hydrostaticTesting": "Hydrostatic Testing Addendum",
        "hydrostaticAddendum": "Hydrostatic Testing Addendum",
        "environmentalAssessment": "Environmental Assessment Addendum",
        "environmentalAddendum": "Environmental Assessment Addendum",
        "mineralReservation": "Mineral Reservation Addendum",
        "mineralReservationAddendum": "Mineral Reservation Addendum",
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

    if seller_temp_flag:
        seller_temporary_lease_execution_parties(offer)
    if selected_leases:
        paragraph4_execution_parties(offer)

    return True


MAX_UPLOADED_DISCLOSURE_DOCS = 5
MAX_UPLOADED_DISCLOSURE_DOC_BYTES = 2 * 1024 * 1024
MAX_UPLOADED_DISCLOSURE_TOTAL_BYTES = int(2.5 * 1024 * 1024)


def _uploaded_docs(offer):
    """Decode every uploaded PDF or fail before a packet can omit one silently."""
    docs = (offer or {}).get("uploadedDisclosureDocs") or (offer or {}).get("uploadedDocs") or []
    if not isinstance(docs, list):
        raise ValueError("Uploaded disclosure documents must be a list of PDFs.")
    if len(docs) > MAX_UPLOADED_DISCLOSURE_DOCS:
        raise ValueError(f"A packet can include at most {MAX_UPLOADED_DISCLOSURE_DOCS} uploaded PDFs.")

    decoded = []
    total_bytes = 0

    for index, doc in enumerate(docs):
        if not isinstance(doc, dict):
            raise ValueError(f"Uploaded PDF #{index + 1} is not a valid document.")
        name = str(doc.get("name") or f"uploaded_doc_{index + 1}.pdf")
        encoded = doc.get("base64") or doc.get("file_base64") or doc.get("data") or ""
        if not encoded:
            raise ValueError(f"Uploaded PDF {name} is missing its file data.")
        try:
            if isinstance(encoded, str) and encoded.strip().lower().startswith("data:") and "," in encoded:
                encoded = encoded.split(",", 1)[1]
            raw = base64.b64decode(str(encoded), validate=True)
        except Exception as exc:
            raise ValueError(f"Uploaded PDF {name} could not be decoded.") from exc
        if not raw.startswith(b"%PDF"):
            raise ValueError(f"Uploaded document {name} is not a readable PDF.")
        if len(raw) > MAX_UPLOADED_DISCLOSURE_DOC_BYTES:
            raise ValueError(f"Uploaded PDF {name} exceeds the 2 MB per-file limit.")
        total_bytes += len(raw)
        if total_bytes > MAX_UPLOADED_DISCLOSURE_TOTAL_BYTES:
            raise ValueError("Uploaded PDFs exceed the 2.5 MB combined limit.")
        try:
            reader = PdfReader(BytesIO(raw))
            if not reader.pages:
                raise ValueError(f"Uploaded PDF {name} has no readable pages.")
            copied = dict(doc)
            copied["name"] = name
            copied["raw"] = raw
            copied["page_count"] = len(reader.pages)
            decoded.append(copied)
        except Exception as exc:
            if isinstance(exc, ValueError):
                raise
            raise ValueError(f"Uploaded PDF {name} could not be read.") from exc

    return decoded


def fill_and_merge_20_19(offer):
    """Generate the verified 20-19 packet, Paragraph 4 forms, then uploads."""
    validate_supported_offer(offer)
    docs = _uploaded_docs(offer)
    lease_docs = _paragraph4_documents(offer)
    packet = verified.fill_and_merge(offer)
    if not docs and not lease_docs:
        return packet

    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(packet)))
    for doc in lease_docs:
        writer.append(PdfReader(BytesIO(doc["raw"])))
    for doc in docs:
        writer.append(PdfReader(BytesIO(doc["raw"])))

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_20_19(offer, pdf_bytes):
    """Use verified 20-19 fields and append approved production placements."""
    fields = verified.build_signwell_fields(offer, pdf_bytes)
    if not fields:
        fields = [[]]
    fields_for_file = fields[0]

    seller_execution_parties = seller_temporary_lease_execution_parties(offer)
    if seller_execution_parties:
        # The source builder already places the Buyer/Landlord fields.  The
        # completed four-party staging packet visually verified these Seller /
        # Tenant coordinates, so production adds only the corresponding
        # Seller/Tenant fields here rather than reusing the staging allowlist.
        by_id = {field.get("api_id"): field for field in fields_for_file}
        main_signature_page = by_id.get("buyer1_main_contract_signature", {}).get("page", 10)
        lease_initial_page = by_id.get("buyer1_initials_seller_temp_lease_p1", {}).get("page")
        lease_signature_page = by_id.get("buyer1_signature_seller_temp_lease", {}).get("page")

        def append_field(api_id, field_type, page, x, y, recipient_id, width, height, **extra):
            if not page:
                return
            field = {
                "api_id": api_id,
                "type": field_type,
                "page": page,
                "x": x,
                "y": y,
                "recipient_id": recipient_id,
                "required": True,
                "width": width,
                "height": height,
            }
            field.update(extra)
            fields_for_file.append(field)

        def append_signature_date(prefix, page, x, y, date_x, date_y, recipient_id):
            append_field(f"{prefix}_signature", "signature", page, x, y, recipient_id, 145, 20)
            append_field(
                f"{prefix}_date", "date", page, date_x, date_y, recipient_id, 66, 16,
                date_format="MM/DD/YYYY", lock_sign_date=True,
            )

        for party in seller_execution_parties:
            recipient_id = party["id"]
            index = party["seller_index"]
            if index == 1:
                append_signature_date("seller1_main_contract", main_signature_page, 420, 433, 591, 433, recipient_id)
                append_field("seller1_initials_seller_temp_lease_p1", "initials", lease_initial_page, 476, 1004, recipient_id, 24, 10)
                append_field("seller1_signature_seller_temp_lease", "signature", lease_signature_page, 440, 777, recipient_id, 145, 20)
            elif index == 2:
                append_signature_date("seller2_main_contract", main_signature_page, 420, 568, 591, 568, recipient_id)
                append_field("seller2_initials_seller_temp_lease_p1", "initials", lease_initial_page, 508, 1004, recipient_id, 24, 10)
                append_field("seller2_signature_seller_temp_lease", "signature", lease_signature_page, 440, 845, recipient_id, 145, 20)

    lease_docs = _paragraph4_documents(offer)
    if lease_docs:
        uploaded_docs = _uploaded_docs(offer)
        first_lease_page = (
            len(PdfReader(BytesIO(pdf_bytes)).pages)
            - sum(doc["page_count"] for doc in uploaded_docs)
            - sum(doc["page_count"] for doc in lease_docs)
            + 1
        )
        page_cursor = first_lease_page
        for doc in lease_docs:
            if doc["form_code"] == "TXR-1953":
                relative_fields = build_signwell_fields_txr1953(doc["render_data"])[0]
            else:
                relative_fields = build_signwell_fields_txr1954(doc["render_data"])[0]
            for field in relative_fields:
                copied = dict(field)
                copied["page"] = page_cursor + int(field["page"]) - 1
                # Core offer packets reserve ids 1 and 2 for Buyers and 3 and
                # 4 for Sellers, regardless of whether Buyer 2 is present.
                recipient_id = str(copied.get("recipient_id") or "")
                buyer_count = len(doc["render_data"].get("buyer_names") or [])
                seller_offset = int(recipient_id) - buyer_count
                if seller_offset >= 1:
                    copied["recipient_id"] = str(seller_offset + 2)
                fields_for_file.append(copied)
            page_cursor += doc["page_count"]

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

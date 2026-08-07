"""Validation-only foundation for seller disclosure drafts.

This module deliberately does not render or sign TREC-55-1/TREC-61-0. It
normalizes the seller/property intake that will later be mapped to an approved
source revision after document-specific visual QA.
"""

from __future__ import annotations

import json
import uuid

from lib.trec_seller_disclosure_schema import validate_response_keys


MAX_ADDRESS = 400
MAX_NAME = 180
MAX_RESPONSE_BYTES = 250_000


def _text(value: object, label: str, maximum: int) -> str:
    result = " ".join(str(value or "").strip().split())
    if not result or len(result) > maximum:
        raise ValueError(f"Enter a valid {label}.")
    return result


def _names(value: object, label: str, *, required: bool) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list.")
    values = [_text(item, label, MAX_NAME) for item in value if str(item or "").strip()]
    if required and not values:
        raise ValueError(f"Enter at least one {label.lower()}.")
    if len(values) > 2:
        raise ValueError(f"Use no more than two {label.lower()}.")
    return values


def _uuid(value: object, label: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        raise ValueError(f"Choose a valid {label}.")


def parse_seller_disclosure_draft(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Seller disclosure draft must be an object.")
    if data.get("formCode") != "TREC-55-1":
        raise ValueError("Only the approved TREC-55-1 seller disclosure source is available.")
    if data.get("status") not in (None, "draft"):
        raise ValueError("Seller disclosure intake can only create a draft.")
    if data.get("sellerReviewAttested") is True:
        raise ValueError("Seller review must be completed by the seller, not the agent intake request.")

    response_data = data.get("responseData") or {}
    water_rights_data = data.get("waterRightsData") or {}
    if not isinstance(response_data, dict) or not isinstance(water_rights_data, dict):
        raise ValueError("Disclosure responses must be objects.")
    validate_response_keys("TREC-55-1", response_data)
    validate_response_keys("TREC-61-0", water_rights_data)
    encoded_response = json.dumps(
        {"responseData": response_data, "waterRightsData": water_rights_data},
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    if len(encoded_response) > MAX_RESPONSE_BYTES:
        raise ValueError("Disclosure responses are too large.")

    seller_names = _names(data.get("sellerNames"), "seller names", required=True)
    buyer_names = _names(data.get("buyerNames") or [], "buyer names", required=False)
    water_source_id = data.get("waterSourceId")
    return {
        "disclosure_source_id": _uuid(data.get("disclosureSourceId"), "approved TREC-55-1 source"),
        "water_source_id": _uuid(water_source_id, "approved TREC-61-0 source") if water_source_id else None,
        "listing_workspace_id": _uuid(data.get("listingWorkspaceId"), "listing workspace") if data.get("listingWorkspaceId") else None,
        "property_address": _text(data.get("propertyAddress"), "property address", MAX_ADDRESS),
        "seller_names": seller_names,
        "buyer_names": buyer_names,
        "response_data": response_data,
        "water_rights_data": water_rights_data,
        "status": "draft",
        "seller_review_attested": False,
    }

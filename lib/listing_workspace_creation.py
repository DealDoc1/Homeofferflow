"""Input validation for agent-owned listing workspace creation."""

import uuid


WORKFLOWS = {"listing_agreement", "seller_disclosure", "lease_listing"}
CREATION_FIELDS = {
    "listingKind", "propertyAddress", "sellerNames", "requestedWorkflows",
    "confidentialNotes", "sellerLeadId",
}
OPTIONAL_CREATION_FIELDS = {"clientRequestId"}


def normalized_uuid(value, message):
    try:
        return str(uuid.UUID(str(value or "")))
    except (TypeError, ValueError, AttributeError):
        raise ValueError(message)


def validate_listing_workspace_creation(data):
    required_fields = {"action", *CREATION_FIELDS}
    allowed_fields = required_fields | OPTIONAL_CREATION_FIELDS
    if (not isinstance(data, dict) or not required_fields.issubset(data)
            or set(data) - allowed_fields):
        raise ValueError("Provide only the listing workspace details.")

    kind = data.get("listingKind")
    if kind not in ("sale", "lease"):
        raise ValueError("Choose sale or lease for this listing workspace.")

    address = data.get("propertyAddress")
    if not isinstance(address, str):
        raise ValueError("Enter the property address before creating a workspace.")
    address = address.strip()
    if not 3 <= len(address) <= 400:
        raise ValueError("Keep the property address between 3 and 400 characters.")

    raw_sellers = data.get("sellerNames")
    if not isinstance(raw_sellers, list) or not 1 <= len(raw_sellers) <= 4:
        raise ValueError("Enter between one and four seller or landlord names.")
    sellers = []
    for value in raw_sellers:
        if not isinstance(value, str):
            raise ValueError("Enter valid seller or landlord names.")
        name = value.strip()
        if not name or len(name) > 180:
            raise ValueError("Keep each seller or landlord name to 180 characters or fewer.")
        sellers.append(name)

    raw_workflows = data.get("requestedWorkflows")
    if not isinstance(raw_workflows, list) or len(raw_workflows) > len(WORKFLOWS):
        raise ValueError("Choose valid optional listing planning topics.")
    workflows = []
    for value in raw_workflows:
        if not isinstance(value, str) or value not in WORKFLOWS or value in workflows:
            raise ValueError("Choose valid optional listing planning topics.")
        workflows.append(value)

    notes = data.get("confidentialNotes")
    if notes is None:
        notes = None
    elif not isinstance(notes, str):
        raise ValueError("Enter valid private workspace notes.")
    else:
        notes = notes.strip() or None
        if notes and len(notes) > 4000:
            raise ValueError("Keep private workspace notes to 4000 characters or fewer.")

    raw_lead_id = data.get("sellerLeadId")
    lead_id = None if raw_lead_id in (None, "") else normalized_uuid(
        raw_lead_id, "Refresh your seller leads before connecting this workspace."
    )
    raw_request_id = data.get("clientRequestId")
    request_id = None if raw_request_id in (None, "") else normalized_uuid(
        raw_request_id, "Choose a valid listing workspace save attempt."
    )
    return {
        "listing_kind": kind,
        "property_address": address,
        "seller_names": sellers,
        "requested_workflows": workflows,
        "confidential_notes": notes,
        "seller_lead_id": lead_id,
        "client_request_id": request_id,
    }

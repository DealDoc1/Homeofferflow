import math


def document_matches_signing_request(document, expected_fields, expected_recipients):
    """Confirm SignWell retained every requested field, geometry, and signer.

    SignWell accepts a document creation request before it is visible to a
    signer.  Treat that acceptance as provisional: a field dropped, moved, or
    assigned to the wrong recipient must never result in a live signature
    email. SignWell returns page, position, and dimensions with Get Document,
    so compare every supplied geometry value before sending the draft.
    """
    def field_map(field_groups):
        if not isinstance(field_groups, list):
            return None
        fields = {}
        for page_fields in field_groups:
            if not isinstance(page_fields, list):
                return None
            for field in page_fields:
                if not isinstance(field, dict):
                    return None
                api_id = str(field.get("api_id") or "").strip()
                if not api_id or api_id in fields:
                    return None
                fields[api_id] = field
        return fields

    if not isinstance(document, dict):
        return False
    expected_by_id = field_map(expected_fields)
    returned_by_id = field_map(document.get("fields"))
    if expected_by_id is None or returned_by_id is None or set(expected_by_id) != set(returned_by_id):
        return False

    for api_id, expected in expected_by_id.items():
        returned = returned_by_id[api_id]
        if str(expected.get("recipient_id") or "").strip() != str(returned.get("recipient_id") or "").strip():
            return False
        if str(expected.get("type") or "").strip().casefold() != str(returned.get("type") or "").strip().casefold():
            return False
        for key in ("page", "x", "y", "width", "height"):
            if key not in expected:
                continue
            try:
                # The API serializes dimensions as strings in some responses.
                # A sub-point serialization difference is harmless; a field
                # outside this tolerance is not the reviewed signing map.
                left, right = float(expected[key]), float(returned[key])
                if not math.isfinite(left) or not math.isfinite(right) or abs(left - right) > 0.5:
                    return False
            except (TypeError, ValueError, KeyError):
                return False

    actual_recipients = document.get("recipients")
    if any(not isinstance(items, list) or any(not isinstance(item, dict) for item in items)
           for items in (expected_recipients, actual_recipients)):
        return False
    expected_recipient_ids = {str(recipient.get("id") or "").strip() for recipient in expected_recipients}
    returned_recipient_ids = {
        str(recipient.get("id") or "").strip()
        for recipient in (document.get("recipients") or [])
    }
    if '' in expected_recipient_ids or expected_recipient_ids != returned_recipient_ids:
        return False
    if len(expected_recipient_ids) != len(expected_recipients) or len(returned_recipient_ids) != len(document.get("recipients") or []):
        return False
    returned_recipients = {str(item.get("id") or "").strip(): item for item in document.get("recipients") or []}
    for expected in expected_recipients:
        actual = returned_recipients[str(expected.get("id") or "").strip()]
        for key in ("name", "email"):
            if key in expected:
                left, right = str(expected.get(key) or "").strip(), str(actual.get(key) or "").strip()
                if (left.casefold() if key == "email" else left) != (right.casefold() if key == "email" else right):
                    return False
    return True


def send_options(payload):
    """Forward only supported options to SignWell's update-and-send endpoint.

    The document, recipients and fields have already been created and checked.
    In particular, with_signature_page is a create-only setting, not a send
    option. Keep this allowlist explicit so new creation options cannot leak
    into the final request. Contract: developers.signwell.com/reference/senddocument
    """
    keys = (
        "test_mode", "name", "subject", "message", "reminders",
        "apply_signing_order", "embedded_signing", "custom_requester_name",
        "metadata",
    )
    return {key: payload[key] for key in keys if key in payload}

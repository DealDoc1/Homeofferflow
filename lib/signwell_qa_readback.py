"""Redacted diagnostics for a fixed, fictional owner QA draft only.

This is not an invitation verifier. It explains failed checks without relaxing
them, exporting a provider response, or allowing caller-selected documents.
"""
import math

from lib.signwell_controls import controls_match
from lib.signwell_request import document_matches_signing_request


def readback_report(document, payload):
    """Return booleans, reviewed field IDs and bounded scalar observations.

    Provider strings, field values, recipients, URLs, regexes, metadata values
    and exception messages never enter the result. Malformed shapes stay a
    failed check rather than breaking the operator's read-only inspection.
    """
    def scalar(value):
        if value is None or type(value) is bool:
            return value
        if isinstance(value, (int, float, str)) and type(value) is not bool:
            try:
                number = float(value)
                if math.isfinite(number) and abs(number) <= 100000:
                    return number
            except (ValueError, OverflowError):
                pass
        return "non_scalar"

    checks = {
        "document_id": document.get("id") == payload.get("id"),
        "test_mode": document.get("test_mode") is True,
        "name": document.get("name") == payload["name"],
        "parallel_invitations": document.get("apply_signing_order") is False,
        "metadata": isinstance(document.get("metadata"), dict) and all(
            document["metadata"].get(k) == v for k, v in payload["metadata"].items()),
        "geometry_and_recipients": document_matches_signing_request(
            document, payload["fields"], payload["recipients"]),
        "completion_controls": controls_match(document, payload["fields"],
            payload["checkbox_groups"], payload["conditional_rules"]),
    }
    differences = []
    try:
        rows = document.get("fields")
        if not isinstance(rows, list) or any(not isinstance(group, list) for group in rows):
            raise ValueError("Invalid field groups")
        expected = {f["api_id"]: f for group in payload["fields"] for f in group}
        returned = {f["api_id"]: f for group in document["fields"] for f in group}
        checks["field_set"] = len(returned) == sum(map(len, document["fields"])) and set(expected) == set(returned)
        for key, field in expected.items():
            actual = returned.get(key)
            if not isinstance(actual, dict):
                differences.append({"field": key, "property": "missing"})
                continue
            for prop in ("page", "x", "y", "width", "height", "required", "fixed_width",
                         "validation", "validation_regex", "validation_regex_error_message"):
                if prop in field and field[prop] != actual.get(prop):
                    item = {"field": key, "property": prop, "present": prop in actual}
                    if prop in {"page", "x", "y", "width", "height", "required", "fixed_width"}:
                        item.update(expected=scalar(field[prop]), returned=scalar(actual.get(prop)))
                    differences.append(item)
            for prop in ("type", "recipient_id"):
                if str(field.get(prop)) != str(actual.get(prop)):
                    differences.append({"field": key, "property": prop})

        # Isolate group/rule equality from text-option equality using only field
        # aliases. The production verifier and its strict comparison are unchanged.
        aliases = [[{k: f[k] for k in ("api_id", "id") if k in f} for f in group]
                   for group in document["fields"]]
        expected_aliases = [[{"api_id": key} for key in expected]]
        for name, other in (("checkbox_groups", "conditional_rules"), ("conditional_rules", "checkbox_groups")):
            isolated = {"fields": aliases, name: document.get(name), other: []}
            checks[name] = controls_match(isolated, expected_aliases,
                payload[name] if name == "checkbox_groups" else [],
                payload[name] if name == "conditional_rules" else [])
        groups = document.get("checkbox_groups") or []
        group_ids = {str(g.get("id")) for g in groups if isinstance(g, dict) and g.get("id")}
        field_aliases = set(expected) | {str(f.get("id")) for f in returned.values() if f.get("id")}
        for group in payload["checkbox_groups"]:
            rows = [g for g in groups if isinstance(g, dict) and g.get("group_name") == group["group_name"]]
            for actual in rows[:1]:
                differences.append({"group": group["group_name"], "property": "group_readback",
                    "recipient_matches": actual.get("recipient_id") == group["recipient_id"],
                    "recipient_is_null": actual.get("recipient_id") is None,
                    "required": scalar(actual.get("required")), "exact_value": scalar(actual.get("exact_value")),
                    "validation_matches": actual.get("validation") == group["validation"]})
        for index, rule in enumerate((document.get("conditional_rules") or [])[:len(payload["conditional_rules"]) + 1]):
            target = str(rule.get("target_id"))
            differences.append({"rule_index": index, "property": "target_kind",
                "kind": "field" if target in field_aliases else "group" if target in group_ids else "unrecognized"})
    except (KeyError, TypeError, ValueError, AttributeError):
        checks["readback_shape"] = False
    return {"checks": checks, "differences": differences[:120]}

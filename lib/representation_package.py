"""Compose an approved representation agreement with selected related forms.

Callers must resolve private sources, render them with server-owned data and
verify each source revision before composition. This module has no network,
database or delivery side effects.
"""
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfWriter

from lib.listing_packet import MAX_PAGES, MAX_INPUT_BYTES, _fields, _reader


@dataclass(frozen=True)
class RepresentationPackage:
    pdf: bytes
    fields: list
    manifest: dict


def compose_representation_package(primary_pdf, primary_fields, related_pdf=None, related_fields=None,
                                    *, recipients, related_code="TXR-1506", information_documents=()):
    """Append the optional TXR-1506 form and information-only agent IABS."""
    if related_pdf is not None and related_code != "TXR-1506":
        raise ValueError("This related representation document is not available.")
    if not isinstance(primary_pdf, bytes) or not isinstance(information_documents, (list, tuple)):
        raise ValueError("The representation package exceeds the supported size.")
    inputs = [primary_pdf]
    if related_pdf is not None:
        inputs.append(related_pdf)
    parsed_information = []
    for item in information_documents:
        if (not isinstance(item, tuple) or len(item) != 2 or item[0] != "IABS"
                or not isinstance(item[1], bytes)):
            raise ValueError("This information document is not available for the package.")
        parsed_information.append((item[0], _reader(item[1])))
        inputs.append(item[1])
    if sum(len(value) for value in inputs) > MAX_INPUT_BYTES:
        raise ValueError("The representation package exceeds the supported size.")
    primary = _reader(primary_pdf)
    related = _reader(related_pdf) if related_pdf is not None else None
    total_pages = len(primary.pages) + (len(related.pages) if related else 0)
    for _, reader in parsed_information:
        total_pages += len(reader.pages)
    if total_pages > MAX_PAGES:
        raise ValueError("The representation package exceeds the supported page count.")
    allowed = {str(value) for value in recipients}
    if not allowed or len(allowed) != len(recipients):
        raise ValueError("Review the representation package signers.")
    identity = {value: value for value in allowed}
    fields = _fields(primary_fields, primary, identity, allowed, prefix="", offset=0)
    if related is not None:
        fields.extend(_fields(related_fields, related, identity, allowed,
                              prefix="txr1506_", offset=len(primary.pages)))
    if len({field["api_id"] for field in fields}) != len(fields):
        raise ValueError("The representation package contains conflicting signing fields.")
    writer = PdfWriter()
    if primary.get_fields():
        primary.add_form_topname("hof_representation_primary")
    if related is not None and related.get_fields():
        related.add_form_topname("hof_representation_txr1506")
    writer.append(primary, import_outline=False)
    if related is not None:
        writer.append(related, import_outline=False)
    for _, reader in parsed_information:
        writer.append(reader, import_outline=False)
    output = BytesIO()
    writer.write(output)
    page_ranges = {}
    if related is not None:
        page_ranges.update(related_code=related_code,
                           related_start_page=len(primary.pages) + 1,
                           related_end_page=len(primary.pages) + len(related.pages))
    cursor = len(primary.pages) + (len(related.pages) if related else 0)
    for code, reader in parsed_information:
        page_ranges[f"{code.lower()}_start_page"] = cursor + 1
        cursor += len(reader.pages)
        page_ranges[f"{code.lower()}_end_page"] = cursor
    return RepresentationPackage(
        pdf=output.getvalue(), fields=[fields],
        manifest={"primary_pages": len(primary.pages), **page_ranges,
                  "included_codes": ([related_code] if related is not None else [])
                                    + [code for code, _ in parsed_information],
                  "page_count": total_pages, "field_count": len(fields)},
    )

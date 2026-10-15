"""Prepare fictional full-source explanation cases. No network or provider send."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from lib import trec_seller_disclosure as forms
from lib.seller_disclosure_explanations import DETAILS, append_explanations, continuation_fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disclosure-source", type=Path, required=True)
    parser.add_argument("--water-source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sources = {"TREC-55-1": args.disclosure_source.read_bytes(), "TREC-61-0": args.water_source.read_bytes()}
    for code, source in sources.items():
        forms.validate_source_bytes(code, source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    for name, seller_count, buyer_count, water, long in (
        ("one-seller", 1, 0, False, False), ("two-sellers-water", 2, 2, True, False),
        ("unicode-overflow", 2, 2, True, True),
    ):
        parties = {"seller_names": [f"QA Seller {i + 1}" for i in range(seller_count)],
                   "buyer_names": [f"QA Buyer {i + 1}" for i in range(buyer_count)]}
        main_values = {key: "QA only: the seller provided these details." for key, _, _, blanks in DETAILS["TREC-55-1"] if blanks}
        water_values = {key: "QA only: water details reviewed." for key, _, _, blanks in DETAILS["TREC-61-0"] if blanks}
        main_values.update({"working_smoke_detectors": "N", "property_needs_repair": "Y", "defect_roof": "Y"})
        water_values.update({"in_groundwater_district": "Y", "water_wells_known": "Y"})
        if seller_count == 1:
            main_values["conditions_explanation"] = ("QA only - Listing-stage detail reviewed by the sole Seller. " * 15).strip()
        if long:
            main_values["conditions_explanation"] = ("QA only - Élodie reviewed the façade; 张伟 noted <paint> & trim. " * 35).strip()
            water_values["well_agreement"] = ("QA only - José reviewed the shared well agreement with Zoë. " * 35).strip()
        address = "QA ONLY - 100 Fictional Example Lane"
        notes, writer = [], PdfWriter()
        for code, values in [("TREC-55-1", main_values)] + ([("TREC-61-0", water_values)] if water else []):
            preview = forms.render_unsigned_preview(sources[code], code, {**values, "propertyAddress": address},
                                                    qa_mode=True, continuation_sink=notes)
            for page in PdfReader(BytesIO(preview)).pages:
                writer.add_page(page)
        stream = BytesIO(); writer.write(stream)
        packet, pages = append_explanations(stream.getvalue(), notes, property_address=address, parties=parties)
        fields = forms.build_signwell_fields("TREC-55-1", parties)[0]
        if water:
            fields += forms.build_signwell_fields("TREC-61-0", parties, page_offset=4)[0]
        fields += continuation_fields(parties, pages)
        target = args.output_dir / (name + ".pdf"); target.write_bytes(packet)
        cases.append({"case": name, "pages": len(PdfReader(BytesIO(packet)).pages),
                      "continuation_pages": pages, "fields": fields,
                      "packet_sha256": hashlib.sha256(packet).hexdigest()})
    (args.output_dir / "manifest.json").write_text(json.dumps({"nothing_sent": True, "cases": cases}, indent=2) + "\n")
    print(json.dumps({"nothing_sent": True, "cases": [{k: c[k] for k in ("case", "pages", "continuation_pages")} for c in cases]}))


if __name__ == "__main__":
    main()

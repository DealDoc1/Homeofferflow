"""Prepare fictional full-source explanation cases. No network or provider send."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib import trec_seller_disclosure as forms
from lib.seller_disclosure_explanations import DETAILS, COUNT_KEYS, append_explanations, continuation_fields

def show_qa_fields(packet, fields):
    writer = PdfWriter()
    for i, page in enumerate(PdfReader(BytesIO(packet)).pages, 1):
        overlay=BytesIO(); canvas=Canvas(overlay,pagesize=(612,792))
        for field in fields:
            if field['page'] != i: continue
            x,y,width,height=field['x']*.75,792-(field['y']+field['height'])*.75,field['width']*.75,field['height']*.75
            canvas.setStrokeColorRGB(0,.25,.8);canvas.setLineWidth(.4);canvas.rect(x,y,width,height)
            canvas.setFillColorRGB(0,.25,.8);canvas.setFont('Helvetica',6)
            canvas.drawString(x+1,y+2,('Q'+field['recipient_id']) if field['type']=='initials' else 'QA '+field['type'])
        canvas.showPage();canvas.save();page.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0]);writer.add_page(page)
    output=BytesIO();writer.write(output);return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disclosure-source", type=Path, required=True)
    parser.add_argument("--water-source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--show-qa-fields", action="store_true", help="Draw labeled fictional field rectangles, not actual signatures")
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
        for rows in (forms.TREC_55_1_ITEM_ROWS,forms.TREC_55_1_CONDITION_ROWS,forms.TREC_55_1_CONDITION4_ROWS,
                     forms.TREC_55_1_FLOOD_ROWS,forms.TREC_55_1_ADDITIONAL_ROWS):
            main_values.update({key:'N' if j%2 else 'Y' for j,(key,_,_) in enumerate(rows)})
        main_values.update({key:'N' for key in forms.TREC_55_1_FEATURE_RESPONSES})
        main_values.update({"working_smoke_detectors": "N", "property_needs_repair": "Y", "defect_roof": "Y",
                           "seller_occupancy":"N","seller_occupancy_duration":"2 years","roof_type":"Metal","roof_age":"8 years",
                           "property_items_condition_issue":"U","filed_flood_claim":"Y","received_fema_or_sba_assistance":"N"})
        for key in ('in_100_year_floodplain','in_500_year_floodplain','in_floodway','in_flood_pool','in_reservoir'):
            main_values[key]='Y';main_values[key+'_extent']='partly' if long else 'wholly'
        water_values.update({key:str(j) for j,key in enumerate(sorted(COUNT_KEYS))})
        water_values.update({"in_groundwater_district": "Y", "water_wells_known": "Y", "well_ownership":"other",
                            "water_well_on_another_property":"Y","water_well_relies_on_outside_rights":"N",
                            "groundwater_rights_severed_sold_leased":"Y","surface_water_right":"Y","pond_lake_or_water_tank":"N"})
        if seller_count==1:main_values.update({"seller_occupancy":"Y","seller_occupancy_duration":"", "working_smoke_detectors":"Y","property_needs_repair":"N"})
        if seller_count==1:main_values.update({"filed_flood_claim":"N","received_fema_or_sba_assistance":"Y","property_items_condition_issue":"N"})
        if seller_count == 1:
            main_values["conditions_explanation"] = ("QA only - Listing-stage detail reviewed by the sole Seller. " * 15).strip()
        if long:
            main_values.update({"working_smoke_detectors":"U","property_items_condition_issue":"Y"})
            water_values.update({"in_groundwater_district":"U","well_ownership":"seller_only"})
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
        if args.show_qa_fields:packet=show_qa_fields(packet,fields)
        target = args.output_dir / (name + ".pdf"); target.write_bytes(packet)
        cases.append({"case": name, "pages": len(PdfReader(BytesIO(packet)).pages),
                      "continuation_pages": pages, "fields": fields,
                      "packet_sha256": hashlib.sha256(packet).hexdigest()})
    (args.output_dir / "manifest.json").write_text(json.dumps({"nothing_sent": True, "cases": cases}, indent=2) + "\n")
    print(json.dumps({"nothing_sent": True, "cases": [{k: c[k] for k in ("case", "pages", "continuation_pages")} for c in cases]}))


if __name__ == "__main__":
    main()

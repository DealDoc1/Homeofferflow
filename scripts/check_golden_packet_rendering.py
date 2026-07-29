#!/usr/bin/env python3
"""Render supported golden packets and compare page-level visual fingerprints.

Run with --write-baseline only after the rendered packets have received human
visual approval. The committed manifest intentionally contains hashes, not
customer data or PDFs.
"""

import argparse
import contextlib
import hashlib
import json
import shutil
import subprocess
import tempfile
from io import BytesIO, StringIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "tests" / "fixtures" / "golden_packet_rendering.json"
POPPLER = shutil.which("pdftoppm")
PYTHON_TEST_ROOT = ROOT


def _offer_scenarios():
    conventional = {
        "financing": "conventional", "thirdPartyFinancing": "yes", "loanAmount": "400000",
        "cashAmount": "100000", "loanType": "conventional", "loanTerm": "30",
        "interestRate": "6.5", "loanOriginationFee": "0",
    }
    backup = {
        "backupOffer": "yes", "backupAdditionalEarnest": "500", "backupAdditionalOptionFee": "100",
        "backupAdditionalDays": "3", "firstContractDate": "2026-06-01", "backupTerminationDate": "2026-08-01",
    }
    return {
        "cash_single": {},
        "cash_two": {"buyer2": "Second Buyer", "buyer2Email": "second@example.com"},
        "conventional_single": conventional,
        "conventional_two_buyers": {**conventional, "buyer2": "Second Buyer", "buyer2Email": "second@example.com", "asIs": "no", "repairsText": "Repair window", "homeWarrantyAmount": "700", "concessionAmount": "5000"},
        "hoa": {"hoa": "yes", "hoaDelivery": "seller", "hoaDeliveryDays": "7", "hoaTransferFeeCap": "0", "hoaName": "Example HOA"},
        "appraisal": {**conventional, "appraisalAddendum": "partialWaiver", "appraisalWaiverType": "partialWaiver", "appraisalMinimum": "475000"},
        "sale_of_other_property": {"saleContingency": "yes", "salePropertyAddress": "1 Sale St", "saleContingencyDate": "2026-08-01", "saleWaiverDays": "3", "saleAdditionalEarnest": "1000"},
        "backup_contract": backup,
        "all_supported_addenda": {**conventional, **backup, "buyer2": "Second Buyer", "buyer2Email": "second@example.com", "hoa": "yes", "hoaDelivery": "seller", "hoaDeliveryDays": "7", "hoaTransferFeeCap": "0", "hoaName": "Example HOA", "appraisalAddendum": "partialWaiver", "appraisalWaiverType": "partialWaiver", "appraisalMinimum": "475000", "saleContingency": "yes", "salePropertyAddress": "1 Sale St", "saleContingencyDate": "2026-08-01", "saleWaiverDays": "3", "saleAdditionalEarnest": "1000", "nonRealtyItems": "yes", "nonRealtyItemsAmount": "750", "nonRealtyItemsText": "Refrigerator"},
        "sparse_optional_fields": {"buyer2": "", "buyer2Email": "", "earnest": "", "optionFee": "", "optionDays": "", "survey": "noSurvey", "surveyDays": "", "objectionDays": "", "escrowAgent": "", "escrowAddress": "", "titleCompany": ""},
    }


def _image_hash(path):
    with Image.open(path) as image:
        normalized = image.convert("RGB")
        digest = hashlib.sha256(normalized.tobytes()).hexdigest()
        return {"width": normalized.width, "height": normalized.height, "sha256": digest}


def build_manifest(selected=None):
    if not POPPLER:
        raise RuntimeError("pdftoppm is required for golden packet rendering.")
    from tests.test_controlled_launch import configure_local_forms, minimal_offer
    from api import fill_pdf_20_19_production_adapter as adapter

    configure_local_forms()
    manifest = {"version": 1, "renderer": "pdftoppm", "max_width": 612, "scenarios": {}}
    with tempfile.TemporaryDirectory(prefix="hof-golden-render-") as tmp:
        tmp_path = Path(tmp)
        for name, overrides in _offer_scenarios().items():
            if selected and name != selected:
                continue
            print(f"Rendering {name}...", flush=True)
            offer = minimal_offer(**overrides)
            with contextlib.redirect_stdout(StringIO()):
                packet = adapter.fill_and_merge_20_19(offer)
                fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
            pdf_path = tmp_path / f"{name}.pdf"
            pdf_path.write_bytes(packet)
            prefix = tmp_path / name
            subprocess.run([POPPLER, "-scale-to-x", "612", "-scale-to-y", "-1", "-jpeg", "-jpegopt", "quality=80", str(pdf_path), str(prefix)], check=True, capture_output=True)
            pages = sorted(tmp_path.glob(f"{name}-*.jpg"))
            manifest["scenarios"][name] = {
                "page_count": len(PdfReader(BytesIO(packet)).pages),
                "field_ids": sorted(field["api_id"] for field in fields),
                "pages": [_image_hash(page) for page in pages],
            }
            for page in pages:
                page.unlink()
            pdf_path.unlink()
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true", help="Write a candidate manifest after visual approval.")
    parser.add_argument("--scenario", choices=sorted(_offer_scenarios()), help="Render one scenario; useful for local visual approval.")
    args = parser.parse_args()
    actual = build_manifest(args.scenario)
    if args.write_baseline:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if args.scenario and BASELINE_PATH.exists():
            existing = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
            existing["scenarios"].update(actual["scenarios"])
            actual = existing
        BASELINE_PATH.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote {BASELINE_PATH.relative_to(ROOT)}")
        return
    expected = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    if args.scenario:
        expected = {**expected, "scenarios": {args.scenario: expected["scenarios"].get(args.scenario)}}
    if actual != expected:
        raise SystemExit("Golden packet rendering changed. Review rendered PDFs before updating the approved baseline.")
    print("Golden packet rendering matches the approved baseline.")


if __name__ == "__main__":
    main()

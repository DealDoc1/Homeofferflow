#!/usr/bin/env python3
"""Render supported golden packets and compare page-level visual fingerprints.

Run with --write-baseline only after the rendered packets have received human
visual approval. The committed manifest intentionally contains hashes, not
customer data or PDFs.
"""

import argparse
import base64
import contextlib
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from io import BytesIO, StringIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "tests" / "fixtures" / "golden_packet_rendering.json"
POPPLER = shutil.which("pdftoppm")
LAYOUT_COLUMNS = 24
LAYOUT_ROWS = 32
MAX_LAYOUT_CELL_DELTA = 18
MAX_LAYOUT_MEAN_DELTA = 2.5
SIGNING_GEOMETRY_KEYS = (
    "api_id",
    "type",
    "page",
    "x",
    "y",
    "width",
    "height",
    "recipient_id",
    "required",
)

# Running a script by file path places ``scripts/`` on sys.path, not the
# repository root. Add the root explicitly so the documented command can
# import the controlled packet fixtures and production adapter.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
        "seller_temporary_lease": {
            "buyer2": "Second Buyer", "buyer2Email": "second@example.com",
            "buyerMailAddr": "721 Broderick Lane, Prosper, TX 75078", "buyerPhone": "2143649890",
            "seller": "Seller One and Seller Two",
            "seller1Name": "Seller One", "seller1Email": "seller1@example.com",
            "seller2Name": "Seller Two", "seller2Email": "seller2@example.com",
            "sellerMailAddr": "100 Seller Lane, Van Alstyne, TX 75495",
            "sellerPhone": "9725550134",
            "possession": "sellerTemporaryLease", "sellerTemporaryLease": "yes",
            "sellerTemporaryLeaseTerminationDate": "2026-08-31",
            "sellerTemporaryLeaseRentPerDay": "125",
            "sellerTemporaryLeaseDeposit": "1000",
            "sellerTemporaryLeaseUtilitiesPaidByBuyer": "Water and trash",
            "sellerTemporaryLeasePetsAllowed": "One dog under 40 pounds",
            "sellerTemporaryLeaseSpecialProvisions": "Tenant will maintain the yard and return all keys and garage remotes when possession is surrendered.",
            "sellerTemporaryLeaseHoldoverPerDay": "300",
        },
        # The historic buyer-temporary-lease signing packet lacked the
        # two-page lease attachment.  Keep the released attachment, its
        # two-buyer initials, and both execution rows in the visual baseline.
        "buyer_temporary_lease": {
            "buyer2": "Second Buyer", "buyer2Email": "second@example.com",
            "buyerMailAddr": "721 Broderick Lane, Prosper, TX 75078", "buyerPhone": "2143649890",
            "seller": "Seller One and Seller Two",
            "sellerMailAddr": "100 Seller Lane, Van Alstyne, TX 75495",
            "sellerPhone": "9725550134",
            "possession": "temporaryLease", "buyerTemporaryLease": "yes",
            "buyerTemporaryLeaseStartDate": "2026-08-01",
            "buyerTemporaryLeaseRentPerDay": "100",
            "buyerTemporaryLeaseTotalRent": "1400",
            "buyerTemporaryLeaseDeposit": "500",
            "buyerTemporaryLeaseUtilitiesPaidBySeller": "Water and trash",
            "buyerTemporaryLeasePetsAllowed": "One dog under 40 pounds",
            "buyerTemporaryLeaseSpecialProvisions": "Tenant will maintain the yard and return all keys and garage remotes at closing.",
            "buyerTemporaryLeaseHoldoverPerDay": "250",
        },
        "all_supported_addenda": {**conventional, **backup, "buyer2": "Second Buyer", "buyer2Email": "second@example.com", "hoa": "yes", "hoaDelivery": "seller", "hoaDeliveryDays": "7", "hoaTransferFeeCap": "0", "hoaName": "Example HOA", "appraisalAddendum": "partialWaiver", "appraisalWaiverType": "partialWaiver", "appraisalMinimum": "475000", "saleContingency": "yes", "salePropertyAddress": "1 Sale St", "saleContingencyDate": "2026-08-01", "saleWaiverDays": "3", "saleAdditionalEarnest": "1000", "nonRealtyItems": "yes", "nonRealtyItemsAmount": "750", "nonRealtyItemsText": "Refrigerator"},
        "sparse_optional_fields": {"buyer2": "", "buyer2Email": "", "earnest": "", "optionFee": "", "optionDays": "", "survey": "noSurvey", "surveyDays": "", "objectionDays": "", "escrowAgent": "", "escrowAddress": "", "titleCompany": ""},
    }


def _image_hash(path):
    with Image.open(path) as image:
        normalized = image.convert("RGB")
        digest = hashlib.sha256(normalized.tobytes()).hexdigest()
        # Raw pixel hashes are useful on the same renderer, but Poppler's
        # anti-aliasing varies slightly between macOS and Linux.  The reduced
        # grayscale layout grid keeps the regression check visual while
        # tolerating those harmless renderer differences. A moved field,
        # missing checkbox, or shifted signature region materially changes
        # one or more grid cells and still fails the check.
        grayscale = normalized.convert("L").resize((LAYOUT_COLUMNS, LAYOUT_ROWS), Image.Resampling.LANCZOS)
        return {
            "width": normalized.width,
            "height": normalized.height,
            "sha256": digest,
            "layout": base64.b64encode(bytes(grayscale.get_flattened_data())).decode("ascii"),
        }


def _cross_platform_visual_match(actual, expected):
    if actual.get("version") != expected.get("version"):
        return False, "manifest version changed"
    if actual.get("max_width") != expected.get("max_width"):
        return False, "render width changed"
    if set(actual.get("scenarios", {})) != set(expected.get("scenarios", {})):
        return False, "golden scenario set changed"

    for scenario_name, actual_scenario in actual["scenarios"].items():
        expected_scenario = expected["scenarios"][scenario_name]
        if actual_scenario["page_count"] != expected_scenario["page_count"]:
            return False, f"{scenario_name}: page count changed"
        if actual_scenario["field_ids"] != expected_scenario["field_ids"]:
            return False, f"{scenario_name}: signing field IDs changed"
        if actual_scenario.get("field_geometry") != expected_scenario.get("field_geometry"):
            return False, f"{scenario_name}: signing field placement changed"
        for page_number, (actual_page, expected_page) in enumerate(zip(actual_scenario["pages"], expected_scenario["pages"]), start=1):
            if (actual_page["width"], actual_page["height"]) != (expected_page["width"], expected_page["height"]):
                return False, f"{scenario_name} page {page_number}: rendered dimensions changed"
            try:
                actual_layout = base64.b64decode(actual_page.get("layout", ""), validate=True)
                expected_layout = base64.b64decode(expected_page.get("layout", ""), validate=True)
            except (ValueError, TypeError):
                return False, f"{scenario_name} page {page_number}: visual layout baseline is invalid"
            if len(actual_layout) != LAYOUT_COLUMNS * LAYOUT_ROWS or len(expected_layout) != LAYOUT_COLUMNS * LAYOUT_ROWS:
                return False, f"{scenario_name} page {page_number}: visual layout baseline is missing"
            deltas = [abs(current - approved) for current, approved in zip(actual_layout, expected_layout)]
            mean_delta = sum(deltas) / len(deltas)
            if mean_delta > MAX_LAYOUT_MEAN_DELTA or max(deltas, default=0) > MAX_LAYOUT_CELL_DELTA:
                return False, (
                    f"{scenario_name} page {page_number}: visual layout changed "
                    f"(mean delta {mean_delta:.2f}, max delta {max(deltas):.0f})"
                )
    return True, ""


def _field_geometry(fields):
    """Return a stable, privacy-safe signer-placement contract.

    The rendered page grid catches broad visual drift, but a signature or
    date widget can move within an otherwise identical page.  Store only the
    field identity, recipient role, required state, page, and rectangle—not
    names, emails, addresses, or any document data—so the approved golden
    suite catches those coordinate regressions too.
    """
    return [
        {key: field.get(key) for key in SIGNING_GEOMETRY_KEYS}
        for field in sorted(fields, key=lambda field: str(field.get("api_id") or ""))
    ]


def build_manifest(selected=None):
    if not POPPLER:
        raise RuntimeError("pdftoppm is required for golden packet rendering.")
    from tests.test_controlled_launch import configure_local_forms, minimal_offer
    from lib import production_adapter as adapter

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
                "field_geometry": _field_geometry(fields),
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
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help="Compare rendered page counts and field IDs without platform-specific image hashes (for CI).",
    )
    parser.add_argument(
        "--cross-platform",
        action="store_true",
        help="Compare approved rendered-page layout grids with cross-platform anti-aliasing tolerance.",
    )
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
    if args.structural_only:
        def structural(manifest):
            return {
                "version": manifest["version"],
                "renderer": manifest["renderer"],
                "max_width": manifest["max_width"],
                "scenarios": {
                    name: {
                        "page_count": scenario["page_count"],
                        "field_ids": scenario["field_ids"],
                        "field_geometry": scenario["field_geometry"],
                    }
                    for name, scenario in manifest["scenarios"].items()
                },
            }
        actual = structural(actual)
        expected = structural(expected)
    if args.cross_platform:
        matches, reason = _cross_platform_visual_match(actual, expected)
        if not matches:
            raise SystemExit("Golden packet visual layout changed: " + reason + ". Review rendered PDFs before updating the approved baseline.")
        print("Golden packet visual layout matches the approved baseline.")
        return
    if actual != expected:
        raise SystemExit("Golden packet rendering changed. Review rendered PDFs before updating the approved baseline.")
    print("Golden packet rendering matches the approved baseline.")


if __name__ == "__main__":
    main()

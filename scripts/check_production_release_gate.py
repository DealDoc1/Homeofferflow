#!/usr/bin/env python3
"""Run HomeOfferFlow's automated production-release preflight.

This command intentionally does not deploy. It confirms the code and rendered
golden-packet safeguards before one deliberate production deployment. Legal
form releases still require a separate broker-approved source and completed
signed-PDF visual QA; those gates cannot be truthfully automated.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ENTRYPOINT = ROOT / "api" / "fill-pdf.py"
CURRENT_CONTRACT = ROOT / "20-19_0.pdf"
GOLDEN_RENDER_CHECK = ROOT / "scripts" / "check_golden_packet_rendering.py"
SIGNWELL_STATUS_TEST = ROOT / "tests" / "test_signwell_status_api.js"


def run_step(label: str, command: list[str]) -> None:
    print(f"\n==> {label}")
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def check_published_contract_route() -> None:
    print("==> Published contract route")
    if not CURRENT_CONTRACT.is_file():
        raise SystemExit("Missing published TREC 20-19 contract PDF: 20-19_0.pdf")
    source = PRODUCTION_ENTRYPOINT.read_text(encoding="utf-8")
    if "fill_pdf_20_19_production_adapter" not in source:
        raise SystemExit("Production entrypoint is not routed through the TREC 20-19 production adapter.")
    print("Production route is configured for the TREC 20-19 adapter.")


def main() -> None:
    check_published_contract_route()
    run_step("Full automated test suite", [sys.executable, "-m", "unittest", "discover", "-s", "tests"])
    run_step("Signed-offer status endpoint regression", ["node", "--test", str(SIGNWELL_STATUS_TEST)])
    run_step("Rendered golden-packet regression", [sys.executable, str(GOLDEN_RENDER_CHECK)])

    print(
        "\nAutomated release gate passed. Before deploying a legal-form or packet change, "
        "also confirm the broker-approved source, signer plan, and completed-signature "
        "rendered PDF visual QA for every affected form."
    )


if __name__ == "__main__":
    main()

"""Prepare two fictional response-letter specimens; never access live services."""
import argparse
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader
from lib import trec_seller_disclosure as disclosure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.read_bytes()
    disclosure.validate_source_bytes("TREC-55-1", source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    cases = {
        "all-no": {key: "N" for key in disclosure.TREC_55_1_FEATURE_RESPONSES},
        "mixed-ynu": {key: ("Y", "N", "U")[i % 3]
                      for i, key in enumerate(disclosure.TREC_55_1_FEATURE_RESPONSES)},
    }
    for name, answers in cases.items():
        values = {"propertyAddress": "QA ONLY - 100 Fictional Example Lane", **answers}
        target = args.output_dir / (name + ".pdf")
        target.write_bytes(disclosure.render_unsigned_preview(
            source, "TREC-55-1", values, qa_mode=True))
        reader = PdfReader(target)
        if len(reader.pages) != 4:
            raise ValueError("Unexpected disclosure source page count")
        records.append({"case": name, "pages": len(reader.pages), "changed_pages": [1],
                        "answers": answers, "pdf_sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    manifest = {"source_sha256": hashlib.sha256(source).hexdigest(),
                "nothing_sent": True, "cases": records}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"cases": len(records), "response_lines": len(disclosure.TREC_55_1_FEATURE_RESPONSES),
                      "source_sha256": manifest["source_sha256"], "nothing_sent": True}))


if __name__ == "__main__":
    main()

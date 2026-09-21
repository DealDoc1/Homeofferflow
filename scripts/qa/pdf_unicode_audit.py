"""Offline purchase-packet character audit using synthetic names and terms.

Exit 1 means character preservation is not verified; never treats PDF creation
alone as success. Generated files stay in tmp and must not be committed.
"""
import json
from io import BytesIO
from pathlib import Path
import unicodedata

from pypdf import PdfReader

from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer


CASES = {
    "western_latin": "Example Jos\u00e9 Garc\u00eda O\u2019Brien",
    "combining_accents": "Example Jose\u0301 Garci\u0301a",
    "extended_latin": "Example \u0141ukasz Nguy\u1ec5n",
    "greek": "Example \u0391\u03bb\u03ad\u03be\u03b1\u03bd\u03b4\u03c1\u03bf\u03c2",
    "cyrillic": "Example \u0410\u043b\u0435\u043a\u0441\u0435\u0439",
    "cjk": "Example \u738b\u5c0f\u660e",
    "punctuation": "Example \u201cleft\u201d \u2014 \u00bd inch \u2265 3",
}


def canonical(text):
    # Compare equivalent composed/decomposed accents without ignoring missing
    # characters. PDF line wrapping is not a content loss.
    return " ".join(unicodedata.normalize("NFC", text).split())


def main():
    configure_local_forms()
    target = Path("tmp/pdfs/unicode-audit")
    target.mkdir(parents=True, exist_ok=True)
    results = []
    for key, value in CASES.items():
        terms = "\n".join(f"Item {i:02d}: Keep this complete synthetic instruction."
                          for i in range(1, 20)) + "\nFinal text: " + value
        offer = minimal_offer(buyer1=value, seller="Example QA Seller",
                              address="123 Example Street", city="Example City",
                              asIs="repairs", repairsText=terms)
        raw = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(raw))
        path = target / (key + ".pdf")
        path.write_bytes(raw)
        main_text = canonical(reader.pages[0].extract_text())
        continuation_text = canonical("\n".join(p.extract_text() for p in reader.pages[12:]))
        result = {
            "case": key,
            "expected": value,
            "main_party_text_preserved": canonical(value) in main_text,
            "continuation_final_text_preserved": canonical("Final text: " + value) in continuation_text,
            "pages": len(reader.pages),
            "pdf": str(path),
            "visual_qa": "required",
        }
        results.append(result)
        print(json.dumps(result, ensure_ascii=False))
    report = {"scope": "unsigned local purchase contract and repair continuation only", "results": results}
    (target / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    return 0 if all(r["main_party_text_preserved"] and r["continuation_final_text_preserved"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

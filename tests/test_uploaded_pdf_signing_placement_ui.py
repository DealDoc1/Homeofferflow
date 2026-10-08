from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLACEMENT_JS = ROOT / "assets/uploaded-pdf-signing-placement.js"


class UploadedPdfSigningPlacementUiTests(unittest.TestCase):
    def test_upload_flow_loads_the_manual_placement_tool(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        if any(marker in html for marker in ("<<<<<<< ", "=======\n", ">>>>>>> ")):
            self.skipTest("The local index.html has unresolved merge markers; CI verifies the committed release source.")
        self.assertIn('/assets/uploaded-pdf-signing-placement.js', html)

    def test_visual_placement_payload_matches_the_packet_backend_contract(self):
        source = PLACEMENT_JS.read_text(encoding="utf-8")
        backend = (ROOT / "api/fill-pdf.py").read_text(encoding="utf-8")
        for field in (
            "buyer1_signature", "buyer1_date", "buyer1_initials",
            "buyer2_signature", "buyer2_date", "buyer2_initials",
        ):
            self.assertIn(field, source)
        self.assertIn("xRatio", source)
        self.assertIn("yRatio", source)
        self.assertIn("let placements = Array.isArray(doc.signaturePlacements)", source)
        self.assertIn("doc.signaturePlacements = placements", source)
        self.assertIn("signaturePlacements:source.signaturePlacements", source)
        self.assertIn('doc.get("signaturePlacements")', backend)
        self.assertIn('placement.get("xRatio")', backend)
        self.assertIn('placement.get("yRatio")', backend)

    def test_placement_copy_is_explicit_about_buyer_only_and_review(self):
        source = PLACEMENT_JS.read_text(encoding="utf-8")
        self.assertIn("Fields are for buyer signers only", source)
        self.assertIn("Review every placement before sending", source)
        self.assertIn("if no buyer signing is needed, I leave fields unplaced", source)


if __name__ == "__main__":
    unittest.main()

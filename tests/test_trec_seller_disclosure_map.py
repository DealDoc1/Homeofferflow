import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "lib" / "trec_seller_disclosure.py"
SPEC = importlib.util.spec_from_file_location("trec_seller_disclosure", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

class TrecSellerDisclosureMapTests(unittest.TestCase):
    def test_source_contracts_are_explicit_and_gated(self):
        for code, pages in (("TREC-55-1", 4), ("TREC-61-0", 2)):
            contract = MODULE.source_contract(code)
            self.assertEqual(contract["page_count"], pages)
            self.assertEqual(contract["activation_status"], "pending_visual_qa")
            self.assertIn("property_address" if code == "TREC-55-1" else "property_address_page_1", contract["field_map"])

    def test_preview_requires_explicit_qa_mode(self):
        with self.assertRaisesRegex(ValueError, "qa_mode"):
            MODULE.render_unsigned_preview(b"%PDF", "TREC-55-1", {}, qa_mode=False)

    def test_unknown_form_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.source_contract("TREC-56-0")

if __name__ == "__main__":
    unittest.main()

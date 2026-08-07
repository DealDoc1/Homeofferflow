import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "lib" / "trec_seller_disclosure_schema.py"
SPEC = importlib.util.spec_from_file_location("trec_seller_disclosure_schema", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

class TrecSellerDisclosureSchemaTests(unittest.TestCase):
    def test_seller_and_purchaser_roles_are_separate(self):
        self.assertEqual(MODULE.schema_for("TREC-55-1")["signers"][0]["role"], "seller")
        self.assertEqual(MODULE.schema_for("TREC-55-1")["signers"][1]["purpose"], "receipt_acknowledgment")
        self.assertEqual(MODULE.schema_for("TREC-61-0")["signers"][0]["required"], True)

    def test_schema_has_all_pages_and_sections(self):
        for code, pages in (("TREC-55-1", 4), ("TREC-61-0", 2)):
            schema = MODULE.schema_for(code)
            self.assertEqual(schema["pages"], pages)
            self.assertTrue(schema["sections"])

    def test_unknown_response_fields_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            MODULE.validate_response_keys("TREC-55-1", {"not_a_real_field": "Y"})

    def test_known_response_fields_allowed(self):
        MODULE.validate_response_keys("TREC-55-1", {"property_address": "1438 Whitaker Road", "range": "Y", "conditions_explanation": "None"})

if __name__ == "__main__":
    unittest.main()

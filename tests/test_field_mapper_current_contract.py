import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class FieldMapperCurrentContractTests(unittest.TestCase):
    def test_internal_mapper_identifies_current_trec_20_19_contract(self):
        source = (ROOT / "field-mapper.html").read_text(encoding="utf-8")
        self.assertIn("current TREC 20-19 PDF", source)
        self.assertIn("trec_20-19.pdf", source)
        self.assertIn("TREC_20-19_DEBUG_FIELD_NAMES.pdf", source)
        self.assertIn("TREC_20-19_TEST_FILLED.pdf", source)
        self.assertNotIn("TREC 20-18 PDF", source)
        self.assertNotIn("trec_20-18.pdf", source)
        self.assertNotIn("TREC_20-18_", source)


if __name__ == "__main__":
    unittest.main()

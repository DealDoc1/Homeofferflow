from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (ROOT / "docs" / "TEXAS_AGENT_FORM_CATALOG.md").read_text(encoding="utf-8")


class TxrCatalogInventoryReconciliationTests(unittest.TestCase):
    def test_high_value_inventory_forms_are_explicitly_sequenced(self):
        for form_code in (
            "TXR-1503",
            "TXR-1505",
            "TXR-1925",
            "TXR-1958",
            "TXR-2517",
            "TXR-1904",
            "TXR-1902",
            "TXR-1945",
            "TXR-1950",
            "TXR-1912",
            "TXR-1407",
            "TXR-1421",
            "TXR-1420",
            "TXR-1502",
        ):
            self.assertIn(form_code, CATALOG)

    def test_inventory_reconciliation_keeps_source_and_signature_gates(self):
        self.assertIn("does not authorize", CATALOG)
        self.assertIn("production distribution", CATALOG)
        self.assertIn("completed signed-PDF QA", CATALOG)
        self.assertIn("release approval", CATALOG)


if __name__ == "__main__":
    unittest.main()

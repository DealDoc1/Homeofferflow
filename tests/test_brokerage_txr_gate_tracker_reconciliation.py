from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_brokerage_txr_gate_tracker_reconciliation.sql").read_text(encoding="utf-8")


class BrokerageTxrGateTrackerTests(unittest.TestCase):
    def test_tracker_records_live_gate_and_keeps_forms_source_gated(self):
        self.assertIn("9eb03b4 Secure brokerage Texas REALTORS authorization control", SQL)
        self.assertIn("9eb03b4 Explicit Texas REALTORS/NAR authorization gate", SQL)
        self.assertIn("completed signed visual QA", SQL)
        self.assertIn("No form is exposed, generated, sent, or signed", SQL)
        for slug in (
            "txr-1507-short-buyer-tenant-representation",
            "txr-1501-long-buyer-tenant-representation",
            "txr-1508-unrepresented-showing",
            "txr-1506-general-information-notice",
        ):
            self.assertIn(f"'{slug}'", SQL)


if __name__ == "__main__":
    unittest.main()

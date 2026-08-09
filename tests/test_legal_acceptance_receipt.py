from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class LegalAcceptanceReceiptTests(unittest.TestCase):
    def test_dashboard_receipt_reads_only_the_signed_in_users_policy_records(self):
        self.assertIn('id="hof-legal-acceptance-receipt-v1"', INDEX)
        self.assertIn(".from('hof_legal_acceptances')", INDEX)
        self.assertIn(".select('policy_version, source, accepted_at')", INDEX)
        self.assertIn(".order('accepted_at', { ascending: false })", INDEX)
        self.assertIn(".limit(5)", INDEX)

    def test_receipt_explains_empty_and_temporary_failure_states(self):
        self.assertIn("Your acceptance receipt will appear here", INDEX)
        self.assertIn("Your acceptance receipt is temporarily unavailable.", INDEX)


if __name__ == "__main__":
    unittest.main()

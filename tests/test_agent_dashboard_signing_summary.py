from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AgentDashboardSigningSummaryTests(unittest.TestCase):
    def test_completed_signatures_do_not_count_as_pending(self):
        start = HTML.index("const pendingSignatureCount = safeOffers.filter")
        end = HTML.index("const draftCount", start)
        summary = HTML[start:end]

        self.assertIn("status.includes('awaiting')", summary)
        self.assertIn("status.includes('viewed')", summary)
        self.assertIn("status.includes('partial')", summary)
        self.assertNotIn("status.includes('signed')", summary)

    def test_dashboard_labels_signature_attention_clearly(self):
        self.assertIn("Signatures pending", HTML)
        self.assertIn("awaiting, viewed, or partially signed", HTML)


if __name__ == "__main__":
    unittest.main()

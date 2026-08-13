from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class SellerFollowUpPriorityTests(unittest.TestCase):
    def test_new_urgent_seller_requests_are_visibly_prioritized(self):
        self.assertIn("function sellerLeadFollowUpPriority(row)", HTML)
        self.assertIn("timeline === 'asap' ? 0", HTML)
        self.assertIn("timeline === '30_days' ? 1", HTML)
        self.assertIn("Priority: ASAP", HTML)
        self.assertIn("Priority: 30 days", HTML)

    def test_follow_up_queue_uses_priority_without_promising_a_response_time(self):
        self.assertIn("function prioritizeSellerFollowUpQueue(rows)", HTML)
        self.assertIn("prioritizeSellerFollowUpQueue(sellerLeads).slice(0, 24)", HTML)
        self.assertIn("internal follow-up priority, not a response-time promise", HTML)


from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BillingReturnRefreshTests(unittest.TestCase):
    def test_billing_portal_return_refreshes_authoritative_access_state(self):
        self.assertIn("async function checkBillingReturn()", HTML)
        self.assertIn("params.get('billing') !== 'returned'", HTML)
        self.assertIn("await loadOrCreateSubscription();", HTML)
        self.assertIn("await loadCurrentUsage();", HTML)
        self.assertIn("Billing settings refreshed.", HTML)

    def test_billing_return_is_registered_and_cleans_query_string(self):
        self.assertIn("typeof checkBillingReturn === 'function'", HTML)
        self.assertIn("window.__hofBillingReturn = true;", HTML)
        self.assertIn("window.history.replaceState({}, document.title, window.location.origin + window.location.pathname);", HTML)


if __name__ == "__main__":
    unittest.main()

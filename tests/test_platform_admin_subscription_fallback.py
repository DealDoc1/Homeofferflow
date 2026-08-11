import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class PlatformAdminSubscriptionFallbackTests(unittest.TestCase):
    def test_platform_admin_fallback_is_free_admin_only_for_platform_admins(self):
        marker = "root.loadOrCreateSubscription = async function loadSubscription()"
        start = INDEX.index(marker)
        end = INDEX.index("const priorSubscriptionRender", start)
        segment = INDEX[start:end]
        self.assertIn("const platformAdmin = typeof root.isCurrentAdmin === 'function' && root.isCurrentAdmin();", segment)
        self.assertIn("status: platformAdmin ? 'free_admin' : 'inactive'", segment)
        self.assertIn("does not grant free access to brokerage administrators or agents", segment)
        self.assertNotIn("brokerage_admin", segment)

    def test_platform_admin_allowlist_is_separate_from_brokerage_role_access(self):
        allowlist_start = INDEX.index("const HOF_ADMIN_EMAILS")
        allowlist_end = INDEX.index("];", allowlist_start) + 2
        allowlist = INDEX[allowlist_start:allowlist_end]
        self.assertIn("const HOF_ADMIN_EMAILS", allowlist)
        self.assertNotIn("brokerage_admin", allowlist)

    def test_free_admin_dashboard_access_is_not_presented_as_customer_billing(self):
        card_start = INDEX.index("function renderSubscriptionCard()")
        card_end = INDEX.index("function renderMyOffers", card_start)
        card = INDEX[card_start:card_end]
        self.assertIn("const isInternalAdminAccess = status === 'free_admin';", card)
        self.assertIn("Your internal platform access is active.", card)
        self.assertIn("Platform Access", card)
        self.assertNotIn("isPaid = ['active', 'trialing', 'free_admin']", card)

    def test_brokerage_admin_identity_is_not_a_platform_admin_bypass(self):
        allowlist_start = INDEX.index("const HOF_ADMIN_EMAILS")
        allowlist_end = INDEX.index("];", allowlist_start) + 2
        allowlist = INDEX[allowlist_start:allowlist_end].lower()
        self.assertNotIn("tyler@ondemanddfw.com", allowlist)

        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8").lower()
        default_admin_start = backend.index("default_admin_emails")
        default_admin_end = backend.index("}", default_admin_start) + 1
        default_admins = backend[default_admin_start:default_admin_end]
        self.assertNotIn("tyler@ondemanddfw.com", default_admins)


if __name__ == "__main__":
    unittest.main()

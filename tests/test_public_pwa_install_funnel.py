from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
SCRIPT = (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8")


class PublicPwaInstallFunnelTests(unittest.TestCase):
    def test_public_install_endpoint_is_allowlisted_and_aggregate_only(self):
        self.assertIn("PUBLIC_PWA_INSTALL_EVENT_TYPES", API)
        self.assertIn("def _record_public_pwa_install_event(data):", API)
        self.assertIn("Unsupported public PWA install event.", API)
        self.assertIn("Unsupported public PWA install platform.", API)
        self.assertIn("Unsupported public PWA install surface.", API)
        self.assertIn("public_pwa_install_event", API)
        self.assertIn('"public": True', API)
        self.assertIn('"/texas-home-service-partner-guide"', API)

    def test_public_install_script_records_platform_and_surface_without_identity(self):
        self.assertIn("trackPublicInstallEvent", SCRIPT)
        self.assertIn("public_pwa_install_event", SCRIPT)
        self.assertIn("publicInstallPlatform", SCRIPT)
        self.assertIn("window.location.pathname", SCRIPT)
        self.assertIn("sessionStorage", SCRIPT)
        self.assertNotIn("user_id", SCRIPT)

    def test_admin_exposes_platform_and_public_surface_install_counts(self):
        self.assertIn("pwaInstallPlatformCounts", ADMIN)
        self.assertIn("pwa_install_platform_counts", ADMIN)
        self.assertIn("/texas-agent-form-library", ADMIN)
        self.assertIn("/texas-home-service-partner-guide", ADMIN)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
PWA = (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8")
METRICS = (ROOT / "assets" / "fsbo-closing-checklist-metrics.js").read_text(encoding="utf-8")


class FsboClosingChecklistFunnelTests(unittest.TestCase):
    def test_checklist_records_only_allowlisted_aggregate_funnel_stages(self):
        self.assertIn("fsbo_closing_checklist_viewed", METRICS)
        self.assertIn("fsbo_closing_checklist_cta_selected", METRICS)
        self.assertIn("fsbo_closing_checklist", METRICS)
        self.assertIn("sessionStorage.getItem(key)", METRICS)
        self.assertIn("keepalive: true", METRICS)
        self.assertNotIn("location.href", METRICS)
        self.assertNotIn("document.referrer", METRICS.lower())
        self.assertNotIn("seller_email", METRICS.lower())
        self.assertNotIn("address", METRICS.lower())

    def test_api_accepts_only_the_closing_checklist_aggregate_surface(self):
        self.assertIn('"fsbo_closing_checklist_viewed": "viewed"', API)
        self.assertIn('"fsbo_closing_checklist_cta_selected": "selected"', API)
        self.assertIn('"fsbo_closing_checklist" if event_type.startswith("fsbo_closing_checklist_")', API)
        self.assertIn('"fsbo_closing_checklist"', API)

    def test_public_page_uses_the_shared_low_cost_loader_and_admin_can_measure_conversion(self):
        self.assertIn("window.location.pathname === '/texas-fsbo-closing-checklist'", PWA)
        self.assertIn("/assets/fsbo-closing-checklist-metrics.js", PWA)
        for metric in (
            "fsboClosingChecklistViewCount",
            "fsboClosingChecklistCtaCount",
            "fsboClosingChecklistCtaRate",
            "fsboClosingChecklistPackageCtaCounts",
        ):
            self.assertIn(metric, ADMIN)


if __name__ == "__main__":
    unittest.main()

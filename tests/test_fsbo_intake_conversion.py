from pathlib import Path
import re
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class FsboIntakeConversionTests(unittest.TestCase):
    def test_minimum_viable_seller_request_is_clear_and_accessible(self):
        self.assertIn("Start in under a minute.", HTML)
        self.assertIn("Property address and email are all we need", HTML)
        self.assertIn('id="fsboPropertyAddress"', HTML)
        self.assertIn('id="fsboSellerEmail"', HTML)
        self.assertGreaterEqual(HTML.count('aria-required="true"'), 2)
        self.assertIn("Seller Name <span", HTML)
        self.assertIn("Phone <span", HTML)
        self.assertIn("Target Asking Price <span", HTML)
        self.assertIn("Save My Seller Request", HTML)

    def test_seller_funnel_events_are_analytics_only_and_never_include_identity(self):
        start = HTML.index("const fsboFunnel =")
        end = HTML.index("const __oldOpenAccountDashboardFsbo", start)
        script = HTML[start:end]

        for event in (
            "FSBO Seller Intake Opened",
            "FSBO Seller Intake Required Fields Ready",
            "FSBO Seller Package Selected",
            "FSBO Seller Request Submission Started",
            "FSBO Seller Request Saved",
            "FSBO Seller Request Save Failed",
        ):
            self.assertIn(event, script)

        self.assertIn("trackEvent(name, data)", script)
        tracked_arguments = "\n".join(re.findall(r"trackFsboFunnel\\(([^;]+)\\);", script))
        self.assertNotIn("sellerEmail", tracked_arguments)
        self.assertNotIn("seller_email", tracked_arguments)
        self.assertNotIn("propertyAddress", tracked_arguments)
        self.assertNotIn("property_address", tracked_arguments)

    def test_restoring_a_draft_does_not_inflate_package_selection_analytics(self):
        self.assertIn("window.selectFsboNeed?.(draft.fsboNeed, false)", HTML)
        self.assertIn("function(key, shouldTrack = true)", HTML)
        self.assertIn("if (shouldTrack) trackFsboFunnel", HTML)


if __name__ == "__main__":
    unittest.main()

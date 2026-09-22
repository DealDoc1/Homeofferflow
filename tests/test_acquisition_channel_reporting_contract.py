import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
PARTNER_FOCUS = (ROOT / "assets" / "partner-landing-focus.js").read_text(encoding="utf-8")
PARTNER_GUIDE = (ROOT / "assets" / "partner-guide-metrics.js").read_text(encoding="utf-8")


def quoted_values_after(source, marker, closing):
    start = source.index(marker) + len(marker)
    end = source.index(closing, start)
    return set(re.findall(r'["\']([^"\']+)["\']', source[start:end]))


class AcquisitionChannelReportingContractTests(unittest.TestCase):
    def test_admin_channel_breakdowns_cover_every_accepted_backend_channel(self):
        contracts = (
            ("PARTNER_LANDING_CHANNELS = {", "partner_landing_channels = ("),
            ("ONDEMAND_LANDING_CHANNELS = {", "ondemand_landing_channels = ("),
            ("HOMEBUYER_LANDING_CHANNELS = {", "homebuyer_landing_channels = ("),
            ("AGENT_LANDING_CHANNELS = {", "agent_landing_channels = ("),
            ("INVESTOR_LANDING_CHANNELS = {", "investor_landing_channels = ("),
            ("FSBO_LANDING_CHANNELS = {", "seller_landing_channels = ("),
        )
        for api_marker, admin_marker in contracts:
            with self.subTest(api_marker=api_marker):
                accepted = quoted_values_after(API, api_marker, "}")
                reported = quoted_values_after(ADMIN, admin_marker, ")")
                self.assertEqual(accepted, reported)

    def test_partner_post_load_events_preserve_homepage_and_receipt_attribution(self):
        self.assertIn("'homepage'", PARTNER_FOCUS)
        self.assertIn("rawSource === 'homeofferflow'", PARTNER_FOCUS)
        self.assertIn("rawMedium === 'partner_receipt'", PARTNER_FOCUS)

    def test_partner_guide_preserves_owned_directory_attribution(self):
        self.assertIn("const rawMedium", PARTNER_GUIDE)
        self.assertIn("rawMedium === 'owned_directory'", PARTNER_GUIDE)
        self.assertIn("? 'owned_directory'", PARTNER_GUIDE)


if __name__ == "__main__":
    unittest.main()

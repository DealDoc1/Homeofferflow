import unittest

from lib.partner_directory_metrics import build_readiness_traffic_by_placement


class PartnerDirectoryMetricsTests(unittest.TestCase):
    def test_build_readiness_counts_are_aggregated_by_active_placement(self):
        events = [
            {"event_type": "partner_directory_impression", "metadata": {"partnerId": "builder-1", "directorySurface": "build_readiness"}},
            {"event_type": "partner_directory_impression", "metadata": {"partnerId": "builder-1", "directorySurface": "build_readiness"}},
            {"event_type": "partner_directory_outbound_click", "metadata": {"partnerId": "builder-1", "directorySurface": "build_readiness"}},
            {"event_type": "partner_directory_impression", "metadata": {"partnerId": "builder-2", "directorySurface": "build_readiness"}},
            {"event_type": "partner_directory_outbound_click", "metadata": {"partnerId": "retired-builder", "directorySurface": "build_readiness"}},
            {"event_type": "partner_directory_impression", "metadata": {"partnerId": "builder-1", "directorySurface": "public_directory"}},
            {"event_type": "other_event", "metadata": {"partnerId": "builder-1", "directorySurface": "build_readiness"}},
        ]

        totals, placements = build_readiness_traffic_by_placement(events, {"builder-1", "builder-2"})

        self.assertEqual(totals, {"impressions": 3, "outboundClicks": 2})
        self.assertEqual(placements["builder-1"], {"impressions": 2, "outboundClicks": 1})
        self.assertEqual(placements["builder-2"], {"impressions": 1, "outboundClicks": 0})
        self.assertNotIn("retired-builder", placements)

    def test_empty_or_malformed_events_produce_zero_counts(self):
        totals, placements = build_readiness_traffic_by_placement([None, {}, {"metadata": None}], ["builder-1"])

        self.assertEqual(totals, {"impressions": 0, "outboundClicks": 0})
        self.assertEqual(placements, {"builder-1": {"impressions": 0, "outboundClicks": 0}})


if __name__ == "__main__":
    unittest.main()

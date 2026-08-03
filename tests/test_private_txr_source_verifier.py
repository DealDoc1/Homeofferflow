import unittest

from scripts.verify_private_txr_sources import EXPECTED


class PrivateTxrSourceVerifierTests(unittest.TestCase):
    def test_inventory_matches_the_authorized_source_handoff(self):
        self.assertEqual(set(EXPECTED), {"TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"})
        for item in EXPECTED.values():
            self.assertTrue(item["filename"].endswith(".pdf"))
            self.assertGreater(item["pages"], 0)
            self.assertRegex(item["revision"], r"^\d{2}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260908164000_expand_standalone_agreement_forms_and_parties.sql"
).read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class StandaloneAgreementSchemaContractTests(unittest.TestCase):
    def test_live_form_allowlist_matches_released_draft_forms(self):
        for form_code in (
            "TXR-1501",
            "TXR-1506",
            "TXR-1507",
            "TXR-1508",
            "TXR-1905",
            "TXR-1914",
            "TXR-1917",
            "TXR-1919",
            "TXR-1948",
            "TXR-1953",
            "TXR-1954",
        ):
            self.assertIn(f"'{form_code}'", MIGRATION)

    def test_schema_accepts_two_buyers_and_two_sellers(self):
        self.assertIn("jsonb_array_length(client_names) between 1 and 4", MIGRATION)

    def test_new_signing_forms_describe_the_real_next_step(self):
        self.assertIn("send it to the named Buyers and Sellers for signature", HTML)
        self.assertIn("before I send it for signature", HTML)
        self.assertNotIn("It does not advise on leases, send, or sign the addendum", HTML)


if __name__ == "__main__":
    unittest.main()

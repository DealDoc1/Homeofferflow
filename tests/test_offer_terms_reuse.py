from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class OfferTermsReuseTests(unittest.TestCase):
    def setUp(self):
        start = HTML.index("async function reuseOfferTerms(id)")
        end = HTML.index("\n  async function deleteOffer", start)
        self.body = HTML[start:end]

    def test_terms_reuse_uses_a_restrictive_allow_list(self):
        self.assertIn("const reusableTermKeys = [", self.body)
        self.assertIn("reusableTermKeys.reduce", self.body)
        self.assertNotIn("const termData = { ...source }", self.body)

        for reusable_key in (
            "'financing'",
            "'loanYears'",
            "'appraisalAddendum'",
            "'titlePayer'",
            "'survey'",
            "'asIs'",
        ):
            self.assertIn(reusable_key, self.body)

    def test_terms_reuse_resets_prior_offer_identity_and_uploaded_documents(self):
        self.assertIn("_hofOfferId: null", self.body)
        self.assertIn("resetUploadedDisclosureDraftForOffer({});", self.body)
        self.assertIn("client and property details cleared", self.body)
        self.assertIn("reuse_mode: 'terms_only'", self.body)

    def test_terms_reuse_does_not_allow_list_prior_party_property_or_money_fields(self):
        for sensitive_key in (
            "'buyer1'",
            "'buyerEmail'",
            "'seller1Name'",
            "'address'",
            "'legalDescription'",
            "'price'",
            "'closingDate'",
            "'signwellDocumentId'",
        ):
            self.assertNotIn(sensitive_key, self.body)

    def test_workspace_exposes_terms_only_start_without_removing_full_duplicate(self):
        self.assertIn("Reuse Last Terms", HTML)
        self.assertIn("Keep deal choices; clear client and property details.", HTML)
        self.assertIn("hofReuseTermsFromMostRecentOffer", HTML)
        self.assertIn("root.reuseOfferTerms(offers[0].id)", HTML)
        self.assertGreaterEqual(HTML.count('>Reuse terms</button>'), 2)
        self.assertIn("Duplicate &amp; edit", HTML)


if __name__ == "__main__":
    unittest.main()

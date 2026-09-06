from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class ExplicitMaterialTermsTests(unittest.TestCase):
    def test_interview_does_not_apply_material_term_defaults(self):
        body = re.search(
            r"function applySmartDefaults\(\) \{(?P<body>.*?)\n  \}",
            HTML,
            re.DOTALL,
        ).group("body")

        self.assertNotIn("setDefaultValue(", body)
        self.assertNotIn("setRadioDefault(", body)
        self.assertNotIn("setRadioValue(", body)
        self.assertIn("updateSurveyExistingDetails(getRadio('survey') || '')", body)

    def test_title_amendment_starts_unselected(self):
        amendment = re.search(
            r'<input type="radio" name="titleAmendment" value="ii_buyer"[^>]*>',
            HTML,
        ).group(0)
        self.assertNotIn("checked", amendment)
        self.assertNotIn('radio-card selected" onclick="selectCard(this,\'titleAmendment\'', HTML)

    def test_financing_and_addendum_inputs_start_blank(self):
        for field in (
            'id="loanYears" value=',
            'id="interestRateCap" value=',
            'id="interestFirstYears" value=',
            'id="originationCap" value=',
            'id="buyerApprovalDays" value=',
            'id="hoaDays" value=',
            'id="hoaReserves" value=',
            'id="saleWaiverDays" value=',
            'id="bkupAdditionalDays" value=',
            'id="disclosureDays" value=',
        ):
            self.assertNotIn(field, HTML)

        for select in (
            'id="hoaSubdivisionInfo"><option value="">Select...</option>',
            'id="hoaTitleCost"><option value="">Select...</option>',
            'id="surveyIfRejectedPaidBy"><option value="">Select...</option>',
        ):
            self.assertIn(select, HTML)

    def test_material_choices_are_required_before_review(self):
        for group in (
            "hoa",
            "saleContingency",
            "backupOffer",
            "nonRealtyItems",
            "titlePayer",
            "titleAmendment",
            "survey",
            "sellerDisclosure",
            "asIs",
            "financing",
            "appraisalAddendum",
            "brokerFeeType",
            "wantsConcessions",
            "homeWarranty",
        ):
            self.assertIn(f"requireRadioSelection('{group}'", HTML)

    def test_packet_data_does_not_restore_silent_material_defaults(self):
        for fallback in (
            "s.titlePayer = getRadio('titlePayer') || 'seller'",
            "s.titleAmendment = getRadio('titleAmendment') || 'ii_buyer'",
            "s.survey = getRadio('survey') || 'sellerExisting'",
            "s.sellerDisclosure = getRadio('sellerDisclosure') || 'received'",
            "s.asIs = getRadio('asIs') || 'yes'",
            "s.possession = getVal('possession') || 'funding'",
            "s.optionFee = moneyNumber(getVal('optionFee')) || 250",
            "s.optionDays = getVal('optionDays') || '7'",
            "s.hasBuyerAgent = (s.userType === 'agent') ? 'yes' : (agentRadio || s.hasBuyerAgent || 'no')",
            "s.homeWarranty = getRadio('homeWarranty') || 'no'",
            "s.homeWarrantyAmount = s.homeWarranty === 'yes' ? (moneyNumber(getVal('homeWarrantyAmount')) || 650) : ''",
        ):
            self.assertNotIn(fallback, HTML)

    def test_manual_yes_choices_do_not_insert_a_home_warranty_amount(self):
        home_warranty = HTML[HTML.index("if (group === 'homeWarranty')"):HTML.index("  }\n\n  function nextBusinessDay", HTML.index("if (group === 'homeWarranty')"))]
        self.assertNotIn("setDefaultValue('homeWarrantyAmount'", home_warranty)
        self.assertIn("requireField('homeWarrantyAmount', 'home warranty amount', missing)", HTML)

    def test_review_does_not_label_a_missing_choice_as_a_substantive_term(self):
        for fallback in (
            "s.titlePayer === 'seller' ? 'Seller (standard)' : 'Buyer'",
            "s.survey === 'sellerExisting' ? 'Seller provides existing' : s.survey === 'buyerNew' ? 'Buyer orders new' : 'No survey'",
            "s.surveyIfRejectedPaidBy === 'buyer' ? 'Buyer' : 'Seller'",
            "s.sellerDisclosure === 'received' ? 'Received' : s.sellerDisclosure === 'notReceived' ? `Not received — ${s.disclosureDays} days` : 'Seller exempt'",
            "s.asIs === 'yes' ? 'As Is' : 'As Is with repairs'",
            "fmtM(s.homeWarrantyAmount || 650)",
        ):
            self.assertNotIn(fallback, HTML)


if __name__ == "__main__":
    unittest.main()

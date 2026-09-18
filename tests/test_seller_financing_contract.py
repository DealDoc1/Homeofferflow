import unittest

from lib.seller_financing import SOURCE_SHA256, purchase_terms, validate_terms


def canonical_terms(**changes):
    data = {
        "credit_days": "7",
        "credit_documents": ["credit_report", "employment", "other"],
        "credit_other": "2025 tax return",
        "note_amount": "250000.50",
        "interest_rate": "6.25",
        "payment": {
            "plan": "monthly_installments",
            "installment_amount": "1800.25",
            "interest_style": "including_interest",
            "begins_after_months": "1",
            "payoff_after_months": "180",
        },
        "property_transfer": "consent_required",
        "casualty_insurance": "required",
        "escrow": {"choice": "required", "third_party_servicer": "will", "cost_paid_by": "buyer"},
    }
    data.update(changes)
    return data


class SellerFinancingContractTests(unittest.TestCase):
    def test_source_identity_is_fixed_to_the_reviewed_two_page_form(self):
        self.assertEqual(SOURCE_SHA256, "a331f1fab915b749639895fb6083c17291cd0964f4cf6327480c54f6dcffd9f9")

    def test_canonical_terms_preserve_cents_and_conditional_choices(self):
        result = validate_terms(canonical_terms())
        self.assertEqual(result["note_amount"], "250,000.50")
        self.assertEqual(result["payment"]["installment_amount"], "1,800.25")
        self.assertEqual(result["escrow"], {
            "choice": "required", "third_party_servicer": "will", "cost_paid_by": "buyer"})

    def test_one_payment_omits_inapplicable_installment_answers(self):
        result = validate_terms(canonical_terms(payment={
            "plan": "one_payment", "due_after_months": "0", "interest_timing": "maturity",
            "installment_amount": "999",
        }))
        self.assertEqual(result["payment"], {
            "plan": "one_payment", "due_after_months": "0", "interest_timing": "maturity"})

    def test_no_escrow_omits_hidden_servicer_answers(self):
        result = validate_terms(canonical_terms(escrow={
            "choice": "not_required", "third_party_servicer": "will", "cost_paid_by": "seller"}))
        self.assertEqual(result["escrow"], {"choice": "not_required"})

    def test_purchase_fields_translate_to_the_same_contract(self):
        offer = {
            "sellerFinancingCreditDays": "7",
            "sellerFinancingCreditDocuments": ["credit_report", "employment", "other"],
            "sellerFinancingCreditOther": "2025 tax return",
            "sellerFinancingNoteAmount": "250000.50",
            "sellerFinancingInterestRate": "6.25",
            "sellerFinancingPaymentPlan": "monthly_installments",
            "sellerFinancingInstallmentAmount": "1800.25",
            "sellerFinancingInstallmentInterestStyle": "including_interest",
            "sellerFinancingInstallmentBeginsAfterMonths": "1",
            "sellerFinancingPayoffAfterMonths": "180",
            "sellerFinancingPropertyTransfer": "consent_required",
            "sellerFinancingCasualtyInsurance": "required",
            "sellerFinancingEscrow": "required",
            "sellerFinancingThirdPartyServicer": "will",
            "sellerFinancingEscrowCostPaidBy": "buyer",
        }
        self.assertEqual(purchase_terms(offer), validate_terms(canonical_terms()))

    def test_invalid_or_missing_conditional_answers_fail_closed(self):
        cases = [
            ({"credit_documents": []}, "credit-documentation"),
            ({"note_amount": "250000.555"}, "promissory-note"),
            ({"interest_rate": "101"}, "annual interest"),
            ({"payment": {"plan": "one_payment", "due_after_months": "1", "interest_timing": ""}}, "interest is payable"),
            ({"payment": {"plan": "monthly_installments", "installment_amount": "1800", "interest_style": "", "begins_after_months": "1", "payoff_after_months": "180"}}, "installment includes"),
            ({"escrow": {"choice": "required", "third_party_servicer": "", "cost_paid_by": "buyer"}}, "third-party escrow"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, message):
                validate_terms(canonical_terms(**changes))

    def test_other_credit_documentation_is_limited_to_the_source_blank(self):
        with self.assertRaisesRegex(ValueError, "180 characters"):
            validate_terms(canonical_terms(credit_other="x" * 181))


if __name__ == "__main__":
    unittest.main()

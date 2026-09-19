"""Seller-financing purchase packet foundation; synthetic parties and sources only."""
import hashlib
from io import BytesIO
import unittest
from unittest.mock import patch

import pdfplumber
from pypdf import PdfReader

from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms, minimal_offer
from tests.test_txr_1914_renderer import blank_pdf


SOURCE = blank_pdf()


def seller_financing_offer(**changes):
    offer = minimal_offer(
        financing="seller financing",
        price="500000.55",
        loanAmount="1",
        downPayment="1",
        seller1Name="QA Seller",
        seller1Email="seller@example.test",
        sellerFinancingCreditDays="7",
        sellerFinancingCreditDocuments=["credit_report"],
        sellerFinancingNoteAmount="250000.50",
        sellerFinancingInterestRate="6.25",
        sellerFinancingPaymentPlan="monthly_installments",
        sellerFinancingInstallmentAmount="1800.25",
        sellerFinancingInstallmentInterestStyle="including_interest",
        sellerFinancingInstallmentBeginsAfterMonths="1",
        sellerFinancingPayoffAfterMonths="180",
        sellerFinancingPropertyTransfer="consent_required",
        sellerFinancingCasualtyInsurance="required",
        sellerFinancingEscrow="required",
        sellerFinancingThirdPartyServicer="will",
        sellerFinancingEscrowCostPaidBy="buyer",
        _paragraph4_source_pdf_bytes={"TXR-1914": SOURCE},
    )
    offer.update(changes)
    return offer


class SellerFinancingPurchasePacketTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()
        guard = patch.object(
            adapter, "SELLER_FINANCING_SOURCE_SHA256", hashlib.sha256(SOURCE).hexdigest()
        )
        guard.start()
        self.addCleanup(guard.stop)

    def test_exact_note_amount_drives_main_contract_and_appends_txr_1914(self):
        offer = seller_financing_offer()
        raw = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(offer["financing"], "seller_financing")
        self.assertEqual(offer["loanAmount"], "250000.50")
        self.assertEqual(offer["downPayment"], "250000.05")
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages), 14)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            page_one_marks = [
                char for char in pdf.pages[0].chars
                if char["text"] == "X" and 252 <= char["x0"] <= 263 and 510 <= char["top"] <= 526
            ]
            paragraph_22_marks = [
                char for char in pdf.pages[8].chars
                if char["text"] == "X" and 59 <= char["x0"] <= 70 and 151 <= char["top"] <= 168
            ]
            self.assertEqual(len(page_one_marks), 1)
            self.assertEqual(len(paragraph_22_marks), 1)

    def test_txr_1914_fields_keep_buyer_and_seller_recipient_ids(self):
        offer = seller_financing_offer()
        raw = adapter.fill_and_merge_20_19(offer)
        fields = [
            field for field in adapter.build_signwell_fields_20_19(offer, raw)[0]
            if field["api_id"].startswith("txr1914")
        ]
        self.assertEqual({field["page"] for field in fields if field["type"] == "initials"}, {13})
        self.assertEqual({field["page"] for field in fields if field["type"] == "signature"}, {14})
        self.assertEqual({field["recipient_id"] for field in fields}, {"1", "3"})
        self.assertEqual(
            offer["_signing_render_revisions"]["TXR-1914"], adapter.SELLER_FINANCING_RENDER_REVISION
        )

    def test_invalid_terms_source_or_amount_fail_before_core_rendering(self):
        cases = [
            {"sellerFinancingCreditDays": "0"},
            {"sellerFinancingCreditDocuments": []},
            {"sellerFinancingInterestRate": "101"},
            {"sellerFinancingNoteAmount": "600000"},
            {"seller1Email": "bad"},
            {"_paragraph4_source_pdf_bytes": {"TXR-1914": b"wrong"}},
        ]
        for changes in cases:
            with self.subTest(changes=changes), patch.object(adapter.verified, "fill_and_merge") as render:
                with self.assertRaises(adapter.UnsupportedOfferPathError):
                    adapter.fill_and_merge_20_19(seller_financing_offer(**changes))
                render.assert_not_called()


if __name__ == "__main__":
    unittest.main()

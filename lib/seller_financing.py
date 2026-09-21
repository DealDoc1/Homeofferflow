"""Shared validation for source-bound TXR-1914 seller-financing terms.

The module is intentionally independent of HTTP, browser, storage, payment and
PDF code so the same contract can serve the web interview and a future app.
It validates only choices printed on TXR-1914; it does not create loan
documents, assess credit, or recommend financing terms.
"""
from decimal import Decimal
import re


SOURCE_SHA256 = "a331f1fab915b749639895fb6083c17291cd0964f4cf6327480c54f6dcffd9f9"

ALLOWED_CREDIT_DOCUMENTS = (
    "credit_report", "employment", "funds", "financial_statement", "other",
)
PAYMENT_PLANS = (
    "one_payment", "monthly_installments", "interest_only_then_installments",
)


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _whole_number(value, label, *, allow_zero=False):
    value = str(value or "").strip()
    if not re.fullmatch(r"\d{1,3}", value) or (not allow_zero and int(value) < 1):
        qualifier = "0 to 999" if allow_zero else "1 to 999"
        raise ValueError(f"Enter {label} from {qualifier} months.")
    return str(int(value))


def _money(value, label, *, positive=False):
    raw = str(value if value is not None else "").strip()
    if not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?", raw):
        raise ValueError(f"Enter a valid {label}, with no more than two decimal places.")
    amount = Decimal(raw.replace(",", ""))
    if amount > Decimal("999999999.99") or (positive and amount <= 0):
        raise ValueError(f"Enter a valid {label}.")
    return format(amount, ",.2f") if amount != amount.to_integral_value() else format(amount, ",.0f")


def _percentage(value, label):
    raw = str(value if value is not None else "").strip()
    if not re.fullmatch(r"\d{1,3}(?:\.\d{1,4})?", raw) or Decimal(raw) > 100:
        raise ValueError(f"Enter {label} from 0 to 100%.")
    return raw


def validate_terms(data):
    """Return canonical renderer terms after validating every conditional choice."""
    data = data or {}
    credit_days = _whole_number(data.get("credit_days"), "credit-document delivery time")
    documents = data.get("credit_documents")
    if not isinstance(documents, list) or not documents or any(
            value not in ALLOWED_CREDIT_DOCUMENTS for value in documents):
        raise ValueError("Choose at least one credit-documentation item.")
    documents = list(dict.fromkeys(documents))
    credit_other = _clean(data.get("credit_other")) if "other" in documents else ""
    if "other" in documents and (not credit_other or len(credit_other) > 180):
        raise ValueError("Describe the other credit documentation in 180 characters or fewer.")

    note_amount = _money(data.get("note_amount"), "promissory-note amount", positive=True)
    interest_rate = _percentage(data.get("interest_rate"), "annual interest rate")
    raw_payment = data.get("payment") if isinstance(data.get("payment"), dict) else {}
    plan = str(raw_payment.get("plan") or "").strip()
    if plan not in PAYMENT_PLANS:
        raise ValueError("Choose the promissory-note payment plan printed on the addendum.")
    payment = {"plan": plan}
    if plan == "one_payment":
        payment["due_after_months"] = _whole_number(
            raw_payment.get("due_after_months"), "the one-payment due time", allow_zero=True)
        timing = str(raw_payment.get("interest_timing") or "").strip()
        if timing not in ("maturity", "monthly", "quarterly"):
            raise ValueError("Choose when interest is payable for the one-payment plan.")
        payment["interest_timing"] = timing
    else:
        payment["installment_amount"] = _money(
            raw_payment.get("installment_amount"), "installment amount", positive=True)
        style = str(raw_payment.get("interest_style") or "").strip()
        if style not in ("including_interest", "plus_interest"):
            raise ValueError("Choose whether the installment includes or is plus interest.")
        payment["interest_style"] = style
        payment["begins_after_months"] = _whole_number(
            raw_payment.get("begins_after_months"), "the installment start time", allow_zero=True)
        payment["payoff_after_months"] = _whole_number(
            raw_payment.get("payoff_after_months"), "the payoff time")
        if plan == "interest_only_then_installments":
            payment["interest_only_months"] = _whole_number(
                raw_payment.get("interest_only_months"), "the interest-only period")

    transfer = str(data.get("property_transfer") or "").strip()
    if transfer not in ("consent_not_required", "consent_required"):
        raise ValueError("Choose the property-transfer consent term.")
    insurance = str(data.get("casualty_insurance") or "").strip()
    if insurance not in ("required", "not_required"):
        raise ValueError("Choose the casualty-insurance term.")
    raw_escrow = data.get("escrow") if isinstance(data.get("escrow"), dict) else {}
    choice = str(raw_escrow.get("choice") or "").strip()
    if choice not in ("required", "not_required"):
        raise ValueError("Choose the tax-and-insurance escrow term.")
    escrow = {"choice": choice}
    if choice == "required":
        servicer = str(raw_escrow.get("third_party_servicer") or "").strip()
        payer = str(raw_escrow.get("cost_paid_by") or "").strip()
        if servicer not in ("will", "will_not"):
            raise ValueError("Choose whether a third-party escrow servicer will be used.")
        if payer not in ("buyer", "seller"):
            raise ValueError("Choose who pays the escrow-service cost.")
        escrow.update(third_party_servicer=servicer, cost_paid_by=payer)

    return {
        "credit_days": credit_days,
        "credit_documents": documents,
        "credit_other": credit_other,
        "note_amount": note_amount,
        "interest_rate": interest_rate,
        "payment": payment,
        "property_transfer": transfer,
        "casualty_insurance": insurance,
        "escrow": escrow,
    }


def purchase_terms(offer):
    """Translate the purchase interview's flat fields into canonical terms."""
    offer = offer or {}
    plan = str(offer.get("sellerFinancingPaymentPlan") or "").strip()
    payment = {"plan": plan}
    if plan == "one_payment":
        payment.update(
            due_after_months=offer.get("sellerFinancingOnePaymentDueAfterMonths"),
            interest_timing=offer.get("sellerFinancingOnePaymentInterestTiming"),
        )
    else:
        payment.update(
            installment_amount=offer.get("sellerFinancingInstallmentAmount"),
            interest_style=offer.get("sellerFinancingInstallmentInterestStyle"),
            begins_after_months=offer.get("sellerFinancingInstallmentBeginsAfterMonths"),
            payoff_after_months=offer.get("sellerFinancingPayoffAfterMonths"),
            interest_only_months=offer.get("sellerFinancingInterestOnlyMonths"),
        )
    return validate_terms({
        "credit_days": offer.get("sellerFinancingCreditDays"),
        "credit_documents": offer.get("sellerFinancingCreditDocuments"),
        "credit_other": offer.get("sellerFinancingCreditOther"),
        "note_amount": offer.get("sellerFinancingNoteAmount"),
        "interest_rate": offer.get("sellerFinancingInterestRate"),
        "payment": payment,
        "property_transfer": offer.get("sellerFinancingPropertyTransfer"),
        "casualty_insurance": offer.get("sellerFinancingCasualtyInsurance"),
        "escrow": {
            "choice": offer.get("sellerFinancingEscrow"),
            "third_party_servicer": offer.get("sellerFinancingThirdPartyServicer"),
            "cost_paid_by": offer.get("sellerFinancingEscrowCostPaidBy"),
        },
    })

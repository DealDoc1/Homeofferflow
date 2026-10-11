"""Source-bounded contacts for pages 8 and 11 of the 05-04-2026 contract."""

from lib.txr_addenda_layout import SourceAnswers, clean
from lib import lease_terms_continuation
from lib.brokerage_defaults import broker_license


RENDER_REVISION = "trec-20-19-2026-10-11-contacts-execution-v1"

# PDF coordinates, measured from the printed rules rather than earlier maps.
BROKER_BLANKS = {
    "agentBrokerage": (53, 498, 230),
    "agentAddress": (107, 484, 447),
    "agentBrokerLicense": (179, 470, 375),
    "agentName": (150, 455, 404),
    "teamName": (125, 441, 429),
    "agentEmail": (148, 426, 406),
    "agentPhone": (170, 412, 140),
    "agentLicense": (423, 412, 131),
}
LABELS = {
    "agentBrokerage": "Buyer broker firm",
    "agentAddress": "Buyer agent address",
    "agentBrokerLicense": "Buyer broker firm license number",
    "agentName": "Buyer associate name",
    "teamName": "Buyer agent team name",
    "agentEmail": "Buyer agent email",
    "agentPhone": "Buyer agent phone",
    "agentLicense": "Buyer associate license number",
}


def agent_address(offer):
    # A firm name is not a mailing address. Never invent the missing address.
    return offer.get("agentAddress") or offer.get("agentMailAddr") or ""


def answer_layout(offer, *, lease_kind=""):
    buyers = [offer.get("buyer1") or "Buyer"]
    if offer.get("buyer2Email"):
        buyers.append(offer.get("buyer2") or "Buyer 2")
    answers = SourceAnswers({
        "buyer_names": buyers,
        "seller": offer.get("seller") or "",
        "property_address": f"{offer.get('address','')}, {offer.get('city','')}, TX {offer.get('zip','')}".strip(", "),
    }, "Purchase Contract - Contact Information Continuation", 11)
    answers.put(offer.get("buyerMailAddr"), [(108, 381, 189), (63, 347, 234)],
                "Buyer mailing address", page=8)
    _reuse_lease_notice(answers, offer, lease_kind, "Buyer mailing address", "_mail", (108, 381, 189))
    answers.put(offer.get("buyerPhone"), [(113, 312, 184)], "Buyer phone", page=8)
    answers.put(offer.get("buyerEmail"), [(110, 243, 187), (63, 209, 234)],
                "Buyer email", page=8)
    _reuse_lease_notice(answers, offer, lease_kind, "Buyer email", "_email", (110, 243, 187))
    has_agent = offer.get("hasBuyerAgent") == "yes" or offer.get("userType") in ("agent", "broker")
    if has_agent:
        answers.put(agent_address(offer), [(108, 155, 189), (63, 121, 234)],
                    "Buyer agent notice address", page=8)
        answers.put(offer.get("agentPhone"), [(99, 87, 198)], "Buyer agent notice phone", page=8)
        answers.put(offer.get("agentEmail"), [(96, 52, 201)], "Buyer agent notice email", page=8)
        for key, blank in BROKER_BLANKS.items():
            value = agent_address(offer) if key == "agentAddress" else offer.get(key)
            if key == "agentBrokerLicense":
                value = broker_license(offer.get("agentBrokerage"), value)
            answers.put(value, [blank], LABELS[key], page=11)
    return answers


def _reuse_lease_notice(answers, offer, kind, label, suffix, blank):
    """Reference the already attached, exact Buyer notice instead of duplicating it."""
    if not kind or label not in answers.overflow:
        return
    section = ("tenant" if kind == "buyer" else "landlord") + suffix
    value = lease_terms_continuation.terms(offer, kind, section)
    if (clean(value) != answers.overflow[label]
            or lease_terms_continuation.inline_entries(value, kind, section) is not None):
        return
    del answers.overflow[label]
    # These are the only page-eight entries when called immediately after put.
    answers.pages[8].pop()
    x, y, _ = blank
    answers.pages[8].append((x, y, "See temporary lease continuation.", 7))

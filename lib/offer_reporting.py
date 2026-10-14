"""Read-only offer progress: signer activity is not packet completion."""


def offer_status_bucket(value, *, provider=False):
    status = " ".join(str(value or "").strip().lower().replace("_", " ").replace("-", " ").split())
    if status.startswith("document "):
        status = status[len("document "):]
    if status == "signed":
        # A raw provider signed event concerns one recipient. Legacy main
        # offer status Signed is the app's completed packet label instead.
        return "partial" if provider else "signed"
    if status in {"complete", "completed", "fully signed", "buyer signed", "buyer signatures complete"}:
        return "signed"
    if status in {"partial", "partially signed", "partially buyer signed", "pending", "in progress"}:
        return "partial"
    if status in {"viewed", "buyer viewed"}:
        return "viewed"
    if status in {"sent", "shared", "sent for signature", "awaiting signature", "awaiting signatures", "awaiting buyer signature", "awaiting buyer signatures", "awaiting signing"}:
        return "awaiting"
    if status in {"draft", "created", "generated", "saved", "draft not sent"}:
        return "draft"
    return "other"


def reporting_bucket(offer):
    provider_status = str(offer.get("signwell_status") or "").strip()
    return offer_status_bucket(provider_status, provider=True) if provider_status else offer_status_bucket(offer.get("status"))


def signing_summary(offers):
    counts = {"signedCount": 0, "awaitingCount": 0, "signingStartedCount": 0}
    for offer in offers:
        bucket = reporting_bucket(offer)
        if bucket == "signed":
            counts["signedCount"] += 1
        if bucket in {"awaiting", "viewed", "partial"}:
            counts["awaitingCount"] += 1
        if bucket in {"signed", "awaiting", "viewed", "partial"}:
            counts["signingStartedCount"] += 1
    return counts

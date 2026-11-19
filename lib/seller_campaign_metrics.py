"""Privacy-safe aggregate attribution for tracked seller requests."""


SELLER_CAMPAIGN_CHANNELS = (
    "direct",
    "homepage",
    "organic",
    "pwa_shortcut",
    "build_readiness",
    "direct_outreach",
    "email",
    "seller_receipt",
    "social",
    "referral",
    "local_event",
    "print",
    "other_tracked",
)
OUTREACH_CHANNELS = {"direct_outreach", "email", "social", "referral", "local_event", "print"}


def _campaign_channel(lead):
    source = str(lead.get("utm_source") or "").strip().lower()
    medium = str(lead.get("utm_medium") or "").strip().lower()
    if medium == "seller_receipt":
        return "seller_receipt"
    if medium == "installed_app" or source == "pwa_shortcut":
        return "pwa_shortcut"
    if medium == "organic_content" or source == "organic":
        return "organic"
    if source == "homeofferflow" or medium == "homepage":
        return "homepage"
    if source == "build_readiness":
        return "build_readiness"
    if source == "homeofferflow_admin" and medium in OUTREACH_CHANNELS:
        return medium
    if source in OUTREACH_CHANNELS:
        return source
    return "other_tracked"


def build_seller_campaign_channel_counts(leads):
    """Count tracked seller leads by fixed source channel; never return raw UTM values."""
    counts = {channel: 0 for channel in SELLER_CAMPAIGN_CHANNELS}
    for lead in leads or []:
        if not isinstance(lead, dict):
            continue
        if str(lead.get("source") or "").strip().lower() != "tracked_seller_landing":
            continue
        counts[_campaign_channel(lead)] += 1
    return counts

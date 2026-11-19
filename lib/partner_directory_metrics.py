"""Privacy-safe aggregate metrics for partner-directory placements."""


def build_readiness_traffic_by_placement(events, placement_ids):
    """Return total Blueprint traffic and active-placement traffic counts.

    Events retain only placement ID and allowlisted directory metadata. Clicks
    indicate a link activation, not a confirmed visit to the partner website.
    """
    totals = {"impressions": 0, "outboundClicks": 0}
    by_placement = {
        str(placement_id): {"impressions": 0, "outboundClicks": 0}
        for placement_id in placement_ids if str(placement_id or "").strip()
    }
    for item in events or []:
        if not isinstance(item, dict):
            continue
        event_type = str(item.get("event_type") or "").strip().lower()
        if event_type not in {"partner_directory_impression", "partner_directory_outbound_click"}:
            continue
        metadata = item.get("metadata") or {}
        if not isinstance(metadata, dict):
            continue
        if str(metadata.get("directorySurface") or "").strip() != "build_readiness":
            continue
        key = "impressions" if event_type == "partner_directory_impression" else "outboundClicks"
        totals[key] += 1
        partner_id = str(metadata.get("partnerId") or "").strip()
        if partner_id in by_placement:
            by_placement[partner_id][key] += 1
    return totals, by_placement

"""Read-only partner operations; a public placement is not proof of payment."""


def is_paid_partner(lead):
    return (str((lead or {}).get('partner_program') or 'commercial').strip().lower() == 'commercial'
            and str((lead or {}).get('payment_status') or '').strip().lower() == 'paid')


def annotate_partner_operations(leads, placements):
    """Join existing central records in memory; no additional reads or writes."""
    by_id = {str(lead['id']): lead for lead in leads if lead.get('id')}
    active_ids = {str(p['source_lead_id']) for p in placements
                  if p.get('is_active') and p.get('source_lead_id')}
    annotated_leads = [{**lead, 'has_active_placement': str(lead.get('id') or '') in active_ids}
                       for lead in leads]
    annotated_placements = []
    for placement in placements:
        lead = by_id.get(str(placement.get('source_lead_id') or ''))
        program = str((lead or {}).get('partner_program') or ('commercial' if lead else 'unknown')).strip().lower()
        annotated_placements.append({**placement, 'partner_program': program})
    return annotated_leads, annotated_placements

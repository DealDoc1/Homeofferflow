"""Purchase-packet composition and reviewed recipient merging, without sends."""
from dataclasses import dataclass
from lib.purchase_disclosure_execution import append_execution
from lib.seller_review_access import normalize_email, normalize_seller_name

RECIPE_KEY = 'purchaseDisclosurePacket'
PENDING_MESSAGE = "Seller's disclosure is not included. Complete it separately when it is ready."


@dataclass(frozen=True)
class PreparedPurchaseDisclosurePacket:
    pdf: bytes
    fields: list
    plan: object = None
    pending: tuple = ()


def compose_purchase_disclosure(pdf, fields, plan=None, *, pending=False):
    if plan is not None:
        pdf, added = append_execution(pdf, plan)
        fields = [[*fields[0], *added]]
    return PreparedPurchaseDisclosurePacket(pdf, fields, plan, (PENDING_MESSAGE,) if pending else ())


def merge_recipients(existing, prepared):
    """Keep prior addendum roles; refuse a conflicting name or destination."""
    if not prepared or prepared.plan is None:
        return existing
    recipients = {str(row['id']): dict(row) for row in existing}
    for row in prepared.plan.recipients:
        prior = recipients.get(row['id'])
        if prior and (normalize_email(prior['email']) != normalize_email(row['email'])
                      or normalize_seller_name(prior['name']) != normalize_seller_name(row['name'])):
            raise ValueError('Use the same buyer and seller names and signing emails throughout the package.')
        recipients[row['id']] = dict(row)
    result = sorted(recipients.values(), key=lambda row: int(row['id']))
    if len({normalize_email(row['email']) for row in result}) != len(result):
        raise ValueError('Each signing recipient must use a different email.')
    return result

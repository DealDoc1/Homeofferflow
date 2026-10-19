"""Buyer receipt fields for an unchanged, seller-signed HomeOfferFlow PDF.

The original signed PDF and audit pages remain in the packet. Reuse the already
calibrated disclosure rectangles, not the generic uploaded-document sizes.
"""
import hashlib
import re
from lib.seller_disclosure_explanations import RENDER_REVISION
from lib.trec_seller_disclosure import build_signwell_fields


def normalize_address(value):
    return re.sub(r'[^\w]+', ' ', str(value or '').casefold()).strip()


def address_matches(saved, offer):
    address = str(offer.get('address') or '').strip()
    parts = [address, str(offer.get('city') or '').strip(),
             str(offer.get('state') or 'TX').strip(), str(offer.get('zip') or '').strip()]
    target = normalize_address(saved)
    return bool(address and target and target in {
        normalize_address(address), normalize_address(' '.join(parts))})


def receipt_fields(doc, offer, *, page_offset=0, namespace='disclosure'):
    receipt = doc.get('homeOfferFlowDisclosureReceipt')
    if receipt is None:
        return []
    raw = doc.get('raw') or b''
    if (not isinstance(receipt, dict) or doc.get('type') != 'seller_disclosure'
            or receipt.get('renderRevision') != RENDER_REVISION
            or receipt.get('sourceRevision') != '05-04-2026'
            or not isinstance(receipt.get('hasWaterRights'), bool)
            or not raw or receipt.get('sha256') != hashlib.sha256(raw).hexdigest()):
        raise ValueError('The saved disclosure attachment changed. Remove it and choose the signed disclosure again.')
    if not address_matches(receipt.get('propertyAddress'), offer):
        raise ValueError('This signed disclosure is for a different property. Remove it or choose the matching disclosure.')
    has_water = receipt['hasWaterRights']
    if doc.get('page_count', 0) < (6 if has_water else 4):
        raise ValueError('The signed disclosure is missing pages. Choose its complete signed PDF.')
    buyers = ['Buyer 1'] + (['Buyer 2'] if str(offer.get('buyer2Email') or '').strip() else [])
    data = {'seller_names': ['Already signed'], 'buyer_names': buyers}
    fields = []
    for code, offset in [('TREC-55-1', 0)] + ([('TREC-61-0', 4)] if has_water else []):
        for field in build_signwell_fields(code, data, page_offset=page_offset + offset)[0]:
            if '_buyer' not in field['api_id']:
                continue
            fields.append({**field, 'api_id': namespace + '_' + field['api_id'],
                           'recipient_id': str(int(field['recipient_id']) - 1)})
    return fields

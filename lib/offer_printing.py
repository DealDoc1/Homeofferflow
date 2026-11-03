"""Read-only unsigned copies of an authenticated owner's saved offer terms."""
import copy
import uuid


def unsigned_offer_copy(offer_id, user_id, *, load, render):
    try:
        offer_id = str(uuid.UUID(str(offer_id)))
        user_id = str(uuid.UUID(str(user_id)))
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Choose a valid saved offer.') from None
    record = load(offer_id, user_id)
    if not isinstance(record, dict) or record.get('id') != offer_id or record.get('user_id') != user_id:
        raise PermissionError('That offer is unavailable.')
    if str(record.get('status') or '').lower() in {'draft', 'generating', 'generation failed'}:
        raise ValueError('Finish preparing this offer before printing its packet.')
    answers = record.get('offer_data')
    if not isinstance(answers, dict) or not answers:
        raise ValueError('The saved offer terms are unavailable.')
    # Provider responses and bookkeeping are never print authority. Rendering
    # receives a copy, and cannot mutate the persisted interview or signing state.
    snapshot = copy.deepcopy(answers)
    for key in ('signwell', '_hof_signature_delivery', 'backend_saved'):
        snapshot.pop(key, None)
    expected = {key: copy.deepcopy(snapshot.get(key)) for key in
                ('_signing_source_hashes', '_signing_render_revisions')}
    pdf = render(snapshot, copy.deepcopy(record))
    for key, value in expected.items():
        if value is not None and snapshot.get(key) != value:
            raise ValueError('The document version has changed. Retrieve the original packet before printing or signing.')
    if not isinstance(pdf, bytes) or not pdf.startswith(b'%PDF-'):
        raise RuntimeError('The offer PDF is temporarily unavailable.')
    return pdf

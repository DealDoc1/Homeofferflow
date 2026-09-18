"""Local synthetic packet bridge. No database, payment, or signing calls."""
import contextlib
from io import BytesIO
import json
import os
from pathlib import Path
import sys

from pypdf import PdfReader
from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms, minimal_offer


def main():
    answers = json.load(sys.stdin)
    allowed = {'hydrostaticTesting', 'hydrostaticAddendum', 'hydrostaticRiskAllocation',
               'hydrostaticBuyerLiabilityLimit', 'seller1Name', 'seller1Email',
               'seller2Name', 'seller2Email', 'mineralReservation', 'mineralReservationAddendum',
               'mineralReservationChoice', 'mineralUndividedInterest', 'mineralSurfaceRights',
               'environmentalAssessment', 'environmentalAddendum', 'environmentalReviewTypes', 'environmentalTerminationDays'}
    offer = minimal_offer(buyer1='QA Buyer', buyerEmail='buyer@example.test',
                          seller='QA Seller', address='100 QA Street', city='Frisco',
                          county='Collin', zip='75034', closingDate='2026-10-30')
    offer.update({key: value for key, value in answers.items() if key in allowed})
    if os.environ.get('HOF_QA_ASSUMPTION_SOURCE') or os.environ.get('HOF_QA_CURRENCY'):
        assumption_keys = {'financing', 'price', 'loanAssumption', 'assumptionCreditDays',
                           'assumptionCreditDocuments', 'assumptionCreditOther',
                           'assumptionVarianceAdjustment', 'assumptionVarianceThreshold'}
        assumption_keys.update(('loanAmount','downPayment','earnest','optionFee','optionDays','loanYears',
                                'interestRateCap','interestFirstYears','originationCap','buyerApprovalDays',
                                'appraisalAddendum','appraisalPartialValue','appraisalTerminateDays','appraisalTerminateValue'))
        assumption_keys.update('assumption' + key + field for key in ('First', 'Second')
                               for field in ('Enabled', 'Lender', 'Balance', 'Payment', 'FeeCap', 'RateCap'))
        offer.update({key: value for key, value in answers.items() if key in assumption_keys})
    sources = {}
    for requested, code, variable in (
        (adapter.mineral_requested(offer), 'TXR-1905', 'HOF_QA_MINERAL_SOURCE'),
        (adapter.environmental_requested(offer), 'TXR-1917', 'HOF_QA_ENVIRONMENTAL_SOURCE'),
        (adapter.assumption_requested(offer), 'TXR-1919', 'HOF_QA_ASSUMPTION_SOURCE'),
    ):
        if not requested:
            continue
        # The operator supplies a local private source, never via browser input.
        source = Path(os.environ[variable]).read_bytes()
        reader = PdfReader(BytesIO(source))
        assert not reader.get_fields() and not any(a.get_object().get('/Subtype') == '/Widget'
            for page in reader.pages for a in page.get('/Annots', [])), 'Inspect interactive source before rendering'
        sources[code] = source
    offer['_paragraph4_source_pdf_bytes'] = sources
    configure_local_forms()
    with contextlib.redirect_stdout(sys.stderr):
        packet = adapter.fill_and_merge_20_19(offer)
        signing = adapter.build_signwell_fields_20_19(offer, packet)[0]
    reader = PdfReader(BytesIO(packet))
    fields = reader.get_fields() or {}
    hydro = {name: str(field.get('/V', '')) for name, field in fields.items()
             if name.startswith('hof_trec48_1.')}
    widgets_checked = 0
    for page in reader.pages:
        for ref in page.get('/Annots', []):
            widget = ref.get_object()
            name = 'hof_trec48_1.' + str(widget.get('/T', ''))
            if name not in fields or widget.get('/FT') == '/Sig':
                continue
            assert widget.get('/Parent'), 'Hydrostatic widget lost canonical parent'
            assert widget.get('/V') == fields[name].get('/V'), name
            assert widget['/AP']['/N'], 'Missing appearance: ' + name
            widgets_checked += 1
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(packet)
    print(json.dumps({'pages': len(reader.pages), 'price': offer.get('price'),
                      'loan': offer.get('loanAmount'), 'cash': offer.get('downPayment'), 'hydrostaticFields': hydro,
                      'widgetsChecked': widgets_checked,
                      'signatureFields': [field for field in signing
                                          if field['api_id'].startswith(('trec48_1_', 'txr1905_', 'txr1917_', 'txr1919_'))],
                      'providerContacted': False}))


if __name__ == '__main__':
    main()

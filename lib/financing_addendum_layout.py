"""Source-measured TREC 40-11 answers for the supported purchase loan paths."""
from lib.contract_money import format_currency
from lib.txr_addenda_layout import SourceAnswers


RENDER_REVISION = 'trec-40-11-2026-09-18-bounded-answers-v1'
TEXT_BLANKS = {
    'address': (56, 640, 500), 'address_p2': (59, 731, 493),
    'approval_days': (365, 685, 25), 'appraised_value': (78, 413, 122),
    'fha_section': (284, 416.4, 97),
}
# Amount, term, rate cap, initial rate period, origination-charge cap.
LOAN_BLANKS = {
    'conventional': ((376,545.2,97),(295,533.8,32),(517,533.8,25),(223,523.1,36),(353,512.5,38)),
    'fha': ((97,405,102),(117,394.3,41),(339,394.3,39),(90,383.6,37),(207,372.9,34)),
    'va': ((447,359.2,103),(485,347.7,32),(229,337,33),(400,337,30),(89,315.7,38)),
    'usda': ((487,301,65),(484,290.6,33),(231,279.8,23),(394,279.8,34),(518,269.1,23)),
}
CHECK_CENTERS = {
    'conventional': (1,62.2,562.8), 'first_mortgage': (1,92,548.3),
    'fha': (1,62.2,419.4), 'va': (1,62.2,362.3), 'usda': (1,62.2,305.1),
    'approval_yes': (2,88,697.9), 'approval_no': (2,89,597.9),
}
BUYER_INITIAL_BOXES = ((275,1007,28,16),(318,1007,32,16))
BUYER_SIGNATURE_BOXES = ((76,805,320,26),(76,873,320,26))


def first(offer, *keys, default=''):
    return next((offer[key] for key in keys if offer.get(key) not in (None,'')), default)


def answer_layout(offer, financing):
    if financing not in LOAN_BLANKS:
        raise ValueError('Choose a supported loan type for the financing addendum.')
    address = f"{offer.get('address','')}, {offer.get('city','')}, TX {offer.get('zip','')}".strip(', ')
    data = {'property_address':address, 'buyer_names':[offer.get('buyer1') or 'Buyer'] +
            ([offer.get('buyer2') or 'Buyer 2'] if offer.get('buyer2Email') else []),
            'seller':offer.get('seller') or '', '_for_signing':True}
    answers = SourceAnswers(data, 'TREC 40-11 - Financing Addendum Continuation', 2)
    for key,page in (('address',1),('address_p2',2)):
        answers.put(address,[TEXT_BLANKS[key]],'Property',page=page,size=9)
    # Preserve legacy payload defaults; this geometry correction does not
    # silently change terms in existing drafts or add new financing products.
    values = (
        (format_currency(offer.get('loanAmount')), 'Loan amount'),
        (first(offer,'loanYears','loanTermYears',default='30'), 'Loan term (years)'),
        (first(offer,'interestRateCap','loanInterestCap',default='7'), 'Maximum annual interest rate (%)'),
        (first(offer,'interestFirstYears','loanYears','loanTermYears',default='30'), 'Initial interest-rate period (years)'),
        (first(offer,'originationCap','loanOriginationCap',default='1'), 'Maximum origination charges (%)'),
    )
    for (value,label),blank in zip(values,LOAN_BLANKS[financing]):
        answers.put(value,[blank],f'Paragraph 1 - {financing.upper()} - {label}',size=9)
    if financing == 'fha':
        answers.put(first(offer,'fhaSection','fhaProgram',default='203(b)'),
                    [TEXT_BLANKS['fha_section']],'Paragraph 1C - FHA section',size=9)
    approval = offer.get('buyerApproval','yes') != 'no'
    if approval:
        answers.put(first(offer,'buyerApprovalDays','financingApprovalDays',default='21'),
                    [TEXT_BLANKS['approval_days']],'Paragraph 2A - Buyer approval period (days)',page=2,size=9)
    if financing in ('fha','va'):
        answers.put(format_currency(first(offer,'appraisedValue','price')),
                    [TEXT_BLANKS['appraised_value']],'Paragraph 4 - Appraised value',page=2,size=9)
    answers.checks = [financing, 'approval_yes' if approval else 'approval_no']
    if financing == 'conventional':
        answers.checks.append('first_mortgage')
    return answers


def page_entries(answers):
    pages = {page-1:[(*entry,'text') for entry in entries] for page,entries in answers.pages.items()}
    for key in answers.checks:
        page,x,y = CHECK_CENTERS[key]
        pages[page-1].append((x-2,y-2.15,'X',6,'check_cell'))
    return pages

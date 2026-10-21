"""Exact-source lease-listing answers, lossless overlays and signing geometry.

No rates, tax facts, eligibility decisions, sources, recipients or sends are
inferred. The existing authenticated API must own those responsibilities.
Rental marketing preferences are optional, not a lease or screening decision.
"""
from datetime import date
from decimal import Decimal
import hashlib
from io import BytesIO
import re

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.brokerage_defaults import broker_license
from lib.pdf_text import draw_text
from lib.txr_addenda_layout import clean, inline
from lib.txr1501_answers import render_continuation, continuation_fields
from lib.txr_1101 import _number, _mark, _remove_member_footer, NOTICE_CONTACT_LIMITS

SOURCE_SHA256 = '30ae702ee94d71fc2aec5717f0d1b6d78b4fea53b5b418f7d74b39f658e44657'
SOURCE_PAGES = 11
REVISION = 'txr-1102-2026-01-05-overlay-v1'
DOCUMENT_CHOICES = (
    ('A','Information About Brokerage Services'),('B','Rental flood disclosure'),
    ('C','Lead-based paint disclosure for a lease'),('D','Owners’ association information request'),
    ('E','Special flood hazard information'),('F','Condominium listing addendum'),
    ('G','Tenant keybox authorization'),('H','On-site sewer information'),('I','IRS Form W-9 or W-8'),
    ('J','Owner’s authorization for unescorted access'),('K','Assistance-animal information for landlords'),
    ('L','Other related documents'),
)
TEXT_LIMITS = {
    'client_address':300,'client_city_state_zip':180,'client_phone':80,'client_email':180,'client_email_2':180,
    'property_address':400,'lot':150,'block':150,'subdivision':600,'city':180,'county':120,
    'non_real_estate_items':2000,'exclusions':2000,'fee_other':2000,'renewal_other':2000,'sale_fee_other':2000,
    'reimbursable_expenses':2000,'payment_county':120,'mls_delay_purpose':1500,'scheduling_companies':800,
    'make_ready_service_fee':1500,'financial_exceptions':2000,'liens':2000,'common_area_fees':2000,
    'health_safety_conditions':3000,'special_provisions':4000,'other_documents':2000,
}
CHOICES = {
    'hoa':('yes','no'),'fee_scope':('with_other_broker','broker_only'),
    'fee_basis':('month_percentage','total_percentage','other'),
    'renewal_basis':('month_percentage','total_percentage','other'),
    'sale_fee_basis':('percentage','other'),
    'mls_filing':('standard','delayed','none'),
    'internet_display':('full','hide_address','hide_listing','not_applicable'),
    'keybox':('yes','no'),'intermediary':('authorized','not_authorized'),
    'make_ready':('not_authorized','landlord_pays','broker_reimbursed'),
    'signer_plan':('clients_and_associate','clients_and_broker'),
}
PREFERENCE_TEXT_LIMITS = {
    'rent_due_other':300,'animal_restrictions':1500,'utilities_exceptions':1500,
    'yard_contractor':400,'pool_contractor':400,'pool_other':1000,
    'repair_phone':100,'unrepaired_items':2000,'lease_special_provisions':3000,'lease_other':2000,
}
PREFERENCE_CHOICES = {
    'rent_due':('first','other'), 'initial_late_basis':('flat','percentage'),
    'animals':('not_permitted','permitted'),
    'yard':('landlord','tenant','tenant_contractor','named_contractor'),
    'pool':('landlord','tenant','tenant_contractor','named_contractor','other'),
    'tenant_replacement_basis':('flat','percentage'), 'landlord_replacement_basis':('flat','percentage'),
}
PREFERENCE_INTEGERS = ('late_after_days','guests_days','vehicle_count','keybox_last_days','inventory_days')
PREFERENCE_AMOUNTS = ('initial_late_amount','daily_late_amount','animal_deposit','animal_monthly_rent',
    'animal_one_time_fee','animal_violation_initial','animal_violation_daily','security_deposit','trip_charge',
    'keybox_withdrawal_fee','liability_insurance','tenant_replacement_amount','landlord_replacement_amount')

# Human-readable continuation labels, anchored to the source paragraph rather
# than exposing storage keys such as "rent due other" to a signing client.
LABELS = {
    'client_address':'Paragraph 1 - Landlord mailing address','client_city_state_zip':'Paragraph 1 - Landlord city, state and ZIP code',
    'client_phone':'Paragraph 1 - Landlord phone','lot':'Paragraph 2A - Lot','block':'Paragraph 2A - Block',
    'subdivision':'Paragraph 2A - Subdivision','city':'Paragraph 2A - City','county':'Paragraph 2A - County',
    'property_address':'Paragraph 2A - Property address','non_real_estate_items':'Paragraph 2B - Included non-real-estate items',
    'exclusions':'Paragraph 2C - Exclusions','listing_price':'Paragraph 3A - Monthly rent',
    'lease_min_months':'Paragraph 3B - Minimum lease term','lease_max_months':'Paragraph 3B - Maximum lease term',
    'term_start':'Paragraph 4A - Listing start date','term_end':'Paragraph 4A - Listing end date',
    'reimbursable_expenses':'Paragraph 5E(5) - Reimbursable expenses','protection_days':'Paragraph 5F - Protection period',
    'payment_county':'Paragraph 5G - Payment county','mls_delay_days':'Paragraph 6A - MLS filing delay',
    'mls_delay_purpose':'Paragraph 6A - Purpose of the MLS filing delay',
    'scheduling_companies':'Paragraph 7B - Appointment scheduling companies',
    'make_ready_limit':'Paragraph 11D - Make-ready spending limit','financial_exceptions':'Paragraph 12E - Financial-obligation exceptions',
    'liens':'Paragraph 12F - Liens and encumbrances','common_area_fees':'Paragraph 12I - Optional common-area fees',
    'health_safety_conditions':'Paragraph 12J - Health or safety conditions','special_provisions':'Paragraph 15 - Special provisions',
    'other_documents':'Paragraph 19L - Other documents','rent_due_other':'Paragraph 20A - Rent due date',
    'late_after_days':'Paragraph 20B - Late-charge timing','initial_late_amount':'Paragraph 20B(1) - Initial late charge',
    'daily_late_amount':'Paragraph 20B(2) - Daily late charge','animal_restrictions':'Paragraph 20C - Animal restrictions',
    'animal_deposit':'Paragraph 20C(1)(a) - Animal deposit','animal_monthly_rent':'Paragraph 20C(1)(b) - Additional monthly rent',
    'animal_one_time_fee':'Paragraph 20C(1)(c) - One-time animal payment',
    'animal_violation_initial':'Paragraph 20C(2) - Initial animal-violation charge',
    'animal_violation_daily':'Paragraph 20C(2) - Daily animal-violation charge',
    'security_deposit':'Paragraph 20D - Security deposit','utilities_exceptions':'Paragraph 20E - Utility payment exceptions',
    'guests_days':'Paragraph 20F - Guest days','vehicle_count':'Paragraph 20G - Number of vehicles',
    'trip_charge':'Paragraph 20H - Trip charge','keybox_last_days':'Paragraph 20I - Keybox authorization period',
    'keybox_withdrawal_fee':'Paragraph 20I - Early keybox withdrawal fee','inventory_days':'Paragraph 20J - Condition-form delivery period',
    'yard_contractor':'Paragraph 20K - Named yard contractor','pool_contractor':'Paragraph 20L - Named pool or spa contractor',
    'pool_other':'Paragraph 20L - Other pool or spa arrangement','repair_phone':'Paragraph 20M - Emergency repair phone',
    'unrepaired_items':'Paragraph 20M - Items excluded from repairs','liability_insurance':'Paragraph 20N - Liability insurance amount',
    'tenant_replacement_amount':'Paragraph 20O(1) - Tenant-procured replacement fee',
    'landlord_replacement_amount':'Paragraph 20O(2) - Landlord-procured replacement fee',
    'lease_special_provisions':'Paragraph 20P - Lease preferences: special provisions','lease_other':'Paragraph 20Q - Other lease preferences',
}


def _text(value, key, limit):
    if not isinstance(value,str) or len(value)>limit:
        raise ValueError('Check '+key.replace('_',' ')+'.')
    return clean(value)


def _integer(value, key, *, minimum=0, required=False):
    raw=str(value if value is not None else '').strip()
    if not raw and not required:return ''
    if not re.fullmatch(r'\d{1,4}',raw) or not minimum<=int(raw)<=9999:
        raise ValueError('Enter valid whole '+key.replace('_',' ')+'.')
    return str(int(raw))


def validate_answers(data):
    """Stable answer contract reusable by the web interview and a future app."""
    preference_keys=set(PREFERENCE_TEXT_LIMITS)|set(PREFERENCE_CHOICES)|set(PREFERENCE_INTEGERS)|set(PREFERENCE_AMOUNTS)
    allowed=set(TEXT_LIMITS)|set(CHOICES)|preference_keys|{
        'client_names','broker_notice_contacts','term_start','term_end','listing_price','lease_min_months','lease_max_months',
        'fee_amount','cobroker_basis','cobroker_amount','renewal_amount','sale_fee_amount',
        'protection_days','mls_delay_days','make_ready_limit','addenda','built_before_1978',
        'include_rental_preferences','_for_signing'}
    if not isinstance(data,dict) or set(data)-allowed:raise ValueError('Check the lease-listing details.')
    result={}
    names=data.get('client_names')
    if not isinstance(names,list) or len(names) not in (1,2) or any(not isinstance(n,str) or not clean(n) or len(n)>300 for n in names):
        raise ValueError('Enter one or two landlord names.')
    result['client_names']=[clean(n) for n in names]
    for key,limit in TEXT_LIMITS.items():result[key]=_text(data.get(key,''),key,limit)
    if not result['property_address']:raise ValueError('Enter the property address.')
    for key in ('client_email','client_email_2'):
        if result[key] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',result[key]):
            raise ValueError('Enter a valid landlord contact email.')
    if 'broker_notice_contacts' in data:
        contacts=data['broker_notice_contacts']
        if not isinstance(contacts,dict) or set(contacts)-set(NOTICE_CONTACT_LIMITS):raise ValueError('Check the brokerage contacts.')
        result['broker_notice_contacts']={key:_text(contacts.get(key,''),key,limit) for key,limit in NOTICE_CONTACT_LIMITS.items()}
        for key in ('email','email_2'):
            value=result['broker_notice_contacts'][key]
            if value and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):raise ValueError('Enter a valid brokerage contact email.')
    for key,choices in CHOICES.items():
        if data.get(key) not in choices:raise ValueError('Choose '+key.replace('_',' ')+'.')
        result[key]=data[key]
    for key in ('term_start','term_end'):
        value=data.get(key)
        if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError('Enter valid listing dates.')
        try:result[key]=date.fromisoformat(value).isoformat()
        except ValueError:raise ValueError('Enter valid listing dates.')
    if result['term_end']<result['term_start']:raise ValueError('The listing cannot end before it starts.')
    result['listing_price']=_number(data.get('listing_price'),'monthly rent')
    if Decimal(result['listing_price'])<=0:raise ValueError('The monthly rent must be greater than zero.')
    for key in ('lease_min_months','lease_max_months'):
        result[key]=_integer(data.get(key),key,minimum=1,required=True)
    if int(result['lease_min_months'])>int(result['lease_max_months']):raise ValueError('The maximum lease term cannot be shorter than the minimum.')
    for prefix in ('fee','renewal','sale_fee'):
        basis=result[prefix+'_basis'];value=data.get(prefix+'_amount')
        if basis=='other':
            if value not in ('',None):raise ValueError('Remove the unused percentage amount.')
            if not result[prefix+'_other']:raise ValueError('Enter the agreed '+prefix.replace('_',' ')+'.')
            result[prefix+'_amount']=''
        else:
            if result[prefix+'_other']:raise ValueError('Remove the unused compensation description.')
            result[prefix+'_amount']=_number(value,'compensation percentage',maximum=Decimal('9999.9999'),places=4)
    if result['fee_scope']=='with_other_broker':
        basis=data.get('cobroker_basis')
        if basis not in ('month_percentage','total_percentage','flat'):raise ValueError('Choose the other broker compensation basis.')
        result['cobroker_basis']=basis
        result['cobroker_amount']=_number(data.get('cobroker_amount'),'other broker compensation',
            maximum=Decimal('9999.9999') if basis!='flat' else Decimal('999999999999.99'),places=4 if basis!='flat' else 2)
        # Do not compare a flat fee to an unknown total-rent term. For matching
        # percentage bases the promised share cannot exceed the total fee.
        if basis==result['fee_basis'] and Decimal(result['cobroker_amount'])>Decimal(result['fee_amount']):
            raise ValueError('The other broker share cannot exceed the total compensation on the same basis.')
    else:
        if data.get('cobroker_basis') not in ('',None) or data.get('cobroker_amount') not in ('',None):
            raise ValueError('Remove other broker compensation from the broker-only option.')
        result.update(cobroker_basis='',cobroker_amount='')
    result['protection_days']=_integer(data.get('protection_days'),'protection days')
    result['mls_delay_days']=_integer(data.get('mls_delay_days'),'MLS delay days')
    if result['mls_filing']=='delayed':
        if not result['mls_delay_days'] or int(result['mls_delay_days'])<1 or not result['mls_delay_purpose']:
            raise ValueError('Enter the MLS delay and purpose.')
    elif result['mls_delay_days'] or result['mls_delay_purpose']:raise ValueError('Remove unused MLS delay details.')
    if (result['mls_filing']=='none')!=(result['internet_display']=='not_applicable'):
        raise ValueError('Internet instructions must match the MLS filing choice.')
    if result['make_ready']=='not_authorized':
        if data.get('make_ready_limit') not in ('',None) or result['make_ready_service_fee']:
            raise ValueError('Remove make-ready spending details when that authority is not given.')
        result['make_ready_limit']=''
    else:
        result['make_ready_limit']=_number(data.get('make_ready_limit'),'make-ready limit')
        if not result['make_ready_service_fee']:raise ValueError('Enter the agreed make-ready service fee, including zero if applicable.')
    age=data.get('built_before_1978','unanswered')
    if age not in ('yes','no','unanswered'):raise ValueError('Check the property age answer.')
    result['built_before_1978']=age
    addenda=data.get('addenda',[])
    if not isinstance(addenda,list) or any(not isinstance(v,str) or v not in tuple('ABCDEFGHIJKL') for v in addenda) or len(set(addenda))!=len(addenda):
        raise ValueError('Choose each applicable related document once.')
    if 'L' in addenda and not result['other_documents']:
        raise ValueError('Describe the other documents selected for this listing.')
    # An unknown construction year is not an assertion that the property is
    # newer. Keep the lead document requested until age is confirmed; the
    # package adapter must distinguish requested/pending from actually included.
    # Rental flood disclosure is requested for every rental, without guessing
    # the landlord's flood answers. The composer still proves actual inclusion.
    result['addenda']=sorted(set(addenda)|{'B'}|({'C'} if age!='no' else set())|({'L'} if result['other_documents'] else set()))
    include=data.get('include_rental_preferences',False)
    if not isinstance(include,bool):raise ValueError('Choose whether to include rental preferences.')
    result['include_rental_preferences']=include
    if not include and any(data.get(k) not in ('',None,'unspecified') for k in preference_keys):
        raise ValueError('Review the entered rental preferences before excluding them.')
    for key,limit in PREFERENCE_TEXT_LIMITS.items():result[key]=_text(data.get(key,''),key,limit)
    for key,options in PREFERENCE_CHOICES.items():
        value=data.get(key,'unspecified')
        if value not in (*options,'unspecified'):raise ValueError('Check '+key.replace('_',' ')+'.')
        result[key]=value
    for key in PREFERENCE_INTEGERS:result[key]=_integer(data.get(key),key)
    for key in PREFERENCE_AMOUNTS:
        value=data.get(key)
        percent_basis={'initial_late_amount':'initial_late_basis','tenant_replacement_amount':'tenant_replacement_basis',
                       'landlord_replacement_amount':'landlord_replacement_basis'}.get(key)
        is_percent=percent_basis and result[percent_basis]=='percentage'
        result[key]='' if value in ('',None) else _number(value,key.replace('_',' '),
            maximum=Decimal('100') if is_percent else Decimal('999999999999.99'),places=4 if is_percent else 2)
        if percent_basis and (bool(result[key])!=(result[percent_basis]!='unspecified')):
            raise ValueError('Choose the amount and basis together for '+key.replace('_',' ')+'.')
    for choice,selected,detail in [('rent_due','other','rent_due_other'),('yard','named_contractor','yard_contractor'),
        ('pool','named_contractor','pool_contractor'),('pool','other','pool_other')]:
        if (result[choice]==selected)!=bool(result[detail]):raise ValueError('Review '+detail.replace('_',' ')+'.')
    if result['animals']!='permitted' and any(result[k] for k in ('animal_restrictions','animal_deposit','animal_monthly_rent','animal_one_time_fee')):
        raise ValueError('Review the animal permission and related amounts together.')
    if '_for_signing' in data:
        if not isinstance(data['_for_signing'],bool):raise ValueError('Check the document rendering choice.')
        result['_for_signing']=data['_for_signing']
    return result


# Bottom-origin PDF points from the exact eleven-page source.
BLANKS = {
    'client_address':(1,[(121,606,453)]),'client_city_state_zip':(1,[(153,594,421)]),
    'client_phone':(1,[(110,581,464)]),'lot':(1,[(124,390,162)]),'block':(1,[(324,390,70)]),
    'subdivision':(1,[(405,390,169),(75,378,247)]),'city':(1,[(407,378,167)]),
    'county':(1,[(86,365,215)]),'property_address':(1,[(433,365,141),(75,353,400)]),
    'non_real_estate_items':(1,[(515,304,59),(75,291,499),(75,278,499)]),
    'exclusions':(1,[(308,256,266),(75,243,499)]),'listing_price':(1,[(188,155,98)]),
    'lease_min_months':(1,[(233,142,53)]),'lease_max_months':(1,[(425,142,33)]),
    'term_start':(1,[(184,97,111)]),'term_end':(1,[(434,97,140)]),
    'reimbursable_expenses':(3,[(214,398,360),(93,385,481)]),
    'protection_days':(3,[(544,343,30)]),'payment_county':(3,[(389,148,185),(75,135,205)]),
    'mls_delay_days':(4,[(485,612,26)]),'mls_delay_purpose':(4,[(347,601,227),(93,588,479)]),
    'scheduling_companies':(5,[(272,592,302)]),'make_ready_limit':(7,[(283,624,39)]),
    'financial_exceptions':(7,[(248,289,326)]),'liens':(7,[(499,277,75),(76,264,498)]),
    'common_area_fees':(7,[(206,201,368),(73,188,501)]),
    'health_safety_conditions':(7,[(203,163,371),(73,150,480)]),
    'special_provisions':(8,[(39,y,535) for y in (241,227,213,199,185,171)]),
    'other_documents':(9,[(72,457,502)]),
    'rent_due_other':(9,[(337,371,237)]),'late_after_days':(9,[(434,350,32)]),
    'daily_late_amount':(9,[(223,312,63)]),'animal_restrictions':(9,[(73,274,501)]),
    'animal_deposit':(9,[(218,230,32)]),'animal_monthly_rent':(9,[(292,217,66)]),
    'animal_one_time_fee':(9,[(309,204,85)]),'animal_violation_initial':(9,[(99,173,59)]),
    'animal_violation_daily':(9,[(213,173,37)]),'security_deposit':(9,[(165,89,409)]),
    'utilities_exceptions':(9,[(309,64,265)]),
    'guests_days':(10,[(344,726,230)]),'vehicle_count':(10,[(332,707,242)]),
    'trip_charge':(10,[(145,688,429)]),'keybox_last_days':(10,[(227,669,59)]),
    'keybox_withdrawal_fee':(10,[(479,669,95)]),'inventory_days':(10,[(339,650,54)]),
    'yard_contractor':(10,[(124,619,270)]),'pool_contractor':(10,[(140,587,281)]),
    'pool_other':(10,[(140,575,434)]),'repair_phone':(10,[(310,556,264)]),
    'unrepaired_items':(10,[(339,543,235)]),'liability_insurance':(10,[(482,524,61)]),
    'lease_special_provisions':(10,[(169,468,405),(73,455,465)]),
    'lease_other':(10,[(107,442,467),(73,429,501)]),
}
CHECKS = {
    'hoa':{'yes':(1,255,217),'no':(1,295,217)},
    'mls_filing':{'standard':(4,74,661),'delayed':(4,74,613),'none':(4,56,451)},
    'internet_display':{'hide_listing':(6,55,362),'hide_address':(6,55,350)},
    'keybox':{'yes':(5,127,476),'no':(5,164,476)},
    'intermediary':{'authorized':(5,38,307),'not_authorized':(6,38,730)},
    'make_ready':{'not_authorized':(7,55,659),'landlord_pays':(7,55,636),'broker_reimbursed':(7,55,636)},
    'signer_plan':{'clients_and_broker':(11,29,184),'clients_and_associate':(11,29,174)},
    'rent_due':{'first':(9,205,370),'other':(9,324,370)},
    'initial_late_basis':{'flat':(9,188,324),'percentage':(9,335,324)},
    'animals':{'not_permitted':(9,124,293),'permitted':(9,217,293)},
    'yard':dict(zip(('landlord','tenant','tenant_contractor','named_contractor'),[(10,215,631),(10,277,631),(10,330,631),(10,110,618)])),
    'pool':dict(zip(('landlord','tenant','tenant_contractor','named_contractor','other'),[(10,232,599),(10,294,599),(10,347,599),(10,126,587),(10,126,575)])),
    'tenant_replacement_basis':{'flat':(10,218,499),'percentage':(10,291,499)},
    'landlord_replacement_basis':{'flat':(10,218,486),'percentage':(10,291,486)},
}


def answer_layout(data, brokerage, associate):
    data=validate_answers(data);pages={p:[] for p in range(1,12)};overflow={}
    def put(page,value,label,blanks,size=8):
        entries=inline(value,blanks,size)
        if entries is None:
            overflow[label]=clean(value)
            entries=next((v for ref in ('See exhibit','Exhibit','Ref.','*') if (v:=inline(ref,blanks[:1],7)) is not None),None)
            if entries is None:raise ValueError('The answer continuation reference cannot fit this blank.')
        pages[page].extend(entries)
    for key,(page,blanks) in BLANKS.items():
        value=data[key]
        if key in ('term_start','term_end'):value=date.fromisoformat(value).strftime('%m/%d/%Y')
        put(page,value,LABELS[key],blanks)
    put(1,', '.join(data['client_names']),'Paragraph 1 - Landlords',[(102,632,472),(102,619,472)])
    put(1,'; '.join(filter(None,[data['client_email'],data['client_email_2']])),'Landlord contact email',[(112,569,462)])
    broker=brokerage.get('legal_name') or brokerage.get('name') or brokerage.get('dba_name') or ''
    put(1,broker,'Paragraph 1 - Broker',[(92,546,482),(93,533,481)])
    contacts=data.get('broker_notice_contacts',brokerage)
    for key,x,y,width in [('address',121,520,453),('city_state_zip',153,508,421),('phone',110,495,464)]:
        put(1,contacts.get(key),'Broker '+key,[(x,y,width)])
    put(1,'; '.join(filter(None,[contacts.get('email'),contacts.get('email_2')])),'Broker contact email',[(115,482,459)])
    fee_y=589 if data['fee_scope']=='with_other_broker' else 267
    for prefix,page,rows in [('fee',2,(fee_y,fee_y-20,fee_y-39)),('renewal',3,(663,650,637)),('sale_fee',3,(554,541))]:
        basis=data[prefix+'_basis'];index=0 if basis in ('month_percentage','percentage') else 1 if basis=='total_percentage' else len(rows)-1
        x,width=(124,54) if prefix=='fee' else (113,29) if prefix=='renewal' else (147,67)
        if basis=='other':x,width=(124,450) if prefix=='fee' else (110,464) if prefix=='renewal' else (147,427)
        label={'fee':'Paragraph 5A(1) - Total broker compensation' if data['fee_scope']=='with_other_broker' else 'Paragraph 5B(1) - Broker compensation',
            'renewal':'Paragraph 5E(1) - Renewal compensation','sale_fee':'Paragraph 5E(2) - Sale compensation'}[prefix]
        put(page,data[prefix+'_other'] if basis=='other' else data[prefix+'_amount'],label,[(x,rows[index],width)])
    if data['cobroker_basis']:
        basis=data['cobroker_basis'];row={'month_percentage':461,'total_percentage':448,'flat':435}[basis]
        put(2,data['cobroker_amount'],'Paragraph 5A(2) - Other broker compensation',[(129 if basis!='flat' else 194,row,49 if basis!='flat' else 92)])
    if data['make_ready']!='not_authorized':
        blanks=[(400,586,174),(110,573,197)] if data['make_ready']=='landlord_pays' else [(141,548,397)]
        put(7,data['make_ready_service_fee'],'Paragraph 11D - Make-ready service fee',blanks)
    for key,page,flat,percent in [('initial_late_amount',9,(224,325,98),(366,325,64)),
        ('tenant_replacement_amount',10,(250,499,17),(318,499,8)),('landlord_replacement_amount',10,(250,487,17),(318,487,8))]:
        basis=data[{'initial_late_amount':'initial_late_basis','tenant_replacement_amount':'tenant_replacement_basis','landlord_replacement_amount':'landlord_replacement_basis'}[key]]
        if basis!='unspecified':put(page,data[key],LABELS[key],[percent if basis=='percentage' else flat],7)
    for page in range(2,12):
        header=inline(data['property_address'],[(190,749,382)],8) or inline('Property identified in Paragraph 2',[(190,749,382)],8)
        pages[page].extend(header)
    for value,label,x,y,width in [(broker,'Broker printed name',29,226,197),
        (broker_license(broker,brokerage.get('license_number')),'Broker license',232,226,54),
        ((associate.get('name') or associate.get('agent_name')) if data['signer_plan']=='clients_and_associate' else '',
         'Associate printed name',29,154,197),
        (associate.get('license_number') if data['signer_plan']=='clients_and_associate' else '',
         'Associate license',232,154,54),
        (data['client_names'][0],'Landlord 1 printed name',326,226,248),
        (data['client_names'][1] if len(data['client_names'])==2 else '','Landlord 2 printed name',326,154,248)]:
        put(11,value,'Execution - '+label,[(x,y,width)])
    if overflow:
        # The source's own Other documents line identifies the attached exhibit.
        other=data['other_documents'];overflow.pop(LABELS['other_documents'],None)
        if other:overflow['Paragraph 19L - Other documents']=other
        pages[9]=[entry for entry in pages[9] if entry[1]!=457]
        put(9,'Answer continuation (attached)','Continuation reference',[(72,457,502)])
    return pages,overflow


def _overlay(data,brokerage,associate):
    data=validate_answers(data);pages,overflow=answer_layout(data,brokerage,associate)
    marks={p:[] for p in range(1,12)}
    for key,options in CHECKS.items():
        if data[key] in options:
            page,x,y=options[data[key]];marks[page].append((x,y))
    for key,page,x,rows in [('fee_basis',2,92,(589,569,550) if data['fee_scope']=='with_other_broker' else (267,247,228)),
        ('renewal_basis',3,74,(663,650,637)),('sale_fee_basis',3,110,(554,541))]:
        basis=data[key];index=0 if basis in ('month_percentage','percentage') else 1 if basis=='total_percentage' else len(rows)-1
        marks[page].append((x,rows[index]))
    if data['cobroker_basis']:marks[2].append((110,{'month_percentage':461,'total_percentage':448,'flat':435}[data['cobroker_basis']]))
    if data['mls_filing']!='none':marks[4].append((56,684))
    if data['make_ready']!='not_authorized':marks[7].append((75,585 if data['make_ready']=='landlord_pays' else 560))
    for key,y in [('animal_deposit',230),('animal_monthly_rent',217),('animal_one_time_fee',204)]:
        if data[key]!='':marks[9].append((72,y))
    marks[9].extend((38,596-12.65*(ord(code)-ord('A'))) for code in data['addenda'])
    if overflow or data['other_documents']:
        if 'L' not in data['addenda']:marks[9].append((38,457))
    out=BytesIO();canvas=Canvas(out,pagesize=(612,792))
    for page in range(1,12):
        for x,y,value,size in pages[page]:draw_text(canvas,value,x,y,size)
        for x,y in marks[page]:_mark(canvas,x,y)
        canvas.showPage()
    canvas.save();return out.getvalue(),overflow


def render_txr_1102(source_pdf_bytes,data,brokerage,associate):
    if hashlib.sha256(source_pdf_bytes).hexdigest()!=SOURCE_SHA256:raise ValueError('Use the reviewed January 5, 2026 lease-listing source.')
    data=validate_answers(data);source=PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages)!=11 or any(abs(float(p.mediabox.width)-612)>.01 or abs(float(p.mediabox.height)-792)>.01 for p in source.pages):
        raise ValueError('Keep all eleven original lease-listing pages.')
    overlay,overflow=_overlay(data,brokerage,associate);writer=PdfWriter()
    for page in source.pages:writer.add_page(page)
    _remove_member_footer(writer)
    for i,page in enumerate(PdfReader(BytesIO(overlay)).pages):writer.pages[i].merge_page(page)
    if overflow:
        overflow.pop(LABELS['property_address'],None)
        overflow.pop('Paragraph 1 - Landlords',None)
        overflow={'Property':data['property_address'],'Landlord(s)':', '.join(data['client_names']),**overflow}
        continuation=render_continuation(data,overflow,title='TXR-1102 - Answer Continuation',party_label='Landlord',
            description='Entered answers referenced in the attached lease-listing agreement.')
        writer.append(PdfReader(BytesIO(continuation)))
    out=BytesIO();writer.write(out);return out.getvalue()


def build_signwell_fields_txr1102(data,*,client_count=1,page_count=11):
    data=validate_answers(data)
    if isinstance(client_count,bool) or client_count not in (1,2) or client_count!=len(data['client_names']):raise ValueError('Match the named landlords and signing recipients.')
    if isinstance(page_count,bool) or not isinstance(page_count,int) or not 11<=page_count<=100:raise ValueError('Keep all source and continuation pages.')
    role='associate' if data['signer_plan']=='clients_and_associate' else 'broker';fields=[]
    def field(key,kind,page,x,y,width,height,recipient):
        item={'api_id':f'txr1102_{key}_p{page}','type':kind,'page':page,'x':x*4/3,'y':(792-y-height)*4/3,
            'width':width*4/3,'height':height*4/3,'recipient_id':recipient,'required':True}
        if kind=='date':item.update(date_format='MM/DD/YYYY',lock_sign_date=True)
        fields.append(item)
    for label,recipient,x,y in [('landlord1','1',324,194),(role,role,27,194),
        *([('landlord2','2',324,122)] if client_count==2 else [])]:
        field(label+'_signature','signature',11,x,y,180,16,recipient)
        field(label+'_date','date',11,x+198,y,54,16,recipient)
    for page in range(1,12):
        for label,recipient,x,width in [(role,role,307,38),('landlord1','1',402,38),
            *([('landlord2','2',450,45)] if client_count==2 else [])]:
            field(label+'_initials','initials',page,x,38,width,10,recipient)
    fields.extend(continuation_fields(data,client_count,page_count,source_pages=11,prefix='txr1102'))
    return [fields]

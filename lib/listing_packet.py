"""Compose a sale or lease listing packet from server-verified documents.

This is not a source resolver, upload endpoint or authorization boundary. The
caller must load owner-scoped records and verify each source/revision before
supplying its rendered PDF and source-specific signing fields. Missing related
documents remain pending; they never make an otherwise valid listing vanish.
No seller answers, receipt acknowledgements or delivery states are inferred.
"""
from copy import deepcopy
from dataclasses import dataclass, field as data_field
import hashlib
from io import BytesIO
import json
import math
import re

from pypdf import PdfReader, PdfWriter

from lib.txr_1101 import validate_answers


REVISION = 'listing-packet-composition-v2'
MAX_PAGES = 160
MAX_INPUT_BYTES = 20_000_000
DOCUMENT_CHOICES = (
    ('A', 'Information About Brokerage Services'),
    ('B', 'Seller’s Disclosure Notice'),
    ('C', 'Lead-based paint disclosure'),
    ('D', 'Existing survey affidavit or declaration'),
    ('E', 'Water or statutory tax district notice'),
    ('F', 'Public improvement district notice'),
    ('G', 'Owners’ association information request'),
    ('H', 'Mortgage information request'),
    ('I', 'Mineral clause information'),
    ('J', 'On-site sewer information'),
    ('K', 'Property insurance information'),
    ('L', 'Flood hazard information'),
    ('M', 'Condominium listing addendum'),
    ('N', 'Tenant keybox authorization'),
    ('O', 'Authorization to disclose and advertise information'),
    ('P', 'Groundwater and surface water rights disclosure'),
)


@dataclass(frozen=True)
class PreparedDocument:
    """Trusted renderer output, not browser-supplied base64/field coordinates.

    content_fingerprint binds source hash, renderer revision, saved answers and
    record version. Do not use the rendered PDF hash alone: PDF timestamps can
    differ across identical retries. The caller owns that content binding.
    recipient_map explicitly maps this form's local recipient IDs to the
    listing's already reviewed seller/associate/broker IDs.
    """
    code: str
    pdf: bytes
    fields: list
    recipient_map: dict
    content_fingerprint: str
    checkbox_groups: list = data_field(default_factory=list)
    conditional_rules: list = data_field(default_factory=list)
    contained_documents: dict = data_field(default_factory=dict)
    disclosure_binding: dict = data_field(default_factory=dict)
    remaining_actions: tuple = ()


@dataclass(frozen=True)
class ListingPacket:
    pdf: bytes
    fields: list
    manifest: dict
    content_fingerprint: str
    checkbox_groups: list = data_field(default_factory=list)
    conditional_rules: list = data_field(default_factory=list)


def _controls(document, recipients, prefix):
    """Namespace controls with their fields; never leave dangling references."""
    fields={f['api_id']:f for group in document.fields for f in group}
    groups=[];names=set()
    if not isinstance(document.checkbox_groups,list) or not isinstance(document.conditional_rules,list):
        raise ValueError('Review the document completion controls.')
    for original in document.checkbox_groups:
        group=deepcopy(original)
        if not isinstance(group,dict) or set(group)-{'group_name','recipient_id','checkbox_ids','validation','required','min_value','max_value','exact_value'}:
            raise ValueError('Review the checkbox selection requirements.')
        name=group.get('group_name');ids=group.get('checkbox_ids');recipient=group.get('recipient_id')
        if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',name) or name in names
                or not isinstance(ids,list) or len(ids)<2 or any(not isinstance(v,str) for v in ids)
                or len(set(ids))!=len(ids) or recipient not in document.recipient_map
                or document.recipient_map[recipient] not in recipients
                or any(key not in fields or fields[key].get('type')!='checkbox' or fields[key].get('recipient_id')!=recipient for key in ids)):
            raise ValueError('Review the checkbox field and signer assignments.')
        names.add(name)
        if group.get('validation')!='exact' or type(group.get('exact_value')) is not int or not 1<=group['exact_value']<=len(ids) or type(group.get('required')) is not bool:
            raise ValueError('Use an explicit exact-selection checkbox requirement.')
        group.update(group_name=prefix+name,checkbox_ids=[prefix+v for v in ids],recipient_id=document.recipient_map[recipient])
        groups.append(group)
    rules=[]
    for original in document.conditional_rules:
        rule=deepcopy(original)
        if not isinstance(rule,dict) or set(rule)-{'target_id','action_type','action_field_ids','conditions'}:
            raise ValueError('Review the conditional completion requirements.')
        target=rule.get('target_id');actions=rule.get('action_field_ids');conditions=rule.get('conditions')
        if (not isinstance(target,str) or target not in fields or rule.get('action_type') not in {'show','hide','require'}
                or not isinstance(actions,list) or not actions or any(not isinstance(v,str) or v not in fields or v==target for v in actions)
                or len(set(actions))!=len(actions) or not isinstance(conditions,list) or not 1<=len(conditions)<=5):
            raise ValueError('A conditional rule references an unavailable field.')
        owner=fields[target]['recipient_id']
        for index,condition in enumerate(conditions,start=1):
            if (not isinstance(condition,dict) or set(condition)-{'condition_type','status','field_api_ids','position','join_operator'}
                    or condition.get('condition_type') not in {'any_of','all_of','none_of','not_all_of'}
                    or condition.get('status') not in {'completed','not_completed'}
                    or condition.get('join_operator','and_operator') not in {'and_operator','or_operator'}
                    or not isinstance(condition.get('field_api_ids'),list) or not condition['field_api_ids']
                    or any(not isinstance(v,str) or v not in fields for v in condition['field_api_ids'])):
                raise ValueError('Review the conditional field trigger.')
            if any(fields[v]['recipient_id']!=owner for v in actions+condition['field_api_ids']):
                raise ValueError('A completion rule cannot change another signer’s fields.')
            condition.update(field_api_ids=[prefix+v for v in condition['field_api_ids']],position=index)
        rule.update(target_id=prefix+target,action_field_ids=[prefix+v for v in actions])
        rules.append(rule)
    return groups,rules


def _reader(payload):
    if not isinstance(payload, bytes) or not payload.startswith(b'%PDF') or len(payload) > MAX_INPUT_BYTES:
        raise ValueError('A prepared listing document is not a supported PDF.')
    try:
        reader = PdfReader(BytesIO(payload), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= MAX_PAGES:
            raise ValueError('Unsupported listing document page count or encryption.')
        for page in reader.pages:
            box = page.mediabox
            if any(not math.isfinite(float(v)) or float(v) <= 0 for v in (box.width, box.height)):
                raise ValueError('Review the dimensions before adding this document.')
        # Copying a cryptographically signed PDF would invalidate its signature.
        # Ordinary provider-rendered signatures remain printed source content.
        if any(field.get('/FT') == '/Sig' and field.get('/V') for field in (reader.get_fields() or {}).values()):
            raise ValueError('Keep the digitally certified original separate from this signing packet.')
        return reader
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('A prepared listing document could not be read.') from exc


def _fields(groups, reader, mapping, recipients, *, prefix, offset):
    if not isinstance(groups, list) or len(groups) > 1 or (groups and not isinstance(groups[0], list)):
        raise ValueError('Use one signing-field group for each prepared document.')
    if not isinstance(mapping, dict) or any(not isinstance(k, str) or not isinstance(v, str) or v not in recipients for k,v in mapping.items()):
        raise ValueError('Review the prepared document’s signer assignments.')
    result = []
    seen = set()
    for source in groups[0] if groups else []:
        if not isinstance(source, dict):
            raise ValueError('Review the prepared document’s signing fields.')
        field = deepcopy(source)
        local_id = field.get('recipient_id')
        if local_id not in mapping:
            raise ValueError('A prepared document requests an unreviewed signer.')
        api_id = field.get('api_id')
        if not isinstance(api_id, str) or not re.fullmatch(r'[A-Za-z0-9_\-]{1,180}', api_id) or api_id in seen:
            raise ValueError('Each prepared signing field needs a unique identifier.')
        seen.add(api_id)
        page_number = field.get('page')
        if type(page_number) is not int or not 1 <= page_number <= len(reader.pages):
            raise ValueError('A prepared signing field points outside its document.')
        page = reader.pages[page_number-1]
        if (page.get('/Rotate',0) not in (0,None) or page.get('/UserUnit',1) != 1
                or list(page.cropbox) != list(page.mediabox)
                or float(page.mediabox.left) != 0 or float(page.mediabox.bottom) != 0):
            raise ValueError('Review the signing map for this page orientation.')
        coords = [field.get(key) for key in ('x','y','width','height')]
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in coords):
            raise ValueError('A prepared signing field has invalid bounds.')
        x,y,width,height = coords
        if (x < 0 or y < 0 or width <= 0 or height <= 0
                or x+width > float(page.mediabox.width)*4/3 + 0.01
                or y+height > float(page.mediabox.height)*4/3 + 0.01):
            raise ValueError('A prepared signing field extends beyond its page.')
        field.update(api_id=prefix+api_id, page=page_number+offset, recipient_id=mapping[local_id])
        result.append(field)
    return result


def assemble_listing_packet(answers, listing_pdf, listing_fields, *, documents=(), pending_reasons=None):
    """Return one actual merged PDF, one field group and an honest manifest.

    Primary and continuation pages always stay together. Related documents are
    ordered by the source Paragraph 19 checklist, not arrival order. Only
    PDFs actually merged are marked included; all other selected items remain
    pending. Invalid supplied documents fail visibly instead of disappearing.
    Caller authorization and source validation cannot be replaced by this API.
    """
    data = validate_answers(answers)
    return _compose_listing_packet(data,listing_pdf,listing_fields,documents=documents,pending_reasons=pending_reasons,
        document_choices=DOCUMENT_CHOICES,primary_code='TXR-1101',primary_label='Sale listing agreement',
        revision=REVISION,allow_seller_disclosure=True)


def assemble_lease_listing_packet(answers, listing_pdf, listing_fields, *, documents=(), pending_reasons=None):
    """Use the lease's own answers/checklist; never relabel a sale disclosure."""
    from lib.txr_1102 import validate_answers as validate_lease, DOCUMENT_CHOICES as LEASE_DOCUMENT_CHOICES
    return _compose_listing_packet(validate_lease(answers),listing_pdf,listing_fields,
        documents=documents,pending_reasons=pending_reasons,document_choices=LEASE_DOCUMENT_CHOICES,
        primary_code='TXR-1102',primary_label='Lease listing agreement',
        revision='lease-listing-packet-composition-v1',allow_seller_disclosure=False)


def _compose_listing_packet(data, listing_pdf, listing_fields, *, documents, pending_reasons,
                            document_choices, primary_code, primary_label, revision, allow_seller_disclosure):
    if not isinstance(documents, (tuple,list)):
        raise ValueError('Choose prepared related documents.')
    selected = data['addenda']
    labels = dict(document_choices)
    by_code = {}
    contained_by = {}
    for document in documents:
        if not isinstance(document, PreparedDocument) or document.code not in selected or document.code in by_code:
            raise ValueError('Add each selected related document only once.')
        if not allow_seller_disclosure and document.disclosure_binding:
            raise ValueError('Use lease-specific related documents, not a sale disclosure.')
        if (not isinstance(document.remaining_actions,(tuple,list)) or len(document.remaining_actions)>10
                or any(not isinstance(action,str) or not action.strip() or len(action)>300 for action in document.remaining_actions)):
            raise ValueError('Review the remaining document steps.')
        if not isinstance(document.content_fingerprint,str) or not re.fullmatch(r'[a-f0-9]{64}',document.content_fingerprint):
            raise ValueError('The prepared document’s saved content could not be confirmed.')
        by_code[document.code] = document
        if not isinstance(document.contained_documents, dict):
            raise ValueError('Review the combined disclosure documents.')
        for code, bounds in document.contained_documents.items():
            if (code not in selected or code <= document.code or code in contained_by
                    or not isinstance(bounds, (tuple,list)) or len(bounds) != 2
                    or any(type(n) is not int for n in bounds) or not 1 <= bounds[0] <= bounds[1]):
                raise ValueError('Review the combined disclosure document pages.')
            contained_by[code] = (document.code, bounds)
    if set(contained_by) & set(by_code):
        raise ValueError('Add each selected related document only once.')
    if (not isinstance(listing_pdf,bytes) or any(not isinstance(item.pdf,bytes) for item in by_code.values())
            or len(listing_pdf)+sum(len(item.pdf) for item in by_code.values()) > MAX_INPUT_BYTES):
        raise ValueError('The prepared listing documents exceed the packet size limit.')
    recipients = {str(n) for n in range(1,len(data['client_names'])+1)}
    recipients.add('associate' if data['signer_plan']=='clients_and_associate' else 'broker')
    primary = _reader(listing_pdf)
    fields = _fields(listing_fields,primary,{value:value for value in recipients},recipients,prefix='',offset=0)
    checkbox_groups=[];conditional_rules=[]
    # Retain primary api_ids for compatibility with its existing source map.
    writer = PdfWriter()
    if primary.get_fields(): primary.add_form_topname('hof_listing_primary')
    writer.append(primary,import_outline=False)
    page_count = len(primary.pages)
    included = [{'code':primary_code,'label':primary_label,'status':'included',
                 'start_page':1,'end_page':page_count}]
    pending = []
    for code in selected:
        if code in contained_by:
            parent, (first, last) = contained_by[code]
            parent_row = next(row for row in included if row['code'] == parent)
            if last > parent_row['end_page'] - parent_row['start_page'] + 1:
                raise ValueError('A combined disclosure points outside its document.')
            included.append({'code':code,'label':labels[code],'status':'included',
                'start_page':parent_row['start_page']+first-1,'end_page':parent_row['start_page']+last-1,
                'included_with':parent,'content_fingerprint':parent_row['content_fingerprint']})
            continue
        prepared = by_code.get(code)
        if prepared is None:
            row = {'code':code,'label':labels[code],'status':'pending'}
            if pending_reasons and pending_reasons.get(code): row['reason'] = pending_reasons[code]
            pending.append(row)
            continue
        reader = _reader(prepared.pdf)
        if page_count+len(reader.pages) > MAX_PAGES:
            raise ValueError('The listing packet is too large. Keep additional documents separate.')
        fields.extend(_fields(prepared.fields,reader,prepared.recipient_map,recipients,
                              prefix=f'listing_{code}_',offset=page_count))
        groups,rules=_controls(prepared,recipients,f'listing_{code}_')
        checkbox_groups.extend(groups);conditional_rules.extend(rules)
        if len(conditional_rules)>10:
            raise ValueError('This packet exceeds the signing service’s conditional-rule limit.')
        if reader.get_fields(): reader.add_form_topname(f'hof_listing_{code}')
        writer.append(reader,import_outline=False)
        included.append({'code':code,'label':labels[code],'status':'included',
                         'start_page':page_count+1,'end_page':page_count+len(reader.pages),
                         'content_fingerprint':prepared.content_fingerprint})
        if prepared.remaining_actions:
            included[-1]['remaining_actions']=list(prepared.remaining_actions)
        page_count += len(reader.pages)
    if len({field['api_id'] for field in fields}) != len(fields):
        raise ValueError('The listing packet contains conflicting signing fields.')
    output = BytesIO();writer.write(output)
    manifest = {'revision':revision,'page_count':page_count,'included':included,'pending':pending,
                'other_documents':data['other_documents'],'has_pending_documents':bool(pending or data['other_documents'])}
    if allow_seller_disclosure and by_code.get('B') and by_code['B'].disclosure_binding:
        manifest['seller_disclosure'] = deepcopy(by_code['B'].disclosure_binding)
    # Stable content identity, not a volatile renderer timestamp. The existing
    # delivery layer additionally binds primary source/revision, identity and
    # these combined fields and actual recipients before any invitation.
    fingerprint = hashlib.sha256(json.dumps({'answers':{key:value for key,value in data.items() if key!='_for_signing'},'manifest':manifest,'fields':fields,
        'checkbox_groups':checkbox_groups,'conditional_rules':conditional_rules},
        sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    # Avoid rewriting a standalone source when nothing has actually been added.
    return ListingPacket(output.getvalue() if by_code else listing_pdf,[fields],deepcopy(manifest),fingerprint,checkbox_groups,conditional_rules)

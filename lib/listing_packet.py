"""Compose a sale-listing packet from server-verified prepared documents.

This is not a source resolver, upload endpoint or authorization boundary. The
caller must load owner-scoped records and verify each source/revision before
supplying its rendered PDF and source-specific signing fields. Missing related
documents remain pending; they never make an otherwise valid listing vanish.
No seller answers, receipt acknowledgements or delivery states are inferred.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import math
import re

from pypdf import PdfReader, PdfWriter

from lib.txr_1101 import validate_answers


REVISION = 'listing-packet-composition-v1'
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


@dataclass(frozen=True)
class ListingPacket:
    pdf: bytes
    fields: list
    manifest: dict
    content_fingerprint: str


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


def assemble_listing_packet(answers, listing_pdf, listing_fields, *, documents=()):
    """Return one actual merged PDF, one field group and an honest manifest.

    Primary and continuation pages always stay together. Related documents are
    ordered by the source Paragraph 19 checklist, not arrival order. Only
    PDFs actually merged are marked included; all other selected items remain
    pending. Invalid supplied documents fail visibly instead of disappearing.
    Caller authorization and source validation cannot be replaced by this API.
    """
    data = validate_answers(answers)
    if not isinstance(documents, (tuple,list)):
        raise ValueError('Choose prepared related documents.')
    selected = data['addenda']
    labels = dict(DOCUMENT_CHOICES)
    by_code = {}
    for document in documents:
        if not isinstance(document, PreparedDocument) or document.code not in selected or document.code in by_code:
            raise ValueError('Add each selected related document only once.')
        if not isinstance(document.content_fingerprint,str) or not re.fullmatch(r'[a-f0-9]{64}',document.content_fingerprint):
            raise ValueError('The prepared document’s saved content could not be confirmed.')
        by_code[document.code] = document
    if (not isinstance(listing_pdf,bytes) or any(not isinstance(item.pdf,bytes) for item in by_code.values())
            or len(listing_pdf)+sum(len(item.pdf) for item in by_code.values()) > MAX_INPUT_BYTES):
        raise ValueError('The prepared listing documents exceed the packet size limit.')
    recipients = {str(n) for n in range(1,len(data['client_names'])+1)}
    recipients.add('associate' if data['signer_plan']=='clients_and_associate' else 'broker')
    primary = _reader(listing_pdf)
    fields = _fields(listing_fields,primary,{value:value for value in recipients},recipients,prefix='',offset=0)
    # Retain primary api_ids for compatibility with its existing source map.
    writer = PdfWriter()
    if primary.get_fields(): primary.add_form_topname('hof_listing_primary')
    writer.append(primary,import_outline=False)
    page_count = len(primary.pages)
    included = [{'code':'TXR-1101','label':'Sale listing agreement','status':'included',
                 'start_page':1,'end_page':page_count}]
    pending = []
    for code in selected:
        prepared = by_code.get(code)
        if prepared is None:
            pending.append({'code':code,'label':labels[code],'status':'pending'})
            continue
        reader = _reader(prepared.pdf)
        if page_count+len(reader.pages) > MAX_PAGES:
            raise ValueError('The listing packet is too large. Keep additional documents separate.')
        fields.extend(_fields(prepared.fields,reader,prepared.recipient_map,recipients,
                              prefix=f'listing_{code}_',offset=page_count))
        if reader.get_fields(): reader.add_form_topname(f'hof_listing_{code}')
        writer.append(reader,import_outline=False)
        included.append({'code':code,'label':labels[code],'status':'included',
                         'start_page':page_count+1,'end_page':page_count+len(reader.pages),
                         'content_fingerprint':prepared.content_fingerprint})
        page_count += len(reader.pages)
    if len({field['api_id'] for field in fields}) != len(fields):
        raise ValueError('The listing packet contains conflicting signing fields.')
    output = BytesIO();writer.write(output)
    manifest = {'revision':REVISION,'page_count':page_count,'included':included,'pending':pending,
                'other_documents':data['other_documents'],'has_pending_documents':bool(pending or data['other_documents'])}
    # Stable content identity, not a volatile renderer timestamp. The existing
    # delivery layer additionally binds primary source/revision, identity and
    # these combined fields and actual recipients before any invitation.
    fingerprint = hashlib.sha256(json.dumps({'answers':{key:value for key,value in data.items() if key!='_for_signing'},'manifest':manifest,'fields':fields},
        sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    # Avoid rewriting a standalone source when nothing has actually been added.
    return ListingPacket(output.getvalue() if by_code else listing_pdf,[fields],deepcopy(manifest),fingerprint)

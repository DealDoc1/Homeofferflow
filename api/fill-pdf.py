import json
import os
import base64
import hashlib
import hmac
import httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler

# ── CONFIG ──
RESEND_API_KEY   = os.environ.get('RESEND_API_KEY', '')
STRIPE_WHSEC     = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
SIGNWELL_API_KEY = os.environ.get('SIGNWELL_API_KEY', '')
FROM_EMAIL       = 'offers@homeofferflow.com'
SUPPORT_EMAIL    = 'support@homeofferflow.com'
BASE_URL         = 'https://homeofferflow.com'

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PDF      = os.path.join(BASE_DIR, '20-18_0.pdf')
FINANCING_PDF = os.path.join(BASE_DIR, 'third_party_financing_addendum.pdf')
HOA_PDF       = os.path.join(BASE_DIR, 'hoa_addendum.pdf')
SALE_CONT_PDF = os.path.join(BASE_DIR, 'sale_of_other_property_addendum.pdf')
BACKUP_PDF    = os.path.join(BASE_DIR, 'back_up_contract_addendum.pdf')

# ── SIGNWELL COORDINATE MAP ──
# All coordinates as percentages of page (top-left origin)
# Format: [x%, y%, w%, h%]

# Main contract initials - bottom of pages 1-8
# Each page has: buyer1_initials, buyer2_initials, seller1_initials, seller2_initials
MAIN_INITIALS = {
    1: [[34.43,96.15,5.77,1.15],[41.25,96.15,5.96,1.15],[56.63,96.15,6.63,1.15],[64.71,96.15,5.90,1.15]],
    2: [[34.43,95.83,5.77,1.48],[41.34,95.83,6.00,1.48],[56.63,95.83,5.77,1.48],[64.71,95.89,5.90,1.41]],
    3: [[34.43,95.63,5.77,1.67],[41.44,95.63,5.77,1.67],[56.63,95.63,5.77,1.67],[64.71,95.63,5.90,1.67]],
    4: [[34.43,96.05,5.77,1.26],[41.34,96.05,5.77,1.26],[56.63,96.05,6.63,1.26],[64.82,96.05,5.81,1.26]],
    5: [[34.43,96.05,5.77,1.26],[41.34,96.05,5.77,1.26],[56.63,96.05,6.63,1.26],[64.71,96.05,5.90,1.26]],
    6: [[34.43,95.61,5.77,1.69],[41.34,95.70,5.77,1.62],[56.63,95.69,6.63,1.60],[64.71,95.77,5.90,1.53]],
    7: [[34.53,95.91,5.82,1.63],[41.06,95.88,6.01,1.62],[56.31,95.83,6.83,1.63],[64.44,95.81,6.23,1.62]],
    8: [[34.53,96.10,5.77,1.28],[41.44,96.22,6.01,1.28],[56.63,96.22,6.63,1.28],[64.71,96.22,5.90,1.28]],
}

# Main contract page 9 signatures
MAIN_SIGS = [
    [11.70, 47.89, 36.86, 4.04],  # Buyer 1
    [51.29, 47.89, 37.88, 4.04],  # Seller 1
    [11.70, 61.57, 36.86, 4.04],  # Buyer 2
    [51.29, 61.63, 37.88, 4.04],  # Seller 2
]

# Addenda signature positions (last sig page, 2 buyer + 2 seller)
FINANCING_INITIALS_P1 = [[34.43,96.0,5.77,1.2],[41.34,96.0,5.77,1.2],[56.63,96.0,6.63,1.2],[64.71,96.0,5.90,1.2]]
FINANCING_SIGS = [
    [9.0, 74.0, 38.0, 4.04],   # Buyer 1
    [52.0, 74.0, 38.0, 4.04],  # Seller 1
    [9.0, 83.0, 38.0, 4.04],   # Buyer 2
    [52.0, 83.0, 38.0, 4.04],  # Seller 2
]

HOA_SIGS = [
    [9.0, 82.0, 38.0, 4.04],   # Buyer 1
    [52.0, 82.0, 38.0, 4.04],  # Seller 1
    [9.0, 89.0, 38.0, 4.04],   # Buyer 2
    [52.0, 89.0, 38.0, 4.04],  # Seller 2
]

SALE_SIGS = [
    [9.12, 64.36, 39.71, 4.04],   # Buyer 1
    [51.05, 64.36, 40.42, 4.04],  # Seller 1
    [9.04, 72.02, 39.62, 4.04],   # Buyer 2
    [51.13, 71.96, 40.34, 4.04],  # Seller 2
]

BACKUP_INITIALS_P1 = [[34.43,96.0,5.77,1.2],[41.34,96.0,5.77,1.2],[56.63,96.0,6.63,1.2],[64.71,96.0,5.90,1.2]]
BACKUP_SIGS = [
    [10.78, 18.27, 38.82, 4.04],  # Buyer 1
    [52.63, 18.33, 37.71, 4.04],  # Seller 1
    [10.87, 27.70, 38.74, 4.04],  # Buyer 2
    [52.96, 27.70, 37.47, 4.04],  # Seller 2
]


def fmt_money(val):
    try:
        return f'${int(float(val)):,}'
    except:
        return str(val) if val else ''


def fmt_date(val):
    if not val:
        return ''
    try:
        from datetime import datetime
        d = datetime.strptime(val, '%Y-%m-%d')
        return d.strftime('%B %d, %Y').replace(' 0', ' ')
    except:
        return val


def parse_lot_block(lot_str):
    import re
    lot_num = block_num = ''
    if not lot_str:
        return lot_num, block_num
    lot_m = re.search(r'lot\s*(\S+)', lot_str, re.I)
    blk_m = re.search(r'block\s*(\S+)', lot_str, re.I)
    lot_num   = lot_m.group(1) if lot_m else ''
    block_num = blk_m.group(1) if blk_m else ''
    return lot_num, block_num


def fill_and_merge(offer):
    from pypdf import PdfReader, PdfWriter

    s = offer
    lot_num, block_num = parse_lot_block(s.get('lot', ''))
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"

    try:
        price = float(s.get('price', 0))
        loan  = float(s.get('loanAmount', 0))
        cash  = price - loan
    except:
        price = loan = cash = 0

    buyer_name = s.get('buyer1', '')
    if s.get('buyer2'):
        buyer_name += f" and {s['buyer2']}"

    has_loan      = s.get('financing') in ['conventional', 'fha', 'va', 'usda']
    has_hoa       = s.get('hoa') in ['yes', 'unknown']
    has_sale_cont = s.get('saleContingency') == 'yes'
    has_backup    = s.get('backupOffer') == 'yes'
    has_mud       = s.get('mud') in ['yes', 'unknown']
    survey        = s.get('survey', '')
    title_payer   = s.get('titlePayer', 'seller')
    title_amend   = s.get('titleAmendment', 'i')
    seller_disc   = s.get('sellerDisclosure', 'received')
    as_is         = s.get('asIs', 'yes')

    # ── TEXT FIELDS ──
    field_values = {
        '1 PARTIES The parties to this contract are': s.get('seller', ''),
        'Seller and':                                  buyer_name,
        'A LAND Lot':       lot_num,
        'Block':            block_num,
        'undefined':        s.get('subdiv', ''),
        'Addition City of': s.get('city', ''),
        'County of':        s.get('county', ''),
        'Texas known as':   addr_full,
        'undefined_2': fmt_money(cash) if has_loan else fmt_money(price),
        'undefined_4': fmt_money(loan) if has_loan else '',
        'undefined_5': fmt_money(price),
        'as earnest money to':   fmt_money(s.get('earnest')),
        'as earnest money to 2': fmt_money(s.get('earnest')),
        'acknowledged by Seller and Buyers agreement to pay Seller':   fmt_money(s.get('optionFee')),
        'acknowledged by Seller and Buyers agreement to pay Seller 1': str(s.get('optionDays', '')),
        'acknowledged by Seller and Buyers agreement to pay Seller2':  fmt_money(s.get('optionFee')),
        'Option Fee in the form of': fmt_money(s.get('optionFee')),
        'insurance Title Policy issued by': s.get('titleCompany', ''),
        'A The closing of the sale will be on or before': fmt_date(s.get('closingDate')),
        # Buyer contact info (Section 21)
        'when mailed to': s.get('buyerMailAddr', ''),
        'Phone 51':       s.get('buyerPhone', ''),
        'AC1':            s.get('buyerEmail', ''),
        # Buyer agent info (Section 8/10 broker info)
        'Associates Name':              s.get('agentName', '') if s.get('hasBuyerAgent') == 'yes' else '',
        'License No':                   s.get('agentLicense', '') if s.get('hasBuyerAgent') == 'yes' else '',
        'Associates Email Address':     s.get('agentEmail', '') if s.get('hasBuyerAgent') == 'yes' else '',
        'Phone':                        s.get('agentPhone', '') if s.get('hasBuyerAgent') == 'yes' else '',
        'Other Broker Firm':            s.get('agentBrokerage', '') if s.get('hasBuyerAgent') == 'yes' else '',
        # Seller concessions (Section 12A(1)(c))
        'Buyers Expenses as allowed by the lender': fmt_money(s.get('concessionAmount', '')) if s.get('wantsConcessions') == 'yes' else '',
        # Intended use (Section 6D)
        'Commitment other than items 6A1 through 9 above or which prohibit the following use': s.get('intendedUse', ''),
        # Seller disclosure days
        'Within': str(s.get('disclosureDays', '3')) if seller_disc == 'notReceived' else '',
        # Survey days
        'receipt or the date specified in this paragraph whichever is earlier': str(s.get('surveyDays', '7')),
        # Address headers
        'Contract Concerning':   addr_full,
        'Contract Concerning_2': addr_full,
        'Contract Concerning_3': addr_full,
        'Contract Concerning_4': addr_full,
        'Address of Property':   addr_full,
        'Address of Property_2': addr_full,
        'Addr of Prop':          addr_full,
    }

    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, field_values)

    # ── CHECKBOXES ──
    checkbox_map = {
        'Third Party Financing Addendum': has_loan,
        '1Within':   survey == 'sellerExisting',
        '2 Within':  survey == 'buyerNew',
        '3Within':   survey == 'noSurvey',
        'A TITLE POLICY Seller shall furnish to Buyer at': title_payer == 'seller',
        'Sellers':   title_payer == 'seller',
        'Seller':    title_payer == 'buyer',
        'i will not be amended or deleted from the title policy or': title_amend == 'i',
        'ii will be amended to read shortages in area at the expense of': title_amend in ['ii_buyer','ii_seller'],
        'Buyer':     title_amend == 'ii_buyer',
        'is':        has_hoa,
        'is not':    not has_hoa,
        '1 Buyer accepts the Property As Is': as_is == 'yes',
        '2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the': as_is == 'repairs',
        'upon':      s.get('possession') == 'funding',
        'Addendum for Property Subject to':       has_hoa,
        'Addendum for Sale of Other Property by': has_sale_cont,
        'Addendum for BackUp Contract':           has_backup,
        'PID':                                    has_mud,
        # Seller disclosure
        'Within one':   seller_disc == 'received',
        'Within two':   seller_disc == 'notReceived',
        'Within three': seller_disc == 'exempt',
        # Buyer agent
        'Buyer only': s.get('hasBuyerAgent') == 'yes',
    }

    for field_name, should_check in checkbox_map.items():
        val = '/Yes' if should_check else '/Off'
        try:
            for page in writer.pages:
                writer.update_page_form_field_values(page, {field_name: val})
        except:
            pass

    # ── MERGE ADDENDA ──
    addenda_info = []  # (path, pages, has_initials_p1)
    if has_loan:
        addenda_info.append((FINANCING_PDF, 2, True))
    if has_hoa:
        addenda_info.append((HOA_PDF, 1, False))
    if has_sale_cont:
        addenda_info.append((SALE_CONT_PDF, 1, False))
    if has_backup:
        addenda_info.append((BACKUP_PDF, 2, True))

    for path, pages, has_init in addenda_info:
        try:
            writer.append(PdfReader(path))
        except Exception as e:
            print(f'Warning: could not load addendum {path}: {e}')

    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue(), addenda_info


def build_signwell_fields(offer, addenda_info):
    """Build SignWell field placement for the complete merged document."""
    has_buyer2  = bool(offer.get('buyer2', '').strip())
    has_seller2 = False  # sellers don't sign via our flow — listing agent handles

    fields = []
    field_id = 1

    def make_field(signer_id, ftype, page, coords, field_id):
        x, y, w, h = coords
        return {
            "id": str(field_id),
            "type": ftype,  # "signature" or "initials"
            "placeholder_uuid": None,
            "page": page,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "required": True,
            "signer_id": signer_id,
        }

    # Signer IDs: buyer1 = "1", buyer2 = "2" (if co-buyer)
    # Main contract pages 1-8: initials
    for pg in range(1, 9):
        if pg not in MAIN_INITIALS:
            continue
        coords_list = MAIN_INITIALS[pg]
        # Buyer 1 initials
        fields.append(make_field("1", "initials", pg, coords_list[0], field_id)); field_id += 1
        # Buyer 2 initials (if co-buyer)
        if has_buyer2:
            fields.append(make_field("2", "initials", pg, coords_list[1], field_id)); field_id += 1

    # Main contract page 9: signatures
    fields.append(make_field("1", "signature", 9, MAIN_SIGS[0], field_id)); field_id += 1
    if has_buyer2:
        fields.append(make_field("2", "signature", 9, MAIN_SIGS[2], field_id)); field_id += 1

    # Addenda
    current_page = 11  # main contract is 11 pages

    addenda_sigs_map = {
        FINANCING_PDF: (FINANCING_SIGS, FINANCING_INITIALS_P1, 2),
        HOA_PDF:       (HOA_SIGS, None, 1),
        SALE_CONT_PDF: (SALE_SIGS, None, 1),
        BACKUP_PDF:    (BACKUP_SIGS, BACKUP_INITIALS_P1, 2),
    }

    for path, num_pages, has_init in addenda_info:
        sig_coords, init_coords, _ = addenda_sigs_map.get(path, ([], None, num_pages))

        # Initials on page 1 of addendum (if applicable)
        if init_coords and has_init:
            p = current_page + 1
            fields.append(make_field("1", "initials", p, init_coords[0], field_id)); field_id += 1
            if has_buyer2:
                fields.append(make_field("2", "initials", p, init_coords[1], field_id)); field_id += 1

        # Signatures on last page of addendum
        sig_page = current_page + num_pages
        fields.append(make_field("1", "signature", sig_page, sig_coords[0], field_id)); field_id += 1
        if has_buyer2:
            fields.append(make_field("2", "signature", sig_page, sig_coords[2], field_id)); field_id += 1

        current_page += num_pages

    return fields


def send_to_signwell(pdf_bytes, offer, addenda_info):
    """Upload filled PDF to SignWell and create signing request."""
    api_key  = SIGNWELL_API_KEY
    auth     = base64.b64encode(f"access:{api_key}".encode()).decode()
    headers  = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

    pdf_b64  = base64.b64encode(pdf_bytes).decode()
    buyer1   = offer.get('buyer1', 'Buyer')
    buyer1_email = offer.get('buyerEmail') or offer.get('_paymentEmail', '')
    buyer2   = offer.get('buyer2', '').strip()
    addr     = offer.get('address', 'Property')

    signers = [
        {
            "id": "1",
            "name": buyer1,
            "email": buyer1_email,
            "order": 1,
        }
    ]
    if buyer2 and offer.get('buyer2Email'):
        signers.append({
            "id": "2",
            "name": buyer2,
            "email": offer.get('buyer2Email', ''),
            "order": 2,
        })

    fields = build_signwell_fields(offer, addenda_info)

    payload = {
        "test_mode": False,
        "files": [{
            "name": f"HomeOfferFlow_Offer_{addr.replace(' ','_')}.pdf",
            "file_base64": pdf_b64,
        }],
        "name": f"Offer — {addr}",
        "subject": f"Please sign your offer: {addr}",
        "message": f"Your HomeOfferFlow offer for {addr} is ready to sign. Please review and sign below.",
        "signers": signers,
        "fields": fields,
        "send_emails": True,
        "allow_decline": True,
        "redirect_url": f"{BASE_URL}/?signed=true",
        "callback_url": f"{BASE_URL}/api/fill-pdf",
    }

    resp = httpx.post(
        "https://www.signwell.com/api/v1/documents/",
        headers=headers,
        json=payload,
        timeout=60
    )

    if resp.status_code in [200, 201]:
        data = resp.json()
        return data.get('id'), data.get('signers', [{}])[0].get('sign_url', '')
    else:
        raise Exception(f"SignWell error {resp.status_code}: {resp.text[:300]}")


def send_confirmation_email(to_email, buyer_name, addr, sign_url):
    """Send email with signing link."""
    payload = {
        'from': FROM_EMAIL,
        'to': [to_email],
        'bcc': [SUPPORT_EMAIL],
        'subject': f'Your Offer is Ready to Sign — {addr}',
        'html': f'''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2 style="color:#1a2f4a;">Your Offer is Ready to Sign, {buyer_name}!</h2>
          <p>Your HomeOfferFlow TREC offer for <strong>{addr}</strong> has been prepared and is ready for your signature.</p>
          <div style="text-align:center;margin:2rem 0;">
            <a href="{sign_url}" style="background:#c8973f;color:#0d1f35;padding:1rem 2rem;border-radius:8px;text-decoration:none;font-weight:700;font-size:1rem;">
              Review & Sign Your Offer →
            </a>
          </div>
          <h3 style="color:#1a2f4a;">After Signing:</h3>
          <ol>
            <li>You'll be able to <strong>send directly to the listing agent</strong> or download to send yourself</li>
            <li><strong>Deliver earnest money</strong> to the title company within 3 days of acceptance</li>
            <li><strong>Option period begins</strong> on the Effective Date — schedule your inspection right away</li>
          </ol>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.85rem;">
            ⚠️ <strong>Important:</strong> HomeOfferFlow is not a law firm. This is not legal advice.
            Consider having a licensed Texas agent or attorney review before submitting.
          </p>
          <p style="color:#666;font-size:0.85rem;">
            Questions? Reply to this email or visit homeofferflow.com<br>
            HomeOfferFlow · BrewBQ Investments LLC · Texas
          </p>
        </div>
        ''',
    }
    resp = httpx.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'},
        json=payload,
        timeout=30
    )
    return resp.status_code, resp.text


def handle_signwell_callback(event):
    """Handle SignWell webhook — document fully signed."""
    if event.get('event_type') != 'document_completed':
        return {'status': 'ignored'}

    doc = event.get('data', {})
    doc_id   = doc.get('id')
    signers  = doc.get('signers', [])
    buyer_email = signers[0].get('email', '') if signers else ''

    # Download completed PDF from SignWell
    auth = base64.b64encode(f"access:{SIGNWELL_API_KEY}".encode()).decode()
    resp = httpx.get(
        f"https://www.signwell.com/api/v1/documents/{doc_id}/completed_pdf/",
        headers={"Authorization": f"Basic {auth}"},
        timeout=60
    )
    if resp.status_code != 200:
        raise Exception(f"Could not download signed PDF: {resp.status_code}")

    signed_pdf = resp.content
    signed_b64 = base64.b64encode(signed_pdf).decode()

    # Get document name for filename
    doc_name = doc.get('name', 'Signed Offer')
    filename = f"{doc_name.replace(' ','_')}_SIGNED.pdf"

    # Email signed PDF to buyer with post-sign options
    buyer_name = signers[0].get('name', 'Buyer') if signers else 'Buyer'
    addr = doc_name.replace('Offer — ', '').strip()

    payload = {
        'from': FROM_EMAIL,
        'to': [buyer_email],
        'bcc': [SUPPORT_EMAIL],
        'subject': f'✅ Signed Offer Ready — {addr}',
        'html': f'''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2 style="color:#4a8c6f;">Your Offer is Signed, {buyer_name}!</h2>
          <p>Your signed TREC offer for <strong>{addr}</strong> is attached. Here are your next steps:</p>
          <h3 style="color:#1a2f4a;">Send Your Offer:</h3>
          <p><strong>Option 1 — Send directly to listing agent:</strong><br>
          Forward this email with the attached PDF to the listing agent.</p>
          <p><strong>Option 2 — Submit through MLS/ShowingTime:</strong><br>
          Download the attached PDF and upload through your preferred submission method.</p>
          <h3 style="color:#1a2f4a;">After Submission:</h3>
          <ol>
            <li>Follow up with the listing agent to confirm receipt</li>
            <li>If accepted — deliver earnest money to the title company within 3 days</li>
            <li>Schedule your inspection immediately — don't wait on the option period</li>
          </ol>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.85rem;">
            ⚠️ <strong>Not legal advice.</strong> Consider having a licensed Texas agent or attorney review before submitting.
          </p>
        </div>
        ''',
        'attachments': [{
            'filename': filename,
            'content': signed_b64,
            'content_type': 'application/pdf',
        }]
    }
    httpx.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'},
        json=payload,
        timeout=30
    )
    return {'status': 'signed_pdf_sent'}


def verify_stripe_signature(body, sig_header, secret):
    try:
        elements   = dict(e.split('=', 1) for e in sig_header.split(','))
        timestamp  = elements.get('t', '')
        signatures = [v for k, v in elements.items() if k == 'v1']
        signed_payload = f'{timestamp}.{body}'
        expected = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected, sig) for sig in signatures)
    except:
        return False


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Debug — dump all PDF field names."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(MAIN_PDF)
            fields = reader.get_fields()
            if fields:
                field_info = {}
                for name, field in fields.items():
                    ft = field.get('/FT', 'unknown')
                    if hasattr(ft, 'name'): ft = ft.name
                    field_info[name] = {'type': str(ft), 'value': str(field.get('/V', ''))}
                self._respond(200, {'total': len(field_info), 'fields': field_info})
            else:
                self._respond(200, {'error': 'No fields found'})
        except Exception as e:
            self._respond(500, {'error': str(e)})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body     = self.rfile.read(content_length)
        body_str = body.decode('utf-8')

        # ── SIGNWELL CALLBACK ──
        # SignWell posts to this endpoint when signing is complete
        if self.headers.get('X-SignWell-Signature') or \
           self.headers.get('User-Agent', '').startswith('SignWell'):
            try:
                event = json.loads(body_str)
                result = handle_signwell_callback(event)
                self._respond(200, result)
            except Exception as e:
                print(f'SignWell callback error: {e}')
                self._respond(500, {'error': str(e)})
            return

        # ── STRIPE WEBHOOK ──
        sig_header = self.headers.get('stripe-signature', '')
        if STRIPE_WHSEC and not verify_stripe_signature(body_str, sig_header, STRIPE_WHSEC):
            self._respond(401, {'error': 'Invalid signature'})
            return

        try:
            event = json.loads(body_str)
        except:
            self._respond(400, {'error': 'Invalid JSON'})
            return

        if event.get('type') != 'checkout.session.completed':
            self._respond(200, {'status': 'ignored'})
            return

        session        = event['data']['object']
        customer_email = (session.get('customer_email') or
                          session.get('customer_details', {}).get('email', ''))
        metadata       = session.get('metadata', {})
        offer_data_str = metadata.get('offer_data', '')

        if not offer_data_str:
            self._respond(200, {'status': 'no offer data in metadata'})
            return

        try:
            offer = json.loads(offer_data_str)
        except:
            self._respond(400, {'error': 'Invalid offer data'})
            return

        # Store payment email so SignWell can use it if buyerEmail not set
        if not offer.get('buyerEmail') and customer_email:
            offer['_paymentEmail'] = customer_email

        try:
            pdf_bytes, addenda_info = fill_and_merge(offer)
            doc_id, sign_url = send_to_signwell(pdf_bytes, offer, addenda_info)

            buyer_name  = offer.get('buyer1', 'Buyer')
            buyer_email = offer.get('buyerEmail') or customer_email
            addr        = offer.get('address', 'Property')

            send_confirmation_email(buyer_email, buyer_name, addr, sign_url)
            self._respond(200, {'status': 'ok', 'doc_id': doc_id})
        except Exception as e:
            print(f'Error: {e}')
            self._respond(500, {'error': str(e)})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass

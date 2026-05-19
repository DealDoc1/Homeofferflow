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
FROM_EMAIL       = 'offers@homeofferflow.com'
SUPPORT_EMAIL    = 'support@homeofferflow.com'

# PDF paths — Vercel serves static files from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PDF         = os.path.join(BASE_DIR, '20-18_0.pdf')
FINANCING_PDF    = os.path.join(BASE_DIR, 'third_party_financing_addendum.pdf')
HOA_PDF          = os.path.join(BASE_DIR, 'hoa_addendum.pdf')
SALE_CONT_PDF    = os.path.join(BASE_DIR, 'sale_of_other_property_addendum.pdf')
BACKUP_PDF       = os.path.join(BASE_DIR, 'back_up_contract_addendum.pdf')


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
    lot_num   = lot_m.group(1) if lot_m else lot_str.split()[0]
    block_num = blk_m.group(1) if blk_m else ''
    return lot_num, block_num


def fill_and_merge(offer):
    from pypdf import PdfReader, PdfWriter

    s = offer
    lot_num, block_num = parse_lot_block(s.get('lot', ''))
    addr_full = f"{s.get('address','')} {s.get('city','')} TX {s.get('zip','')}"

    try:
        price = float(s.get('price', 0))
        loan  = float(s.get('loanAmount', 0))
        cash  = price - loan
    except:
        price = loan = cash = 0

    buyer_name = s.get('buyer1', '')
    if s.get('buyer2'):
        buyer_name += f" and {s['buyer2']}"

    field_values = {
        '1 PARTIES The parties to this contract are': buyer_name,
        'Seller and':                                  s.get('seller', ''),
        'A LAND Lot':                                  lot_num,
        'Block':                                       block_num,
        'undefined':                                   s.get('subdiv', ''),
        'Addition City of':                            s.get('city', ''),
        'County of':                                   s.get('county', ''),
        'Texas known as':                              addr_full,
        'as earnest money to':                         fmt_money(s.get('earnest')),
        'as earnest money to 2':                       fmt_money(s.get('earnest')),
        'acknowledged by Seller and Buyers agreement to pay Seller':   fmt_money(s.get('optionFee')),
        'acknowledged by Seller and Buyers agreement to pay Seller 1': s.get('optionDays', ''),
        'Option Fee in the form of':                   fmt_money(s.get('optionFee')),
        'A The closing of the sale will be on or before': fmt_date(s.get('closingDate')),
        'insurance Title Policy issued by':            s.get('titleCompany', ''),
        'undefined_3':                                 fmt_money(cash),
        'undefined_4':                                 fmt_money(loan),
        'undefined_5':                                 fmt_money(price),
        'Address of Property':                         addr_full,
        'Address of Property_2':                       addr_full,
        'Contract Concerning':                         addr_full,
        'Contract Concerning_2':                       addr_full,
        'Contract Concerning_3':                       addr_full,
        'Contract Concerning_4':                       addr_full,
        'Addr of Prop':                                addr_full,
    }

    # Load and fill main contract
    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, field_values)

    # Checkboxes
    checkbox_map = {
        'Third Party Financing Addendum': s.get('financing') in ['conventional','fha','va','usda'],
        'Addendum for Property Subject to': s.get('hoa') in ['yes','unknown'],
        'Addendum for Sale of Other Property by': s.get('saleContingency') == 'yes',
        'Addendum for BackUp Contract': s.get('backupOffer') == 'yes',
        'upon': s.get('possession') == 'funding',
        '1 Buyer accepts the Property As Is': True,
    }
    for field_name, should_check in checkbox_map.items():
        if should_check:
            try:
                writer.update_page_form_field_values(
                    writer.pages[0], {field_name: True}
                )
            except:
                pass

    # Merge addenda
    addenda_paths = []
    if s.get('financing') in ['conventional','fha','va','usda']:
        addenda_paths.append('/var/task/third_party_financing_addendum.pdf')
    if s.get('hoa') in ['yes','unknown']:
        addenda_paths.append(HOA_PDF)
    if s.get('saleContingency') == 'yes':
        addenda_paths.append(SALE_CONT_PDF)
    if s.get('backupOffer') == 'yes':
        addenda_paths.append(BACKUP_PDF)

    for path in addenda_paths:
        try:
            add_reader = PdfReader(path)
            writer.append(add_reader)
        except Exception as e:
            print(f'Warning: could not load addendum {path}: {e}')

    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def send_email(to_email, pdf_bytes, offer):
    addr = offer.get('address', 'Property')
    pdf_b64 = base64.b64encode(pdf_bytes).decode()
    buyer = offer.get('buyer1', 'Buyer')

    payload = {
        'from': FROM_EMAIL,
        'to': [to_email],
        'bcc': [SUPPORT_EMAIL],
        'subject': f'Your HomeOfferFlow Offer — {addr}',
        'html': f'''
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2 style="color:#1a2f4a;">Your Offer is Ready, {buyer}!</h2>
          <p>Thank you for using HomeOfferFlow. Your completed TREC offer contract is attached.</p>
          <h3 style="color:#1a2f4a;">Next Steps:</h3>
          <ol>
            <li><strong>Review your offer</strong> carefully before signing</li>
            <li><strong>Sign the contract</strong> where indicated</li>
            <li><strong>Send to the listing agent</strong> with your earnest money</li>
            <li><strong>Deliver earnest money</strong> to the title company within 3 days</li>
          </ol>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;">
            ⚠️ <strong>Important:</strong> HomeOfferFlow is not a law firm and this is not legal advice.
            Consider having a licensed agent or attorney review your offer before submitting.
          </p>
          <p style="color:#666;font-size:0.85rem;">
            Questions? Reply to this email or visit homeofferflow.com<br>
            HomeOfferFlow · BrewBQ Investments LLC · Texas
          </p>
        </div>
        ''',
        'attachments': [{
            'filename': f'HomeOfferFlow_Offer_{addr.replace(" ","_")}.pdf',
            'content': pdf_b64,
            'content_type': 'application/pdf',
        }]
    }

    resp = httpx.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'},
        json=payload,
        timeout=30
    )
    return resp.status_code, resp.text


def verify_stripe_signature(body, sig_header, secret):
    try:
        elements = dict(e.split('=', 1) for e in sig_header.split(','))
        timestamp = elements.get('t', '')
        signatures = [v for k, v in elements.items() if k == 'v1']
        signed_payload = f'{timestamp}.{body}'
        expected = hmac.new(
            secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()
        return any(hmac.compare_digest(expected, sig) for sig in signatures)
    except:
        return False


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        body_str = body.decode('utf-8')

        # Verify Stripe signature
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

        session = event['data']['object']
        customer_email = session.get('customer_email') or session.get('customer_details', {}).get('email', '')
        metadata = session.get('metadata', {})
        offer_data_str = metadata.get('offer_data', '')

        if not offer_data_str:
            self._respond(200, {'status': 'no offer data in metadata'})
            return

        try:
            offer = json.loads(offer_data_str)
        except:
            self._respond(400, {'error': 'Invalid offer data'})
            return

        try:
            pdf_bytes = fill_and_merge(offer)
            status, resp_text = send_email(customer_email, pdf_bytes, offer)
            self._respond(200, {'status': 'ok', 'email_status': status})
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

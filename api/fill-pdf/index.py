import json, os, base64, hashlib, hmac, httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject, ArrayObject, BooleanObject

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC   = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FROM_EMAIL     = "offers@homeofferflow.com"
SUPPORT_EMAIL  = "support@homeofferflow.com"

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PDF      = os.path.join(BASE_DIR, "20-18_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF       = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_PDF      = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF    = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")


# ── HELPERS ──────────────────────────────────────────────────────────────────

def fmt_money(v):
    try:
        if v in [None, ""]: return ""
        return f"{int(float(v)):,}"
    except:
        return str(v or "")


def split_date(v):
    if not v: return "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(v, "%Y-%m-%d")
        return d.strftime("%B %d").replace(" 0", " "), str(d.year)[-2:]
    except:
        return str(v), ""


def parse_lot_block(v):
    import re
    lot = block = ""
    if not v: return lot, block
    m = re.search(r"lot\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: lot = m.group(1)
    m = re.search(r"block\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: block = m.group(1)
    return lot, block


def set_field(writer, name, value, page_idx=None):
    """Set AcroForm text field value across all pages."""
    if value is None: value = ""
    value = str(value)
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                t = annot.get("/T", "")
                if hasattr(t, "original_bytes"): t = t.original_bytes.decode("utf-8", errors="replace")
                else: t = str(t)
                if t == name:
                    annot.update({NameObject("/V"): TextStringObject(value)})
            except: pass


def check_box(writer, name, checked=True):
    """Check or uncheck an AcroForm checkbox."""
    val = NameObject("/Yes") if checked else NameObject("/Off")
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                t = annot.get("/T", "")
                if hasattr(t, "original_bytes"): t = t.original_bytes.decode("utf-8", errors="replace")
                else: t = str(t)
                if t == name:
                    annot_ref.get_object().update({NameObject("/V"): val, NameObject("/AS"): val})
            except: pass


def verify_stripe_signature(body, sig_header, secret):
    if not secret: return True
    try:
        parts = {}
        for item in sig_header.split(","):
            k, v = item.split("=", 1)
            parts.setdefault(k, []).append(v)
        timestamp  = parts.get("t", [""])[0]
        signatures = parts.get("v1", [])
        expected   = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected, s) for s in signatures)
    except: return False


# ── FILL + MERGE ──────────────────────────────────────────────────────────────

def fill_and_merge(offer):
    s = offer
    lot, block       = parse_lot_block(s.get("lot", ""))
    addr_full        = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"
    closing_md, closing_yy = split_date(s.get("closingDate"))

    buyer = s.get("buyer1", "")
    if s.get("buyer2"): buyer += f" and {s['buyer2']}"

    try:
        price = float(s.get("price", 0) or 0)
        loan  = float(s.get("loanAmount", 0) or 0)
        cash  = price - loan if loan else price
    except: price = loan = cash = 0

    has_loan = s.get("financing") in ["conventional","fha","va","usda"]
    has_hoa  = s.get("hoa") in ["yes","unknown"]
    has_sale = s.get("saleContingency") == "yes"
    has_bkup = s.get("backupOffer") == "yes"

    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    # ── TEXT FIELDS ──
    text_fields = {
        # Section 1 — Parties
        "1 PARTIES The parties to this contract are": s.get("seller",""),
        "Seller and":                                  buyer,

        # Section 2 — Property
        "A LAND Lot":       lot,
        "Block":            block,
        "undefined":        s.get("subdiv",""),
        "Addition City of": s.get("city",""),
        "County of":        s.get("county",""),
        "Texas known as":   addr_full,

        # Section 3 — Sales Price
        # undefined_2 = 3A cash portion (confirmed from field dump)
        # undefined_3 = 3A second line (leave blank)
        # undefined_4 = 3B financing amount
        # undefined_5 = 3C total
        "undefined_2": fmt_money(cash) if has_loan else fmt_money(price),
        "undefined_4": fmt_money(loan) if has_loan else "",
        "undefined_5": fmt_money(price),

        # Section 5 — Earnest Money
        "as earnest money to":   fmt_money(s.get("earnest")),
        "as earnest money to 2": fmt_money(s.get("earnest")),
        "acknowledged by Seller and Buyers agreement to pay Seller":  fmt_money(s.get("optionFee")),
        "acknowledged by Seller and Buyers agreement to pay Seller 1": str(s.get("optionDays","7")),
        "acknowledged by Seller and Buyers agreement to pay Seller2":  fmt_money(s.get("optionFee")),
        "Option Fee in the form of": fmt_money(s.get("optionFee")),

        # Section 6 — Title
        "insurance Title Policy issued by": s.get("titleCompany",""),

        # Section 6C — Survey days
        "receipt or the date specified in this paragraph whichever is earlier": str(s.get("surveyDays","7")),

        # Section 6D — Intended use
        "Commitment other than items 6A1 through 9 above or which prohibit the following use": s.get("intendedUse",""),

        # Section 7B — Seller disclosure days
        "Within": str(s.get("disclosureDays","3")) if s.get("sellerDisclosure") == "notReceived" else "",

        # Section 7D — Repairs
        "following specific repairs and treatments": s.get("repairsText","") if s.get("asIs") == "repairs" else "",

        # Section 9 — Closing date
        "A The closing of the sale will be on or before": closing_md,
        "20":  closing_yy,

        # Section 12A(1)(c) — Seller concessions
        "Buyers Expenses as allowed by the lender": fmt_money(s.get("concessionAmount")) if s.get("wantsConcessions") == "yes" else "",

        # Section 21 — Buyer notices
        "when mailed to": s.get("buyerMailAddr",""),
        "Phone 51":       s.get("buyerPhone",""),
        "AC1":            s.get("buyerEmail",""),

        # Broker info — Page 10
        "Associates Name":          s.get("agentName","")     if s.get("hasBuyerAgent") == "yes" else "",
        "License No":               s.get("agentLicense","")  if s.get("hasBuyerAgent") == "yes" else "",
        "Associates Email Address": s.get("agentEmail","")    if s.get("hasBuyerAgent") == "yes" else "",
        "Phone":                    s.get("agentPhone","")    if s.get("hasBuyerAgent") == "yes" else "",
        "Other Broker Firm":        s.get("agentBrokerage","") if s.get("hasBuyerAgent") == "yes" else "",

        # Address headers on every page
        "Contract Concerning":   addr_full,
        "Contract Concerning_2": addr_full,
        "Contract Concerning_3": addr_full,
        "Contract Concerning_4": addr_full,
        "Address of Property":   addr_full,
        "Address of Property_2": addr_full,
        "Addr of Prop":          addr_full,
    }

    for name, value in text_fields.items():
        set_field(writer, name, value)

    # ── CHECKBOXES ──
    title_payer    = s.get("titlePayer","seller")
    title_amend    = s.get("titleAmendment","i")
    survey         = s.get("survey","")
    seller_disc    = s.get("sellerDisclosure","received")
    as_is          = s.get("asIs","yes")
    possession     = s.get("possession","funding")

    checkbox_map = {
        # Section 3B financing checkbox
        "B Sum of all financing described in the attached": has_loan,
        "Third Party Financing Addendum":                   has_loan,

        # Section 6A title payer
        "A TITLE POLICY Seller shall furnish to Buyer at":  title_payer == "seller",
        "Sellers":    title_payer == "seller",
        "Seller":     title_payer == "buyer",

        # Section 6A(8) title amendment
        "i will not be amended or deleted from the title policy or":                 title_amend == "i",
        "ii will be amended to read shortages in area at the expense of":            title_amend in ["ii_buyer","ii_seller"],
        "Buyer":      title_amend == "ii_buyer",

        # Section 6C survey
        "1Within":    survey == "sellerExisting",
        "2 Within":   survey == "buyerNew",
        "3Within":    survey == "noSurvey",

        # Section 6E(2) HOA membership
        "is":     has_hoa,
        "is not": not has_hoa,

        # Section 7B seller disclosure
        "Within one":   seller_disc == "received",
        "Within two":   seller_disc == "notReceived",
        "Within three": seller_disc == "exempt",

        # Section 7D As Is
        "1 Buyer accepts the Property As Is":                                                        as_is == "yes",
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the":  as_is == "repairs",

        # Section 10 possession
        "upon": possession == "funding",

        # Section 22 addenda checkboxes
        "Addendum for Property Subject to":       has_hoa,
        "Addendum for Sale of Other Property by": has_sale,
        "Addendum for BackUp Contract":           has_bkup,

        # Section 8 broker
        "Buyer only": s.get("hasBuyerAgent") == "yes",

        # MUD/PID
        "PID": s.get("mud") in ["yes","unknown"],
    }

    for name, checked in checkbox_map.items():
        check_box(writer, name, checked)

    # ── MERGE ADDENDA ──
    addenda = []
    if has_loan: addenda.append(FINANCING_PDF)
    if has_hoa:  addenda.append(HOA_PDF)
    if has_sale: addenda.append(SALE_PDF)
    if has_bkup: addenda.append(BACKUP_PDF)

    for path in addenda:
        try:
            add_reader = PdfReader(path)
            writer.append(add_reader)
        except Exception as e:
            print(f"Warning: could not load {path}: {e}")

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


# ── EMAIL ─────────────────────────────────────────────────────────────────────

def send_email(to_email, buyer_name, addr, pdf_bytes):
    payload = {
        "from": FROM_EMAIL,
        "to":   [to_email],
        "bcc":  [SUPPORT_EMAIL],
        "subject": f"Your HomeOfferFlow Offer — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2 style="color:#1a2f4a;">Your Offer is Ready, {buyer_name}!</h2>
          <p>Your filled TREC offer for <strong>{addr}</strong> is attached.</p>
          <h3>Next Steps:</h3>
          <ol>
            <li>Review the attached PDF carefully</li>
            <li>Sign and send to the listing agent</li>
            <li>Deliver earnest money within 3 days of acceptance</li>
            <li>Schedule your inspection immediately — don't wait</li>
          </ol>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.85rem;">
            ⚠️ <strong>Not legal advice.</strong> Consider having a licensed Texas agent or attorney review before submitting.
          </p>
        </div>""",
        "attachments": [{
            "filename": f"HomeOfferFlow_Offer_{addr.replace(' ','_').replace(',','')}.pdf",
            "content":  base64.b64encode(pdf_bytes).decode(),
            "content_type": "application/pdf"
        }]
    }
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json=payload, timeout=30
    )
    if r.status_code not in [200,201,202]:
        raise Exception(f"Resend error {r.status_code}: {r.text[:200]}")


# ── STRIPE HANDLER ────────────────────────────────────────────────────────────

def handle_checkout(event):
    session        = event.get("data",{}).get("object",{})
    customer_email = (session.get("customer_email") or
                      session.get("customer_details",{}).get("email",""))
    metadata       = session.get("metadata",{}) or {}

    if "offer_data" in metadata:
        offer = json.loads(metadata["offer_data"])
    else:
        parts    = int(metadata.get("offer_parts", 0) or 0)
        combined = "".join(metadata.get(f"offer_{i}","") for i in range(parts))
        if not combined:
            raise Exception(f"No offer data. Metadata keys: {list(metadata.keys())}")
        offer = json.loads(combined)

    if not offer.get("buyerEmail") and customer_email:
        offer["buyerEmail"] = customer_email

    pdf_bytes = fill_and_merge(offer)

    send_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1","Buyer"),
        offer.get("address","Property"),
        pdf_bytes
    )
    return {"status": "ok", "message": "PDF created and emailed"}


# ── HANDLER ───────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        from pypdf import PdfReader as PR
        try:
            r  = PR(MAIN_PDF)
            fs = r.get_fields() or {}
            self._json(200, {
                "status": "ok",
                "main_pdf_exists": os.path.exists(MAIN_PDF),
                "field_count": len(fs),
                "fields": {k: str(v.get("/FT","")) for k,v in fs.items()}
            })
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            sig    = self.headers.get("stripe-signature","")
            if sig and not verify_stripe_signature(body, sig, STRIPE_WHSEC):
                self._json(401, {"error": "Invalid Stripe signature"}); return
            event = json.loads(body.decode("utf-8"))
            if event.get("type") == "checkout.session.completed":
                result = handle_checkout(event)
                self._json(200, result)
            else:
                self._json(200, {"status": "ignored"})
        except Exception as e:
            print("ERROR:", str(e))
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


handler = Handler

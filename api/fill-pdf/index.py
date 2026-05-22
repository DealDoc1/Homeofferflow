import json, os, base64, hashlib, hmac, httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC   = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FROM_EMAIL     = "offers@homeofferflow.com"
SUPPORT_EMAIL  = "support@homeofferflow.com"

BASE_DIR      = "/var/task"
MAIN_PDF      = os.path.join(BASE_DIR, "20-18_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF       = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_PDF      = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF    = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")


def fmt_money(v):
    if not v: return ""
    try:
        return f"{int(float(str(v))):,}"
    except:
        return str(v)


def split_date(v):
    """Returns (month day string, 2-digit year string) from YYYY-MM-DD"""
    if not v: return "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(str(v), "%Y-%m-%d")
        return d.strftime("%B %d").replace(" 0", " "), str(d.year)[-2:]
    except:
        return str(v), ""


def parse_lot_block(v):
    """Extract lot and block numbers from a combined string like 'Block 1 Lot 1' or 'Lot A Block B'"""
    import re
    lot = block = ""
    if not v: return lot, block
    m = re.search(r"lot\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: lot = m.group(1)
    m = re.search(r"block\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: block = m.group(1)
    return lot, block


def set_field(writer, name, value):
    if value is None: value = ""
    value = str(value)
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                t = annot.get("/T", "")
                t = t.original_bytes.decode("utf-8", errors="replace") if hasattr(t, "original_bytes") else str(t)
                if t == name:
                    annot.update({NameObject("/V"): TextStringObject(value)})
            except:
                pass


def check_box(writer, name, checked=True):
    val = NameObject("/Yes") if checked else NameObject("/Off")
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                t = annot.get("/T", "")
                t = t.original_bytes.decode("utf-8", errors="replace") if hasattr(t, "original_bytes") else str(t)
                if t == name:
                    annot_ref.get_object().update({
                        NameObject("/V"): val,
                        NameObject("/AS"): val
                    })
            except:
                pass


def verify_stripe_signature(body, sig_header, secret):
    if not secret: return True
    try:
        parts = {}
        for item in sig_header.split(","):
            k, v = item.split("=", 1)
            parts.setdefault(k, []).append(v)
        timestamp  = parts.get("t", [""])[0]
        signatures = parts.get("v1", [])
        expected   = hmac.new(
            secret.encode(),
            timestamp.encode() + b"." + body,
            hashlib.sha256
        ).hexdigest()
        return any(hmac.compare_digest(expected, s) for s in signatures)
    except:
        return False


def fill_and_merge(offer):
    s = offer

    # ── Derived values ─────────────────────────────────────────────────────
    lot, block     = parse_lot_block(s.get("lot", ""))
    addr_full      = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"
    closing_md, closing_yy = split_date(s.get("closingDate"))

    buyer = s.get("buyer1", "")
    if s.get("buyer2"): buyer += f" and {s['buyer2']}"

    try:
        price = float(s.get("price", 0) or 0)
        loan  = float(s.get("loanAmount", 0) or 0)
        cash  = price - loan if loan else price
    except:
        price = loan = cash = 0

    has_loan = s.get("financing") in ["conventional", "fha", "va", "usda"]
    has_hoa  = s.get("hoa") in ["yes", "unknown"]
    has_sale = s.get("saleContingency") == "yes"
    has_bkup = s.get("backupOffer") == "yes"

    title_payer = s.get("titlePayer", "seller")
    title_amend = s.get("titleAmendment", "i")
    survey      = s.get("survey", "sellerExisting")
    seller_disc = s.get("sellerDisclosure", "notReceived")
    as_is       = s.get("asIs", "yes")
    possession  = s.get("possession", "funding")

    # ── Load main PDF ───────────────────────────────────────────────────────
    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    # ── TEXT FIELDS ─────────────────────────────────────────────────────────
    # Numbers reference the field numbers from the marked scan
    text_fields = {
        # §1 Parties (fields 1, 2)
        "1 PARTIES The parties to this contract are": s.get("seller", ""),   # 1 - Seller
        "Seller and":                                  buyer,                 # 2 - Buyer

        # §2 Property (fields 3-8)
        "A LAND Lot":       lot,                        # 3 - Lot
        "Block":            block,                      # 4 - Block
        "undefined":        s.get("subdiv", ""),        # 5 - Subdivision/Addition
        "Addition City of": s.get("city", ""),          # 6 - City
        "County of":        s.get("county", ""),        # 7 - County
        "Texas known as":   addr_full,                  # 8 - Full address

        # §2D Exclusions (field 9) — leave blank, not collected
        # "Exclusions": "",

        # §3 Sales Price (fields 10, 14, 15)
        "undefined_3": fmt_money(cash) if has_loan else fmt_money(price),  # 10 - 3A cash
        "undefined_4": fmt_money(loan) if has_loan else "",                 # 14 - 3B loan
        "undefined_5": fmt_money(price),                                    # 15 - 3C total

        # §4 Leases natural resource days (field 21) — leave blank
        # "NRL days": "",

        # §5 Earnest money (fields 25-31)
        "undefined_6":           s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW"),  # 25
        "undefined_7":           s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033"),  # 26
        "as earnest money to":   fmt_money(s.get("earnest")),              # 27 - Earnest $
        "as earnest money to 2": fmt_money(s.get("optionFee")),            # 28 - Option fee $
        # 29 - Additional earnest $ — not collected, leave blank
        # 30 - Additional earnest days — not collected, leave blank
        "the Title Company and Buyers lenders Check one box only": str(s.get("optionDays", "7")),  # 31 - Option days

        # §6A Title (field 34)
        "insurance Title Policy issued by": s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC"),  # 34

        # §6C Survey days (fields 43, 47, 49)
        "receipt or the date specified in this paragraph whichever is earlier": str(s.get("surveyDays", "7")),  # 43 / 47 / 49

        # §6D Objections (fields 50, 51)
        "Commitment other than items 6A1 through 9 above or which prohibit the following use": s.get("intendedUse", ""),  # 50
        "the Commitment Exception Documents and the survey Buyers failure to object within the": str(s.get("disclosureDays", "3")),  # 51

        # §7D Repairs (field 67)
        "following specific repairs and treatments": s.get("repairsText", "") if as_is == "repairs" else "",  # 67

        # §7H Service contract (field 68) — not collected, leave blank

        # §8 Broker disclosure (field 69) — not collected, leave blank

        # §9 Closing (fields 70, 71)
        "A The closing of the sale will be on or before": closing_md,   # 70 - Closing date
        "20": closing_yy,                                                # 71 - Closing year (2 digits)

        # §11 Special provisions (field 77) — not collected, leave blank

        # §12 Settlement (fields 79, 80, 82)
        # 78 = $ checkbox for broker fee — not collected
        # 79 = $ amount for broker fee — not collected
        # 80 = % checkbox — not collected
        # 81 = % amount — not collected
        "Buyers Expenses as allowed by the lender": fmt_money(s.get("concessionAmount")) if s.get("wantsConcessions") == "yes" else "",  # 82

        # §21 Notices to Buyer (fields 89, 90, 91)
        "when mailed to handdelivered at or transmitted by fax or electronic transmission as follows": s.get("buyerMailAddr", ""),  # 89
        "Phone 51": s.get("buyerPhone", ""),  # 90
        "AC1":      s.get("buyerEmail", ""),  # 91

        # Page 10 Broker info (buyer's agent side only)
        "Associates Name numb 1":   s.get("agentName", "")     if s.get("hasBuyerAgent") == "yes" else "",
        "License No":               s.get("agentLicense", "")  if s.get("hasBuyerAgent") == "yes" else "",
        "Associates Email Address":  s.get("agentEmail", "")   if s.get("hasBuyerAgent") == "yes" else "",
        "Phone":                    s.get("agentPhone", "")    if s.get("hasBuyerAgent") == "yes" else "",
        "Other Broker Firm":        s.get("agentBrokerage", "") if s.get("hasBuyerAgent") == "yes" else "",

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
        set_field(writer, name, str(value) if value else "")

    # ── CHECKBOXES ──────────────────────────────────────────────────────────
    checkbox_map = {
        # §3B financing (field 11)
        "B Sum of all financing described in the attached": has_loan,
        "Third Party Financing Addendum":                   has_loan,   # 11

        # §3B loan assumption, seller financing (fields 12, 13) — always False for us
        "Loan Assumption Addendum":   False,   # 12
        "Seller Financing Addendum":  False,   # 13 (note: same as "Seller Financing Addendum_2" on addenda page)

        # §4 Leases (fields 16, 17, 18, 19, 20) — always False
        "A RESIDENTIAL LEASES The Property is subject to one or more residential leases and the": False,  # 16
        "B FIXTURE LEASES Fixtures on the Property are subject to one or more fixture leases for": False,  # 17
        "C NATURAL RESOURCE LEASES Natural Resource Lease means an existing oil and gas mineral": False,   # 18
        "1 Seller has delivered to Buyer a copy of all the Natural Resource Leases": False,                # 19
        "2 Seller has not delivered to Buyer a copy of all the Natural Resource Leases Seller shall": False,  # 20

        # §6A title payer (fields 32, 33)
        "A TITLE POLICY Seller shall furnish to Buyer at":  title_payer == "seller",  # 32
        "Sellers":    title_payer == "seller",
        "Seller":     title_payer == "buyer",                                          # 33

        # §6A(8) title amendment (fields 35, 36, 37, 38)
        "i will not be amended or deleted from the title policy or":              title_amend == "i",                        # 35
        "ii will be amended to read shortages in area at the expense of":         title_amend in ["ii_buyer", "ii_seller"],   # 36
        "Buyer":      title_amend == "ii_buyer",      # 37 — Buyer pays amendment
        "Sellers_2":  title_amend == "ii_seller",     # 38 — Seller pays amendment
        "Buyers expense no later": title_amend == "ii_buyer",

        # §6C survey (fields 42, 44, 45, 46, 48)
        "1Within":  survey == "sellerExisting",   # 42
        "2Within":  survey == "buyerNew",         # 46
        "2 Within": survey == "buyerNew",         # duplicate field name
        "3Within":  survey == "noSurvey",         # 48
        # 44 = Seller's expense sub-checkbox (part of option 1) — True when sellerExisting
        # 45 = Buyer's expense sub-checkbox (part of option 1) — False
        "Sellers_3": survey == "sellerExisting",  # 44 - Seller's expense if survey needed
        "Buyers_2":  False,                        # 45 - Buyer's expense — always False

        # §6E(2) HOA membership (fields 52, 53)
        "is":     has_hoa,       # 52
        "is not": not has_hoa,   # 53

        # §7B seller disclosure (fields 56, 57, 58, 59, 60, 61)
        "Within one":   seller_disc == "received",       # 56
        "Sellers Disclos": seller_disc == "received",
        "Within two":   seller_disc == "notReceived",    # 57
        "Addend. for Sellers Disclos": seller_disc == "notReceived",
        "Within three": seller_disc == "exempt",         # 58

        # §7D As Is (fields 65, 66)
        "As Is":        as_is == "yes",      # 65
        "As Is except": as_is == "repairs",  # 66
        "1 Buyer accepts the Property As Is": as_is == "yes",
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the": as_is == "repairs",

        # §10 Possession (fields 75, 76)
        "upon":       possession == "funding",   # 75 - upon closing and funding
        "according":  possession == "lease",     # 76 - according to temp lease

        # §5B Option fee credit (always True — fee WILL be credited)
        "will":     True,    # option fee WILL be credited
        "will 1.1": True,    # second instance
        "will not be credited to the Sales Price at closing Time is of the":   False,
        "will not be credited to the Sales Price at closing Time is of the 1": False,

        # §22 Addenda checkboxes (fields 92-113)
        "Third Party Financing Addendum_2":           has_loan,   # 92
        "Seller Financing Addendum_2":                False,      # 93
        "Addendum for Property Subject to":           has_hoa,    # 94
        "Buyers Temporary Residential Lease":         False,      # 95
        "Addendum for Sale of Other Property by":     has_sale,   # 97
        "Addendum for BackUp Contract":               has_bkup,   # 99
        "Addendum for Coastal Area Property":         False,      # 100
        "Addendum for Authorizing Hydrostatic":       False,      # 101
        "Addendum Concerning Right to":               False,      # 102
        "Environmental Assessment Threatened or":     False,      # 103
        "Sellers Temporary Residential Lease":        False,      # 104
        "Short Sale Addendum":                        False,      # 105
        "Addendum for Property Located Seaward":      False,      # 106
        "Addendum for Sellers Disclosure of":         False,      # 107
        "Addendum for Property in a Propane Gas":     False,      # 108
        "Addendum Regarding Residential Leases":      False,      # 109
        "Addendum Regarding Fixture Leases":          False,      # 110
        "Addendum containing Notice of Obligation":   False,      # 111
        "Addendum for Section 1031":                  False,      # 112
        "Addendum for Reservation of Oil Gas":        False,      # 98 (was numbered out of order)
        "Loan Assumption Addendum_2":                 False,      # 96

        # Page 10 broker representation
        "Buyer only":                          s.get("hasBuyerAgent") == "yes",
        "Seller only as Sellers agent":        False,
        "Seller and Buyer as an intermediary": False,

        # MUD/PID
        "PID": s.get("mud") in ["yes", "unknown"],
    }

    for name, checked in checkbox_map.items():
        check_box(writer, name, checked)

    # ── ADDENDA ─────────────────────────────────────────────────────────────
    # Financing addendum
    if has_loan and os.path.exists(FINANCING_PDF):
        fin_reader = PdfReader(FINANCING_PDF)
        fin_writer = PdfWriter()
        fin_writer.append(fin_reader)
        # Check the right financing type
        fin_checks = {
            "A CONVENTIONAL FINANCING":  s.get("financing") == "conventional",
            "C FHA INSURED FINANCING":    s.get("financing") == "fha",
            "D VA GUARANTEED FINANCING":  s.get("financing") == "va",
            "E USDA GUARANTEED FINANCING": s.get("financing") == "usda",
            # Buyer approval — standard: subject to approval
            "This contract is subject to Buyer obtaining Buyer Approval If Buyer cannot obtain Buyer": True,
            "This contract is not subject to Buyer obtaining Buyer Approval": False,
        }
        for fname, fchecked in fin_checks.items():
            check_box(fin_writer, fname, fchecked)
        # Address header on financing addendum
        set_field(fin_writer, "Street Address and City", addr_full)
        fin_out = BytesIO()
        fin_writer.write(fin_out)
        writer.append(PdfReader(BytesIO(fin_out.getvalue())))

    # HOA addendum
    if has_hoa and os.path.exists(HOA_PDF):
        writer.append(PdfReader(HOA_PDF))

    # Sale of other property addendum — fill separately to avoid field name collision on "20"
    if has_sale and os.path.exists(SALE_PDF):
        sale_reader = PdfReader(SALE_PDF)
        sale_writer = PdfWriter()
        sale_writer.append(sale_reader)
        contingency_md, contingency_yy = split_date(s.get("saleContingencyDate", ""))
        sale_fields = {
            "Address of Property":  addr_full,
            "Address on or before": s.get("salePropertyAddr", ""),
            "Contingency is not satisfied or waived by Buyer by the above date the contract will terminate": contingency_md,
            "20":                   contingency_yy,
            "terminate automatically and the earnest money will be refunded to Buyer": s.get("saleWaiverDays", ""),
            "All notices and waivers must be in writing and are": fmt_money(s.get("saleAdditionalEarnest")),
        }
        for fname, fval in sale_fields.items():
            set_field(sale_writer, fname, str(fval) if fval else "")
        sale_out = BytesIO()
        sale_writer.write(sale_out)
        writer.append(PdfReader(BytesIO(sale_out.getvalue())))

    # Back-up contract addendum
    if has_bkup and os.path.exists(BACKUP_PDF):
        writer.append(PdfReader(BACKUP_PDF))

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def send_email(to_email, buyer_name, addr, pdf_bytes):
    filename = f"HomeOfferFlow_Offer_{addr.replace(' ','_').replace(',','')}.pdf"
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
            "filename": filename,
            "content":  base64.b64encode(pdf_bytes).decode(),
            "content_type": "application/pdf"
        }]
    }
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )
    if r.status_code not in [200, 201, 202]:
        raise Exception(f"Resend error {r.status_code}: {r.text[:200]}")


def handle_checkout(event):
    session        = event.get("data", {}).get("object", {})
    customer_email = (session.get("customer_email") or
                      session.get("customer_details", {}).get("email", ""))
    metadata       = session.get("metadata", {}) or {}

    if "offer_data" in metadata:
        offer = json.loads(metadata["offer_data"])
    else:
        parts    = int(metadata.get("offer_parts", 0) or 0)
        combined = "".join(metadata.get(f"offer_{i}", "") for i in range(parts))
        if not combined:
            raise Exception(f"No offer data found. Metadata keys: {list(metadata.keys())}")
        offer = json.loads(combined)

    if not offer.get("buyerEmail") and customer_email:
        offer["buyerEmail"] = customer_email

    pdf_bytes = fill_and_merge(offer)

    send_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property"),
        pdf_bytes
    )

    return {"status": "ok", "message": "PDF created and emailed"}


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            contents = os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else []
        except Exception as e:
            contents = str(e)
        self._json(200, {
            "status": "ok",
            "base_dir": BASE_DIR,
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "cwd": os.getcwd(),
            "dir_contents": contents
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            sig    = self.headers.get("stripe-signature", "")
            if sig and not verify_stripe_signature(body, sig, STRIPE_WHSEC):
                self._json(401, {"error": "Invalid Stripe signature"})
                return
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
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


handler = Handler

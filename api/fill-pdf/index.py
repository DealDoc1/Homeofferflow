import json, os, base64, hashlib, hmac, httpx, re
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_money(v):
    if not v: return ""
    try:
        return f"{int(float(str(v))):,}"
    except:
        return str(v)

def split_date(v):
    if not v: return "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(str(v), "%Y-%m-%d")
        return d.strftime("%B %d").replace(" 0", " "), str(d.year)[-2:]
    except:
        return str(v), ""

def parse_lot_block(v):
    lot = block = ""
    if not v: return lot, block
    m = re.search(r"lot\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: lot = m.group(1)
    m = re.search(r"block\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: block = m.group(1)
    return lot, block

def split_phone(phone):
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) == 10:
        return digits[:3], digits[3:]
    return "", digits


# ---------------------------------------------------------------------------
# Core fill — THE WORKING METHOD
#
# writer.clone_reader_document_root(reader) properly clones the entire PDF
# including AcroForm structure. Then update_page_form_field_values(None, ...)
# fills ALL pages at once with auto_regenerate=True so both text fields
# AND checkboxes render visually.
#
# writer.append(reader) was the root cause of all blank-field issues —
# it clones pages but leaves AcroForm fields as indirect refs to the
# original objects, causing appearance streams to never be generated.
# ---------------------------------------------------------------------------

def fill_pdf_fields(pdf_path, all_fields: dict) -> bytes:
    """
    Fill an AcroForm PDF using clone_reader_document_root.
    Falls back to page-by-page filling if the bulk call hits a /AP error.
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)

    try:
        # Fill all fields across all pages in one call
        writer.update_page_form_field_values(
            None,
            all_fields,
            auto_regenerate=True,
        )
    except Exception as e:
        if "AP" in str(e) or "appearance" in str(e).lower():
            # Some addenda PDFs have checkbox fields without /AP streams.
            # Fall back: fill text fields only via update, skip problem checkboxes.
            text_only = {k: v for k, v in all_fields.items()
                         if not v.startswith("/Yes") and not v.startswith("/Off")}
            checkbox_only = {k: v for k, v in all_fields.items()
                             if v.startswith("/Yes") or v.startswith("/Off")}
            # Fill text fields safely
            if text_only:
                try:
                    writer.update_page_form_field_values(None, text_only, auto_regenerate=True)
                except Exception:
                    pass
            # Set checkbox values directly without touching /AP
            from pypdf.generic import NameObject as NO
            for page in writer.pages:
                for annot_ref in page.get("/Annots", []):
                    try:
                        annot = annot_ref.get_object()
                        if annot.get("/Subtype") != "/Widget":
                            continue
                        t = str(annot.get("/T", ""))
                        if t in checkbox_only:
                            val = NO(checkbox_only[t])
                            annot[NO("/V")]  = val
                            annot[NO("/AS")] = val
                    except Exception:
                        pass
        else:
            raise

    try:
        af = writer._root_object["/AcroForm"].get_object()
        af[NameObject("/NeedAppearances")] = BooleanObject(True)
    except Exception:
        pass

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Stripe signature verification
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main PDF fill + addenda merge
# ---------------------------------------------------------------------------

def fill_and_merge(offer):
    s = offer

    lot, block             = parse_lot_block(s.get("lot", ""))
    addr_full              = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"
    closing_md, closing_yy = split_date(s.get("closingDate"))
    phone_area, phone_num  = split_phone(s.get("buyerPhone", ""))

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

    # ── Build combined fields dict ──────────────────────────────────────────
    # Checkbox values must be "/Yes" or "/Off" strings
    def cb(condition): return "/Yes" if condition else "/Off"

    fields = {
        # §1 Parties
        "1 PARTIES The parties to this contract are": s.get("seller", ""),
        "Seller and":                                  buyer,

        # §2 Property
        "A LAND Lot":       lot,
        "Block":            block,
        "Addition City of": s.get("city", ""),
        "County of":        s.get("county", ""),
        "Texas known as":   addr_full,

        # §3 Sales Price
        "undefined_4": fmt_money(cash) if has_loan else fmt_money(price),
        "undefined_3": fmt_money(loan) if has_loan else "",
        "undefined_5": fmt_money(price),

        # §3B checkboxes
        "B Sum of all financing described in the attached": cb(has_loan),
        "Third Party Financing Addendum":                   cb(has_loan),
        "Loan Assumption Addendum":                         cb(False),
        "Seller Financing Addendum":                        cb(False),

        # §5 Earnest money
        "undefined_6":           s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW"),
        "undefined_7":           s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033"),
        "as earnest money to":   fmt_money(s.get("earnest")),
        "as earnest money to 2": fmt_money(s.get("optionFee")),
        "the Title Company and Buyers lenders Check one box only": str(s.get("optionDays", "7")),

        # §5B option fee credit checkboxes
        "will":     cb(True),
        "will 1.1": cb(True),
        "will not be credited to the Sales Price at closing Time is of the":   cb(False),
        "will not be credited to the Sales Price at closing Time is of the 1": cb(False),

        # §6A Title
        "A TITLE POLICY Seller shall furnish to Buyer at": cb(title_payer == "seller"),
        "Sellers":                                          cb(title_payer == "seller"),
        "Seller":                                           cb(title_payer == "buyer"),
        "insurance Title Policy issued by": s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC"),

        # §6A(8) title amendment
        "i will not be amended or deleted from the title policy or":      cb(title_amend == "i"),
        "ii will be amended to read shortages in area at the expense of": cb(title_amend in ["ii_buyer", "ii_seller"]),
        "Buyer":                   cb(title_amend == "ii_buyer"),
        "Sellers_2":               cb(title_amend == "ii_seller"),
        "Buyers expense no later": cb(title_amend == "ii_buyer"),

        # §6C survey
        "1Within":  cb(survey == "sellerExisting"),
        "2Within":  cb(survey == "buyerNew"),
        "2 Within": cb(survey == "buyerNew"),
        "3Within":  cb(survey == "noSurvey"),
        "receipt or the date specified in this paragraph whichever is earlier": str(s.get("surveyDays", "7")),

        # §6D objections
        "Commitment other than items 6A1 through 9 above or which prohibit the following use": s.get("intendedUse", ""),
        "the Commitment Exception Documents and the survey Buyers failure to object within the": str(s.get("disclosureDays", "3")),

        # §6E(2) HOA
        "is":     cb(has_hoa),
        "is not": cb(not has_hoa),

        # §7B seller disclosure
        "Within one":                  cb(seller_disc == "received"),
        "Sellers Disclos":             cb(seller_disc == "received"),
        "Within two":                  cb(seller_disc == "notReceived"),
        "Addend. for Sellers Disclos": cb(seller_disc == "notReceived"),
        "Within three":                cb(seller_disc == "exempt"),
        "Text4":                       str(s.get("disclosureDays", "3")) if seller_disc == "notReceived" else "",

        # §7D As Is
        "As Is":        cb(as_is == "yes"),
        "As Is except": cb(as_is == "repairs"),
        "1 Buyer accepts the Property As Is":                                                       cb(as_is == "yes"),
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the": cb(as_is == "repairs"),
        "following specific repairs and treatments": s.get("repairsText", "") if as_is == "repairs" else "",

        # §9 Closing
        "A The closing of the sale will be on or before": closing_md,
        "20":                                             closing_yy,

        # §10 Possession
        "upon":      cb(possession == "funding"),
        "according": cb(possession == "lease"),

        # §21 Notices
        "when mailed to handdelivered at or transmitted by fax or electronic transmission as follows": s.get("buyerMailAddr", ""),
        "AC1":      phone_area,
        "Phone 51": phone_num,
        "Phone 52": s.get("buyerEmail", ""),

        # §22 Addenda checkboxes
        "Addendum for Property Subject to":       cb(has_hoa),
        "Addendum for Sale of Other Property by": cb(has_sale),
        "Addendum for BackUp Contract":           cb(has_bkup),
        "Loan Assumption Addendum_2":             cb(False),
        "Environmental Assessment Threatened or": cb(False),
        "Addendum for Property Located Seaward":  cb(False),
        "Addendum for Property in a Propane Gas": cb(False),
        "Sellers Temporary Residential Lease":    cb(False),
        "Buyers Temporary Residential Lease":     cb(False),
        "Short Sale Addendum":                    cb(False),
        "Addendum for Section 1031":              cb(False),
        "Addendum for Reservation of Oil Gas":    cb(False),

        # Broker
        "Buyer only":                          cb(s.get("hasBuyerAgent") == "yes"),
        "Seller only as Sellers agent":        cb(False),
        "Seller and Buyer as an intermediary": cb(False),
        "Associates Name numb 1":   s.get("agentName", "")      if s.get("hasBuyerAgent") == "yes" else "",
        "License No":               s.get("agentLicense", "")   if s.get("hasBuyerAgent") == "yes" else "",
        "Associates Email Address":  s.get("agentEmail", "")    if s.get("hasBuyerAgent") == "yes" else "",
        "Phone":                    s.get("agentPhone", "")     if s.get("hasBuyerAgent") == "yes" else "",
        "Other Broker Firm":        s.get("agentBrokerage", "") if s.get("hasBuyerAgent") == "yes" else "",

        # MUD/PID
        "PID": cb(s.get("mud") in ["yes", "unknown"]),

        # Address headers
        "Contract Concerning":   addr_full,
        "Contract Concerning_2": addr_full,
        "Contract Concerning_3": addr_full,
        "Contract Concerning_4": addr_full,
        "Address of Property":   addr_full,
        "Address of Property_2": addr_full,
        "Addr of Prop":          addr_full,
    }

    # Fill main contract
    main_bytes = fill_pdf_fields(MAIN_PDF, fields)

    # Merge addenda
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(main_bytes)))

    # Third Party Financing Addendum
    if has_loan and os.path.exists(FINANCING_PDF):
        fin_fields = {
            "Street Address and City": addr_full,
            "1 Conventional Financing":   "/Yes" if s.get("financing") == "conventional" else "/Off",
            "3 FHA Insured Financing A Section": "/Yes" if s.get("financing") == "fha" else "/Off",
            "4 VA Guaranteed Financing A VA guaranteed loan of not less than": "/Yes" if s.get("financing") == "va" else "/Off",
            "5 USDA Guaranteed Financing A USDAguaranteed loan of not less than": "/Yes" if s.get("financing") == "usda" else "/Off",
            "This contract is subject to Buyer obtaining Buyer Approval If Buyer cannot obtain Buyer": "/Yes",
        }
        fin_bytes = fill_pdf_fields(FINANCING_PDF, fin_fields)
        writer.append(PdfReader(BytesIO(fin_bytes)))

    # HOA Addendum
    if has_hoa and os.path.exists(HOA_PDF):
        hoa_fields = {
            "Street Address and City": addr_full,
            "Address of Property":     addr_full,
        }
        hoa_bytes = fill_pdf_fields(HOA_PDF, hoa_fields)
        writer.append(PdfReader(BytesIO(hoa_bytes)))

    # Sale of Other Property Addendum
    if has_sale and os.path.exists(SALE_PDF):
        contingency_md, contingency_yy = split_date(s.get("saleContingencyDate", ""))
        sale_fields = {
            "Address of Property":  addr_full,
            "Address on or before": s.get("salePropertyAddr", ""),
            "Contingency is not satisfied or waived by Buyer by the above date the contract will terminate": contingency_md,
            "20":                   contingency_yy,
            "terminate automatically and the earnest money will be refunded to Buyer": s.get("saleWaiverDays", ""),
            "All notices and waivers must be in writing and are": fmt_money(s.get("saleAdditionalEarnest")),
        }
        sale_bytes = fill_pdf_fields(SALE_PDF, sale_fields)
        writer.append(PdfReader(BytesIO(sale_bytes)))

    # Back-Up Contract Addendum
    if has_bkup and os.path.exists(BACKUP_PDF):
        bkup_fields = {
            "Address of Property":     addr_full,
            "Street Address and City": addr_full,
        }
        bkup_bytes = fill_pdf_fields(BACKUP_PDF, bkup_fields)
        writer.append(PdfReader(BytesIO(bkup_bytes)))

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

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
            "filename":     filename,
            "content":      base64.b64encode(pdf_bytes).decode(),
            "content_type": "application/pdf"
        }]
    }
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    if r.status_code not in [200, 201, 202]:
        raise Exception(f"Resend error {r.status_code}: {r.text[:200]}")


# ---------------------------------------------------------------------------
# Stripe webhook
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

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

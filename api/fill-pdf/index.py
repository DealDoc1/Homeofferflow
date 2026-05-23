import json, os, base64, hashlib, hmac, httpx, re
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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

FONT      = "Helvetica"
FONT_SIZE = 9
CHECK     = "■"   # filled square rendered as checkmark overlay


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
# Overlay engine — stamp text/checks directly onto PDF pages
# ---------------------------------------------------------------------------

def make_overlay(page_entries, page_width=612, page_height=792):
    """
    page_entries: list of (x, y, text, font_size=None)
    x, y are PDF coords (origin bottom-left).
    Returns bytes of a single-page transparent PDF overlay.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))
    c.setFont(FONT, FONT_SIZE)
    for entry in page_entries:
        x, y, text = entry[0], entry[1], entry[2]
        fs = entry[3] if len(entry) > 3 else FONT_SIZE
        if not text:
            continue
        c.setFont(FONT, fs)
        c.drawString(x, y, str(text))
    c.save()
    buf.seek(0)
    return buf.read()


def stamp_pdf(base_pdf_path, pages_data: dict) -> bytes:
    """
    Stamp text overlays onto a PDF.
    Clears all existing AcroForm field values first to avoid bleed-through
    from previously filled template data.
    pages_data: {page_index_0based: [(x, y, text), ...]}
    Returns stamped PDF bytes.
    """
    reader = PdfReader(base_pdf_path)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        writer.add_page(page)

        # Clear all AcroForm widget values on this page so old data doesn't show
        for annot_ref in page.get("/Annots", []):
            try:
                obj = annot_ref.get_object()
                if obj.get("/Subtype") == "/Widget":
                    from pypdf.generic import NameObject, TextStringObject
                    ft = obj.get("/FT", "")
                    if ft == "/Btn":
                        obj[NameObject("/V")]  = NameObject("/Off")
                        obj[NameObject("/AS")] = NameObject("/Off")
                    elif ft == "/Tx":
                        obj[NameObject("/V")] = TextStringObject("")
            except:
                pass

        entries = pages_data.get(i, [])
        if not entries:
            continue

        overlay_bytes = make_overlay(entries, w, h)
        overlay_reader = PdfReader(BytesIO(overlay_bytes))
        overlay_page = overlay_reader.pages[0]
        writer.pages[i].merge_page(overlay_page)

    final_out = BytesIO()
    # Force viewer to regenerate appearances so cleared fields render as empty
    try:
        from pypdf.generic import NameObject, BooleanObject
        root = writer._root_object
        if '/AcroForm' in root:
            af = root['/AcroForm'].get_object()
            af[NameObject('/NeedAppearances')] = BooleanObject(True)
    except Exception:
        pass
    writer.write(final_out)
    return final_out.getvalue()
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
# Field coordinate map
# Coordinates are (x, y) — PDF origin is bottom-left.
# y values are the BOTTOM of each field rect from the dump above.
# We draw text slightly above the bottom: y + 2.
# ---------------------------------------------------------------------------

def ck(condition): return CHECK if condition else ""


def build_pages_data(s, addr_full, buyer, closing_md, closing_yy,
                     phone_area, phone_num, has_loan, has_hoa,
                     has_sale, has_bkup, price, loan, cash,
                     title_payer, title_amend, survey, seller_disc,
                     as_is, possession, lot, block):

    pages = {}

    # ── PAGE 1 (index 0) ────────────────────────────────────────────────────
    # Checkbox coordinates from blank template field dump (x=left edge, y=bottom of rect)
    pages[0] = [
        # Text fields
        (280, 690, s.get("seller", "")),           # §1 Seller name
        (124, 679, buyer),                          # §1 Buyer name
        (127, 616, lot),                            # §2A Lot
        (222, 616, block),                          # §2A Block
        (157, 606, s.get("city", "")),              # §2A City
        (387, 606, s.get("county", "")),            # §2A County
        (161, 595, addr_full),                      # §2A Address
        (457, 319, fmt_money(loan) if has_loan else ""),          # §3B loan sum
        (457, 269, fmt_money(cash) if has_loan else fmt_money(price)),  # §3A cash
        (457, 257, fmt_money(price)),               # §3C total
        # §3B checkboxes (x=314 y=283 = Third Party Financing)
        (314, 285, ck(has_loan)),                   # Third Party Financing checkbox
        # §6A(8) title amendment (x=48 y=196/170)
        (48,  198, ck(title_amend == "i")),         # (i) will not be amended
        (48,  172, ck(title_amend in ["ii_buyer", "ii_seller"])),  # (ii) will be amended
        # §6A title payer (x=48 y=134 = seller expense, x=61 y=98 = Sellers, x=60 y=84 = Seller/Buyer)
        (48,  136, ck(title_payer == "seller")),    # Seller's expense checkbox
        (61,  100, ck(title_payer == "seller")),    # "Sellers" radio
        (60,   86, ck(title_payer == "buyer")),     # "Buyer's" radio
    ]

    # ── PAGE 2 (index 1) ────────────────────────────────────────────────────
    pages[1] = [
        # Text fields
        (153, 701, s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW")),
        (75,  691, s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033")),
        (293, 691, fmt_money(s.get("earnest", ""))),   # §5A earnest $
        (488, 691, fmt_money(s.get("optionFee", ""))), # §5A option fee $
        (76,  503, str(s.get("optionDays", "7"))),     # §5B option period days
        (285, 342, s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC")),
        # §6C survey — 2Within x=76 y=178, 3Within x=75 y=167
        (76,  180, ck(survey == "buyerNew")),           # §6C(2) buyer new survey
        (75,  169, ck(survey == "noSurvey")),           # §6C(3) no survey
        # §6E(2) HOA — is x=435 y=168, is not x=499 y=168
        (435, 170, ck(has_hoa)),                        # "is" mandatory HOA
        (499, 170, ck(not has_hoa)),                    # "is not" mandatory HOA
    ]

    # ── PAGE 3 (index 2) ────────────────────────────────────────────────────
    pages[2] = [
        # §6C survey days & option 1
        (124, 579, str(s.get("surveyDays", "7"))),      # Survey days box
        (454, 318, ck(survey == "sellerExisting")),      # §6C(1) seller existing survey
        (478, 317, ck(survey == "buyerNew")),            # §6C(2) buyer new survey
        # §6D objection days
        (371, 515, str(s.get("disclosureDays", "3"))),  # Title objection days
        # §7B seller disclosure — Within one x=144 y=640, Within two x=198 y=640, Within three x=59 y=630
        (144, 642, ck(seller_disc == "received")),       # (1) Buyer received notice
        (198, 642, ck(seller_disc == "notReceived")),    # (2) Buyer not received
        (59,  632, ck(seller_disc == "exempt")),         # (3) Seller exempt
    ]

    # ── PAGE 4 (index 3) — As-Is, Possession ────────────────────────────────
    pages[3] = [
        (128, 751, addr_full),                           # Header
        # §7D As-Is — x=62 y=149/138
        (62,  151, ck(as_is == "yes")),                  # (1) As Is
        (62,  140, ck(as_is == "repairs")),              # (2) As Is with repairs
        # §10 Possession — upon x=62 y=79
        (62,   81, ck(possession == "funding")),         # Upon closing and funding
    ]

    # ── PAGE 5 (index 4) — Closing date, As-Is duplicate, Settlement ─────────
    pages[4] = [
        (128, 751, addr_full),                           # Header
        # §7D As-Is duplicate checkboxes on this page — x=59 y=681/669
        (59,  683, ck(as_is == "yes")),                  # As Is
        (59,  671, ck(as_is == "repairs")),              # As Is except
        # §9 Closing date — x=291 y=195, year x=442 y=195
        (291, 197, closing_md),                          # Closing date (month day)
        (442, 197, closing_yy),                          # Closing year (2 digits)
    ]

    # ── PAGE 6 (index 5) — Option fee credit ─────────────────────────────────
    pages[5] = [
        (129, 751, addr_full),                           # Header
        # §5B option fee WILL be credited — x=351 y=657
        (351, 659, ck(True)),                            # "will" be credited
    ]

    # ── PAGE 8 (index 7) — Notices & Addenda checklist ───────────────────────
    pages[7] = [
        (129, 751, addr_full),                           # Header
        # §21 Buyer notices
        (133, 699, s.get("buyerMailAddr", "")),          # Buyer mailing address
        (139, 649, phone_area),                          # Buyer phone area code
        (166, 650, phone_num),                           # Buyer phone number
        (135, 624, s.get("buyerEmail", "")),             # Buyer email
        # §22 Addenda checkboxes — only check what applies, leave rest blank
        (65,  519, ck(has_loan)),                        # Third Party Financing
        (65,  490, ck(has_hoa)),                         # HOA Addendum
        (65,  427, ck(has_sale)),                        # Sale of Other Property
        (66,  378, ck(has_bkup)),                        # Back-Up Contract
        # All others intentionally left unchecked (empty string = no stamp)
    ]

    # ── PAGE 9 (index 8) — Execution ─────────────────────────────────────────
    pages[8] = [
        (129, 751, addr_full),                           # Header
    ]

    # ── PAGE 10 (index 9) — Broker info ──────────────────────────────────────
    pages[9] = [
        (126, 751, addr_full),                           # Header
        # Buyer's agent info (only if has agent)
        (50,  631, s.get("agentBrokerage", "") if s.get("hasBuyerAgent") == "yes" else ""),
        (50,  562, s.get("agentName", "")      if s.get("hasBuyerAgent") == "yes" else ""),
        (50,  502, s.get("agentEmail", "")     if s.get("hasBuyerAgent") == "yes" else ""),
        (216, 502, s.get("agentPhone", "")     if s.get("hasBuyerAgent") == "yes" else ""),
        # Buyer only rep checkbox x=109 y=598
        (109, 600, ck(s.get("hasBuyerAgent") == "yes")),
    ]

    # ── PAGE 11 (index 10) — Receipts ────────────────────────────────────────
    pages[10] = [
        (127, 751, addr_full),                           # Header
    ]

    return pages


# ---------------------------------------------------------------------------
# Fill and merge
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

    pages_data = build_pages_data(
        s, addr_full, buyer, closing_md, closing_yy,
        phone_area, phone_num, has_loan, has_hoa, has_sale, has_bkup,
        price, loan, cash, title_payer, title_amend, survey,
        seller_disc, as_is, possession, lot, block
    )

    # Stamp main contract
    main_bytes = stamp_pdf(MAIN_PDF, pages_data)

    # Merge addenda with address headers and key fields stamped
    merger = PdfWriter()
    merger.append(PdfReader(BytesIO(main_bytes)))

    # Third Party Financing Addendum
    if has_loan and os.path.exists(FINANCING_PDF):
        fin_pages = {
            0: [
                (55, 638, addr_full),
                (57, 559, ck(s.get("financing") == "conventional")),
                (57, 417, ck(s.get("financing") == "fha")),
                (58, 302, ck(s.get("financing") == "va")),
                (56, 242, ck(s.get("financing") == "usda")),
            ],
            1: [
                (57, 730, addr_full),
                (84, 594, ck(True)),   # subject to buyer approval
            ],
        }
        fin_bytes = stamp_pdf(FINANCING_PDF, fin_pages)
        merger.append(PdfReader(BytesIO(fin_bytes)))

    # HOA Addendum
    if has_hoa and os.path.exists(HOA_PDF):
        hoa_pages = {0: [(36, 660, addr_full)]}
        hoa_bytes = stamp_pdf(HOA_PDF, hoa_pages)
        merger.append(PdfReader(BytesIO(hoa_bytes)))

    # Sale of Other Property Addendum
    if has_sale and os.path.exists(SALE_PDF):
        sale_pages = {0: [(55, 658, addr_full)]}
        sale_bytes = stamp_pdf(SALE_PDF, sale_pages)
        merger.append(PdfReader(BytesIO(sale_bytes)))

    # Back-Up Contract Addendum
    if has_bkup and os.path.exists(BACKUP_PDF):
        bkup_pages = {0: [(55, 658, addr_full)]}
        bkup_bytes = stamp_pdf(BACKUP_PDF, bkup_pages)
        merger.append(PdfReader(BytesIO(bkup_bytes)))

    out = BytesIO()
    merger.write(out)
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
        json=payload, timeout=30
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

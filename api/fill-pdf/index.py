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
                        # Remove appearance stream so old checkmark can't render
                        if NameObject("/AP") in obj:
                            del obj[NameObject("/AP")]
                    elif ft == "/Tx":
                        obj[NameObject("/V")] = TextStringObject("")
                        if NameObject("/AP") in obj:
                            del obj[NameObject("/AP")]
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
# ---------------------------------------------------------------------------

def ck(condition): return CHECK if condition else ""


def build_pages_data(s, addr_full, buyer, closing_md, closing_yy,
                     phone_area, phone_num, has_loan, has_hoa,
                     has_sale, has_bkup, price, loan, cash,
                     title_payer, title_amend, survey, seller_disc,
                     as_is, possession, lot, block):

    pages = {}

    # ── PAGE 1 (index 0) ────────────────────────────────────────────────────
    pages[0] = [
        (280, 690, s.get("seller", "")),
        (124, 679, buyer),
        (127, 616, lot),
        (222, 616, block),
        (157, 606, s.get("city", "")),
        (387, 606, s.get("county", "")),
        (161, 595, addr_full),
        # §3 Sales Price
        (457, 319, fmt_money(loan) if has_loan else ""),
        (457, 269, fmt_money(cash) if has_loan else fmt_money(price)),
        (457, 257, fmt_money(price)),
        # §3B Third Party Financing checkbox
        (314, 285, ck(has_loan)),
        # §4 LEASES — only check if user selected them (all default false)
        (48, 207, ck(s.get("leaseResidential") == "yes")),   # §4A residential leases
        (48, 180, ck(s.get("leaseFixture") == "yes")),        # §4B fixture leases
        (48, 145, ck(s.get("leaseNaturalResource") == "yes")), # §4C natural resource leases
        (61, 109, ck(s.get("leaseNaturalResource") == "yes" and s.get("leaseNRDelivered") == "yes")),  # §4C(1)
        (61,  94, ck(s.get("leaseNaturalResource") == "yes" and s.get("leaseNRDelivered") == "no")),   # §4C(2)
    ]

    # ── PAGE 2 (index 1) ────────────────────────────────────────────────────
    # FIX: address was missing on page 2 — the header line is at y=758
    escrow_agent = s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW")
    escrow_addr  = s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033")
    pages[1] = [
        (128, 758, addr_full),                               # FIX: header address was missing
        (153, 701, escrow_agent,  7),                        # §5A escrow agent (narrow field)
        (75,  691, escrow_addr,   7),                        # §5A escrow address
        (293, 691, fmt_money(s.get("earnest", ""))),
        (488, 691, fmt_money(s.get("optionFee", ""))),
        (76,  503, str(s.get("optionDays", "7"))),
        # §6A title policy — FIX: Seller checkbox was at wrong coords
        # Seller's: x=313.0 top=430.9 -> rl_y=361.1; Buyer's: x=368.1 rl_y=361.1
        (313, 361, ck(title_payer == "seller")),             # FIX: was (48,136) wrong page
        (368, 361, ck(title_payer == "buyer")),
        # §6A(8)(i)/(ii) — FIX: (i) should be checked by default
        # (i) x=75.1 top=604.4 -> rl_y=187.6
        # (ii) x=75.1 top=614.7 -> rl_y=177.3
        (75, 188, ck(title_amend == "i")),                   # FIX: was wrong page
        (75, 177, ck(title_amend in ["ii_buyer", "ii_seller"])),
        # §6A(8)(ii) sub — Buyer x=434.9 rl_y=179.0, Seller x=498.6 rl_y=177.3
        (435, 179, ck(title_amend == "ii_buyer")),
        (499, 177, ck(title_amend == "ii_seller")),
        (285, 342, s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC")),
        # §6C survey — on page 2: option 2 (buyerNew) x=76 rl_y=178, option 3 (noSurvey) x=75 rl_y=169
        (76,  180, ck(survey == "buyerNew")),
        (75,  169, ck(survey == "noSurvey")),
        # §6E(2) HOA membership
        (435, 170, ck(has_hoa)),
        (499, 170, ck(not has_hoa)),
    ]

    # ── PAGE 3 (index 2) ────────────────────────────────────────────────────
    pages[2] = [
        (130, 751, addr_full),
        # §6C survey option 1 — nq glyph at x=58 top=74.5 rl_y=717.5
        (58,  718, ck(survey == "sellerExisting")),          # §6C(1) checkbox
        (125, 717, str(s.get("surveyDays", "7"))),           # §6C(1) days blank
        # §6C(1) sub — Seller's expense x=142 rl_y=651, Buyer's x=197 rl_y=649
        (142, 651, ck(survey == "sellerExisting")),          # §6C(1) Seller's expense default
        (197, 649, ck(False)),                               # §6C(1) Buyer's expense (not default)
        # §6C(3) — x=59.7 top=202.8 rl_y=589.2
        (60,  589, ck(survey == "noSurvey")),                # §6C(3) Seller new survey
        (125, 579, str(s.get("surveyDays", "7"))),           # §6C(2)/(3) days blank
        # §6D objection days — x=371 rl_y=327 (from nqis at top=465)
        (371, 327, str(s.get("objectionDays", "3"))),
        # §7B seller disclosure — checkboxes at:
        # (1) received: x=59.7 top=152.9 rl_y=639.1 (the lone 'q' at top=152.9)
        # Wait — page 3 has §6C and §6E; §7B is on page 4. Let me keep these on page 4.
    ]

    # ── PAGE 4 (index 3) — §7B Seller Disclosure ────────────────────────────
    # §7B checkboxes confirmed at:
    # (1) received: qn at x=61.8 top=632.0 rl_y=160.0
    # (2) not received: q at x=61.8 top=643.0 rl_y=149.0
    # (3) exempt: qn at x=61.8 top=702.0 rl_y=90.0
    pages[3] = [
        (128, 751, addr_full),
        # §7B seller disclosure — FIX: was on wrong page (page 3 index 2); they're on page 4 index 3
        (62,  160, ck(seller_disc == "received")),           # §7B(1) buyer received notice
        (62,  149, ck(seller_disc == "notReceived")),        # §7B(2) buyer NOT received
        (62,   90, ck(seller_disc == "exempt")),             # §7B(3) seller exempt
        # §7B(2) days blank — between 'Within' and 'days after' on that line
        (178, 149, str(s.get("disclosureDays", "3")) if seller_disc == "notReceived" else ""),
    ]

    # ── PAGE 5 (index 4) — §7D As-Is ────────────────────────────────────────
    # §7D(1) As-Is: qn at x=58.2 top=100.0 rl_y=692.0
    # §7D(2) As-Is with repairs: q at x=58.2 top=112.7 rl_y=679.3
    pages[4] = [
        (128, 751, addr_full),
        (59,  692, ck(as_is == "yes")),                      # §7D(1) Buyer accepts As Is
        (59,  679, ck(as_is == "repairs")),                  # §7D(2) As Is with repairs
        # §9A closing date — 'before' ends at x=255; date field starts ~x=291 top=587.9 rl_y=204.1
        (291, 204, closing_md),
        (442, 204, closing_yy),
        # §8 Broker disclosure field
        (73,  241, s.get("brokerDisclosure", "")),
    ]

    # ── PAGE 6 (index 5) — §10 Possession, §12A ────────────────────────────
    # Possession: nqupon at x=351 top=123.8 rl_y=668.2, qaccording at x=498.7 rl_y=668.2
    # §12A(1)(b): q$ at x=110.9 rl_y=314.2, q at x=236.3 rl_y=314.2
    # §12A(1)(c): $ at x=240.4 top=489.4 rl_y=302.6 — draw amount at x=253
    pages[5] = [
        (129, 751, addr_full),
        # §10 Possession — FIX: was on page 4; it's on page 6 (index 5)
        (351, 668, ck(possession == "funding")),             # "upon closing and funding"
        (499, 668, ck(possession == "lease")),               # "according to temp lease"
        # §12A(1)(b) seller concession checkbox + amount
        (111, 314, ck(bool(s.get("concessionAmount")))),     # $ checkbox
        (253, 303, fmt_money(s.get("concessionAmount", "")) if s.get("concessionAmount") else ""),  # §12A(1)(c) amount
    ]

    # ── PAGE 7 (index 6) — no fillable fields ───────────────────────────────

    # ── PAGE 8 (index 7) — Notices & Addenda ─────────────────────────────────
    pages[7] = [
        (129, 751, addr_full),
        (133, 699, s.get("buyerMailAddr", "")),
        (139, 649, phone_area),
        (166, 650, phone_num),
        (135, 624, s.get("buyerEmail", "")),
        # §22 Addenda checkboxes — only check applicable ones
        (65,  519, ck(has_loan)),   # Third Party Financing
        (65,  490, ck(has_hoa)),    # HOA
        (65,  427, ck(has_sale)),   # Sale of Other Property
        (66,  378, ck(has_bkup)),   # Back-Up Contract
    ]

    # ── PAGE 9 (index 8) — Execution ─────────────────────────────────────────
    pages[8] = [
        (129, 751, addr_full),
    ]

    # ── PAGE 10 (index 9) — Broker info ──────────────────────────────────────
    pages[9] = [
        (126, 751, addr_full),
        (50,  631, s.get("agentBrokerage", "") if s.get("hasBuyerAgent") == "yes" else ""),
        (50,  562, s.get("agentName", "")      if s.get("hasBuyerAgent") == "yes" else ""),
        (50,  502, s.get("agentEmail", "")     if s.get("hasBuyerAgent") == "yes" else ""),
        (216, 502, s.get("agentPhone", "")     if s.get("hasBuyerAgent") == "yes" else ""),
        (109, 600, ck(s.get("hasBuyerAgent") == "yes")),
    ]

    # ── PAGE 11 (index 10) — Receipts ────────────────────────────────────────
    pages[10] = [
        (127, 751, addr_full),
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
                # Financing type — check correct box
                (57, 559, ck(s.get("financing") == "conventional")),
                (57, 417, ck(s.get("financing") == "fha")),
                (58, 302, ck(s.get("financing") == "va")),
                (56, 242, ck(s.get("financing") == "usda")),
            ],
            1: [
                (57, 730, addr_full),
                # §2A Buyer Approval
                (82, 694, ck(s.get("buyerApproval") == "yes")),
                (82, 562, ck(s.get("buyerApproval") == "no")),
            ],
        }
        fin_bytes = stamp_pdf(FINANCING_PDF, fin_pages)
        merger.append(PdfReader(BytesIO(fin_bytes)))

    # HOA Addendum
    if has_hoa and os.path.exists(HOA_PDF):
        hoa_name = s.get("hoaName", "")
        hoa_pages = {
            0: [
                (36, 660, addr_full),
                (36, 634, hoa_name),
                (43, 557, ck(s.get("hoaSubdivisionInfo") == "seller")),
                (43, 501, ck(s.get("hoaSubdivisionInfo") == "buyer")),
                (43, 453, ck(s.get("hoaSubdivisionInfo") == "received")),
                (43, 404, ck(s.get("hoaSubdivisionInfo") == "notRequired")),
                (370, 309, fmt_money(s.get("hoaReserves", "")) if s.get("hoaReserves") else ""),
                (227, 234, ck(s.get("hoaTitleCost") == "buyer")),
                (273, 234, ck(s.get("hoaTitleCost") == "seller")),
            ],
        }
        hoa_bytes = stamp_pdf(HOA_PDF, hoa_pages)
        merger.append(PdfReader(BytesIO(hoa_bytes)))

    # Sale of Other Property Addendum
    if has_sale and os.path.exists(SALE_PDF):
        sale_contingent_addr = s.get("salePropertyAddr", "")
        sale_contingency_md, sale_contingency_yy = split_date(s.get("saleContingencyDate", ""))
        sale_waiver_days = str(s.get("saleWaiverDays", "3"))
        sale_additional_earnest = fmt_money(s.get("saleAdditionalEarnest", "")) if s.get("saleAdditionalEarnest") else ""
        sale_pages = {
            0: [
                (54,  624, addr_full),                  # Property address header
                (55,  568, sale_contingent_addr),       # §A buyer's other property address
                                                        #   (top=224.0 rl_y=568.0 — the 'at' line)
                (138, 554, sale_contingency_md),        # §A contingency date (on or before)
                (400, 554, sale_contingency_yy),        # §A year (after '20')
                (150, 457, sale_waiver_days),           # §B waiver days blank
                (497, 423, sale_additional_earnest),    # §C additional earnest $ amount
            ],
        }
        sale_bytes = stamp_pdf(SALE_PDF, sale_pages)
        merger.append(PdfReader(BytesIO(sale_bytes)))

    # Back-Up Contract Addendum
    if has_bkup and os.path.exists(BACKUP_PDF):
        bkup_addl_earnest    = fmt_money(s.get("bkupAdditionalEarnest", "")) if s.get("bkupAdditionalEarnest") else ""
        bkup_addl_option     = fmt_money(s.get("bkupAdditionalOption", ""))  if s.get("bkupAdditionalOption")  else ""
        bkup_addl_days       = str(s.get("bkupAdditionalDays", ""))
        bkup_first_contract_md,  bkup_first_contract_yy  = split_date(s.get("bkupFirstContractDate", ""))
        bkup_terminate_md,       bkup_terminate_yy        = split_date(s.get("bkupTerminateDate", ""))
        bkup_pages = {
            0: [
                (55,  658, addr_full),                  # Address header
                # §A(2) additional earnest/option/days
                # '$_________' blank at x=332.9 top=252.9 rl_y=539.1 — draw after $
                (400, 539, bkup_addl_earnest),          # §A(2) additional earnest money amount
                # 'Option Fee of $' — next segment on same line at x=551.6 top=252.9
                # continues to next line at x=88.1 top=263 (rl_y=529)
                (88,  529, bkup_addl_option),           # §A(2) additional option fee amount
                # 'within ____ days' blank — on line starting 'to Escrow Agent within'
                # that line is top~263 but let's check: x=88.1 top=263.9... need to place
                # days blank after 'within' on page 0 line 3 of §A(2)
                # From coord scan: top=263.9 is continuation. Place days at ~x=230
                (230, 519, bkup_addl_days),             # §A(2) days blank
                # §G first contract date: blank line x=165 top=532 rl_y=260
                (165, 260, bkup_first_contract_md),     # §G first contract date
                (339, 260, bkup_first_contract_yy),     # §G year
                # §H termination date: blank starts after 'before' x=335 top=573 rl_y=219
                (335, 219, bkup_terminate_md),          # §H termination date
                (492, 219, bkup_terminate_yy),          # §H year
            ],
            1: [
                # Back-Up page 2 address header — 'Addendum for Back-Up Contract ___'
                # top=48.2 rl_y=743.8; address goes on the blank line after 'Contract'
                (182, 744, addr_full),                  # FIX: page 2 address header
            ],
        }
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

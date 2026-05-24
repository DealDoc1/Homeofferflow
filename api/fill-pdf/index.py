
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
CHECK     = "X"

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

def make_overlay(page_entries, page_width=612, page_height=792):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    for entry in page_entries:
        x, y, text = entry[0], entry[1], entry[2]
        fs = entry[3] if len(entry) > 3 else FONT_SIZE

        if not text:
            continue

        # Global correction:
        # Text was landing slightly high.
        # Checkmarks were landing slightly high/left.
        if str(text) == CHECK:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x + 2, y - 4, str(text))
        else:
            c.setFont(FONT, fs)
            c.drawString(x, y - 3, str(text))

    c.save()
    buf.seek(0)
    return buf.read()

def stamp_pdf(base_pdf_path, pages_data: dict) -> bytes:
    reader = PdfReader(base_pdf_path)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        writer.add_page(page)
        for annot_ref in page.get("/Annots", []):
            try:
                obj = annot_ref.get_object()
                if obj.get("/Subtype") == "/Widget":
                    from pypdf.generic import NameObject, TextStringObject
                    ft = obj.get("/FT", "")
                    if ft == "/Btn":
                        obj[NameObject("/V")]  = NameObject("/Off")
                        obj[NameObject("/AS")] = NameObject("/Off")
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

def ck(condition): return CHECK if condition else ""


def build_pages_data(s, addr_full, buyer, closing_md, closing_yy,
                     phone_area, phone_num, has_loan, has_hoa,
                     has_sale, has_bkup, price, loan, cash,
                     title_payer, title_amend, survey, seller_disc,
                     as_is, possession, lot, block):
    pages = {}

    # ── PAGE 1 (index 0) ────────────────────────────────────────────────────
    # Lot: field starts after 'Lot' label (x0=109.4), blank at x=127
    # Block: field starts after 'BlockS' label (x0=195.4), blank at x=228
    # Subdivision: 'Addition,' is at x=73.8; blank runs from x=73 to x=122 (before 'City')
    #   → draw subdivision at x=73 (it comes before City label)
    # City: label ends ~x=156; field at x=157
    # County: label ends ~x=386; field at x=387
    # Address (known as): field at x=161, top=189.9, rl_y=602.1
    pages[0] = [
        (280, 690, s.get("seller", "")),
        (124, 679, buyer),
        # §2A Land fields — top=168.9 rl_y=623.1 for filled values
        (127, 622, lot),                                     # Lot blank
        (228, 622, block),                                   # Block blank
        # Subdivision/Addition: blank before 'City of' label at x=122
        # Draw at x=73, same line as Addition label, rl_y=613.1
        (73,  613, s.get("subdivision", "")),                # Subdivision name
        (157, 613, s.get("city", "")),                       # City of ___
        (387, 613, s.get("county", "")),                     # County of ___
        (161, 602, addr_full),                               # known as (address)
        # §3 Sales Price
        (457, 319, fmt_money(loan) if has_loan else ""),
        (457, 269, fmt_money(cash) if has_loan else fmt_money(price)),
        (457, 257, fmt_money(price)),
        # §3B financing checkbox
        (314, 285, ck(has_loan)),
        # §4 Leases — only check if user explicitly selected
        (48, 207, ck(s.get("leaseResidential") == "yes")),
        (48, 180, ck(s.get("leaseFixture") == "yes")),
        (48, 145, ck(s.get("leaseNaturalResource") == "yes")),
        (61, 109, ck(s.get("leaseNaturalResource") == "yes" and s.get("leaseNRDelivered") == "yes")),
        (61,  94, ck(s.get("leaseNaturalResource") == "yes" and s.get("leaseNRDelivered") == "no")),
    ]

    # ── PAGE 2 (index 1) ────────────────────────────────────────────────────
    # §6A Seller's q: x0=313.0 top=430.9 rl_y=361.1
    # §6A Buyer's q:  x0=368.1 top=430.9 rl_y=361.1
    # Draw ■ at exact q glyph position — the glyph baseline IS the draw y
    # §6A(8)(i) q: x0=75.1 top=604.4 rl_y=187.6
    # §6A(8)(ii) q: x0=75.1 top=614.7 rl_y=177.3
    # §6A(8)(ii) Buyer qn: x0=434.9 top=613.0 rl_y=179.0
    # §6A(8)(ii) Seller q: x0=498.6 top=614.7 rl_y=177.3
    escrow_agent = s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW")
    escrow_addr  = s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033")
    pages[1] = [
        (128, 758, addr_full),                               # header address
        (153, 701, escrow_agent, 7),
        (75,  691, escrow_addr,  7),
        (293, 691, fmt_money(s.get("earnest", ""))),
        (488, 691, fmt_money(s.get("optionFee", ""))),
        (76,  503, str(s.get("optionDays", "7"))),
        # §6A title policy — draw at exact q glyph x, y
        (313, 361, ck(title_payer == "seller")),
        (368, 361, ck(title_payer == "buyer")),
        # §6A(8) — draw at exact q positions
        (75,  188, ck(title_amend == "i")),
        (75,  177, ck(title_amend in ["ii_buyer", "ii_seller"])),
        (435, 179, ck(title_amend == "ii_buyer")),
        (499, 177, ck(title_amend == "ii_seller")),
        (285, 342, s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC")),
        # §6C survey options on page 2 (buyerNew=option2, noSurvey=option3 NOT on p2)
        # Page 2 has option2 at q x=59.7 top=152.9 rl_y=639.1 and option3... 
        # Actually page 2 has no §6C — §6C is on page 3. Remove these from p2.
        # §6E(2) HOA is/is not: nqis at x=454 top=465 rl_y=327; qis not at x=478 rl_y=325.3
        # These are on page 3, not page 2. Remove from here too.
    ]

    # ── PAGE 3 (index 2) ────────────────────────────────────────────────────
    # §6C survey:
    #   (1) nq glyph: x0=58.0 top=74.5 rl_y=717.5 — the n is the filled box, q is empty
    #       → draw ■ at x=58, y=717 for option 1
    #   Seller's sub-checkbox: qn at x=142 top=141.0 rl_y=651.0
    #   Buyer's sub-checkbox:  q  at x=197 top=143.2 rl_y=648.8
    #   (2) q at x=59.7 top=152.9 rl_y=639.1
    #   (3) q(3) at x=59.7 top=202.8 rl_y=589.2
    # §6E(2) HOA: nqis at x=454 top=465.0 rl_y=327.0; qis at x=478 top=466.7 rl_y=325.3
    pages[2] = [
        (130, 751, addr_full),
        # §6C survey checkboxes — drawn at exact q glyph positions
        (58,  717, ck(survey == "sellerExisting")),          # §6C(1)
        (125, 717, str(s.get("surveyDays", "7"))),           # §6C(1) days blank
        (142, 651, ck(survey == "sellerExisting")),          # §6C(1) Seller's expense
        (197, 649, ck(False)),                               # §6C(1) Buyer's expense (not default)
        (60,  639, ck(survey == "buyerNew")),                # §6C(2)
        (125, 639, str(s.get("surveyDays", "7"))),           # §6C(2) days blank
        (60,  589, ck(survey == "sellerNew")),               # §6C(3)
        (125, 589, str(s.get("surveyDays", "7"))),           # §6C(3) days blank
        # §6D objection days — from prior measurement x=371 rl_y=327
        (371, 327, str(s.get("objectionDays", "3"))),
        # §6E(2) HOA is/is not — exact q positions
        (454, 327, ck(has_hoa)),                             # "is" subject to HOA
        (478, 325, ck(not has_hoa)),                         # "is not" subject to HOA
    ]

    # ── PAGE 4 (index 3) — §7B Seller Disclosure ────────────────────────────
    # §7B(1) qn: x=61.8 top=632.0 rl_y=160.0
    # §7B(2) q:  x=61.8 top=643.0 rl_y=149.0
    # §7B(3) qn: x=61.8 top=702.0 rl_y=90.0
    # Days blank for (2): 'Within' at x=282.6; blank runs to 'days' at x=370.9 top=645.4
    #   → draw days at x=320, y=146 (slightly below q glyph top for (2))
    pages[3] = [
        (128, 751, addr_full),
        (62,  160, ck(seller_disc == "received")),
        (62,  149, ck(seller_disc == "notReceived")),
        (62,   90, ck(seller_disc == "exempt")),
        (320, 146, str(s.get("disclosureDays", "3")) if seller_disc == "notReceived" else ""),
    ]

    # ── PAGE 5 (index 4) — §7D As-Is ────────────────────────────────────────
    # §7D(1) qn: x=58.2 top=100.0 rl_y=692.0  — option 1
    # §7D(2) q:  x=58.2 top=112.7 rl_y=679.3  — option 2
    pages[4] = [
        (128, 751, addr_full),
        (59,  692, ck(as_is == "yes")),
        (59,  679, ck(as_is == "repairs")),
        # §9A closing date
        (291, 204, closing_md),
        (442, 204, closing_yy),
        (73,  241, s.get("brokerDisclosure", "")),
    ]

    # ── PAGE 6 (index 5) — §10 Possession, §12 ──────────────────────────────
    # Possession: nqupon at x=351.0 top=123.8 rl_y=668.2; qaccording at x=498.7
    # The ■ needs to sit INSIDE the checkbox square.
    # The 'nq' glyph: 'n' = filled box, 'q' = the empty square for user to fill
    # For 'nqupon': the checkbox for "upon closing" is the 'q' part at x=351+char_width
    # Let's draw slightly right of x=351 and slightly below y=668
    pages[5] = [
        (129, 751, addr_full),
        (352, 665, ck(possession == "funding")),             # upon closing
        (500, 665, ck(possession == "lease")),               # according to lease
        # §12A(1)(b) — checkbox for $ concession; §12A(1)(c) amount
        (111, 314, ck(bool(s.get("concessionAmount")))),
        (253, 303, fmt_money(s.get("concessionAmount", "")) if s.get("concessionAmount") else ""),
    ]

    # ── PAGE 7 (index 6) — no fields ────────────────────────────────────────

    # ── PAGE 8 (index 7) — Notices & Addenda ────────────────────────────────
    pages[7] = [
        (129, 751, addr_full),
        (133, 699, s.get("buyerMailAddr", "")),
        (139, 649, phone_area),
        (166, 650, phone_num),
        (135, 624, s.get("buyerEmail", "")),
        (65,  519, ck(has_loan)),
        (65,  490, ck(has_hoa)),
        (65,  427, ck(has_sale)),
        (66,  378, ck(has_bkup)),
    ]

    # ── PAGES 9-11 ───────────────────────────────────────────────────────────
    pages[8]  = [(129, 751, addr_full)]
    pages[9]  = [
        (126, 751, addr_full),
        (50,  631, s.get("agentBrokerage", "") if s.get("hasBuyerAgent") == "yes" else ""),
        (50,  562, s.get("agentName", "")      if s.get("hasBuyerAgent") == "yes" else ""),
        (50,  502, s.get("agentEmail", "")     if s.get("hasBuyerAgent") == "yes" else ""),
        (216, 502, s.get("agentPhone", "")     if s.get("hasBuyerAgent") == "yes" else ""),
        (109, 600, ck(s.get("hasBuyerAgent") == "yes")),
    ]
    pages[10] = [(127, 751, addr_full)]

    return pages


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

    main_bytes = stamp_pdf(MAIN_PDF, pages_data)
    merger = PdfWriter()
    merger.append(PdfReader(BytesIO(main_bytes)))

    # ── THIRD PARTY FINANCING ADDENDUM ───────────────────────────────────────
    # Measured from flat template (952x1260px → 612x792 PDF pts):
    # p1 addr: (23, 697) | conventional: (23, 602) | fha: (23, 490)
    # va: (23, 443) | usda: (23, 404)
    # p2 addr: (23, 759) | subject to approval: (47, 718) | not subject: (47, 614)
    if has_loan and os.path.exists(FINANCING_PDF):
                fin_pages = {
            0: [
                (205, 642, addr_full, 8),

                (61, 557, ck(s.get("financing") == "conventional")),
                (91, 542, ck(s.get("financing") == "conventional")),
                (360, 540, fmt_money(s.get("loanAmount", "")) if s.get("financing") == "conventional" else ""),

                (61, 445, ck(s.get("financing") == "fha")),
                (61, 398, ck(s.get("financing") == "va")),
                (61, 359, ck(s.get("financing") == "usda")),
            ],
            1: [
                (205, 724, addr_full, 8),
                (92, 684, ck(s.get("buyerApproval", "yes") != "no")),
                (92, 584, ck(s.get("buyerApproval") == "no")),
            ],
        }
        fin_bytes = stamp_pdf(FINANCING_PDF, fin_pages)
        merger.append(PdfReader(BytesIO(fin_bytes)))

    # ── HOA ADDENDUM ─────────────────────────────────────────────────────────
    # Measured from flat template (952x1260px → 612x792):
    # addr: (23, 702) | hoa_name: (23, 680)
    # §A opt1: (23, 625) | opt1_days: (55, 625) | opt2: (23, 580) | opt2_days: (55, 580)
    # opt3: (23, 541) | opt4: (23, 505)
    # §C amount: (244, 441) | §D buyer: (147, 394) | §D seller: (176, 394)
    if has_hoa and os.path.exists(HOA_PDF):
        hoa_info  = s.get("hoaSubdivisionInfo", "")
                hoa_pages = {
            0: [
                (180, 662, addr_full, 8),
                (180, 632, s.get("hoaName", ""), 8),

                (52, 555, ck(hoa_info == "seller" or hoa_info == "")),
                (110, 555, str(s.get("hoaDays", "3")) if hoa_info in ["seller", ""] else ""),

                (52, 499, ck(hoa_info == "buyer")),
                (110, 499, str(s.get("hoaDays", "")) if hoa_info == "buyer" else ""),

                (52, 460, ck(hoa_info == "received")),
                (52, 424, ck(hoa_info == "notRequired")),

                (410, 313, fmt_money(s.get("hoaReserves", "")) if s.get("hoaReserves") else ""),

                (400, 235, ck(s.get("hoaTitleCost") == "buyer")),
                (431, 235, ck(s.get("hoaTitleCost") == "seller" or not s.get("hoaTitleCost"))),
            ],
        }
        hoa_bytes = stamp_pdf(HOA_PDF, hoa_pages)
        merger.append(PdfReader(BytesIO(hoa_bytes)))

    # ── SALE OF OTHER PROPERTY ADDENDUM ──────────────────────────────────────
    # Measured from flat template (952x1260px → 612x792):
    # addr_header: (23, 704)
    # §A property address: (35, 633) — line after "at"
    # §A date: (90, 621) | §A year: (254, 621)
    # §B waiver days: (84, 554)
    # §C additional earnest: (315, 530)
    if has_sale and os.path.exists(SALE_PDF):
        sale_contingency_md, sale_contingency_yy = split_date(s.get("saleContingencyDate", ""))
        sale_pages = {
            0: [
                (23,  704, addr_full),
                (35,  633, s.get("salePropertyAddr", "")),
                (90,  621, sale_contingency_md),
                (254, 621, sale_contingency_yy),
                (84,  554, str(s.get("saleWaiverDays", "3"))),
                (315, 530, fmt_money(s.get("saleAdditionalEarnest", "")) if s.get("saleAdditionalEarnest") else ""),
            ],
        }
        sale_bytes = stamp_pdf(SALE_PDF, sale_pages)
        merger.append(PdfReader(BytesIO(sale_bytes)))

    # ── BACK-UP CONTRACT ADDENDUM ─────────────────────────────────────────────
    # Measured from flat template (952x1260px → 612x792):
    # addr_header p1: (23, 712)
    # §A(2) earnest blank: (215, 561) | option fee blank: (39, 549) | days blank: (152, 549)
    # §G date: (95, 426) | §G year: (208, 426)
    # §H date: (212, 396) | §H year: (315, 396)
    # addr_header p2: (118, 766)
    if has_bkup and os.path.exists(BACKUP_PDF):
        bkup_first_md, bkup_first_yy  = split_date(s.get("bkupFirstContractDate", ""))
        bkup_term_md,  bkup_term_yy   = split_date(s.get("bkupTerminateDate", ""))
        bkup_pages = {
            0: [
                (23,  712, addr_full),
                (215, 561, fmt_money(s.get("bkupAdditionalEarnest", "")) if s.get("bkupAdditionalEarnest") else ""),
                (39,  549, fmt_money(s.get("bkupAdditionalOption", ""))  if s.get("bkupAdditionalOption")  else ""),
                (152, 549, str(s.get("bkupAdditionalDays", "")) if s.get("bkupAdditionalDays") else ""),
                (95,  426, bkup_first_md),
                (208, 426, bkup_first_yy),
                (212, 396, bkup_term_md),
                (315, 396, bkup_term_yy),
            ],
            1: [
                (118, 766, addr_full),
            ],
        }
        bkup_bytes = stamp_pdf(BACKUP_PDF, bkup_pages)
        merger.append(PdfReader(BytesIO(bkup_bytes)))

    out = BytesIO()
    merger.write(out)
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

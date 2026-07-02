import json, os, base64, hashlib, hmac, httpx, re
from io import BytesIO
from http.server import BaseHTTPRequestHandler

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC   = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FROM_EMAIL     = "offers@homeofferflow.com"
SUPPORT_EMAIL  = "support@homeofferflow.com"
SHOWING_NOTIFY_EMAIL = os.environ.get("SHOWING_NOTIFY_EMAIL", "andrew@ondemandfw.com,support@homeofferflow.com")
ADMIN_ORDER_EMAIL = os.environ.get("ADMIN_ORDER_EMAIL") or SHOWING_NOTIFY_EMAIL
SIGNWELL_API_KEY = os.environ.get("SIGNWELL_API_KEY", "")
# Safe default: SignWell is OFF unless explicitly enabled in Vercel.
SIGNWELL_ENABLED = os.environ.get("SIGNWELL_ENABLED", "false").strip().lower() in ["1", "true", "yes", "on"]
# Safe default: test mode is ON while we build/signature-coordinate test.
SIGNWELL_TEST_MODE = os.environ.get("SIGNWELL_TEST_MODE", "true").strip().lower() not in ["0", "false", "no", "off"]

BASE_DIR      = "/var/task"
MAIN_PDF      = os.path.join(BASE_DIR, "20-19_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF       = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_PDF      = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF    = os.path.join(BASE_DIR, "backup_contract_addendum_11-9.pdf")
if not os.path.exists(BACKUP_PDF):
    BACKUP_PDF = os.path.join(BASE_DIR, "backup_contract_addendum_11-9")
if not os.path.exists(BACKUP_PDF):
    BACKUP_PDF = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")
APPRAISAL_PDF = os.path.join(BASE_DIR, "appraisal_addendum.pdf")
APPRAISAL_PDF_ALT = os.path.join(os.path.dirname(__file__), "appraisal_addendum.pdf")
NON_REALTY_PDF = os.path.join(BASE_DIR, "non_realty_items_addendum.pdf")
NON_REALTY_PDF_ALT = os.path.join(os.path.dirname(__file__), "non_realty_items_addendum.pdf")
LEAD_PDF = os.path.join(BASE_DIR, "lead_based_paint_56-0.pdf")
LEAD_PDF_ALT = os.path.join(os.path.dirname(__file__), "lead_based_paint_56-0.pdf")

FONT      = "Helvetica"
FONT_SIZE = 9
CHECK     = "X"

# Keep False for production/customer PDFs.
# Set True only temporarily if you want coordinate grid marks on every generated page.
DEBUG_GRID = False


def fmt_money(v):
    if v in [None, ""]:
        return ""
    try:
        return f"{int(float(str(v).replace(',', ''))):,}"
    except Exception:
        return str(v)


def has_positive_money(v):
    if v in [None, ""]:
        return False
    try:
        return float(str(v).replace(",", "").strip()) > 0
    except Exception:
        return bool(str(v).strip())


def split_date(v):
    if not v:
        return "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(str(v), "%Y-%m-%d")
        return d.strftime("%B %d").replace(" 0", " "), str(d.year)[-2:]
    except Exception:
        return str(v), ""


def parse_lot_block_from_text(v):
    lot = ""
    block = ""

    if not v:
        return lot, block

    text = str(v)

    m = re.search(r"lot\s*([A-Za-z0-9\-]+)", text, re.I)
    if m:
        lot = m.group(1)

    m = re.search(r"block\s*([A-Za-z0-9\-]+)", text, re.I)
    if m:
        block = m.group(1)

    return lot, block


def split_phone(phone):
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) == 10:
        return digits[:3], digits[3:]
    return "", digits


def ck(condition):
    return CHECK if condition else ""


def first_present(*vals):
    for v in vals:
        if v not in [None, ""]:
            return v
    return ""


def truthy(v):
    return str(v).strip().lower() in ["yes", "true", "1", "y", "on"]


def normalize_financing(v):
    raw = str(v or "").strip().lower().replace("_", "-")
    aliases = {
        "cash": "cash",
        "all cash": "cash",
        "no financing": "cash",
        "none": "cash",
        "thirdparty": "conventional",
        "third-party": "conventional",
        "third party": "conventional",
        "thirdpartyfinancing": "conventional",
        "third-party-financing": "conventional",
        "third party financing": "conventional",
        "thirdpartyaddendum": "conventional",
        "third-party addendum": "conventional",
        "conventional loan": "conventional",
        "conventional": "conventional",
        "conv": "conventional",
        "fha loan": "fha",
        "fha insured": "fha",
        "fha": "fha",
        "va loan": "va",
        "va guaranteed": "va",
        "veterans": "va",
        "va": "va",
        "usda loan": "usda",
        "usda guaranteed": "usda",
        "usda": "usda",
    }
    return aliases.get(raw, raw)


def normalize_appraisal(v):
    raw = str(v or "none").strip().lower().replace("_", "").replace("-", "").replace(" ", "")
    aliases = {
        "none": "none",
        "no": "none",
        "false": "none",
        "waiver": "waiver",
        "fullwaiver": "waiver",
        "partial": "partial",
        "partialwaiver": "partial",
        "partialappraisalwaiver": "partial",
        "additional": "additional",
        "additionalrighttoterminate": "additional",
        "terminate": "additional",
    }
    return aliases.get(raw, raw)


def get_non_realty_description(s):
    return first_present(
        s.get("nonRealtyDescription"),
        s.get("nonRealtyItemsDescription"),
        s.get("nonRealtyItemsText"),
        s.get("personalPropertyDescription")
    )


def wrapped_entries(x, y, text, max_chars=88, line_gap=11, fs=7, max_lines=10):
    """Return reportlab draw entries for simple wrapped form text."""
    raw = str(text or "").replace("\r", "\n")
    lines = []
    for para in raw.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    out = []
    for i, line in enumerate(lines[:max_lines]):
        out.append((x, y - (i * line_gap), line, fs))
    return out

def val_lower(v):
    return str(v or "").strip().lower()


def debug_grid_entries(step=25):
    entries = []

    # Page border/reference labels
    for x in range(0, 613, step):
        entries.append((x, 780, str(x), 5))
        entries.append((x, 20, str(x), 5))

    for y in range(0, 793, step):
        entries.append((5, y, str(y), 5))
        entries.append((570, y, str(y), 5))

    # Light full-page tick marks every 25 points
    for x in range(0, 613, step):
        for y in range(50, 775, step):
            entries.append((x, y, "|", 4))

    for y in range(0, 793, step):
        for x in range(50, 575, step):
            entries.append((x, y, "-", 4))

    # Denser 10-point labels in common form-fill zones
    for y in range(250, 725, 10):
        entries.append((35, y, str(y), 4))
        entries.append((555, y, str(y), 4))

    for x in range(40, 560, 10):
        entries.append((x, 745, str(x), 4))

    return entries


def add_debug_grid_to_pages(pages_dict):
    if not DEBUG_GRID:
        return pages_dict

    out = {}
    for page_num, entries in pages_dict.items():
        out[page_num] = debug_grid_entries() + entries
    return out


def make_overlay(page_entries, page_width=612, page_height=792):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    for entry in page_entries:
        x, y, text = entry[0], entry[1], entry[2]

        if text in [None, ""]:
            continue

        style = None
        fs = FONT_SIZE

        if len(entry) > 3:
            if isinstance(entry[3], str):
                style = entry[3]
            else:
                fs = entry[3]

        if len(entry) > 4:
            style = entry[4]

        if str(text) == CHECK:
            c.setFont("Helvetica-Bold", 9.5)

            if style == "check_small":
                c.drawString(x, y, str(text))
            else:
                c.drawString(x + 1, y + 1, str(text))
        else:
            c.setFont(FONT, fs)
            c.drawString(x, y, str(text))

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
                        obj[NameObject("/V")] = NameObject("/Off")
                        obj[NameObject("/AS")] = NameObject("/Off")
                        if NameObject("/AP") in obj:
                            del obj[NameObject("/AP")]

                    elif ft == "/Tx":
                        obj[NameObject("/V")] = TextStringObject("")
                        if NameObject("/AP") in obj:
                            del obj[NameObject("/AP")]

            except Exception:
                pass

        entries = pages_data.get(i, [])
        if not entries:
            continue

        overlay_bytes = make_overlay(entries, w, h)
        overlay_reader = PdfReader(BytesIO(overlay_bytes))

        if len(overlay_reader.pages) > 0:
            writer.pages[i].merge_page(overlay_reader.pages[0])

    final_out = BytesIO()

    try:
        from pypdf.generic import NameObject, BooleanObject
        root = writer._root_object
        if "/AcroForm" in root:
            af = root["/AcroForm"].get_object()
            af[NameObject("/NeedAppearances")] = BooleanObject(True)
    except Exception:
        pass

    writer.write(final_out)
    return final_out.getvalue()


def verify_stripe_signature(body, sig_header, secret):
    if not secret:
        return True

    try:
        parts = {}

        for item in sig_header.split(","):
            k, v = item.split("=", 1)
            parts.setdefault(k, []).append(v)

        timestamp = parts.get("t", [""])[0]
        signatures = parts.get("v1", [])

        expected = hmac.new(
            secret.encode(),
            timestamp.encode() + b"." + body,
            hashlib.sha256
        ).hexdigest()

        return any(hmac.compare_digest(expected, s) for s in signatures)

    except Exception:
        return False


def build_pages_data(
    s,
    addr_full,
    buyer,
    closing_md,
    closing_yy,
    phone_area,
    phone_num,
    has_loan,
    has_hoa,
    has_sale,
    has_bkup,
    has_appraisal,
    has_non_realty,
    price,
    loan,
    cash,
    title_payer,
    title_amend,
    survey,
    seller_disc,
    as_is,
    possession,
    lot,
    block
):
    """
    TREC 20-19 STAGING coordinate map.

    This is intentionally separate from the production 20-18 route. It updates the main
    contract mapping for the new 12-page 20-19 form. Coordinates still require visual QA
    against generated test packets before production switch.
    """
    pages = {}

    leases_raw = val_lower(s.get("leases"))
    lease_residential = truthy(s.get("leaseResidential")) or leases_raw in ["residential", "residentiallease", "residential lease"]
    lease_fixture = truthy(s.get("leaseFixture")) or truthy(s.get("fixtureLease")) or leases_raw in ["fixture", "fixturelease", "fixture lease"]
    lease_natural = truthy(s.get("leaseNaturalResource")) or truthy(s.get("naturalResourceLease")) or leases_raw in ["naturalresource", "natural resource", "natural_resource"]
    lease_nr_delivered = first_present(s.get("leaseNRDelivered"), s.get("naturalResourceLeaseDelivered"))
    lease_nr_days = first_present(s.get("naturalResourceLeaseDays"), s.get("leaseNRDays"), "3")
    lease_nr_term_days = first_present(s.get("naturalResourceTerminationDays"), s.get("leaseNRTerminationDays"), "")

    concession_amount = first_present(
        s.get("concessionAmount"),
        s.get("sellerConcessions"),
        s.get("sellerCredit"),
        s.get("buyerExpenseCredit")
    )

    has_buyer_agent = s.get("hasBuyerAgent") == "yes" or s.get("userType") in ["agent", "broker"]
    broker_fee_type = val_lower(s.get("brokerFeeType"))
    broker_fee_amount = first_present(s.get("brokerFeeAmount"), s.get("brokerCompAmount"), s.get("buyerBrokerFeeAmount"))
    broker_fee_percent = first_present(s.get("brokerFeePercent"), s.get("brokerCompPercent"), s.get("buyerBrokerFeePercent"))

    water_disc = val_lower(first_present(s.get("sellerWaterDisclosure"), s.get("waterDisclosure"), s.get("sellerWaterDisclosureStatus"), "notReceived"))
    water_days = first_present(s.get("waterDisclosureDays"), s.get("sellerWaterDisclosureDays"), "3")
    water_source = first_present(s.get("waterSourceProvider"), s.get("waterProvider"), s.get("waterDisclosureProvider"), "")
    lead_required_raw = val_lower(first_present(s.get("leadBuiltBefore1978"), s.get("leadBasedPaint"), s.get("leadRequired")))
    try:
        lead_year_built = int(str(first_present(s.get("yearBuilt"), s.get("propertyYearBuilt"), "0")).strip() or "0")
    except Exception:
        lead_year_built = 0
    lead_required = lead_required_raw in ["yes", "true", "1", "required"] or (lead_year_built and lead_year_built < 1978)

    pages[0] = [
        (280, 690, s.get("seller", "")),
        (124, 679, buyer),

        (127, 616, lot),
        (228, 616, block),
        (310, 616, s.get("subdivision", "")),
        (157, 606, s.get("city", "")),
        (387, 606, s.get("county", "")),
        (161, 595, addr_full),

        (457, 318, fmt_money(cash) if has_loan else fmt_money(price)),
        (457, 269, fmt_money(loan) if has_loan else ""),
        (457, 257, fmt_money(price)),

        (315, 284, ck(has_loan), "check_small"),
    ]

    escrow_agent = s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW")
    escrow_addr  = s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033")
    additional_earnest = first_present(s.get("additionalEarnest"), s.get("additionalEarnestMoney"))

    pages[1] = [
        (128, 751, addr_full),

        (153, 708, escrow_agent, 7),
        (75,  698, escrow_addr, 7),
        (293, 697, fmt_money(s.get("earnest", ""))),
        (488, 697, fmt_money(s.get("optionFee", ""))),

        (324, 660, fmt_money(additional_earnest) if has_positive_money(additional_earnest) else ""),
        # 5A(1) additional earnest days belongs in the right-side blank after "within", not under Paragraph 5A(2).
        (490, 660, str(first_present(s.get("additionalEarnestDays"), s.get("additionalEarnestDeadlineDays"))) if has_positive_money(additional_earnest) else ""),

        (86, 498, str(s.get("optionDays", "7"))),

        (314, 361, ck(title_payer == "seller"), "check_small"),
        (369, 347, ck(title_payer == "buyer"), "check_small"),
        (285, 336, s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC")),

        (78,  180, ck(title_amend == "i"), "check_small"),
        (75,  166, ck(title_amend in ["ii_buyer", "ii_seller"]), "check_small"),
        (435, 166, ck(title_amend == "ii_buyer"), "check_small"),
        (499, 166, ck(title_amend == "ii_seller"), "check_small"),
    ]

    survey_reject_payer = s.get("surveyIfRejectedPaidBy", "seller")

    pages[2] = [
        (130, 751, addr_full),

        (61,  707, ck(survey == "sellerExisting"), "check_small"),
        (129, 707, str(s.get("surveyDays", "7")) if survey == "sellerExisting" else ""),

        (142, 641, ck(survey == "sellerExisting" and survey_reject_payer == "seller"), "check_small"),
        (197, 638, ck(survey == "sellerExisting" and survey_reject_payer == "buyer"), "check_small"),

        (60,  634, ck(survey == "buyerNew"), "check_small"),
        (131, 631, str(s.get("surveyDays", "7")) if survey == "buyerNew" else ""),

        (60,  578, ck(survey == "sellerNew"), "check_small"),
        (125, 578, str(s.get("surveyDays", "7")) if survey == "sellerNew" else ""),

        (113, 527, s.get("intendedUse", ""), 7),
        (388, 512, str(first_present(s.get("objectionDays"), s.get("titleObjectionDays"))) if first_present(s.get("objectionDays"), s.get("titleObjectionDays")) else ""),

        (458, 317, ck(has_hoa), "check_small"),
        (479, 314, ck(not has_hoa), "check_small"),
    ]

    # 20-19 Page 4: seller disclosure moved higher than 20-18.
    pages[3] = [
        (128, 751, addr_full),

        (62,  218, ck(seller_disc == "received"), "check_small"),
        (62,  205, ck(seller_disc == "notReceived"), "check_small"),
        (62,   91, ck(seller_disc == "exempt"), "check_small"),
        (424, 203, str(s.get("disclosureDays", "3")) if seller_disc == "notReceived" else ""),
    ]

    # 20-19 Page 5: property condition plus new Seller's Water Disclosure 7I.
    pages[4] = [
        (128, 751, addr_full),

        (62,  720, ck(as_is == "yes"), "check_small"),
        (62,  715, ck(as_is == "repairs"), "check_small"),
        *wrapped_entries(89, 686, s.get("repairsText", "") if as_is == "repairs" else "", max_chars=88, line_gap=10, fs=7, max_lines=3),

        (420, 395, fmt_money(first_present(
            s.get("residentialServiceAmount"),
            s.get("residentialServiceContractAmount"),
            s.get("homeWarrantyAmount")
        )) if (
            has_positive_money(first_present(s.get("residentialServiceAmount"), s.get("residentialServiceContractAmount"), s.get("homeWarrantyAmount")))
            or str(first_present(s.get("residentialServiceContract"), s.get("requestResidentialServiceContract"), s.get("homeWarranty"))).strip().lower() in ["yes", "true", "1", "on"]
        ) else ""),

        (62, 292, ck(water_disc in ["received", "yes"]), "check_small"),
        (62, 275, ck(water_disc in ["notreceived", "not_received", "no", ""]), "check_small"),
        (438, 283, str(water_days) if water_disc in ["notreceived", "not_received", "no", ""] else ""),
        (62, 207, ck(water_disc in ["notrequired", "not_required", "exempt"]), "check_small"),
        (340, 104, water_source if water_disc in ["notrequired", "not_required", "exempt"] else "", 7),
    ]

    # 20-19 Page 6: broker disclosure, closing date, possession, and 12A buyer-expense contribution.
    pages[5] = [
        (129, 751, addr_full),

        *wrapped_entries(95, 704, s.get("brokerDisclosure", ""), max_chars=105, line_gap=10, fs=7, max_lines=3),

        (295, 669, closing_md),
        (448, 669, closing_yy),

        (356, 449, ck(possession == "funding"), "check_small"),
        (502, 449, ck(possession == "lease"), "check_small"),

        *wrapped_entries(45, 226, first_present(s.get("specialProvisions"), s.get("specialProvisionsText")), max_chars=115, line_gap=10, fs=7, max_lines=3),

        # 20-19 Paragraph 12A(1)(b): seller contribution to Buyer's Expenses, not brokerage compensation.
        (250, 143, fmt_money(concession_amount) if concession_amount else ""),
    ]

    # 20-19 Page 7: Paragraph 12B brokerage compensation contributions.
    pages[6] = [
        (129, 751, addr_full),

        # Existing frontend brokerFeeType means Seller contribution toward Buyer's broker compensation.
        (62, 646, ck(has_buyer_agent and broker_fee_type in ["amount", "percent"]), "check_small"),
        (286, 646, ck(has_buyer_agent and broker_fee_type == "amount"), "check_small"),
        (310, 644, fmt_money(broker_fee_amount) if has_buyer_agent and broker_fee_type == "amount" else "", 8),
        (390, 646, ck(has_buyer_agent and broker_fee_type == "percent"), "check_small"),
        (420, 644, str(broker_fee_percent) if has_buyer_agent and broker_fee_type == "percent" else "", 8),
    ]

    # 20-19 Page 8: expanded notices. Fill buyer/buyer's agent only.
    pages[7] = [
        (129, 751, addr_full),

        (105, 386, s.get("buyerMailAddr", ""), 7),
        (128, 312, f"({phone_area}) {phone_num}" if phone_area else phone_num, 7),
        (128, 242, s.get("buyerEmail", ""), 7),

        (142, 161, s.get("agentBrokerage", "") if has_buyer_agent else "", 7),
        (126, 91, s.get("agentPhone", "") if has_buyer_agent else "", 7),
        (126, 54, s.get("agentEmail", "") if has_buyer_agent else "", 7),
    ]

    # 20-19 Page 9: Paragraph 22 grouped addenda/notices.
    pages[8] = [
        (129, 751, addr_full),

        # Financial
        (68, 664, ck(has_loan), "check_small"),
        (68, 655, ck(has_sale), "check_small"),
        (68, 642, ck(has_appraisal), "check_small"),

        # Statutory disclosures and notices
        (68, 426, ck(lead_required), "check_small"),
        (68, 358, ck(bool(str(s.get("requiredNotices", "")).strip())), "check_small"),
        (338, 350, s.get("requiredNotices", ""), 7),

        # Other
        (68, 285, ck(has_hoa), "check_small"),
        (68, 276, ck(has_non_realty), "check_small"),
        (68, 267, ck(has_bkup), "check_small"),
    ]

    # 20-19 Page 10: execution/signature page. Buyer signatures are SignWell only.
    pages[9] = [
        (129, 751, addr_full),
    ]

    # 20-19 Page 11: Broker Contact Information, buyer broker side only.
    pages[10] = [
        (127, 751, addr_full),

        (50, 516, s.get("agentBrokerage", "") if has_buyer_agent else "", 7),
        (178, 485, s.get("agentBrokerLicense", "") if has_buyer_agent else "", 7),
        (150, 467, s.get("agentName", "") if has_buyer_agent else "", 7),
        (126, 449, s.get("teamName", "") if has_buyer_agent else "", 7),
        (150, 431, s.get("agentEmail", "") if has_buyer_agent else "", 7),
        (170, 414, s.get("agentPhone", "") if has_buyer_agent else "", 7),
        (420, 414, s.get("agentLicense", "") if has_buyer_agent else "", 7),
    ]

    # 20-19 Page 12: receipts, no buyer-generated fields.
    pages[11] = [
        (127, 751, addr_full),
    ]

    return pages

def fill_and_merge(offer):
    s = offer or {}

    lot = first_present(s.get("lotNumber"), s.get("lot"))
    block = first_present(s.get("blockNumber"), s.get("block"))

    if not lot or not block:
        parsed_lot, parsed_block = parse_lot_block_from_text(
            first_present(
                s.get("legalDescription"),
                s.get("lotBlock"),
                s.get("lot")
            )
        )
        lot = lot or parsed_lot
        block = block or parsed_block

    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")
    closing_md, closing_yy = split_date(s.get("closingDate"))
    phone_area, phone_num = split_phone(s.get("buyerPhone", ""))

    buyer = s.get("buyer1", "")
    if s.get("buyer2"):
        buyer += f" and {s['buyer2']}"

    try:
        price = float(s.get("price", 0) or 0)
        loan = float(s.get("loanAmount", 0) or 0)
        cash = price - loan if loan else price
    except Exception:
        price = loan = cash = 0

    normalized_financing_main = normalize_financing(s.get("financing", ""))
    s["financing"] = normalized_financing_main

    has_loan = normalized_financing_main in ["conventional", "fha", "va", "usda"]
    has_hoa  = s.get("hoa") in ["yes", "unknown"]
    has_sale = s.get("saleContingency") == "yes"
    has_bkup = s.get("backupOffer") == "yes"
    lead_required_raw = val_lower(first_present(s.get("leadBuiltBefore1978"), s.get("leadBasedPaint"), s.get("leadRequired")))
    try:
        lead_year_built = int(str(first_present(s.get("yearBuilt"), s.get("propertyYearBuilt"), "0")).strip() or "0")
    except Exception:
        lead_year_built = 0
    lead_required = lead_required_raw in ["yes", "true", "1", "required"] or (lead_year_built and lead_year_built < 1978)
    appraisal_choice_main = normalize_appraisal(s.get("appraisalAddendum"))
    has_appraisal = has_loan and normalized_financing_main not in ["fha", "va"] and appraisal_choice_main in ["waiver", "partial", "additional"]
    has_non_realty = str(s.get("nonRealtyItems") or "no").strip().lower() in ["yes", "true", "1", "on"] and bool(str(get_non_realty_description(s) or "").strip())

    title_payer = s.get("titlePayer", "seller")
    title_amend = s.get("titleAmendment", "i")
    survey      = s.get("survey", "sellerExisting")
    seller_disc = s.get("sellerDisclosure", "notReceived")
    as_is       = str(s.get("asIs", "yes")).strip().lower()
    if as_is in ["no", "repairs", "repair", "seller repairs", "sellerrepairs"] or str(s.get("repairsText") or "").strip():
        as_is = "repairs"
    else:
        as_is = "yes"
    possession  = s.get("possession", "funding")

    pages_data = build_pages_data(
        s,
        addr_full,
        buyer,
        closing_md,
        closing_yy,
        phone_area,
        phone_num,
        has_loan,
        has_hoa,
        has_sale,
        has_bkup,
        has_appraisal,
        has_non_realty,
        price,
        loan,
        cash,
        title_payer,
        title_amend,
        survey,
        seller_disc,
        as_is,
        possession,
        lot,
        block
    )

    pages_data = add_debug_grid_to_pages(pages_data)
    main_bytes = stamp_pdf(MAIN_PDF, pages_data)

    merger = PdfWriter()
    merger.append(PdfReader(BytesIO(main_bytes)))

    if has_loan and os.path.exists(FINANCING_PDF):
        financing = normalize_financing(s.get("financing", ""))

        loan_years = first_present(s.get("loanYears"), s.get("loanTermYears"), "30")
        interest_cap = first_present(s.get("interestRateCap"), s.get("loanInterestCap"), "7")
        interest_first_years = first_present(
            s.get("interestFirstYears"),
            s.get("loanYears"),
            s.get("loanTermYears"),
            "30"
        )
        origination_cap = first_present(s.get("originationCap"), s.get("loanOriginationCap"), "1")

        buyer_approval_days = first_present(
            s.get("buyerApprovalDays"),
            s.get("financingApprovalDays"),
            "21"
        )

        fha_va_value = fmt_money(first_present(s.get("appraisedValue"), s.get("price"))) if financing in ["fha", "va"] else ""

        fin_pages = {
            0: [
                (205, 642, addr_full, 8),

                # A. Conventional financing - confirmed good in tests.
                (58,  558, ck(financing == "conventional"), "check_small"),
                (87, 545, ck(financing == "conventional"), "check_small"),
                (377, 544, fmt_money(s.get("loanAmount", "")) if financing == "conventional" else ""),
                (305, 534, loan_years if financing == "conventional" else ""),
                (525, 531, interest_cap if financing == "conventional" else ""),
                (240, 522, interest_first_years if financing == "conventional" else ""),
                (384, 511, origination_cap if financing == "conventional" else ""),

                # C. FHA insured financing. Frozen after QA.
                (58,  414, ck(financing == "fha"), "check_small"),
                (282, 417, first_present(s.get("fhaSection"), s.get("fhaProgram"), "203(b)") if financing == "fha" else "", 8),
                (101, 407, fmt_money(s.get("loanAmount", "")) if financing == "fha" else ""),
                (142, 394, loan_years if financing == "fha" else ""),
                (356, 394, interest_cap if financing == "fha" else ""),
                (111, 381, interest_first_years if financing == "fha" else ""),
                (229, 371, origination_cap if financing == "fha" else ""),

                # D. VA guaranteed financing. Frozen after QA.
                (58,  358, ck(financing == "va"), "check_small"),
                (466, 363, fmt_money(s.get("loanAmount", "")) if financing == "va" else ""),
                (490, 346, loan_years if financing == "va" else ""),
                (240, 335, interest_cap if financing == "va" else ""),
                (410, 335, interest_first_years if financing == "va" else ""),
                (118, 315, origination_cap if financing == "va" else ""),

                # E. USDA guaranteed financing.
                (58,  307, ck(financing == "usda"), "check_small"),
                (482, 307, fmt_money(s.get("loanAmount", "")) if financing == "usda" else ""),
                (492, 294, loan_years if financing == "usda" else ""),
                (272, 282, interest_cap if financing == "usda" else ""),
                (428, 282, interest_first_years if financing == "usda" else ""),
                (139, 264, origination_cap if financing == "usda" else ""),
            ],
            1: [
                (205, 729, addr_full, 8),

                # Page 13 §2A checkbox.
                (83, 695, ck(s.get("buyerApproval", "yes") != "no"), "check_small"),

                (382, 684, buyer_approval_days if s.get("buyerApproval", "yes") != "no" else ""),

                (90, 584, ck(s.get("buyerApproval") == "no"), "check_small"),

                (125, 410, fha_va_value),
            ],
        }

        fin_pages = add_debug_grid_to_pages(fin_pages)
        merger.append(PdfReader(BytesIO(stamp_pdf(FINANCING_PDF, fin_pages))))

    appraisal_pdf_path = APPRAISAL_PDF if os.path.exists(APPRAISAL_PDF) else APPRAISAL_PDF_ALT
    if has_appraisal and os.path.exists(appraisal_pdf_path):
        appraisal_choice = normalize_appraisal(s.get("appraisalAddendum"))
        appraisal_pages = {
            0: [
                # TREC 49-1 appraisal addendum: tightened from live QA.
                # Keep text slightly above the printed underline and centered in the blanks.
                (238, 656, addr_full, 7),
                (50, 548, ck(appraisal_choice == "waiver"), "check_small"),
                (50, 468, ck(appraisal_choice == "partial"), "check_small"),
                (250, 405, fmt_money(first_present(s.get("appraisalPartialValue"), s.get("appraisalMinimum"), s.get("appraisalMinValue"), s.get("appraisalPartialMinimum"))) if appraisal_choice == "partial" else "", 8),
                (50, 346, ck(appraisal_choice == "additional"), "check_small"),
                (82, 323, str(first_present(s.get("appraisalTerminateDays"), "7")) if appraisal_choice == "additional" else "", 8),
                (151, 288, fmt_money(s.get("appraisalTerminateValue", "")) if appraisal_choice == "additional" else "", 8),
            ],
        }
        appraisal_pages = add_debug_grid_to_pages(appraisal_pages)
        merger.append(PdfReader(BytesIO(stamp_pdf(appraisal_pdf_path, appraisal_pages))))

    non_realty_pdf_path = NON_REALTY_PDF if os.path.exists(NON_REALTY_PDF) else NON_REALTY_PDF_ALT
    if has_non_realty and os.path.exists(non_realty_pdf_path):
        non_realty_description = get_non_realty_description(s)
        non_realty_pages = {
            0: [
                (230, 628, addr_full, 8),
                (164, 536, fmt_money(first_present(s.get("nonRealtyAmount"), s.get("nonRealtyItemsAmount"), s.get("nonRealtyAdditionalSum"))) if first_present(s.get("nonRealtyAmount"), s.get("nonRealtyItemsAmount"), s.get("nonRealtyAdditionalSum")) else "", 8),
                *wrapped_entries(62, 492, non_realty_description, max_chars=88, line_gap=11, fs=7, max_lines=12),
            ],
        }
        non_realty_pages = add_debug_grid_to_pages(non_realty_pages)
        merger.append(PdfReader(BytesIO(stamp_pdf(non_realty_pdf_path, non_realty_pages))))

    lead_pdf_path = LEAD_PDF if os.path.exists(LEAD_PDF) else LEAD_PDF_ALT
    if lead_required and os.path.exists(lead_pdf_path):
        # Attach the required lead-based paint addendum when the Paragraph 22 lead box is checked.
        # Seller disclosure choices are intentionally left blank for the seller/listing side unless supplied.
        lead_pages = {
            0: [
                (205, 679, addr_full, 8),
                (92, 527, ck(str(s.get("leadBuyerInspectionWaived") or "").strip().lower() in ["yes", "true", "1", "on"]), "check_small"),
                (92, 499, ck(str(s.get("leadBuyerInspectionDays") or "").strip() != ""), "check_small"),
                (70, 492, str(s.get("leadBuyerInspectionDays") or "") if str(s.get("leadBuyerInspectionDays") or "").strip() else "", 8),
                (92, 416, ck(str(s.get("leadReceivedInfo") or "yes").strip().lower() in ["yes", "true", "1", "on"]), "check_small"),
                (92, 398, ck(str(s.get("leadReceivedPamphlet") or "yes").strip().lower() in ["yes", "true", "1", "on"]), "check_small"),
            ]
        }
        lead_pages = add_debug_grid_to_pages(lead_pages)
        merger.append(PdfReader(BytesIO(stamp_pdf(lead_pdf_path, lead_pages))))

    if has_hoa and os.path.exists(HOA_PDF):
        hoa_info = s.get("hoaSubdivisionInfo") or "seller"
        hoa_title_cost = s.get("hoaTitleCost") or "seller"
        hoa_days = first_present(s.get("hoaDays"), "7")
        hoa_name = first_present(s.get("hoaName"), s.get("associationName"), s.get("poaName"))

        hoa_pages = {
            0: [
                (180, 662, addr_full, 8),
                (180, 632, hoa_name, 8),

                (47, 555, ck(hoa_info == "seller"), "check_small"),
                (110, 555, str(hoa_days) if hoa_info == "seller" else ""),

                (49, 499, ck(hoa_info == "buyer"), "check_small"),
                (110, 499, str(hoa_days) if hoa_info == "buyer" else ""),

                (49, 460, ck(hoa_info == "received"), "check_small"),
                (49, 424, ck(hoa_info == "notRequired"), "check_small"),

                (410, 310, fmt_money(first_present(s.get("hoaReserves"), "0"))),

                (238, 235, ck(hoa_title_cost == "buyer"), "check_small"),
                (275, 235, ck(hoa_title_cost == "seller"), "check_small"),
            ],
        }

        hoa_pages = add_debug_grid_to_pages(hoa_pages)
        merger.append(PdfReader(BytesIO(stamp_pdf(HOA_PDF, hoa_pages))))

    if has_sale and os.path.exists(SALE_PDF):
        sale_md, sale_yy = split_date(s.get("saleContingencyDate", ""))

        sale_pages = {
            0: [
                (245, 626, addr_full, 8),

                (83, 561, first_present(s.get("salePropertyAddr"), s.get("salePropertyAddress"), s.get("buyerSalePropertyAddress")), 8),

                (225, 550, sale_md),

                # Page 15 §A year: moved down and right.
                (400, 547, sale_yy),

                (204, 453, str(s.get("saleWaiverDays", "3"))),

                (535, 418, fmt_money(s.get("saleAdditionalEarnest", "")) if s.get("saleAdditionalEarnest") else ""),
            ],
        }

        sale_pages = add_debug_grid_to_pages(sale_pages)
        merger.append(PdfReader(BytesIO(stamp_pdf(SALE_PDF, sale_pages))))

    if has_bkup and os.path.exists(BACKUP_PDF):
        # Support both old bkup* keys and more readable backup* keys from frontend variants.
        bkup_first_date = first_present(
            s.get("bkupFirstContractDate"),
            s.get("backupFirstContractDate"),
            s.get("firstContractDate"),
            s.get("firstContractEffectiveDate"),
            ""
        )
        bkup_term_date = first_present(
            s.get("bkupTerminateDate"),
            s.get("backupTerminateDate"),
            s.get("backupTerminationDate"),
            s.get("backupContractTerminationDate"),
            ""
        )
        bkup_addl_earnest = first_present(s.get("bkupAdditionalEarnest"), s.get("backupAdditionalEarnest"), s.get("backupAddlEarnest"), "")
        bkup_addl_option = first_present(s.get("bkupAdditionalOption"), s.get("backupAdditionalOption"), s.get("backupAddlOption"), "")
        bkup_addl_days = first_present(s.get("bkupAdditionalDays"), s.get("backupAdditionalDays"), s.get("backupAddlDays"), "")

        bkup_first_md, bkup_first_yy = split_date(bkup_first_date)
        bkup_term_md,  bkup_term_yy  = split_date(bkup_term_date)

        bkup_pages = {
            0: [
                (245, 660, addr_full, 8),

                (345, 531, fmt_money(bkup_addl_earnest) if bkup_addl_earnest else ""),
                (101, 521, fmt_money(bkup_addl_option) if bkup_addl_option else ""),
                (298, 522, str(bkup_addl_days) if bkup_addl_days else ""),

                (215, 254, bkup_first_md),
                (345, 254, bkup_first_yy),

                (379, 216, bkup_term_md),
                (524, 216, bkup_term_yy),
            ],
            1: [
                (181, 745, addr_full, 8),
            ],
        }

        bkup_pages = add_debug_grid_to_pages(bkup_pages)
        merger.append(PdfReader(BytesIO(stamp_pdf(BACKUP_PDF, bkup_pages))))

    out = BytesIO()
    merger.write(out)
    return out.getvalue()



def build_signwell_fields(offer, pdf_bytes):
    """
    Buyer-only SignWell field map.

    Scope:
    - Buyer 1 + optional Buyer 2 only.
    - No seller signature or seller initials fields.
    - No effective-date field.
    - No generic SignWell signature page.
    - Main contract initials on pages 1-8 only. Buyer 2 main initials shifted right; Buyer 2 signature/addenda coordinates adjusted from two-buyer QA. Buyer 1 addenda micro-nudges applied from v14 baseline.
    - Main contract signature/date on page 10 for TREC 20-19 staging.
    - Add buyer-side fields for included addenda.
    """
    try:
        page_count = len(PdfReader(BytesIO(pdf_bytes)).pages)
    except Exception:
        page_count = 10

    has_buyer2 = bool(first_present(offer.get("buyer2Email"), ""))
    financing = normalize_financing(offer.get("financing"))
    has_financing_addendum = financing in {"conventional", "fha", "va", "usda"}
    has_hoa = str(offer.get("hoa") or "").strip().lower() in {"yes", "unknown"}
    has_sale = str(offer.get("saleContingency") or "").strip().lower() == "yes"
    has_backup = str(offer.get("backupOffer") or "").strip().lower() == "yes"
    has_appraisal = has_financing_addendum and financing not in {"fha", "va"} and normalize_appraisal(offer.get("appraisalAddendum")) in {"waiver", "partial", "additional"}
    has_non_realty = str(offer.get("nonRealtyItems") or "no").strip().lower() in {"yes", "true", "1", "on"} and bool(str(get_non_realty_description(offer) or "").strip())
    lead_required = val_lower(first_present(offer.get("leadBuiltBefore1978"), offer.get("leadBasedPaint"), offer.get("leadRequired"))) in {"yes", "true", "1", "required"}

    main_contract_pages = list(range(1, min(page_count, 9) + 1))
    main_signature_page = 10 if page_count >= 10 else max(page_count, 1)

    # Track appended addendum page numbers in the same order fill_and_merge appends them.
    next_page = 13
    financing_page_1 = financing_signature_page = None
    appraisal_page = None
    non_realty_page = None
    lead_page = None
    hoa_page = None
    sale_page = None
    backup_page_1 = backup_signature_page = None

    if has_financing_addendum:
        financing_page_1 = next_page
        financing_signature_page = next_page + 1
        next_page += 2
    if has_appraisal:
        appraisal_page = next_page
        next_page += 1
    if has_non_realty:
        non_realty_page = next_page
        next_page += 1
    if lead_required:
        lead_page = next_page
        next_page += 1
    if has_hoa:
        hoa_page = next_page
        next_page += 1
    if has_sale:
        sale_page = next_page
        next_page += 1
    if has_backup:
        backup_page_1 = next_page
        backup_signature_page = next_page + 1
        next_page += 2

    fields_for_file = []

    def add_field(api_id, field_type, page, x, y, recipient_id="1", width=80, height=22, required=True, **extra):
        if not page or page < 1 or page > page_count:
            return
        field = {
            "api_id": api_id,
            "type": field_type,
            "page": page,
            "x": x,
            "y": y,
            "recipient_id": str(recipient_id),
            "required": required,
            "width": width,
            "height": height,
        }
        field.update(extra)
        fields_for_file.append(field)

    def add_sig_date_pair(prefix, page, sig_x, sig_y, date_x, date_y, recipient_id="1"):
        add_field(
            f"{prefix}_signature",
            "signature",
            page,
            sig_x,
            sig_y,
            recipient_id=recipient_id,
            width=145,
            height=20,
        )
        add_field(
            f"{prefix}_date",
            "date",
            page,
            date_x,
            date_y,
            recipient_id=recipient_id,
            width=66,
            height=16,
            date_format="MM/DD/YYYY",
            lock_sign_date=True,
        )

    # Main contract page 10 - TREC 20-19 execution page. Coordinates are carried over from the visually similar 20-18 execution page and must be QA-tested.
    add_sig_date_pair("buyer1_main_contract", main_signature_page, 115, 436, 286, 436, "1")
    if has_buyer2:
        add_sig_date_pair("buyer2_main_contract", main_signature_page, 115, 672, 286, 672, "2")

    # Main contract initials: pages 1-9 for 20-19 staging. No signature page, broker-contact page, or receipts page initials.
    for page in main_contract_pages:
        add_field(f"buyer1_initials_main_p{page}", "initials", page, 286, 1018, recipient_id="1", width=24, height=10)
        if has_buyer2:
            add_field(f"buyer2_initials_main_p{page}", "initials", page, 352, 1018, recipient_id="2", width=24, height=10)

    # Third Party Financing Addendum.
    if financing_page_1 and financing_signature_page:
        add_field("buyer1_initials_financing_p1", "initials", financing_page_1, 280, 1004, recipient_id="1", width=24, height=10)
        if has_buyer2:
            add_field("buyer2_initials_financing_p1", "initials", financing_page_1, 314, 1014, recipient_id="2", width=24, height=10)
        # User requested financing fields left/up vs prior bundle.
        add_sig_date_pair("buyer1_financing_addendum", financing_signature_page, 112, 808, 266, 808, "1")
        if has_buyer2:
            add_sig_date_pair("buyer2_financing_addendum", financing_signature_page, 112, 884, 266, 884, "2")

    # Appraisal Addendum - buyer signatures only. No seller fields.
    # Live QA: signature blocks needed to sit higher on the buyer lines and include buyer dates.
    if appraisal_page:
        add_sig_date_pair("buyer1_appraisal_addendum", appraisal_page, 85, 780, 260, 780, "1")
        if has_buyer2:
            add_sig_date_pair("buyer2_appraisal_addendum", appraisal_page, 85, 868, 260, 868, "2")

    # Non-Realty Items Addendum - buyer signatures only. No seller fields.
    if non_realty_page:
        add_sig_date_pair("buyer1_non_realty_items_addendum", non_realty_page, 76, 833, 246, 833, "1")
        if has_buyer2:
            add_sig_date_pair("buyer2_non_realty_items_addendum", non_realty_page, 76, 915, 246, 915, "2")

    # Lead-Based Paint Addendum - buyer signatures only. No seller fields.
    if lead_page:
        add_sig_date_pair("buyer1_lead_based_paint_addendum", lead_page, 76, 762, 246, 762, "1")
        if has_buyer2:
            add_sig_date_pair("buyer2_lead_based_paint_addendum", lead_page, 76, 842, 246, 842, "2")

    # HOA/POA Addendum - buyer signatures only. No seller fields.
    if hoa_page:
        add_sig_date_pair("buyer1_hoa_addendum", hoa_page, 112, 827, 266, 827, "1")
        if has_buyer2:
            add_sig_date_pair("buyer2_hoa_addendum", hoa_page, 112, 914, 266, 914, "2")

    # Sale of Other Property Addendum - buyer signatures only. No seller fields.
    if sale_page:
        add_sig_date_pair("buyer1_sale_other_property_addendum", sale_page, 112, 682, 266, 682, "1")
        if has_buyer2:
            add_sig_date_pair("buyer2_sale_other_property_addendum", sale_page, 112, 780, 266, 780, "2")

    # Backup Contract Addendum - page 1 initial line, page 2 buyer signatures only.
    if backup_page_1:
        add_field("buyer1_initials_backup_p1", "initials", backup_page_1, 280, 1004, recipient_id="1", width=24, height=10)
        if has_buyer2:
            add_field("buyer2_initials_backup_p1", "initials", backup_page_1, 314, 1004, recipient_id="2", width=24, height=10)
    if backup_signature_page:
        # Backup signature lines sit higher than the other addenda. First pass based on screenshot.
        add_sig_date_pair("buyer1_backup_addendum", backup_signature_page, 112, 330, 266, 330, "1")
        if has_buyer2:
            add_sig_date_pair("buyer2_backup_addendum", backup_signature_page, 112, 420, 266, 420, "2")

    fields = [fields_for_file]

    print("SIGNWELL DEBUG field payload:", json.dumps({
        "page_count": page_count,
        "main_signature_page": main_signature_page,
        "has_buyer2": has_buyer2,
        "has_financing_addendum": has_financing_addendum,
        "has_hoa": has_hoa,
        "has_appraisal": has_appraisal,
        "has_non_realty": has_non_realty,
        "lead_required": lead_required,
        "has_sale": has_sale,
        "has_backup": has_backup,
        "pages": {
            "financing_page_1": financing_page_1,
            "financing_signature_page": financing_signature_page,
            "appraisal_page": appraisal_page,
            "non_realty_page": non_realty_page,
            "lead_page": lead_page,
            "hoa_page": hoa_page,
            "sale_page": sale_page,
            "backup_page_1": backup_page_1,
            "backup_signature_page": backup_signature_page,
        },
        "field_count": len(fields_for_file),
        "fields": fields
    })[:5000])

    return fields

def post_signwell_document(payload):
    print("SIGNWELL DEBUG request summary:", json.dumps({
        "test_mode": payload.get("test_mode"),
        "draft": payload.get("draft"),
        "with_signature_page": payload.get("with_signature_page"),
        "recipient_count": len(payload.get("recipients", [])),
        "recipient_emails": [r.get("email") for r in payload.get("recipients", [])],
        "file_count": len(payload.get("files", [])),
        "field_outer_count": len(payload.get("fields", [])) if payload.get("fields") else 0,
        "field_count_file_1": len(payload.get("fields", [[]])[0]) if payload.get("fields") else 0,
    })[:3000])

    r = httpx.post(
        "https://www.signwell.com/api/v1/documents",
        headers={"X-Api-Key": SIGNWELL_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=45
    )

    # Always log the SignWell response while we are stabilizing the integration.
    print("SIGNWELL RESPONSE STATUS:", r.status_code)
    print("SIGNWELL RESPONSE BODY:", r.text[:3000])

    if r.status_code not in [200, 201, 202]:
        return False, {"status_code": r.status_code, "error": r.text[:3000]}

    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text[:3000]}

    return True, data


def create_signwell_signature_request(offer, pdf_bytes):
    """
    SignWell request for HomeOfferFlow.

    Debug/stabilization behavior:
    - OFF unless SIGNWELL_ENABLED=true.
    - Test mode defaults ON unless SIGNWELL_TEST_MODE=false.
    - No generic SignWell signature page.
    - Minimal Buyer 1 signature field only until SignWell accepts the payload.
    - Logs SignWell request summary and full response body to Vercel logs.
    """
    print("SIGNWELL DEBUG env:", json.dumps({
        "enabled": SIGNWELL_ENABLED,
        "test_mode": SIGNWELL_TEST_MODE,
        "api_key_present": bool(SIGNWELL_API_KEY)
    }))

    if not SIGNWELL_ENABLED:
        return {"enabled": False, "skipped": "SIGNWELL_ENABLED is false"}

    if not SIGNWELL_API_KEY:
        return {"enabled": True, "ok": False, "error": "Missing SIGNWELL_API_KEY"}

    buyer_email = first_present(offer.get("buyerEmail"), offer.get("email"), "")
    buyer_name = first_present(offer.get("buyer1"), offer.get("buyerName"), "Buyer")
    addr = first_present(offer.get("address"), "HomeOfferFlow Offer")

    if not buyer_email:
        return {"enabled": True, "ok": False, "error": "Missing buyer email for SignWell"}

    recipients = [{"id": "1", "name": buyer_name, "email": buyer_email}]

    buyer2_email = first_present(offer.get("buyer2Email"), "")
    buyer2_name = first_present(offer.get("buyer2"), "Buyer 2")
    if buyer2_email:
        recipients.append({"id": "2", "name": buyer2_name, "email": buyer2_email})

    filename_safe_addr = re.sub(r"[^A-Za-z0-9_\-]+", "_", str(addr)).strip("_") or "Offer"
    filename = f"HomeOfferFlow_Offer_{filename_safe_addr}.pdf"
    file_payload = [{"name": filename, "file_base64": base64.b64encode(pdf_bytes).decode()}]

    fields = build_signwell_fields(offer, pdf_bytes)

    # SignWell recipient-facing branding:
    # - Keep the signing request branded as HomeOfferFlow.
    # - Make it clear which agent prepared/sent the packet and how the buyer can contact them.
    #
    # Note: SignWell may still append "via SignWell" depending on the plan/account branding.
    # The custom requester name prevents the request from appearing as the individual API account
    # user where SignWell supports this field.
    agent_name = first_present(
        offer.get("agentName"),
        offer.get("agent_name"),
        offer.get("preparedByName"),
        "Your agent"
    )
    agent_email = first_present(
        offer.get("agentEmail"),
        offer.get("agent_email"),
        offer.get("preparedByEmail"),
        ""
    )
    agent_phone = first_present(
        offer.get("agentPhone"),
        offer.get("agent_phone"),
        offer.get("preparedByPhone"),
        ""
    )

    agent_contact_parts = []
    if agent_email:
        agent_contact_parts.append(str(agent_email))
    if agent_phone:
        agent_contact_parts.append(str(agent_phone))

    if agent_contact_parts:
        contact_sentence = f"Questions? Contact {agent_name} at " + " or ".join(agent_contact_parts) + "."
    else:
        contact_sentence = f"Questions? Contact {agent_name}."

    signwell_message = (
        f"{agent_name} prepared this Texas offer packet using HomeOfferFlow.\n\n"
        "Please review and sign your buyer-side offer packet. "
        "Seller-side signatures and seller initials are handled separately by the seller or listing side.\n\n"
        f"{contact_sentence}\n\n"
        "HomeOfferFlow is a form-completion software tool. It is not a law firm, "
        "does not provide legal advice, and does not represent you as your real estate agent."
    )

    payload = {
        "test_mode": SIGNWELL_TEST_MODE,
        "draft": False,
        "reminders": True,
        "apply_signing_order": False,
        "embedded_signing": False,
        "with_signature_page": False,
        "custom_requester_name": "HomeOfferFlow",
        "name": f"HomeOfferFlow Offer — {addr}",
        "subject": f"HomeOfferFlow Offer — {addr}",
        "message": signwell_message,
        "recipients": recipients,
        "files": file_payload,
        "fields": fields,
        "metadata": {
            "source": "HomeOfferFlow",
            "prepared_by_agent_name": str(agent_name)[:250],
            "prepared_by_agent_email": str(agent_email)[:250],
            "prepared_by_agent_phone": str(agent_phone)[:80],
            "property_address": str(addr)[:450],
            "buyer_count": str(len(recipients)),
            "test_mode": str(SIGNWELL_TEST_MODE).lower(),
            "debug_payload": "staging_20_19_buyer_only_all_addenda"
        }
    }

    try:
        ok, data = post_signwell_document(payload)
        if ok:
            return {
                "enabled": True,
                "ok": True,
                "mode": "staging_20_19_buyer_only_all_addenda",
                "test_mode": SIGNWELL_TEST_MODE,
                "field_count": len(fields[0]) if fields else 0,
                "document_id": data.get("id") or data.get("document_id"),
                "response": data
            }

        return {
            "enabled": True,
            "ok": False,
            "mode": "staging_20_19_buyer_only_all_addenda_failed",
            "test_mode": SIGNWELL_TEST_MODE,
            "field_count": len(fields[0]) if fields else 0,
            "signwell_error": data
        }

    except Exception as e:
        print("SIGNWELL EXCEPTION:", str(e))
        return {"enabled": True, "ok": False, "mode": "exception", "error": str(e)}

def send_email(to_email, buyer_name, addr, pdf_bytes, signwell_info=None):
    filename = f"HomeOfferFlow_Offer_{addr.replace(' ','_').replace(',','')}.pdf"

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "bcc": [SUPPORT_EMAIL],
        "subject": f"Your HomeOfferFlow Offer — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2 style="color:#1a2f4a;">Your Offer is Ready, {buyer_name}!</h2>
          <p>Your filled TREC offer for <strong>{addr}</strong> is attached.</p>
          {"<p><strong>Signature request:</strong> A SignWell signature request has also been sent to your email.</p>" if signwell_info and signwell_info.get("ok") else ""}
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
        </div>
        """,
        "attachments": [{
            "filename": filename,
            "content": base64.b64encode(pdf_bytes).decode(),
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

def send_basic_email(to_email, subject, html_body):
    if not to_email:
        raise Exception("Missing recipient email")

    if isinstance(to_email, str):
        recipients = [e.strip() for e in to_email.split(",") if e.strip()]
    else:
        recipients = list(to_email)

    if not recipients:
        raise Exception("Missing recipient email")

    payload = {
        "from": FROM_EMAIL,
        "to": recipients,
        "subject": subject,
        "html": html_body
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


def send_showing_request_emails(showing, customer_email):
    buyer_email = showing.get("buyerEmail") or customer_email
    buyer_name = first_present(
        showing.get("buyerName"),
        showing.get("buyer1"),
        showing.get("name"),
        "Showing Buyer"
    )
    addr = showing.get("showingAddress", "Property address not provided")
    date = showing.get("showingDate", "Date not provided")
    time = showing.get("showingTime", "Time not provided")
    phone = showing.get("showingPhone", "Phone not provided")

    # Optional fields if we add them later to the showing form.
    buyer_note = showing.get("showingNotes", "")
    buyer_status = showing.get("buyerStatus", "Unrepresented buyer / neutral showing request")

    fb_post = f"""🚨 Showing Request — OnDemand Realty Agents

A HomeOfferFlow buyer paid for a neutral showing request.

🏡 Property:
{addr}

📅 Preferred showing time:
{date} at {time}

👤 Buyer:
{buyer_name}
📧 {buyer_email}
📱 {phone}

Notes:
{buyer_note or "No notes provided."}

Important:
This is a neutral showing request. Buyer remains unrepresented unless a separate buyer representation agreement is signed.

Please comment or message me if you are available to help coordinate/show this property."""

    fb_post_html = fb_post.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    admin_html = f"""
      <div style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;">
        <h2 style="color:#1a2f4a;">New $50 Showing Request</h2>
        <p>A showing booking payment was completed through HomeOfferFlow.</p>

        <h3>Buyer Info</h3>
        <table style="border-collapse:collapse;width:100%;margin-top:0.5rem;">
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Name</strong></td><td style="padding:8px;border:1px solid #ddd;">{buyer_name}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Email</strong></td><td style="padding:8px;border:1px solid #ddd;">{buyer_email}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Phone</strong></td><td style="padding:8px;border:1px solid #ddd;">{phone}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Status</strong></td><td style="padding:8px;border:1px solid #ddd;">{buyer_status}</td></tr>
        </table>

        <h3>Property / Showing Info</h3>
        <table style="border-collapse:collapse;width:100%;margin-top:0.5rem;">
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Property</strong></td><td style="padding:8px;border:1px solid #ddd;">{addr}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Preferred Date</strong></td><td style="padding:8px;border:1px solid #ddd;">{date}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Preferred Time</strong></td><td style="padding:8px;border:1px solid #ddd;">{time}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Buyer Notes</strong></td><td style="padding:8px;border:1px solid #ddd;">{buyer_note or "No notes provided."}</td></tr>
        </table>

        <h3>Copy/Paste Facebook Group Post</h3>
        <div style="background:#f6f8fa;border:1px solid #d0d7de;border-radius:8px;padding:1rem;line-height:1.5;font-size:14px;">
          {fb_post_html}
        </div>

        <p style="margin-top:1rem;"><strong>Next step:</strong> post the Facebook copy into the OnDemand Realty agent group or contact an available agent directly.</p>
      </div>
    """

    customer_html = f"""
      <div style="font-family:Arial,sans-serif;max-width:650px;margin:0 auto;">
        <h2 style="color:#1a2f4a;">Showing Request Received</h2>
        <p>Thanks — your $50 showing request has been received.</p>
        <p><strong>Property:</strong> {addr}<br>
        <strong>Preferred Date:</strong> {date}<br>
        <strong>Preferred Time:</strong> {time}<br>
        <strong>Phone:</strong> {phone}</p>
        <p>An OnDemand Realty agent will follow up to coordinate the showing.</p>
        <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.85rem;">
          You remain unrepresented unless you separately sign a representation agreement.
        </p>
      </div>
    """

    send_basic_email(SHOWING_NOTIFY_EMAIL, f"New Showing Request — {addr}", admin_html)

    if buyer_email:
        send_basic_email(buyer_email, "HomeOfferFlow Showing Request Received", customer_html)


def handle_checkout(event):
    session = event.get("data", {}).get("object", {})

    customer_email = (
        session.get("customer_email")
        or session.get("customer_details", {}).get("email", "")
    )

    metadata = session.get("metadata", {}) or {}
    plan = metadata.get("plan", "")

    if "offer_data" in metadata:
        offer = json.loads(metadata["offer_data"])
    else:
        parts = int(metadata.get("offer_parts", 0) or 0)
        combined = "".join(metadata.get(f"offer_{i}", "") for i in range(parts))

        if not combined:
            raise Exception(f"No offer data found. Metadata keys: {list(metadata.keys())}")

        offer = json.loads(combined)

    # Showing booking checkout: send notifications only, do not generate a TREC PDF.
    if plan == "showing-booking" or offer.get("type") == "showing_booking":
        if not offer.get("buyerEmail") and customer_email:
            offer["buyerEmail"] = customer_email

        send_showing_request_emails(offer, customer_email)

        return {
            "status": "ok",
            "message": "Showing request emailed"
        }

    if not offer.get("buyerEmail") and customer_email:
        offer["buyerEmail"] = customer_email

    pdf_bytes = fill_and_merge(offer)

    signwell_info = create_signwell_signature_request(offer, pdf_bytes)

    send_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property"),
        pdf_bytes,
        signwell_info if signwell_info.get("enabled") else None
    )

    return {
        "status": "ok",
        "message": "PDF created and emailed",
        "signwell": signwell_info
    }


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            contents = os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else []
        except Exception as e:
            contents = str(e)

        self._json(200, {
            "status": "ok",
            "debug_grid": DEBUG_GRID,
            "trec_main_form": "20-19 staging",
            "base_dir": BASE_DIR,
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "financing_pdf_exists": os.path.exists(FINANCING_PDF),
            "hoa_pdf_exists": os.path.exists(HOA_PDF),
            "sale_pdf_exists": os.path.exists(SALE_PDF),
            "backup_pdf_exists": os.path.exists(BACKUP_PDF),
            "appraisal_pdf_exists": os.path.exists(APPRAISAL_PDF),
            "non_realty_pdf_exists": os.path.exists(NON_REALTY_PDF),
            "signwell_enabled": SIGNWELL_ENABLED,
            "signwell_test_mode": SIGNWELL_TEST_MODE,
            "signwell_api_key_present": bool(SIGNWELL_API_KEY),
            "cwd": os.getcwd(),
            "dir_contents": contents
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            sig = self.headers.get("stripe-signature", "")

            if sig and not verify_stripe_signature(body, sig, STRIPE_WHSEC):
                self._json(401, {"error": "Invalid Stripe signature"})
                return

            payload = json.loads(body.decode("utf-8") or "{}")

            # Stripe webhook path: paid checkout sends a checkout.session.completed event.
            if isinstance(payload, dict) and payload.get("type") == "checkout.session.completed":
                result = handle_checkout(payload)
                self._json(200, result)
                return

            # Direct PDF test/generation path:
            # Accept either raw offer JSON or {"offerData": {...}} so curl testing works.
            offer = None
            if isinstance(payload, dict) and isinstance(payload.get("offerData"), dict):
                offer = payload.get("offerData")
            elif isinstance(payload, dict):
                offer = payload

            if offer:
                pdf_bytes = fill_and_merge(offer)
                filename_addr = re.sub(r"[^A-Za-z0-9]+", "_", str(offer.get("address", "offer")).strip()).strip("_") or "offer"
                filename = f"HomeOfferFlow_Offer_{filename_addr}.pdf"

                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(pdf_bytes)))
                self.end_headers()
                self.wfile.write(pdf_bytes)
                return

            self._json(400, {"error": "No offer data provided"})

        except Exception as e:
            print("ERROR:", str(e))
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

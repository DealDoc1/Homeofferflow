import json, os, base64, hashlib, hmac, httpx, re
from io import BytesIO
from http.server import BaseHTTPRequestHandler

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC   = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FROM_EMAIL     = "HomeOfferFlow <noreply@homeofferflow.com>"
SUPPORT_EMAIL  = "support@homeofferflow.com"
SHOWING_NOTIFY_EMAIL = os.environ.get("SHOWING_NOTIFY_EMAIL", "andrew@ondemandfw.com,support@homeofferflow.com")
ADMIN_ORDER_EMAIL = os.environ.get("ADMIN_ORDER_EMAIL") or os.environ.get("SHOWING_NOTIFY_EMAIL", "andrew@ondemandfw.com,support@homeofferflow.com")

BASE_DIR      = "/var/task"
MAIN_PDF      = os.path.join(BASE_DIR, "20-18_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF       = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_PDF      = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF    = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")

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
    pages = {}

    # Normalize incoming frontend/test payload variants so max-fill curls and UI values map to the form.
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

    has_buyer_agent = s.get("hasBuyerAgent") == "yes" or s.get("userType") == "agent"
    broker_fee_type = val_lower(s.get("brokerFeeType"))
    broker_fee_amount = first_present(s.get("brokerFeeAmount"), s.get("brokerCompAmount"), s.get("buyerBrokerFeeAmount"))
    broker_fee_percent = first_present(s.get("brokerFeePercent"), s.get("brokerCompPercent"), s.get("buyerBrokerFeePercent"))

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

        # Lease addenda are not currently generated/attached by HomeOfferFlow.
        # Do not check Section 4 lease boxes unless the matching addendum PDFs are included in the final packet.
        #(50, 196, ck(lease_residential), "check_small"),
        #(50, 171, ck(lease_fixture), "check_small"),
        #(50, 135, ck(lease_natural), "check_small"),
        #(63,  99, ck(lease_natural and val_lower(lease_nr_delivered) == "yes"), "check_small"),
        #(63,  85, ck(lease_natural and val_lower(lease_nr_delivered) == "no"), "check_small"),
        #(466, 70, str(lease_nr_days) if lease_natural and val_lower(lease_nr_delivered) == "no" else ""),
        #(350, 45, str(lease_nr_term_days) if lease_natural and val_lower(lease_nr_delivered) == "no" else ""),
    ]

    escrow_agent = s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW")
    escrow_addr  = s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033")
    additional_earnest = first_present(s.get("additionalEarnest"), s.get("additionalEarnestMoney"))

    pages[1] = [
        (128, 751, addr_full),

        (153, 702, escrow_agent, 7),
        (75,  692, escrow_addr, 7),
        (293, 691, fmt_money(s.get("earnest", ""))),
        (488, 691, fmt_money(s.get("optionFee", ""))),

        # Only fill additional earnest money fields if additional earnest is greater than zero.
        (324, 655, fmt_money(additional_earnest) if has_positive_money(additional_earnest) else ""),
        (152, 641, str(first_present(s.get("additionalEarnestDays"), s.get("additionalEarnestDeadlineDays"))) if has_positive_money(additional_earnest) else ""),

        (103, 503, str(s.get("optionDays", "7"))),

        (314, 353, ck(title_payer == "seller"), "check_small"),
        (369, 351, ck(title_payer == "buyer"), "check_small"),
        (285, 342, s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC")),

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

        (60,  628, ck(survey == "buyerNew"), "check_small"),
        (125, 629, str(s.get("surveyDays", "7")) if survey == "buyerNew" else ""),

        (60,  578, ck(survey == "sellerNew"), "check_small"),
        (125, 578, str(s.get("surveyDays", "7")) if survey == "sellerNew" else ""),

        (113, 527, s.get("intendedUse", ""), 7),
        (388, 512, str(first_present(s.get("objectionDays"), s.get("titleObjectionDays"))) if first_present(s.get("objectionDays"), s.get("titleObjectionDays")) else ""),

        (458, 317, ck(has_hoa), "check_small"),
        (479, 314, ck(not has_hoa), "check_small"),
    ]

    pages[3] = [
        (128, 751, addr_full),

        (71, 282, s.get("requiredNotices", ""), 7),

        (62,  148, ck(seller_disc == "received"), "check_small"),
        (65,  141, ck(seller_disc == "notReceived"), "check_small"),
        (62,   78, ck(seller_disc == "exempt"), "check_small"),
        (324, 139, str(s.get("disclosureDays", "3")) if seller_disc == "notReceived" else ""),
    ]

    pages[4] = [
        (128, 751, addr_full),

        (62,  682, ck(as_is == "yes"), "check_small"),
        (59,  668, ck(as_is == "repairs"), "check_small"),
        (89,  654, s.get("repairsText", "") if as_is == "repairs" else "", 8),

        # §7H Residential Service Contract / Home Warranty reimbursement amount.
        (420, 358, fmt_money(first_present(
            s.get("residentialServiceAmount"),
            s.get("residentialServiceContractAmount"),
            s.get("homeWarrantyAmount")
        )) if first_present(
            s.get("residentialServiceContract"),
            s.get("requestResidentialServiceContract"),
            s.get("homeWarranty")
        ) in ["yes", "true", True, "1"] else ""),

        (73,  241, s.get("brokerDisclosure", "")),

        (291, 197, closing_md),
        (442, 197, closing_yy),
    ]

    pages[5] = [
        (129, 751, addr_full),

        (356, 660, ck(possession == "funding"), "check_small"),
        (501, 657, ck(possession == "lease"), "check_small"),

        (253, 295, fmt_money(concession_amount) if concession_amount else ""),
    ]

    pages[6] = [
        (129, 751, addr_full),
    ]

    pages[7] = [
        (129, 751, addr_full),

        (133, 699, s.get("buyerMailAddr", "")),
        (139, 650, phone_area),
        (166, 650, phone_num),
        (135, 624, s.get("buyerEmail", "")),

        (68,  519, ck(has_loan), "check_small"),
        (68,  489, ck(has_hoa), "check_small"),
        (68,  426, ck(has_sale), "check_small"),
        (68,  378, ck(has_bkup), "check_small"),

        # Do not check lease addenda on Section 22 unless those exact addendum PDFs are generated and attached.
        #(319, 352, ck(lease_residential), "check_small"),
        #(319, 337, ck(lease_fixture), "check_small"),
        # Do not check the PID/MUD addendum box unless an actual notice addendum is generated and attached.
        # The wizard should warn users to confirm this with seller/title instead.
        #(319, 305, ck(val_lower(s.get("mud")) in ["yes", "unknown"] or truthy(s.get("pid"))), "check_small"),
    ]

    pages[8] = [
        (129, 751, addr_full),
    ]

    pages[9] = [
        (126, 751, addr_full),

        # Broker fee disclosure is at the bottom of Page 10, not near the top.
        # Only fill if there is a previous, separate agreement for Listing Broker to pay Other Broker.
        (47, 148, ck(has_buyer_agent and broker_fee_type == "amount"), "check_small"),
        (70,  148, fmt_money(broker_fee_amount) if has_buyer_agent and broker_fee_type == "amount" else "", 8),
        (180, 148, ck(has_buyer_agent and broker_fee_type == "percent"), "check_small"),
        (205, 148, str(broker_fee_percent) if has_buyer_agent and broker_fee_type == "percent" else "", 8),

        # Other Broker / buyer agent side.
        (50,  631, s.get("agentBrokerage", "") if has_buyer_agent else ""),
        (195, 631, s.get("agentBrokerLicense", "") if has_buyer_agent else ""),
        (109, 600, ck(has_buyer_agent), "check_small"),

        (50,  562, s.get("agentName", "") if has_buyer_agent else ""),
        (195, 562, s.get("agentLicense", "") if has_buyer_agent else ""),
        (50,  502, s.get("agentEmail", "") if has_buyer_agent else ""),
        (216, 502, s.get("agentPhone", "") if has_buyer_agent else ""),
    ]

    pages[10] = [
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

    financing_raw_main = str(s.get("financing", "")).strip().lower()
    financing_aliases_main = {
        "cash": "cash",
        "all cash": "cash",
        "no financing": "cash",
        "conventional loan": "conventional",
        "conv": "conventional",
        "fha loan": "fha",
        "fha insured": "fha",
        "va loan": "va",
        "va guaranteed": "va",
        "veterans": "va",
        "usda loan": "usda",
        "usda guaranteed": "usda",
    }
    normalized_financing_main = financing_aliases_main.get(financing_raw_main, financing_raw_main)
    s["financing"] = normalized_financing_main

    has_loan = normalized_financing_main in ["conventional", "fha", "va", "usda"]
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
        financing_raw = str(s.get("financing", "")).strip().lower()
        financing_aliases = {
            "conventional loan": "conventional",
            "conv": "conventional",
            "fha loan": "fha",
            "fha insured": "fha",
            "va loan": "va",
            "va guaranteed": "va",
            "veterans": "va",
            "usda loan": "usda",
            "usda guaranteed": "usda",
        }
        financing = financing_aliases.get(financing_raw, financing_raw)

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
                # USDA field coordinates tuned independently from the checkbox.
                (422, 307, fmt_money(s.get("loanAmount", "")) if financing == "usda" else ""),
                (446, 294, loan_years if financing == "usda" else ""),
                (252, 282, interest_cap if financing == "usda" else ""),
                (399, 282, interest_first_years if financing == "usda" else ""),
                (526, 264, origination_cap if financing == "usda" else ""),
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

                (83, 561, s.get("salePropertyAddr", ""), 8),

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
        bkup_first_md, bkup_first_yy = split_date(s.get("bkupFirstContractDate", ""))
        bkup_term_md,  bkup_term_yy  = split_date(s.get("bkupTerminateDate", ""))

        bkup_pages = {
            0: [
                (245, 660, addr_full, 8),

                (345, 531, fmt_money(s.get("bkupAdditionalEarnest", "")) if s.get("bkupAdditionalEarnest") else ""),
                (101, 521, fmt_money(s.get("bkupAdditionalOption", "")) if s.get("bkupAdditionalOption") else ""),
                (298, 522, str(s.get("bkupAdditionalDays", "")) if s.get("bkupAdditionalDays") else ""),

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


def send_email(to_email, buyer_name, addr, pdf_bytes, cc_emails=None):
    filename = f"HomeOfferFlow_Offer_{addr.replace(' ','_').replace(',','')}.pdf"

    recipients = []
    for email in [to_email] + list(cc_emails or []):
        email = str(email or "").strip()
        if email and email not in recipients:
            recipients.append(email)

    if not recipients:
        raise Exception("Missing buyer email for offer packet delivery")

    payload = {
        "from": FROM_EMAIL,
        "to": recipients,
        "bcc": [SUPPORT_EMAIL],
        "subject": f"Your HomeOfferFlow Offer — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2 style="color:#1a2f4a;">Your Offer is Ready, {buyer_name}!</h2>
          <p>Your filled TREC offer for <strong>{addr}</strong> is attached.</p>
          <h3>Next Steps:</h3>
          <ol>
            <li>Review the attached PDF carefully before sending or signing</li>
            <li>Send it to the listing agent or seller side if you are ready to submit</li>
            <li>If the seller/listing side requests changes, ask them to prepare revised documents and send them back for your review/signature</li>
            <li>Deliver earnest money and option fee as required if the offer is accepted</li>
          </ol>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.85rem;">
            ⚠️ <strong>Not legal advice.</strong> This is a one-time generated offer packet. Review all later changes, counteroffers, amendments, and signature requests carefully before signing. Consider having a licensed Texas agent or attorney review before submitting.
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


def money_display(v):
    formatted = fmt_money(v)
    return f"${formatted}" if formatted else "—"


def yn_display(v):
    value = val_lower(v)
    if value in ["yes", "true", "1", "y", "unknown"]:
        return "Yes" if value != "unknown" else "Unknown / included"
    if value in ["no", "false", "0", "n"]:
        return "No"
    return str(v or "—")


def html_escape(v):
    text = str(v if v not in [None, ""] else "—")
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def send_admin_order_email(offer, customer_email="", plan="", stripe_session_id=""):
    if not ADMIN_ORDER_EMAIL:
        return

    buyer_name = first_present(offer.get("buyer1"), offer.get("buyerName"), "Buyer")
    buyer_email = first_present(offer.get("buyerEmail"), customer_email)
    buyer_phone = first_present(offer.get("buyerPhone"), offer.get("phone"))

    addr = first_present(offer.get("address"), offer.get("propertyAddress"), "Property")
    city = first_present(offer.get("city"), offer.get("propertyCity"))
    state = first_present(offer.get("state"), offer.get("propertyState"), "TX")
    zip_code = first_present(offer.get("zip"), offer.get("propertyZip"))
    county = first_present(offer.get("county"), offer.get("propertyCounty"))

    plan_labels = {
        "self": "$99 Self-Serve Offer Packet",
        "agent": "$298 Agent Review",
        "attorney": "$448 Attorney Review",
        "agent-transaction": "$999 Agent Transaction Support",
        "attorney-transaction": "$1,499 Attorney Transaction Support",
    }
    plan_label = plan_labels.get(plan, plan or "$99 Homebuyer Offer Packet")

    addenda = []
    if offer.get("financing") and offer.get("financing") != "cash":
        addenda.append("Third Party Financing")
    if val_lower(offer.get("hoa")) in ["yes", "unknown"]:
        addenda.append("HOA")
    if val_lower(offer.get("saleContingency")) == "yes":
        addenda.append("Sale of Other Property")
    if val_lower(offer.get("backupOffer")) == "yes":
        addenda.append("Back-Up Contract")
    if val_lower(offer.get("mud")) in ["yes", "unknown"]:
        addenda.append("MUD/PID")
    if val_lower(offer.get("leadBuiltBefore1978")) in ["yes", "unknown"]:
        addenda.append("Lead-Based Paint Flag")

    from datetime import datetime, timezone
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    admin_html = f"""
      <div style="font-family:Arial,sans-serif;max-width:720px;margin:0 auto;color:#1a1a1a;">
        <h2 style="color:#1a2f4a;">New HomeOfferFlow Offer Packet Order</h2>
        <p>A paid offer packet order was completed.</p>

        <h3>Buyer</h3>
        <table style="border-collapse:collapse;width:100%;margin-top:0.5rem;">
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Name</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(buyer_name)}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Email</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(buyer_email)}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Phone</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(buyer_phone)}</td></tr>
        </table>

        <h3>Property</h3>
        <table style="border-collapse:collapse;width:100%;margin-top:0.5rem;">
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Address</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(addr)}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>City/State/ZIP</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(city)}, {html_escape(state)} {html_escape(zip_code)}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>County</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(county)}</td></tr>
        </table>

        <h3>Offer Terms</h3>
        <table style="border-collapse:collapse;width:100%;margin-top:0.5rem;">
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Purchase Price</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(money_display(offer.get("price") or offer.get("purchasePrice")))}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Financing</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(offer.get("financing") or "—")}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Loan Amount</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(money_display(offer.get("loanAmount")))}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Earnest Money</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(money_display(offer.get("earnest") or offer.get("earnestMoney")))}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Option Fee / Days</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(money_display(offer.get("optionFee")))} / {html_escape(offer.get("optionDays"))} days</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Closing Date</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(offer.get("closingDate"))}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Possession</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(offer.get("possession"))}</td></tr>
        </table>

        <h3>Addenda / Flags</h3>
        <table style="border-collapse:collapse;width:100%;margin-top:0.5rem;">
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>HOA</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(yn_display(offer.get("hoa")))} {html_escape(offer.get("hoaName") or "")}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Sale Contingency</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(yn_display(offer.get("saleContingency")))}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Backup Offer</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(yn_display(offer.get("backupOffer")))}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Seller Concessions</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(money_display(offer.get("concessionAmount")))}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Included / Flagged</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(", ".join(addenda) if addenda else "No extra addenda flagged")}</td></tr>
        </table>

        <h3>Order</h3>
        <table style="border-collapse:collapse;width:100%;margin-top:0.5rem;">
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Plan</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(plan_label)}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Payment Email</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(customer_email)}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Stripe Session</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(stripe_session_id)}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd;"><strong>Notification Time</strong></td><td style="padding:8px;border:1px solid #ddd;">{html_escape(created_at)}</td></tr>
        </table>

        <p style="margin-top:1rem;background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.9rem;">
          This is an operational notice only. The buyer PDF was sent separately to the buyer email above.
        </p>
      </div>
    """

    safe_addr = str(addr or "Property")[:70]
    safe_buyer = str(buyer_name or "Buyer")[:60]
    send_basic_email(
        ADMIN_ORDER_EMAIL,
        f"New HomeOfferFlow Order — {safe_buyer} — {safe_addr}",
        admin_html
    )


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

    recipient_email = offer.get("buyerEmail") or customer_email
    if not recipient_email:
        raise Exception("Missing buyer email for offer packet delivery")
    if not offer.get("address"):
        raise Exception("Missing property address for offer packet")

    co_buyer_email = first_present(
        offer.get("buyer2Email"),
        offer.get("coBuyerEmail"),
        offer.get("buyerTwoEmail")
    )

    send_email(
        recipient_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property"),
        pdf_bytes,
        cc_emails=[co_buyer_email] if co_buyer_email else []
    )

    send_admin_order_email(
        offer,
        customer_email,
        plan,
        session.get("id", "")
    )

    return {
        "status": "ok",
        "message": "PDF created and emailed"
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
            "base_dir": BASE_DIR,
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "financing_pdf_exists": os.path.exists(FINANCING_PDF),
            "hoa_pdf_exists": os.path.exists(HOA_PDF),
            "sale_pdf_exists": os.path.exists(SALE_PDF),
            "backup_pdf_exists": os.path.exists(BACKUP_PDF),
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

import json, os, base64, hashlib, hmac, httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, DictionaryObject
from reportlab.pdfgen import canvas

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

FROM_EMAIL = "offers@homeofferflow.com"
SUPPORT_EMAIL = "support@homeofferflow.com"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAIN_PDF = os.path.join(BASE_DIR, "20-18_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_CONT_PDF = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")


def fmt_money(v):
    try:
        if v in [None, ""]:
            return ""
        return f"{int(float(v)):,}"
    except Exception:
        return str(v or "")


def fmt_money_dollar(v):
    x = fmt_money(v)
    return f"${x}" if x else ""


def split_date(v):
    if not v:
        return "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(v, "%Y-%m-%d")
        return d.strftime("%B %d").replace(" 0", " "), str(d.year)[-2:]
    except Exception:
        return str(v), ""


def parse_lot_block(v):
    import re
    lot = ""
    block = ""
    if not v:
        return lot, block

    m = re.search(r"lot\s*([A-Za-z0-9\-]+)", v, re.I)
    if m:
        lot = m.group(1)

    m = re.search(r"block\s*([A-Za-z0-9\-]+)", v, re.I)
    if m:
        block = m.group(1)

    return lot, block


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


def field_name_from_annot(annot):
    try:
        if annot.get("/T"):
            return str(annot.get("/T"))
        parent = annot.get("/Parent")
        if parent:
            p = parent.get_object()
            if p.get("/T"):
                return str(p.get("/T"))
    except Exception:
        pass
    return ""


def field_type_from_annot(annot):
    try:
        if annot.get("/FT"):
            return str(annot.get("/FT"))
        parent = annot.get("/Parent")
        if parent:
            p = parent.get_object()
            if p.get("/FT"):
                return str(p.get("/FT"))
    except Exception:
        pass
    return ""


def build_field_positions(reader):
    positions = {}

    for page_index, page in enumerate(reader.pages):
        if "/Annots" not in page:
            continue

        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                name = field_name_from_annot(annot)
                ftype = field_type_from_annot(annot)

                if not name or "/Rect" not in annot:
                    continue

                rect = [float(x) for x in annot["/Rect"]]
                positions.setdefault(name, []).append({
                    "page": page_index,
                    "rect": rect,
                    "type": ftype
                })
            except Exception:
                continue

    return positions


def overlay_page(width, height):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 1)
    c.drawString(0, 0, ".")

    c.setFillColorRGB(0, 0, 0)
    return buf, c


def draw_text_in_rect(c, rect, value, size=8):
    if value in [None, ""]:
        return

    x1, y1, x2, y2 = rect
    h = abs(y2 - y1)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", size)

    x = min(x1, x2) + 2
    y = min(y1, y2) + max(2, (h - size) / 2)

    c.drawString(x, y, str(value))


def draw_money_in_rect(c, rect, value, size=8):
    if value in [None, ""]:
        return

    x1, y1, x2, y2 = rect
    h = abs(y2 - y1)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", size)

    x = max(x1, x2) - 2
    y = min(y1, y2) + max(2, (h - size) / 2)

    c.drawRightString(x, y, fmt_money(value))


def draw_check_in_rect(c, rect):
    x1, y1, x2, y2 = rect
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)

    x = min(x1, x2) + 2
    y = min(y1, y2) + 1

    c.drawString(x, y, "X")


def set_pdf_field_value(reader, name, value):
    for page in reader.pages:
        if "/Annots" not in page:
            continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                fname = field_name_from_annot(annot)
                if fname == name:
                    annot.update({NameObject("/V"): value})
            except Exception:
                pass


def set_pdf_checkbox(reader, name, checked):
    desired = NameObject("/Yes") if checked else NameObject("/Off")

    for page in reader.pages:
        if "/Annots" not in page:
            continue

        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                fname = field_name_from_annot(annot)

                if fname == name:
                    annot.update({
                        NameObject("/V"): desired,
                        NameObject("/AS"): desired
                    })
            except Exception:
                pass


def stamp_by_fields(pdf_path, text_values=None, money_values=None, checkbox_values=None):
    reader = PdfReader(pdf_path)
    positions = build_field_positions(reader)

    overlays = {}

    for page_index, page in enumerate(reader.pages):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        overlays[page_index] = overlay_page(w, h)

    for name, value in (text_values or {}).items():
        if value in [None, ""]:
            continue
        set_pdf_field_value(reader, name, str(value))
        for pos in positions.get(name, []):
            _, c = overlays[pos["page"]]
            draw_text_in_rect(c, pos["rect"], value)

    for name, value in (money_values or {}).items():
        if value in [None, ""]:
            continue
        set_pdf_field_value(reader, name, fmt_money(value))
        for pos in positions.get(name, []):
            _, c = overlays[pos["page"]]
            draw_money_in_rect(c, pos["rect"], value)

    for name, checked in (checkbox_values or {}).items():
        set_pdf_checkbox(reader, name, checked)
        if checked:
            for pos in positions.get(name, []):
                _, c = overlays[pos["page"]]
                draw_check_in_rect(c, pos["rect"])

    writer = PdfWriter()

    for page_index, page in enumerate(reader.pages):
        buf, c = overlays[page_index]
        c.save()
        buf.seek(0)

        overlay_reader = PdfReader(buf)
        if len(overlay_reader.pages) > 0:
            page.merge_page(overlay_reader.pages[0])

        writer.add_page(page)

    try:
        writer._root_object.update({
            NameObject("/AcroForm"): DictionaryObject({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })
        })
    except Exception:
        pass

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def build_main_maps(s):
    lot, block = parse_lot_block(s.get("lot", ""))
    addr = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")

    buyer = s.get("buyer1", "")
    if s.get("buyer2"):
        buyer += f" and {s.get('buyer2')}"

    price = float(s.get("price", 0) or 0)
    loan = float(s.get("loanAmount", 0) or 0)
    cash = price - loan

    financing = s.get("financing", "")
    has_loan = financing in ["conventional", "fha", "va", "usda"]
    has_hoa = s.get("hoa") in ["yes", "unknown"]
    has_sale_cont = s.get("saleContingency") == "yes"
    has_backup = s.get("backupOffer") == "yes"
    has_mud = s.get("mud") in ["yes", "unknown"]

    survey = s.get("survey", "sellerExisting")
    seller_disc = s.get("sellerDisclosure", "notReceived")
    as_is = s.get("asIs", "yes")

    closing_md, closing_yy = split_date(s.get("closingDate"))

    escrow_name = s.get("escrowAgent") or s.get("titleCompany", "")
    escrow_addr = s.get("escrowAddress") or s.get("titleAddress", "")

    text_values = {
        "1 PARTIES The parties to this contract are": s.get("seller", ""),
        "Seller and": buyer,

        "A LAND Lot": lot,
        "Block": block,
        "undefined": s.get("subdiv", ""),
        "Addition City of": s.get("city", ""),
        "County of": s.get("county", ""),
        "Texas known as": addr,

        "be removed prior to delivery of possession": "",

        "undefined_6": escrow_name,
        "undefined_7": escrow_addr,

        "the Title Company and Buyers lenders Check one box only": s.get("surveyDays", "7") if survey == "sellerExisting" else "",
        "receipt or the date specified in this paragraph whichever is earlier": s.get("surveyDays", "7") if survey == "buyerNew" else "",
        "than 3 days prior to Closing Date": s.get("surveyDays", "7") if survey == "sellerNew" else "",

        "Commitment other than items 6A1 through 9 above or which prohibit the following use": s.get("intendedUse", ""),
        "the Commitment Exception Documents and the survey Buyers failure to object within the": s.get("objectionDays", ""),

        "Within": s.get("disclosureDays", "3") if seller_disc == "notReceived" else "",
        "following specific repairs and treatments": s.get("repairsText", "") if as_is == "repairs" else "",

        "A The closing of the sale will be on or before": closing_md,
        "20": closing_yy,

        "at": s.get("buyerMailAddr", addr),
        "Phone 51": s.get("buyerPhone", ""),
        "AC1": s.get("buyerEmail", ""),

        "Contract Concerning": addr,
        "Contract Concerning_2": addr,
        "Contract Concerning_3": addr,
        "Contract Concerning_4": addr,
        "Address of Property": addr,
        "Address of Property_2": addr,
        "Addr of Prop": addr,

        "Escrow Agent": escrow_name,
        "Escrow Agent_2": escrow_name,
        "Escrow Agent_3": escrow_name,

        "Option Fee in the form of": fmt_money(s.get("optionFee")),
    }

    money_values = {
        "undefined_3": cash if has_loan else price,
        "undefined_4": loan if has_loan else "",
        "undefined_5": price,

        "as earnest money to": s.get("earnest"),
        "as earnest money to 2": s.get("optionFee"),

        "Buyers Expenses as allowed by the lender": s.get("concessionAmount") if s.get("wantsConcessions") == "yes" else "",
    }

    checkbox_values = {
        "B Sum of all financing described in the attached": has_loan,
        "Third Party Financing Addendum": has_loan,

        "A TITLE POLICY Seller shall furnish to Buyer at": s.get("titlePayer", "seller") == "seller",
        "Sellers": s.get("titlePayer", "seller") == "seller",
        "Seller": s.get("titlePayer", "seller") == "buyer",

        "i will not be amended or deleted from the title policy or": s.get("titleAmendment", "i") == "i",
        "ii will be amended to read shortages in area at the expense of": s.get("titleAmendment", "i") in ["ii_buyer", "ii_seller"],
        "Buyer": s.get("titleAmendment") == "ii_buyer",
        "Sellers_2": s.get("titleAmendment") == "ii_seller",

        "1Within": survey == "sellerExisting",
        "2Within": survey == "buyerNew",
        "2 Within": survey == "buyerNew",
        "3Within": survey == "sellerNew",

        "is": has_hoa,
        "is not": not has_hoa,

        "Within one": seller_disc == "received",
        "Within two": seller_disc == "notReceived",
        "Within three": seller_disc == "exempt",

        "1 Buyer accepts the Property As Is": as_is == "yes",
        "As Is": as_is == "yes",
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the": as_is == "repairs",
        "As Is except": as_is == "repairs",

        "upon": s.get("possession", "funding") == "funding",

        "Addendum for Property Subject to": has_hoa,
        "Addendum for Sale of Other Property by": has_sale_cont,
        "Addendum for BackUp Contract": has_backup,
        "PID": has_mud,

        "Dollar Amt": s.get("wantsConcessions") == "yes",
        "Buyer only": s.get("hasBuyerAgent") == "yes",
    }

    return text_values, money_values, checkbox_values


def build_financing_maps(s):
    addr_city = f"{s.get('address','')}, {s.get('city','')}"
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")

    financing = s.get("financing", "")
    loan = s.get("loanAmount", "")
    years = s.get("loanYears", "") or "30"
    rate = s.get("interestRate", "")
    approval_days = s.get("buyerApprovalDays", "") or "21"
    origination = s.get("originationPercent", "")

    text_values = {
        "Street Address and City": addr_city,
        "Address of Property": addr_full,

        "any financed PMI premium due in full in 2": years,
        "per annum for the first": rate,
        "shown on Buyers Loan Estimate for the loan not to exceed": origination,

        "Text1": approval_days,

        "than": years,
        "years with interest not to exceed_2": rate,
        "Charges as shown on Buyers Loan Estimate for the loan not to exceed": origination,

        "years": years,
        "with interest not to exceed": rate,
        "Origination Charges as shown on Buyers Loan Estimate for the loan not to exceed": origination,
    }

    money_values = {
        "any financed PMI premium due in full in 1": loan if financing == "conventional" else "",
        "excluding any financed MIP amortizable monthly for not less": loan if financing == "fha" else "",
        "excluding any financed Funding Fee amortizable monthly for not less than": loan if financing == "va" else "",
        "any financed Funding Fee amortizable monthly for not less than": loan if financing == "usda" else "",
    }

    checkbox_values = {
        "1 Conventional Financing": financing == "conventional",
        "a A first mortgage loan in the principal amount of": financing == "conventional",
        "3 FHA Insured Financing A Section": financing == "fha",
        "4 VA Guaranteed Financing A VA guaranteed loan of not less than": financing == "va",
        "5 USDA Guaranteed Financing A USDAguaranteed loan of not less than": financing == "usda",
        "This contract is subject to Buyer obtaining Buyer Approval If Buyer cannot obtain Buyer": financing in ["conventional", "fha", "va", "usda"],
    }

    return text_values, money_values, checkbox_values


def build_hoa_maps(s):
    text_values = {
        "Street Address and City": f"{s.get('address','')}, {s.get('city','')}",
        "Name of Property Owners Association Association and Phone Number": s.get("hoaName", "") or "TBD",
        "the Subdivision Information to the Buyer If Seller delivers the Subdivision Information Buyer may terminate": s.get("hoaDeliveryDays", "") or "3",
    }

    money_values = {
        "D DEPOSITS FOR RESERVES Buyer shall pay any deposits for reserves required at closing by the Association": s.get("hoaTransferCap", "") or "0",
    }

    checkbox_values = {
        "1 Within": True,
        "undefined": False,
        "3Buyer has received and approved the Subdivision Information before signing the contract Buyer": False,
        "4Buyer does not require delivery of the Subdivision Information": False,
        "does": False,
        "does not require an updated resale certificate If Buyer requires an updated resale certificate Seller at": True,
        "Buyer": s.get("hoaInfoPayer") == "buyer",
        "Seller shall pay the Title Company the cost of obtaining the": s.get("hoaInfoPayer", "seller") != "buyer",
    }

    return text_values, money_values, checkbox_values


def build_sale_cont_maps(s):
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")
    md, yy = split_date(s.get("saleContingencyDate") or s.get("closingDate"))

    text_values = {
        "Address of Property": addr_full,
        "Address on or before": s.get("saleContingencyAddress", ""),
        "Contingency is not satisfied or waived by Buyer by the above date the contract will terminate": md,
        "20": yy,
        "terminate automatically and the earnest money will be refunded to Buyer": s.get("saleContingencyWaiverDays", ""),
    }

    money_values = {
        "All notices and waivers must be in writing and are": s.get("saleContingencyAdditionalEarnest", ""),
    }

    return text_values, money_values, {}


def build_backup_maps(s):
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")
    first_md, first_yy = split_date(s.get("backupFirstContractDate"))
    exp_md, exp_yy = split_date(s.get("backupExpirationDate") or s.get("closingDate"))

    text_values = {
        "Address of Property": addr_full,
        "Except as provided by this Addendum neither party is required to perform under the": first_md,
        "20": first_yy,
        "the BackUp Contract terminates and the earnest money will be refunded to Buyer  Seller must": exp_md,
        "20_2": exp_yy,
        "Text1 2": s.get("backupAdditionalDays", ""),
    }

    money_values = {
        "Text1": s.get("backupAdditionalEarnest", ""),
        "Text1 1": s.get("backupAdditionalOptionFee", ""),
    }

    return text_values, money_values, {}


def append_pdf_bytes(writer, pdf_bytes):
    writer.append(PdfReader(BytesIO(pdf_bytes)))


def fill_and_merge(offer):
    s = offer or {}
    final_writer = PdfWriter()

    t, m, c = build_main_maps(s)
    main_bytes = stamp_by_fields(MAIN_PDF, t, m, c)
    append_pdf_bytes(final_writer, main_bytes)

    if s.get("financing") in ["conventional", "fha", "va", "usda"]:
        t, m, c = build_financing_maps(s)
        append_pdf_bytes(final_writer, stamp_by_fields(FINANCING_PDF, t, m, c))

    if s.get("hoa") in ["yes", "unknown"]:
        t, m, c = build_hoa_maps(s)
        append_pdf_bytes(final_writer, stamp_by_fields(HOA_PDF, t, m, c))

    if s.get("saleContingency") == "yes":
        t, m, c = build_sale_cont_maps(s)
        append_pdf_bytes(final_writer, stamp_by_fields(SALE_CONT_PDF, t, m, c))

    if s.get("backupOffer") == "yes":
        t, m, c = build_backup_maps(s)
        append_pdf_bytes(final_writer, stamp_by_fields(BACKUP_PDF, t, m, c))

    out = BytesIO()
    final_writer.write(out)
    return out.getvalue(), []


def send_confirmation_email(to_email, buyer_name, addr, pdf_bytes=None):
    if not RESEND_API_KEY:
        raise Exception("Missing RESEND_API_KEY")

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "bcc": [SUPPORT_EMAIL],
        "subject": f"Your Filled Offer PDF — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2>Your HomeOfferFlow offer PDF is ready, {buyer_name}.</h2>
          <p>Your payment was successful and your filled offer for <strong>{addr}</strong> is attached.</p>
          <p><strong>Review every field carefully.</strong></p>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.9rem;">
            HomeOfferFlow is not a law firm and does not provide legal advice.
          </p>
        </div>
        """
    }

    if pdf_bytes:
        safe_addr = (addr or "Property").replace(" ", "_").replace("/", "_")
        payload["attachments"] = [{
            "filename": f"HomeOfferFlow_Offer_{safe_addr}.pdf",
            "content": base64.b64encode(pdf_bytes).decode(),
            "content_type": "application/pdf"
        }]

    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )

    if resp.status_code not in [200, 201, 202]:
        raise Exception(f"Resend error {resp.status_code}: {resp.text[:1000]}")

    return resp.json()


def handle_stripe_checkout(event):
    session = event.get("data", {}).get("object", {})
    customer_email = (
        session.get("customer_email")
        or session.get("customer_details", {}).get("email")
        or ""
    )

    metadata = session.get("metadata", {}) or {}

    if "offer_data" in metadata:
        offer = json.loads(metadata["offer_data"])
    else:
        parts = int(metadata.get("offer_parts", 0) or 0)
        combined = "".join(metadata.get(f"offer_{i}", "") for i in range(parts))

        if not combined:
            raise Exception("No offer data found in Stripe session metadata")

        offer = json.loads(combined)

    if not offer.get("buyerEmail") and customer_email:
        offer["buyerEmail"] = customer_email

    pdf_bytes, _ = fill_and_merge(offer)

    send_confirmation_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property"),
        pdf_bytes
    )

    return {"status": "ok", "message": "Field-coordinate stamped PDF created and emailed"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._json(200, {
            "status": "field-coordinate stamped fill-pdf live",
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "financing_pdf_exists": os.path.exists(FINANCING_PDF),
            "hoa_pdf_exists": os.path.exists(HOA_PDF),
            "sale_cont_pdf_exists": os.path.exists(SALE_CONT_PDF),
            "backup_pdf_exists": os.path.exists(BACKUP_PDF),
            "resend_key_set": bool(RESEND_API_KEY),
            "stripe_webhook_secret_set": bool(STRIPE_WHSEC)
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            sig = self.headers.get("stripe-signature", "")
            if sig and not verify_stripe_signature(body, sig, STRIPE_WHSEC):
                self._json(401, {"error": "Invalid Stripe signature"})
                return

            event = json.loads(body.decode("utf-8"))

            if event.get("type") == "checkout.session.completed":
                self._json(200, handle_stripe_checkout(event))
                return

            self._json(200, {"status": "ignored", "event_type": event.get("type")})

        except Exception as e:
            print("ERROR:", str(e))
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


handler = Handler
"""Render the HomeOfferFlow-authored Partner Marketplace Agreement."""

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


def render(lead):
    """Return a deterministic commercial-agreement PDF for one paid lead."""
    clean = lambda value, maximum: " ".join(str(value or "").strip().split())[:maximum]
    company = clean(lead.get("company_name"), 250) or "Partner"
    contact = clean(lead.get("contact_name"), 250) or "Authorized representative"
    market = clean(lead.get("onboarding_market_area") or lead.get("market_area"), 300) or "the agreed market"
    category = (clean(lead.get("partner_type"), 100) or "partner service").replace("_", " ")
    tier = (clean(lead.get("preferred_model"), 100) or "paid partner").replace("_", " ")
    paragraphs = [
        ("HOME OFFER FLOW PARTNER MARKETPLACE AGREEMENT", True),
        ("This Agreement is between BrewBQ Investments LLC, a Texas limited liability company doing business as HomeOfferFlow (HomeOfferFlow), and the paid Partner identified below (Partner).", False),
        (f"Partner: {company} | Authorized representative: {contact}", False),
        (f"Category: {category} | Market: {market} | Selected commercial tier: {tier}", False),
        ("1. PURPOSE AND ORDER FORM. This Agreement governs Partner's paid digital marketplace placement with HomeOfferFlow. The applicable Stripe Checkout confirmation or receipt and any signed order form (together, the Order Form) identify the applicable fee, initial launch period or term, billing interval, placement tier, market, and any expressly agreed exclusivity. The Order Form is incorporated by reference. If this Agreement and an Order Form conflict on fees, term, billing, tier, market, or exclusivity, the Order Form controls. Payment or onboarding alone does not create a right to publication.", False),
        ("2. PLACEMENT; EDITORIAL CONTROL. HomeOfferFlow may display approved company, category, market, logo, website, and call-to-action information in its marketplace. HomeOfferFlow may format, label, defer, suspend, remove, or decline Content and a Placement at any time to protect users, comply with law, maintain a neutral directory, address credible, material, or repeated user complaints, address material breach, or enforce this Agreement. No impressions, clicks, leads, transactions, revenue, ranking, availability, referral, recommendation, or exclusivity is guaranteed unless an Order Form expressly says otherwise.", False),
        ("3. SPONSORED DISCLOSURE AND NEUTRAL CHOICE. HomeOfferFlow may label the Placement Sponsored, Paid Partner, Advertisement, or similarly. Partner will not obscure that disclosure or state or imply that HomeOfferFlow has independently selected, endorsed, guaranteed, ranked, or recommended Partner. Users may choose any qualified provider; this Agreement creates no agency, fiduciary, brokerage, referral, or preferred-provider relationship with users.", False),
        ("4. PARTNER CONTENT AND COMPLIANCE. Partner represents that all submitted Content, licenses, qualifications, testimonials, offers, prices, websites, trademarks, and claims are accurate, current, substantiated, lawful, and non-misleading. Partner is solely responsible for its services, personnel, licenses, insurance, permits, advertising, communications, privacy practices, taxes, and compliance with all applicable legal or professional rules. Partner will promptly report a material change and will not submit unlawful, discriminatory, infringing, deceptive, privacy-invasive, or unsubstantiated Content.", False),
        ("5. NO PROFESSIONAL SERVICES BY HOMEOFFERFLOW. HomeOfferFlow is not providing real-estate brokerage, lending, title, appraisal, insurance, inspection, construction, legal, tax, or other regulated professional services through this Agreement. Partner may not state or imply otherwise.", False),
        ("6. CONTENT LICENSE; INTELLECTUAL PROPERTY. Partner grants HomeOfferFlow a non-exclusive, worldwide, royalty-free license during the Term to host, reproduce, technically format, make accessible, display, distribute, and link to approved Partner Content solely to operate, promote, measure, and improve the Placement. Partner retains its pre-existing Content rights. Partner acquires no right, title, or interest in HomeOfferFlow's name, logos, trademarks, platform, software, or other intellectual property.", False),
        ("7. FEES, TERM, RENEWAL, AND CANCELLATION. The Order Form controls fees, term length, and renewal terms. Stripe's successful payment records control payment processing. Unless an Order Form states otherwise, the founding-partner launch period is 90 days and the Placement then renews month-to-month at the disclosed recurring price until cancelled. By signing, Partner authorizes the recurring Stripe charges disclosed in the Order Form until cancellation takes effect. Either Party may cancel a month-to-month Placement on 30 days' written notice. Cancellation stops future renewal after the paid period and does not create a pro-rata refund except as required by law or expressly stated in an Order Form. HomeOfferFlow may suspend or remove a Placement for failed, reversed, disputed, expired, or overdue payment, and may terminate this Agreement immediately for material breach, insolvency, or regulatory issues.", False),
        ("8. DATA AND COMMUNICATIONS. Each Party is an independent controller of information it collects. This Agreement gives Partner no right to HomeOfferFlow user, offer, transaction, or account data. HomeOfferFlow may provide aggregate placement metrics. Partner will comply with applicable consent, opt-out, email, text, telemarketing, privacy, and advertising law and will not market to a HomeOfferFlow user merely because the user viewed or clicked a Placement.", False),
        ("9. INDEMNITY. Partner will defend, indemnify, and hold harmless HomeOfferFlow and its officers, directors, employees, and agents from and against third-party claims, losses, liabilities, damages, costs, and reasonable attorney fees arising out of or related to Partner Content, services, advertising, communications, data practices, licenses, professional conduct, breach of this Agreement, or any allegedly unlawful, deceptive, or infringing Content or activity.", False),
        ("10. DISCLAIMERS AND LIMITATION OF LIABILITY. Except for the express terms of this Agreement, the platform and any Placement are provided AS IS. To the maximum extent permitted by law, neither Party is liable for indirect, incidental, special, consequential, exemplary, or punitive damages, including lost profits, revenue, data, or business opportunities. Subject to non-waivable rights, each Party's total aggregate liability under this Agreement is capped at the fees paid or payable under the applicable Order Form in the twelve months preceding the claim.", False),
        ("11. GENERAL. The Parties are independent contractors. This Agreement is governed by Texas law, without regard to conflict-of-law principles. Exclusive venue and jurisdiction for a dispute arising out of or relating to this Agreement lies in the state or federal courts located in the Texas county where BrewBQ Investments LLC maintains its principal place of business, unless non-waivable law requires otherwise. Electronic records and signatures are intended to be effective as permitted by law. This Agreement, together with the applicable Order Form, is the entire agreement concerning its subject matter and supersedes prior or contemporaneous agreements, representations, and understandings. Sections 4 through 11, and any accrued payment obligations, survive expiration or termination to the extent their purpose requires.", False),
        ("By signing electronically, Partner's authorized representative confirms authority to bind Partner and accepts this Agreement. A completed agreement is required before a public Placement can be activated.", False),
        ("COMMERCIAL AGREEMENT NOTICE: This is a HomeOfferFlow-authored commercial marketplace agreement, not a Texas REALTORS or TREC form.", True),
    ]
    buffer = BytesIO(); pdf = Canvas(buffer, pagesize=letter)
    width, height = letter; left, right, bottom = 54, 54, 54; y = height - 54
    def header():
        nonlocal y
        pdf.setFont("Helvetica", 8); pdf.setFillColorRGB(.28, .32, .39)
        pdf.drawRightString(width - right, height - 34, "HomeOfferFlow Partner Marketplace Agreement")
        pdf.setFillColorRGB(0, 0, 0); y = height - 54
    def lines(text, font, size):
        output, current, available = [], "", width - left - right
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if current and stringWidth(candidate, font, size) > available:
                output.append(current); current = word
            else: current = candidate
        return output + ([current] if current else [])
    header()
    for text, emphasized in paragraphs:
        font, size, leading = ("Helvetica-Bold", 11, 14) if emphasized else ("Helvetica", 9, 12)
        for line in lines(text, font, size):
            if y - leading < bottom: pdf.showPage(); header()
            pdf.setFont(font, size); pdf.drawString(left, y, line); y -= leading
        y -= 7
    pdf.save()
    return buffer.getvalue()

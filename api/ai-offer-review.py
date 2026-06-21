import os
import json
import re
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone

import httpx

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
GEMINI_MODEL = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
GEMINI_GROUNDING_MODEL = os.environ.get("GEMINI_GROUNDING_MODEL") or GEMINI_MODEL
ENABLE_PROPERTY_CONTEXT = (os.environ.get("ENABLE_PROPERTY_CONTEXT") or "true").lower() not in {"0", "false", "no"}
MAX_BODY_BYTES = 120_000


def _json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _safe_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace("$", "").replace(",", ""))
    except Exception:
        return default


def _safe_text(value, max_len=220):
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    return text[:max_len]


def _clamp_score(n):
    try:
        return max(1, min(100, int(round(float(n)))))
    except Exception:
        return 60


def _extract_grounding_sources(data):
    candidate = (data.get("candidates") or [{}])[0]
    meta = candidate.get("groundingMetadata") or candidate.get("grounding_metadata") or {}
    chunks = meta.get("groundingChunks") or meta.get("grounding_chunks") or []
    sources = []
    for chunk in chunks[:8]:
        web = chunk.get("web") or {}
        uri = web.get("uri") or ""
        title = web.get("title") or uri
        if uri:
            sources.append({"title": _safe_text(title, 120), "url": uri})
    queries = meta.get("webSearchQueries") or meta.get("web_search_queries") or []
    return sources, queries[:5]


def _try_json_from_text(text):
    if not text:
        return None
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.strip("`")
        if clean.lower().startswith("json"):
            clean = clean[4:].strip()
    start = clean.find("{")
    end = clean.rfind("}")
    if start >= 0 and end > start:
        clean = clean[start:end + 1]
    try:
        return json.loads(clean)
    except Exception:
        return None



def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(round(float(str(value).replace(",", "").strip())))
    except Exception:
        return default


def _infer_market_leverage(offer, property_context=None):
    """Infer seller/buyer leverage from explicit listing intel first, then public context."""
    property_context = property_context or {}
    dom = _safe_int(
        offer.get("daysOnMarket") or offer.get("dom") or offer.get("listingDom") or property_context.get("daysOnMarket")
    )
    reductions = _safe_int(
        offer.get("priceReductionCount") or offer.get("reductions") or offer.get("priceReductions")
    )

    pc_changes = str(property_context.get("priceChanges") or "").lower()
    if not reductions and pc_changes:
        reductions = len(re.findall(r"down|reduc|drop|\$[0-9]", pc_changes))

    listing_status = str(offer.get("listingStatus") or property_context.get("status") or "").lower()
    notes = " ".join([
        str(offer.get("listingNotes") or ""),
        str(property_context.get("propertySummary") or ""),
        " ".join(property_context.get("marketContext") or []),
    ]).lower()

    list_price = _safe_number(offer.get("listPrice") or property_context.get("listPrice"))
    original_price = _safe_number(offer.get("originalListPrice") or offer.get("originalPrice"))
    price_drop_pct = 0
    if list_price and original_price and original_price > list_price:
        price_drop_pct = ((original_price - list_price) / original_price) * 100
        if not reductions:
            reductions = 1

    buyer_terms = ["seller motivated", "bring offer", "reduced", "price reduction", "vacant", "builder", "relocation", "must sell"]
    seller_terms = ["multiple offers", "highest and best", "new listing", "coming soon", "deadline", "hot home"]
    buyer_signal = sum(1 for term in buyer_terms if term in notes)
    seller_signal = sum(1 for term in seller_terms if term in notes)

    score = 0
    evidence = []

    if dom:
        evidence.append(f"Days on market: {dom}")
        if dom <= 7:
            score -= 35
        elif dom <= 21:
            score -= 18
        elif dom <= 45:
            score -= 6
        elif dom <= 75:
            score += 10
        elif dom <= 120:
            score += 22
        else:
            score += 30

    if reductions:
        score += min(24, 8 * reductions)
        evidence.append(f"Price reductions identified: {reductions}")

    if price_drop_pct:
        score += min(18, price_drop_pct * 1.5)
        evidence.append(f"Approximate list-price reduction from original: {price_drop_pct:.1f}%")

    if buyer_signal:
        score += min(20, 8 * buyer_signal)
        evidence.append("Listing language/context suggests seller motivation.")
    if seller_signal:
        score -= min(20, 10 * seller_signal)
        evidence.append("Listing language/context suggests stronger seller leverage.")

    if "pending" in listing_status or "under contract" in listing_status:
        score -= 35
        evidence.append("Listing status may not be fully active.")
    elif "active" in listing_status:
        evidence.append("Listing status appears active.")

    if score >= 35:
        label = "strong buyer advantage"
    elif score >= 18:
        label = "buyer advantage"
    elif score >= 6:
        label = "slight buyer advantage"
    elif score <= -30:
        label = "strong seller advantage"
    elif score <= -14:
        label = "seller advantage"
    elif score <= -5:
        label = "slight seller advantage"
    else:
        label = "balanced/unknown"

    return {
        "score": round(score),
        "label": label,
        "dom": dom,
        "reductions": reductions,
        "priceDropPct": round(price_drop_pct, 1) if price_drop_pct else 0,
        "evidence": evidence[:6],
    }


def _days_until(date_text):
    if not date_text:
        return 0
    try:
        dt = datetime.fromisoformat(str(date_text).replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo or timezone.utc)
        return int(round((dt - now).total_seconds() / 86400))
    except Exception:
        try:
            dt = datetime.fromisoformat(str(date_text) + "T12:00:00+00:00")
            return int(round((dt - datetime.now(timezone.utc)).total_seconds() / 86400))
        except Exception:
            return 0


def _rules_fallback(offer, property_context=None):
    property_context = property_context or {}
    price = _safe_number(offer.get("offerPrice"))
    list_price = _safe_number(offer.get("listPrice") or property_context.get("listPrice"))
    earnest = _safe_number(offer.get("earnestMoney"))
    option_fee = _safe_number(offer.get("optionFee"))
    option_days = _safe_number(offer.get("optionDays"))
    financing = str(offer.get("financing") or "").lower()
    sale_contingency = str(offer.get("saleContingency") or "").lower()
    wants_concessions = str(offer.get("wantsConcessions") or "").lower()
    concessions = _safe_number(offer.get("concessionAmount"))
    appraisal = str(offer.get("appraisalAddendum") or "").lower()
    title_payer = str(offer.get("titlePayer") or "").lower()
    title_amendment = str(offer.get("titleAmendment") or "").lower()
    survey = str(offer.get("survey") or "").lower()
    as_is = str(offer.get("asIs") or "").lower()
    possession = str(offer.get("possession") or "").lower()
    seller_disclosure = str(offer.get("sellerDisclosure") or "").lower()
    hoa = str(offer.get("hoa") or "").lower()
    lead = str(offer.get("leadBuiltBefore1978") or "").lower()
    city = _safe_text(offer.get("city"), 80)
    county = _safe_text(offer.get("county"), 80)
    closing_days = _days_until(offer.get("closingDate"))

    leverage = _infer_market_leverage(offer, property_context)
    market_label = leverage["label"]

    risks = []
    strengths = []
    market = []
    suggestions = []

    # v2 calibration: market is the first driver when real market data exists, but missing market data should not
    # drag down a clean seller-favored offer. The initial score is term-neutral, then market and terms adjust it.
    has_market_evidence = bool(leverage.get("evidence") or list_price or property_context.get("found"))
    score = 52
    if has_market_evidence:
        score += leverage["score"]
        market.extend(leverage.get("evidence") or [])
    else:
        market.append("No reliable DOM, price-reduction, list-price, or seller-motivation data was available, so the review relies on offer terms and general Texas resale norms.")

    if price and list_price:
        pct_of_list = (price / list_price) * 100 if list_price else 0
        market.append(f"Offer is approximately {pct_of_list:.1f}% of list price.")
        if pct_of_list >= 102:
            strengths.append("Offer price is above list price, improving seller economics.")
            score += 12
        elif pct_of_list >= 100:
            strengths.append("Offer price is at or above list price.")
            score += 9
        elif pct_of_list >= 98:
            strengths.append("Offer price is close to list price.")
            score += 3
        elif pct_of_list < 95:
            risks.append("Offer price is materially below list price.")
            score -= 13 if "seller advantage" in market_label else 7

    earnest_pct = (earnest / price * 100) if price and earnest else 0
    if earnest:
        if earnest_pct >= 3:
            strengths.append("Earnest money is very strong relative to price.")
            score += 14
        elif earnest_pct >= 2:
            strengths.append("Earnest money is strong relative to price.")
            score += 12
        elif earnest_pct >= 1:
            strengths.append("Earnest money is around or above a common 1% Texas starting point.")
            score += 8
        elif earnest_pct >= 0.5:
            strengths.append("Earnest money is present, though below a strong seller-favorable level.")
            score += 3
        else:
            risks.append("Earnest money appears light versus seller-favorable norms.")
            score -= 2
    else:
        risks.append("Earnest money is missing.")
        score -= 10

    if option_days:
        if option_days <= 3:
            strengths.append("Very short option period is strongly seller-friendly if inspections can be completed quickly.")
            score += 12
        elif option_days <= 5:
            strengths.append("Short option period can improve seller confidence.")
            score += 9
        elif option_days <= 7:
            strengths.append("Option period is within a common Texas starter range.")
            score += 5
        elif option_days <= 10:
            risks.append("Option period is a little longer than a seller-favored posture.")
            score -= 3
        else:
            risks.append("Long option period weakens seller confidence.")
            score -= 9
    else:
        risks.append("Option period days are missing.")
        score -= 8

    if option_fee >= 1000:
        strengths.append("Large option fee improves seller economics and seriousness signal.")
        score += 6
    elif option_fee >= 500:
        strengths.append("Option fee is stronger than a basic starter amount.")
        score += 4
    elif option_fee >= 250:
        strengths.append("Option fee is present and appears within a typical starter range.")
        score += 2
    elif option_fee > 0:
        strengths.append("Option fee is present.")
    else:
        risks.append("Option fee is missing.")
        score -= 4

    if financing == "cash":
        strengths.append("Cash financing is highly seller-friendly because it improves certainty and removes lender risk.")
        score += 18
    elif financing == "conventional":
        strengths.append("Conventional financing is generally cleaner than FHA/VA/USDA if pre-approval is strong.")
        score += 10
        market.append("Financed offer strength depends on pre-approval quality, appraisal posture, and closing timeline.")
    elif financing in {"fha", "va", "usda"}:
        risks.append("Government-backed financing may add appraisal or property-condition sensitivity.")
        score += 2
    else:
        risks.append("Financing type is missing or unclear.")
        score -= 7

    if sale_contingency == "no":
        strengths.append("No sale-of-other-property contingency keeps the offer cleaner for the seller.")
        score += 6
    elif sale_contingency == "yes":
        risks.append("Sale-of-other-property contingency can materially reduce seller confidence.")
        score -= 24
        suggestions.append("Remove or tighten the sale contingency if possible.")

    if wants_concessions == "no" or concessions <= 0:
        strengths.append("No seller concessions preserves seller net proceeds.")
        score += 6
    else:
        con_pct = (concessions / price * 100) if price else 0
        risks.append("Seller concessions reduce seller net proceeds.")
        score -= min(18, 7 + con_pct * 2)
        suggestions.append("Reduce or remove seller concessions if competitiveness matters more than cash-to-close relief.")

    if title_payer == "buyer":
        strengths.append("Buyer paying the owner title policy is seller-favorable.")
        score += 7
    elif title_payer == "seller":
        score -= 2
    if "buyer" in title_amendment:
        strengths.append("Buyer-paid title amendment cost reduces seller expense.")
        score += 3
    if survey in {"buyernew", "nosurvey"}:
        strengths.append("Survey election appears cleaner for seller expense/timing.")
        score += 4
    elif survey == "sellerexisting":
        score += 1
    if as_is == "yes":
        strengths.append("As-is posture keeps the initial offer cleaner for the seller.")
        score += 5

    if appraisal == "waiver":
        strengths.append("Appraisal waiver posture can materially improve a financed offer.")
        score += 8
    elif appraisal == "none":
        score += 2
    elif appraisal == "partial":
        risks.append("Partial appraisal protection can be less seller-friendly than a waiver.")
        score -= 3
    elif appraisal == "additional":
        risks.append("Additional appraisal termination rights may weaken a financed offer.")
        score -= 9

    if closing_days and closing_days <= 21:
        strengths.append("Fast closing timeline can improve seller confidence if lender/title can perform.")
        score += 6
    elif closing_days > 45:
        risks.append("Longer closing timeline may reduce seller appeal.")
        score -= 5
    elif not closing_days:
        risks.append("Closing date is missing.")
        score -= 4

    if possession in {"funding", "closing"}:
        score += 2
    if seller_disclosure == "received":
        strengths.append("Seller disclosure status appears clear.")
    if hoa == "unknown":
        risks.append("HOA status is unknown and should be verified before submitting.")
    if lead in {"yes", "unknown"}:
        risks.append("Lead-based paint disclosure status should be confirmed before signing or sending.")

    if score >= 78:
        suggestions.append("This reads seller-favorable from the entered terms. Verify live market context before relying on the score.")
    if "seller advantage" in market_label:
        suggestions.append("In a seller-advantaged situation, keep terms clean and verify proof of funds/pre-approval strength.")
    elif "buyer advantage" in market_label:
        suggestions.append("Buyer leverage may support more negotiation if DOM/reductions/motivation evidence is reliable.")
    else:
        suggestions.append("Verify DOM, price changes, listing status, and seller motivation to make the score more market-specific.")

    if city or county:
        market.append(f"Location used: {city + ', ' if city else ''}{county} County.")

    score = _clamp_score(score)
    components = {
        "contractQuality": _clamp_score(82 + min(8, len(strengths)) - min(16, len(risks) * 2)),
        "competitiveness": score,
        "closingCertainty": _clamp_score(70 + (18 if financing == "cash" else 8 if financing == "conventional" else 0) + (8 if sale_contingency == "no" else 0) - (22 if sale_contingency == "yes" else 0) - (4 if concessions else 0) + (5 if closing_days and closing_days <= 30 else 0)),
        "buyerProtection": _clamp_score(82 + (6 if option_days and option_days >= 7 else 0) - (10 if appraisal == "waiver" else 0) - (5 if as_is == "yes" else 0) - (8 if option_days and option_days <= 3 else 0)),
        "marketFit": _clamp_score((60 + leverage["score"] + (8 if score >= 80 else 0)) if has_market_evidence else max(68, min(82, score - 6)))
    }
    return {
        "score": score,
        "summary": "Entered terms read seller-favorable. Market data is still needed to judge how aggressive this is for the specific property." if score >= 78 else f"Built-in competitiveness review completed. Market leverage appears {market_label}.",
        "risks": risks[:6],
        "strengths": strengths[:6],
        "marketContext": market[:8],
        "suggestions": suggestions[:6],
        "marketMode": market_label if has_market_evidence else "unknown/general Texas resale norms",
        "components": components,
        "disclaimer": "This is a software-generated educational competitiveness review, not legal advice, broker advice, a valuation opinion, or a guarantee of acceptance.",
        "source": "rules_fallback_v2_seller_favorability_calibrated",
        "propertyContext": property_context or None
    }


def _grounded_property_context(offer):
    if not (ENABLE_PROPERTY_CONTEXT and GEMINI_API_KEY):
        return {"found": False, "reason": "property_context_disabled_or_no_api_key"}

    address = _safe_text(offer.get("propertyAddress"), 160)
    city = _safe_text(offer.get("city"), 80)
    state = _safe_text(offer.get("state") or "TX", 10)
    zip_code = _safe_text(offer.get("zip"), 20)
    county = _safe_text(offer.get("county"), 80)
    price = _safe_text(offer.get("offerPrice"), 40)

    if not address and not (city and zip_code):
        return {"found": False, "reason": "missing_address"}

    query_context = ", ".join([x for x in [address, city, state, zip_code] if x])
    prompt = f"""
You are collecting PUBLIC real estate listing context for HomeOfferFlow's educational offer competitiveness review.
Search the public web for current or recent listing/market context for this property or nearby public listing pages.

Property: {query_context}
County: {county}
Offer price entered: {price}

Return ONLY compact JSON with these keys:
{{
  "found": boolean,
  "confidence": "high" | "medium" | "low" | "none",
  "propertySummary": string,
  "listPrice": string,
  "status": string,
  "daysOnMarket": string,
  "priceChanges": string,
  "marketMode": "strong seller advantage" | "seller advantage" | "balanced/unknown" | "buyer advantage" | "strong buyer advantage",
  "sellerLeverage": "high" | "medium" | "low" | "unknown",
  "marketEvidence": [string],
  "marketContext": [string],
  "limitations": [string]
}}

Rules:
- Do not claim MLS-verified unless the source is an authorized MLS/RESO source.
- Prefer public listing facts over general neighborhood fluff.
- If facts conflict or are stale, say confidence is low and include that limitation.
- Prioritize DOM, listing status, price reductions, stale-listing signals, multiple-offer/new-listing signals, vacancy, builder/investor ownership, and seller motivation language.
- Keep marketContext practical for offer competitiveness, not valuation advice.
- Do not recommend a price.
""".strip()

    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.15,
            "topP": 0.8,
            "maxOutputTokens": 1200
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_GROUNDING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    try:
        with httpx.Client(timeout=16.0) as client:
            resp = client.post(url, json=request_body)
        if resp.status_code >= 400:
            return {"found": False, "reason": "grounding_error", "detail": resp.text[:300]}
        data = resp.json()
        candidate = (data.get("candidates") or [{}])[0]
        text = (((candidate.get("content") or {}).get("parts") or [{}])[0].get("text") or "")
        parsed = _try_json_from_text(text) or {"found": False, "rawText": _safe_text(text, 900)}
        sources, queries = _extract_grounding_sources(data)
        parsed["sources"] = sources
        parsed["searchQueries"] = queries
        parsed["sourceType"] = "public_web_google_grounding"
        parsed["notMlsVerified"] = True
        return parsed
    except Exception as exc:
        return {"found": False, "reason": "grounding_exception", "detail": str(exc)[:300]}


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "summary": {"type": "string"},
        "risks": {"type": "array", "items": {"type": "string"}},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "marketContext": {"type": "array", "items": {"type": "string"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
        "marketMode": {"type": "string"},
        "components": {
            "type": "object",
            "properties": {
                "contractQuality": {"type": "integer"},
                "competitiveness": {"type": "integer"},
                "closingCertainty": {"type": "integer"},
                "buyerProtection": {"type": "integer"},
                "marketFit": {"type": "integer"}
            },
            "required": ["contractQuality", "competitiveness", "closingCertainty", "buyerProtection", "marketFit"]
        },
        "disclaimer": {"type": "string"}
    },
    "required": ["score", "summary", "risks", "strengths", "marketContext", "suggestions", "marketMode", "components", "disclaimer"]
}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_BODY_BYTES:
                return _json_response(self, 400, {"error": "Invalid request size."})
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            offer = payload.get("offer") or payload
            if not isinstance(offer, dict):
                return _json_response(self, 400, {"error": "Missing offer object."})

            property_context = _grounded_property_context(offer)
            fallback = _rules_fallback(offer, property_context)

            if not GEMINI_API_KEY:
                return _json_response(self, 200, {**fallback, "source": "rules_fallback_no_api_key"})

            prompt = {
                "role": "HomeOfferFlow AI Offer Competitiveness Review",
                "instructions": [
                    "Review a Texas residential resale purchase offer for educational OFFER COMPETITIVENESS feedback.",
                    "The score is NOT a contract-quality score. It is how attractive or competitive this offer appears for THIS property in THIS market.",
                    "Market leverage is the primary driver. DOM, price reductions, active status, listing remarks, seller motivation, and buyer/seller leverage should materially affect the score.",
                    "The same offer should score much lower on a fresh/hot listing than on a stale listing with reductions or seller-motivation signals.",
                    "Do not anchor on generic Texas contract norms. Market data drives the score; contract terms adjust it.",
                    "First determine seller leverage: strong seller advantage, seller advantage, balanced/unknown, buyer advantage, or strong buyer advantage.",
                    "Then score the offer relative to that leverage.",
                    "For strong seller advantage: penalize long option periods, contingencies, concessions, low earnest money, weak financing, and below-list offers more heavily.",
                    "For buyer advantage: tolerate reasonable concessions, inspection time, and negotiation terms more if DOM/reductions/motivation support it.",
                    "If market data is missing or low-confidence, clearly say the score is limited, but do NOT automatically cap or depress the score when entered terms are strongly seller-favorable.",
                    "Strong seller-favorable terms can score in the 80s even without DOM/listing history; market data changes confidence and property-specific fit.",
                    "Do not provide legal advice, brokerage advice, fiduciary advice, steering, valuation advice, or a guarantee of acceptance.",
                    "Use cautious language: may, commonly, often, consider, confirm, verify.",
                    "For homebuyer userType: make the market reasoning, score, and improvement suggestions clear and practical.",
                    "For agent userType: de-emphasize the score; focus on market leverage, risk review, missing items, and client strategy checks.",
                    "For investor userType: focus on deal-term clarity, contingencies, speed, seller net, and closing certainty.",
                    "Return components: contractQuality, competitiveness, closingCertainty, buyerProtection, and marketFit as 1-100 integers that explain the score.",
                    "In marketContext, lead with market evidence such as DOM, price reductions, listing status, and seller motivation if available.",
                    "Keep each risk/strength/suggestion under 140 characters when possible."
                ],
                "offer": offer,
                "propertyContext": property_context,
                "reviewDateUtc": datetime.now(timezone.utc).isoformat()
            }

            request_body = {
                "contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
                "generationConfig": {
                    "temperature": 0.22,
                    "topP": 0.9,
                    "maxOutputTokens": 1500,
                    "responseMimeType": "application/json",
                    "responseSchema": RESPONSE_SCHEMA
                }
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            with httpx.Client(timeout=18.0) as client:
                resp = client.post(url, json=request_body)
            if resp.status_code >= 400:
                return _json_response(self, 200, {**fallback, "source": "rules_fallback_gemini_error", "gemini_error": resp.text[:500]})

            data = resp.json()
            text = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [{}])[0].get("text") or ""
            try:
                review = json.loads(text)
            except Exception:
                return _json_response(self, 200, {**fallback, "source": "rules_fallback_parse_error"})

            review["score"] = _clamp_score(review.get("score") or fallback["score"])
            market_text = " ".join(review.get("marketContext") or []).lower()
            concrete_market = any(term in market_text for term in ["days on market", "dom", "price reduction", "list price", "multiple offer", "active", "pending", "seller motivation", "reduced"])
            if fallback.get("score", 0) >= 78 and review["score"] < fallback["score"] - 8 and not concrete_market:
                review["score"] = fallback["score"]
                review["summary"] = "Entered terms read seller-favorable. Live market context was limited, so the terms-calibrated score is shown."
                review["strengths"] = list(dict.fromkeys((fallback.get("strengths") or []) + (review.get("strengths") or [])[:2]))[:6]
                review["suggestions"] = list(dict.fromkeys((fallback.get("suggestions") or []) + (review.get("suggestions") or [])[:2]))[:6]
                review["marketMode"] = fallback.get("marketMode") or review.get("marketMode")
            comps = review.get("components") or {}
            clean_comps = {}
            for key in ["contractQuality", "competitiveness", "closingCertainty", "buyerProtection", "marketFit"]:
                clean_comps[key] = _clamp_score(comps.get(key, review["score"]))
            review["components"] = clean_comps
            review["marketMode"] = review.get("marketMode") or property_context.get("marketMode") or "unknown/general Texas resale norms"
            review["source"] = "gemini_with_public_property_context" if property_context.get("found") else "gemini"
            review["model"] = GEMINI_MODEL
            review["propertyContext"] = property_context

            if property_context.get("sources"):
                source_lines = [f"Public source: {s.get('title') or s.get('url')}" for s in property_context.get("sources", [])[:3]]
                existing = review.get("marketContext") or []
                review["marketContext"] = (existing + source_lines)[:8]

            return _json_response(self, 200, review)
        except Exception as exc:
            return _json_response(self, 500, {"error": str(exc)[:500]})

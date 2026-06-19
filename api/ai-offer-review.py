import os
import json
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


def _rules_fallback(offer, property_context=None):
    property_context = property_context or {}
    price = _safe_number(offer.get("offerPrice"))
    earnest = _safe_number(offer.get("earnestMoney"))
    option_fee = _safe_number(offer.get("optionFee"))
    option_days = _safe_number(offer.get("optionDays"))
    financing = str(offer.get("financing") or "").lower()
    sale_contingency = str(offer.get("saleContingency") or "").lower()
    concessions = _safe_number(offer.get("concessionAmount"))
    hoa = str(offer.get("hoa") or "").lower()
    lead = str(offer.get("leadBuiltBefore1978") or "").lower()
    appraisal = str(offer.get("appraisalAddendum") or "").lower()
    city = offer.get("city") or ""
    county = offer.get("county") or "Texas"

    market_mode = property_context.get("marketMode") or "unknown/general Texas resale norms"
    has_public_context = bool(property_context.get("found"))

    score = 40
    risks, strengths, market, suggestions = [], [], [], []

    if price:
        score += 5
    else:
        risks.append("Offer price is missing, so the offer cannot be meaningfully scored yet.")
        suggestions.append("Enter the offer price before relying on the review.")

    if price and earnest:
        earnest_pct = earnest / price * 100
        if earnest_pct >= 1:
            score += 8
            strengths.append("Earnest money is around or above a common Texas resale starting point of roughly 1% of price.")
        elif earnest_pct >= 0.5:
            score += 3
            strengths.append("Earnest money is present, though it is below a common 1% starting point.")
        else:
            score -= 6
            risks.append("Earnest money appears low compared with a common Texas resale starting point.")
            suggestions.append("Consider whether a stronger earnest money deposit is appropriate for this property and market.")
    else:
        score -= 5
        risks.append("Earnest money is missing.")

    if option_days and option_days <= 5:
        score += 7
        strengths.append("The option period is short, which can be attractive if inspections can be completed quickly.")
    elif option_days and option_days <= 7:
        score += 4
        strengths.append("The option period is within a common Texas starter range.")
    elif option_days:
        score -= 10
        risks.append("The option period is longer than a common 5–7 day Texas starting point.")
        suggestions.append("Confirm the longer option period is needed before submitting.")
    else:
        score -= 4
        risks.append("Option period days are missing.")

    if option_fee >= 250:
        score += 3
        strengths.append("The option fee is present and appears within a typical starter range.")
    elif option_fee > 0:
        strengths.append("The option fee is present.")
    else:
        risks.append("Option fee is missing.")

    if financing == "cash":
        score += 12
        strengths.append("Cash financing generally improves offer certainty because there is no lender approval condition.")
    elif financing in {"conventional", "fha", "va", "usda"}:
        score += 3
        market.append("Financed offer strength depends on the quality of pre-approval, appraisal posture, and closing timeline.")
        if financing in {"fha", "va", "usda"}:
            risks.append("Government-backed financing can involve additional appraisal or property-condition sensitivity.")
    else:
        risks.append("Financing type is missing or unclear.")

    if sale_contingency == "yes":
        score -= 20
        risks.append("A sale-of-other-property contingency can materially reduce offer strength.")
        suggestions.append("Confirm the sale contingency is necessary and complete all related deadline fields.")

    if concessions > 0:
        score -= 10
        risks.append("Seller concessions reduce the seller's net proceeds and may reduce competitiveness in multiple-offer situations.")

    if appraisal == "waiver":
        score += 5
        strengths.append("Appraisal waiver posture may improve offer strength if suitable for the buyer's financial situation.")
    elif appraisal == "additional":
        score -= 5
        risks.append("Additional appraisal termination rights may weaken the financed offer.")

    if hoa == "unknown":
        risks.append("HOA status is unknown and should be verified before submitting.")
    if lead in {"yes", "unknown"}:
        risks.append("Lead-based paint disclosure status should be confirmed before signing or sending.")

    if has_public_context:
        pc_lines = property_context.get("marketContext") or []
        market.extend([_safe_text(x, 180) for x in pc_lines[:4] if x])
        market.append("Public listing/search context was used. This is not MLS-verified unless an authorized MLS source is connected.")
    elif city or county:
        market.append(f"Property context used: {city + ', ' if city else ''}{county} County. Live MLS/comps data is not connected.")
        market.append("This review compares entered terms against Texas resale-contract norms, not verified MLS data.")

    # Market weighting adjustments
    mm = str(market_mode).lower()
    earnest_pct = (earnest / price * 100) if (price and earnest) else 0

    if any(x in mm for x in ["hot", "seller", "competitive"]):
        if option_days and option_days > 7:
            score -= 8
        if sale_contingency == "yes":
            score -= 15
        if earnest_pct >= 1:
            score += 5
        if financing == "cash":
            score += 8

    elif any(x in mm for x in ["buyer", "negotiable", "soft"]):
        if option_days >= 10:
            score += 2
        if concessions > 0:
            score -= 2

    score = max(1, min(100, round(score)))
    components = {
        "contractQuality": max(1, min(100, round(score + 8 - len(risks) * 2))),
        "competitiveness": max(1, min(100, round(score - 4 + len(strengths) * 2 - len(risks)))),
        "closingCertainty": max(1, min(100, round(score + 2 - len(risks)))),
        "buyerProtection": max(1, min(100, round(score + 6))),
        "marketFit": max(1, min(100, round(score - 2 if has_public_context else score - 8)))
    }
    return {
        "score": score,
        "summary": "Built-in HomeOfferFlow review completed using Texas resale norms, entered offer terms, and available public property context.",
        "risks": risks[:6],
        "strengths": strengths[:6],
        "marketContext": market[:6],
        "suggestions": suggestions[:5],
        "marketMode": market_mode,
        "components": components,
        "disclaimer": "This is a software-generated educational review, not legal advice, broker advice, a valuation opinion, or a guarantee of acceptance.",
        "source": "rules_fallback",
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
You are collecting PUBLIC real estate listing context for HomeOfferFlow's educational offer-strength review.
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
  "marketMode": "hot/seller" | "balanced" | "buyer/negotiable" | "unknown",
  "marketContext": [string],
  "limitations": [string]
}}

Rules:
- Do not claim MLS-verified unless the source is an authorized MLS/RESO source.
- Prefer public listing facts over general neighborhood fluff.
- If facts conflict or are stale, say confidence is low and include that limitation.
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
                "role": "HomeOfferFlow AI Offer Review",
                "instructions": [
                    "Review a Texas residential resale purchase offer for educational offer-strength feedback.",
                    "Do not provide legal advice, brokerage advice, fiduciary advice, steering, valuation advice, or a guarantee of acceptance.",
                    "Use cautious language: may, commonly, often, consider, confirm, verify.",
                    "Do not say strongest, best, must, should win, or guaranteed unless describing missing required data.",
                    "Adjust the review emphasis by offer.userType.",
                    "For homebuyer userType: make the score and improvement suggestions clear, practical, and central because the user may lack market experience.",
                    "For agent userType: de-emphasize the score; focus on risk review, missing items, consistency checks, and market context because the agent should apply professional judgment.",
                    "For investor userType: de-emphasize the score; focus on deal-term clarity, contingencies, speed, net-to-seller issues, and closing certainty.",
                    "Score 1-100 based on Texas resale contract norms, risk, clarity, and property context, but explain that the score is most useful for self-serve homebuyers.",
                    "Use dynamic market-aware weighting based on supplied public property context when available.",
                    "If property_context.sourceType is public_web_google_grounding, treat it as public listing/search context, not MLS-verified data.",
                    "If public context is low confidence or missing, state that market weighting is limited and do not pretend to know DOM/comps/listing activity.",
                    "When evidence suggests a hotter seller market, weight competitiveness, contingencies, certainty, earnest money, option period, and net-to-seller more heavily.",
                    "When evidence suggests a buyer/negotiable market, weight buyer protection, disclosures, inspections, and negotiated terms more heavily.",
                    "Return components: contractQuality, competitiveness, closingCertainty, buyerProtection, and marketFit as 1-100 integers that explain the score.",
                    "Keep each risk/strength/suggestion under 140 characters when possible."
                ],
                "offer": offer,
                "propertyContext": property_context,
                "rulesFallbackScore": fallback["score"],
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

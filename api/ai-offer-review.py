import os
import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone

import httpx

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
GEMINI_MODEL = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"

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


def _rules_fallback(offer):
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

    score = 55
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
        score -= 5
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
        score -= 12
        risks.append("A sale-of-other-property contingency can materially reduce offer strength.")
        suggestions.append("Confirm the sale contingency is necessary and complete all related deadline fields.")

    if concessions > 0:
        score -= 5
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

    if city or county:
        market.append(f"Property context used: {city + ', ' if city else ''}{county} County. Live MLS/comps data is not included unless connected separately.")
    market.append("This review compares entered terms against Texas resale-contract norms, not live MLS market data.")

    score = max(1, min(100, round(score)))
    components = {
        "contractQuality": max(1, min(100, round(score + 8 - len(risks) * 2))),
        "competitiveness": max(1, min(100, round(score - 4 + len(strengths) * 2 - len(risks)))),
        "closingCertainty": max(1, min(100, round(score + 2 - len(risks)))),
        "buyerProtection": max(1, min(100, round(score + 6))),
        "marketFit": max(1, min(100, round(score - 6)))
    }
    return {
        "score": score,
        "summary": "Built-in HomeOfferFlow review completed using Texas resale norms and the entered offer terms.",
        "risks": risks[:6],
        "strengths": strengths[:6],
        "marketContext": market[:4],
        "suggestions": suggestions[:5],
        "marketMode": "unknown/general Texas resale norms",
        "components": components,
        "disclaimer": "This is a software-generated educational review, not legal advice, broker advice, a valuation opinion, or a guarantee of acceptance.",
        "source": "rules_fallback"
    }


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

            fallback = _rules_fallback(offer)
            if not GEMINI_API_KEY:
                return _json_response(self, 200, {**fallback, "source": "rules_fallback_no_api_key"})

            prompt = {
                "role": "HomeOfferFlow AI Offer Review",
                "instructions": [
                    "Review a Texas residential resale purchase offer for educational offer-strength feedback.",
                    "Do not provide legal advice, brokerage advice, fiduciary advice, steering, or a guarantee of acceptance.",
                    "Use cautious language: may, commonly, often, consider, confirm, verify.",
                    "Do not say strongest, best, must, should win, or guaranteed unless describing missing required data.",
                    "Score 1-100 based on Texas resale contract norms, risk, clarity, and limited property context.",
                    "Use dynamic market-aware weighting. If no live MLS/comps/DOM/list-price data is supplied, use marketMode='unknown/general Texas resale norms'.",
                    "When the property appears to be in a hotter seller market, weight competitiveness, contingencies, certainty, earnest money, option period, and net-to-seller more heavily.",
                    "When the property appears to be in a buyer market, weight buyer protection, disclosures, inspections, and negotiated terms more heavily.",
                    "If actual live market data is not provided, do not pretend to know it; explain that live market weighting improves when MLS/comps/DOM/list-price data is connected.",
                    "Return components: contractQuality, competitiveness, closingCertainty, buyerProtection, and marketFit as 1-100 integers that explain the score.",
                    "Keep each risk/strength/suggestion under 140 characters when possible."
                ],
                "offer": offer,
                "rulesFallbackScore": fallback["score"],
                "reviewDateUtc": datetime.now(timezone.utc).isoformat()
            }

            request_body = {
                "contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
                "generationConfig": {
                    "temperature": 0.25,
                    "topP": 0.9,
                    "maxOutputTokens": 1400,
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

            score = int(review.get("score") or fallback["score"])
            review["score"] = max(1, min(100, score))
            comps = review.get("components") or {}
            clean_comps = {}
            for key in ["contractQuality", "competitiveness", "closingCertainty", "buyerProtection", "marketFit"]:
                try:
                    clean_comps[key] = max(1, min(100, int(comps.get(key, review["score"]))))
                except Exception:
                    clean_comps[key] = review["score"]
            review["components"] = clean_comps
            review["marketMode"] = review.get("marketMode") or "unknown/general Texas resale norms"
            review["source"] = "gemini"
            review["model"] = GEMINI_MODEL
            return _json_response(self, 200, review)
        except Exception as exc:
            return _json_response(self, 500, {"error": str(exc)[:500]})

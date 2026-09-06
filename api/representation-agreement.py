"""Generate the TXR 1507 buyer/tenant representation short-form packet."""

import json
import os
import re
from http.server import BaseHTTPRequestHandler

from api.representation_agreement import SHORT_FORM, build_short_form, send_short_form_signature_request
from api.representation_long_form import LONG_FORM, build_long_form, send_long_form_signature_request


REQUIRED_FIELDS = ("clientName", "brokerName", "marketArea", "startDate", "endDate")
SIGNWELL_API_KEY = os.environ.get("SIGNWELL_API_KEY", "")
SIGNWELL_ENABLED = os.environ.get("SIGNWELL_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
SIGNWELL_TEST_MODE = os.environ.get("SIGNWELL_TEST_MODE", "false").strip().lower() not in {"0", "false", "no", "off"}


class handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self):
        self._json(200, {
            "status": "ok",
            "form": "TXR 1507 Residential Buyer/Tenant Representation Agreement - Short Form",
            "source_available": SHORT_FORM.is_file(),
            "detailed_source_available": LONG_FORM.is_file(),
            "signature_requests_enabled": SIGNWELL_ENABLED and bool(SIGNWELL_API_KEY),
            "signwell_test_mode": SIGNWELL_TEST_MODE,
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(data, dict):
                raise ValueError("Agreement details must be an object")
            missing = [field for field in REQUIRED_FIELDS if not str(data.get(field) or "").strip()]
            if missing:
                self._json(400, {"error": "Missing required agreement details", "fields": missing})
                return
            detailed = data.get("agreementFormat") == "detailed"
            packet = build_long_form(data) if detailed else build_short_form(data)
            if data.get("action") == "signature_request":
                if not SIGNWELL_ENABLED:
                    self._json(503, {"error": "Signature requests are not enabled"})
                    return
                sender = send_long_form_signature_request if detailed else send_short_form_signature_request
                result = sender(data, packet, SIGNWELL_API_KEY, test_mode=SIGNWELL_TEST_MODE)
                self._json(200, result)
                return
            safe_client = re.sub(r"[^A-Za-z0-9]+", "_", str(data["clientName"])).strip("_") or "client"
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            form_name = "Detailed_Representation_Agreement" if detailed else "Representation_Agreement"
            self.send_header("Content-Disposition", f'attachment; filename="HomeOfferFlow_{form_name}_{safe_client}.pdf"')
            self.send_header("Content-Length", str(len(packet)))
            self.end_headers()
            self.wfile.write(packet)
        except ValueError as error:
            self._json(400, {"error": str(error)})
        except Exception as error:
            print("REPRESENTATION AGREEMENT ERROR:", str(error))
            self._json(500, {"error": "Could not prepare the representation agreement"})

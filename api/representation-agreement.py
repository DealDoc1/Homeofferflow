"""Generate the TXR 1507 buyer/tenant representation short-form packet."""

import json
import re
from http.server import BaseHTTPRequestHandler

from api.representation_agreement import SHORT_FORM, build_short_form


REQUIRED_FIELDS = ("clientName", "brokerName", "marketArea", "startDate", "endDate")


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
            "signature_requests_enabled": False,
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
            packet = build_short_form(data)
            safe_client = re.sub(r"[^A-Za-z0-9]+", "_", str(data["clientName"])).strip("_") or "client"
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'attachment; filename="HomeOfferFlow_Representation_Agreement_{safe_client}.pdf"')
            self.send_header("Content-Length", str(len(packet)))
            self.end_headers()
            self.wfile.write(packet)
        except ValueError as error:
            self._json(400, {"error": str(error)})
        except Exception as error:
            print("REPRESENTATION AGREEMENT ERROR:", str(error))
            self._json(500, {"error": "Could not prepare the representation agreement"})

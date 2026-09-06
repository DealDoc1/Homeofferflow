"""Prepare the TXR 1508 neutral showing form for a scheduled property visit."""

import json
import re
from http.server import BaseHTTPRequestHandler

from api.unrepresented_showing import SHOWING_FORM, build_showing_form


REQUIRED_FIELDS = ("propertyAddress", "customerName", "brokerName", "associateName")


class handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self):
        self._json(200, {
            "status": "ok",
            "form": "TXR 1508 Unrepresented Customer Showing Form",
            "source_available": SHOWING_FORM.is_file(),
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(data, dict):
                raise ValueError("Showing details must be an object")
            missing = [field for field in REQUIRED_FIELDS if not str(data.get(field) or "").strip()]
            if missing:
                self._json(400, {"error": "Missing required showing details", "fields": missing})
                return
            packet = build_showing_form(data)
            safe_address = re.sub(r"[^A-Za-z0-9]+", "_", str(data["propertyAddress"])).strip("_") or "property"
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'attachment; filename="HomeOfferFlow_Unrepresented_Showing_{safe_address}.pdf"')
            self.send_header("Content-Length", str(len(packet)))
            self.end_headers()
            self.wfile.write(packet)
        except ValueError as error:
            self._json(400, {"error": str(error)})
        except Exception as error:
            print("UNREPRESENTED SHOWING FORM ERROR:", str(error))
            self._json(500, {"error": "Could not prepare the showing form"})

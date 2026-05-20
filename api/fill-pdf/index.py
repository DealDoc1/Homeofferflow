import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._json(200, {"status": "fill-pdf endpoint working"})

    def do_POST(self):
        self._json(200, {
            "status": "received",
            "message": "Webhook received. Next step is restoring full PDF/SignWell logic."
        })

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

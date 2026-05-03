#!/usr/bin/env python3
"""Tiny HTTP healthcheck server for Railway.

Binds to $PORT (Railway sets this for services with a network domain)
and returns 200 OK on any GET request. Hermes itself is a Telegram-
polling bot with no native HTTP server; this exists purely to satisfy
Railway's healthcheck step during deploy verification.

Spawned as a background process by docker/entrypoint.sh.
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8080"))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Respond 200 to any path so Railway's healthcheck succeeds
        # regardless of which path the operator configured.
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok\n")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        # Silence access log noise — healthcheck pings every few seconds.
        pass


def main():
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    except OSError as e:
        print(f"[healthcheck] FATAL: cannot bind 0.0.0.0:{PORT}: {e}",
              file=sys.stderr, flush=True)
        sys.exit(1)
    print(f"[healthcheck] listening on 0.0.0.0:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

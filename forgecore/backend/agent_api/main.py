"""Agent API module.
Provides simple API endpoints for other services or agents.
"""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from ...config.config import POOL


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()


def run_server(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Serving on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent API test harness")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on")
    args = parser.parse_args()

    run_server(args.port)

"""Stdlib-only HTTP listener that plays the part of Dragos's canary
collector. It logs every GET to /canary/<token> with a timestamp, the
source address, and the user agent, then gets out of the way.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HITS_LOCK = threading.Lock()


def make_handler(hits: list):
    class CanaryHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/canary/"):
                token = self.path.split("/canary/", 1)[1]
                with HITS_LOCK:
                    hits.append(
                        {
                            "token": token,
                            "hit_at": time.time(),
                            "source": self.client_address[0],
                            "user_agent": self.headers.get("User-Agent", ""),
                        }
                    )
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, fmt, *args):
            return  # keep demo output readable; hits are tracked in `hits`

    return CanaryHandler


def start_server(port: int = 8743):
    hits: list = []
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(hits))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, hits


def dump_hits(hits: list, path: str = "canary_hits.jsonl"):
    with open(path, "w") as f:
        for hit in hits:
            f.write(json.dumps(hit) + "\n")

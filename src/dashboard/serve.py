"""Serve the HTML dashboard locally, with caching turned off so a rebuilt page or data file is always picked up.

    uv run python src/dashboard/serve.py [--port 8000]      # then open http://127.0.0.1:8000

Plain `python -m http.server` sends no Cache-Control header, so browsers cache the ES modules heuristically and can
mix an old module with a new one after an edit (a chart module from yesterday with today's shell). This server sends
`Cache-Control: no-cache` on every response: the browser keeps its copy but revalidates it each load (a 304 when
nothing changed), so what you see is always what is on disk. It binds to 127.0.0.1 only.
"""

from __future__ import annotations

import argparse
import functools
import http.server
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "dashboard"


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript", ".json": "application/json"}

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    handler = functools.partial(NoCacheHandler, directory=str(DASHBOARD))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as httpd:
        print(f"Serving {DASHBOARD} at http://127.0.0.1:{args.port} (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

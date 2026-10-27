"""
Lightweight HTTP Server for N-Queens Web Application.
Built entirely using Python's standard library (no third-party dependencies).

Features:
- Serves the frontend from the 'web/' directory.
- Provides '/api/search' endpoint to run the real Python AI algorithms and stream events to the browser.
- Automatically selects an available port (default 8000) and opens the browser.
"""

import http.server
import json
import os
import socketserver
import sys
import urllib.parse
import webbrowser
from typing import Any, Dict, List

from algorithms.astar import astar_generator
from algorithms.csp import csp_generator
from algorithms.hill_climbing import (
    simple_hill_climbing_generator,
    steepest_hill_climbing_generator,
)


WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class NQueensRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handles static files and API requests for N-Queens search."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self) -> None:
        # Enable CORS for local convenience
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            algo = query_params.get("algorithm", ["simple_hc"])[0].lower()
            try:
                n = int(query_params.get("n", ["4"])[0])
            except ValueError:
                n = 4

            seed_val = query_params.get("seed", [None])[0]
            seed = int(seed_val) if seed_val and seed_val.isdigit() else None

            self._handle_search(algo, n, seed)
            return

        # Redirect root to index.html
        if parsed_url.path in ("", "/"):
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path == "/api/search":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}

            algo = data.get("algorithm", "simple_hc").lower()
            try:
                n = int(data.get("n", 4))
            except (ValueError, TypeError):
                n = 4

            seed = data.get("seed", None)
            if seed is not None:
                try:
                    seed = int(seed)
                except (ValueError, TypeError):
                    seed = None

            self._handle_search(algo, n, seed)
            return

        super().do_GET()

    def _handle_search(self, algo: str, n: int, seed: Any) -> None:
        """Executes the chosen algorithm generator and sends JSON response."""
        if n <= 0:
            self._send_json({"success": False, "error": "Board size N must be positive (N >= 1)."}, status=400)
            return

        events: List[Dict[str, Any]] = []
        algo_title = ""

        try:
            if algo in ("simple_hc", "simple hill climbing", "simple"):
                algo_title = "Simple Hill Climbing"
                gen = simple_hill_climbing_generator(n=n, max_restarts=50, max_steps_per_restart=200, random_seed=seed)
            elif algo in ("steepest_hc", "steepest hill climbing", "steepest", "steepest-ascent hill climbing"):
                algo_title = "Steepest-Ascent Hill Climbing"
                gen = steepest_hill_climbing_generator(n=n, max_restarts=50, max_steps_per_restart=200, random_seed=seed)
            elif algo in ("astar", "a*", "a* search"):
                algo_title = "A* Search"
                max_nodes = 50_000 if n > 8 else 100_000
                gen = astar_generator(n=n, max_nodes=max_nodes)
            elif algo in ("csp", "csp backtracking", "backtracking"):
                algo_title = "CSP Backtracking"
                gen = csp_generator(n=n)
            else:
                self._send_json({"success": False, "error": f"Unknown algorithm: '{algo}'"}, status=400)
                return

            # Collect discrete search events
            for event in gen:
                events.append(event.to_dict())

            response_data = {
                "success": True,
                "algorithm": algo_title,
                "n": n,
                "total_events": len(events),
                "events": events,
            }
            self._send_json(response_data)

        except Exception as err:
            self._send_json({"success": False, "error": str(err)}, status=500)

    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run_server(port: int = 8000, auto_open: bool = True) -> None:
    """Starts the HTTP server and opens the browser."""
    # Try finding an open port if default is in use
    server = None
    for p in range(port, port + 20):
        try:
            server = socketserver.TCPServer(("", p), NQueensRequestHandler)
            port = p
            break
        except OSError:
            continue

    if not server:
        print(f"Error: Could not bind to any port in range {port}-{port+20}.")
        sys.exit(1)

    url = f"http://localhost:{port}"
    print("=" * 68)
    print("  N-QUEENS INTERACTIVE SEARCH VISUALIZER (CLASSROOM WEB APP)")
    print("=" * 68)
    print(f"  Web application running at: {url}")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 68)

    if auto_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    port_arg = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port_arg = int(sys.argv[1])
    run_server(port=port_arg)

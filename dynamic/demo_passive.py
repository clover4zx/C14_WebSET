"""
demo_passive.py

Self-contained test for the passive scanner. Since we can't (and
shouldn't) point WebSET at an arbitrary real website for a demo, this
spins up a tiny local HTTP server serving a synthetic "vulnerable" page -
deliberately containing an outdated jQuery reference, a hardcoded API key
in an inline script, an eval() call, a form that submits over HTTP without
a CSRF-looking field, and a link to an untrusted third-party domain - and
scans it with PassiveScanner, the same way you'd point it at DVWA or
Juice Shop.

Run with (from the repo root):
    python -m dynamic.demo_passive

Or just right-click this file in PyCharm and choose Run.
"""

import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from pathlib import Path

try:
    from .passive_scanner import PassiveScanner
    from .scan_profile import ScanProfile
    from .console_report import print_report
except ImportError:
    from passive_scanner import PassiveScanner
    from scan_profile import ScanProfile
    from console_report import print_report

PROFILE_PATH = Path(__file__).parent / "scan_profile_example.yaml"

VULNERABLE_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Demo Vulnerable Site</title>
    <script src="/static/jquery-1.12.4.min.js"></script>
</head>
<body>
    <h1>Welcome</h1>

    <script>
        var API_KEY = "demo_key_abcdefghijklmnop1234";
        function loadWidget(userInput) {
            eval(userInput);  // deliberately unsafe for demo purposes
        }
    </script>

    <form action="http://127.0.0.1:8000/login" method="post">
        <input type="text" name="username">
        <input type="password" name="password">
        <button type="submit">Login</button>
    </form>

    <p>Check out our partner: <a href="https://totally-unrelated-promo-site.com/promo">
    special offer</a></p>

    <p>Internal status page: internal-dash01.corp.local</p>
</body>
</html>
"""


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(VULNERABLE_PAGE.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # keep test output quiet


def main():
    server = HTTPServer(("127.0.0.1", 8000), DemoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)  # give the server a moment to be ready

    try:
        profile = ScanProfile.load(str(PROFILE_PATH))
        scanner = PassiveScanner(profile)
        report = scanner.scan("http://127.0.0.1:8000/")
        print_report(report)

        print("\n--- Raw summary ---")
        print(report["summary"], "total:", report["total_findings"])
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()

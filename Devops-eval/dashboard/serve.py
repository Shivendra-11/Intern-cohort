#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

PORT = 5173
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
ROOT = os.path.dirname(DIRECTORY)
TASK_FOLDERS = [
    "d1-terraform",
    "d2-compose-stack",
    "d3-ci-pipeline",
    "d4-kubernetes",
    "d5-dev-env",
    "d6-observability",
]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        path = self.translate_path(self.path)
        if not os.path.exists(path) and "." not in os.path.basename(path):
            self.path = "/index.html"
        return super().do_GET()


def ensure_report_symlinks():
    reports_dir = os.path.join(DIRECTORY, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    for folder in TASK_FOLDERS:
        target = os.path.join(ROOT, folder)
        link = os.path.join(reports_dir, folder)
        if os.path.islink(link) or os.path.exists(link):
            continue
        try:
            os.symlink(target, link)
        except OSError as exc:
            print(f"Warning: could not link {folder}: {exc}")


if __name__ == "__main__":
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory {DIRECTORY} does not exist. Run 'npm run build' first.")
        sys.exit(1)

    ensure_report_symlinks()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving dashboard from built assets at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server.")

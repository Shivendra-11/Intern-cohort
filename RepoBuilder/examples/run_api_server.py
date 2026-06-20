#!/usr/bin/env python3
"""Example: start dashboard API on localhost:8000."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.api_server import main  # noqa: E402


if __name__ == "__main__":
    dashboard = os.path.join(ROOT, "workspace", "py_app", "dashboard_data.json")
    argv = [f"--dashboard={dashboard}"] + sys.argv[1:]
    raise SystemExit(main(argv))

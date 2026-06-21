#!/usr/bin/env python3
"""B2 — API endpoint & frontend route map.

Detects externally exposed HTTP routes (backend frameworks) and client-side
routes (frontend frameworks), reporting METHOD + path + handler + file:line.

Backend coverage: FastAPI, Flask, Express, NestJS, Spring (MVC), Django urls.
Frontend coverage: React Router, Vue Router, Next.js file routing.

Stdlib-only, regex-based, best-effort.

Usage:
  python3 endpoints.py <repo_path> [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (
    detect,  # noqa: E402
    route_dedupe,  # noqa: E402
)

HTTP_METHODS = "get|post|put|patch|delete|head|options"

# --- backend patterns: each yields (method, path) -----------------------------
# FastAPI / Flask blueprint-style: @app.get("/x") / @router.post("/x") / @bp.route("/x", methods=[...])
PY_DECORATOR = re.compile(
    r"@(?:\w+)\.(" + HTTP_METHODS + r")\(\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
PY_FLASK_ROUTE = re.compile(
    r"@(?:\w+)\.route\(\s*[\"']([^\"']+)[\"'](?:.*?methods\s*=\s*\[([^\]]*)\])?", re.IGNORECASE | re.DOTALL)

# Express / Nest functional: app.get('/x'), router.post('/x')
JS_ROUTER = re.compile(
    r"\b(?:app|router|api)\.(" + HTTP_METHODS + r")\(\s*[`\"']([^`\"']+)[`\"']", re.IGNORECASE)
# NestJS decorators: @Get('x') on a method, with @Controller('prefix') on the class.
NEST_METHOD = re.compile(r"@(" + HTTP_METHODS + r")\(\s*[`\"']?([^`\"')]*)[`\"']?\s*\)", re.IGNORECASE)
NEST_CONTROLLER = re.compile(r"@Controller\(\s*[`\"']?([^`\"')]*)[`\"']?\s*\)")

# Spring: @GetMapping("/x"), @RequestMapping(value="/x", method=RequestMethod.GET)
SPRING_MAPPING = re.compile(r"@(Get|Post|Put|Patch|Delete)Mapping\(\s*(?:value\s*=\s*)?[\"']?([^\"')]*)[\"']?")
SPRING_REQ_CLASS = re.compile(r"@RequestMapping\(\s*(?:value\s*=\s*)?[\"']?([^\"',)]*)")

# Django: path('x/', view) / re_path(r'^x$', view) / url(...)
DJANGO_PATH = re.compile(r"\b(?:path|re_path|url)\(\s*[r]?[\"']([^\"']*)[\"']\s*,\s*([\w\.]+)")

# --- frontend patterns --------------------------------------------------------
REACT_ROUTE = re.compile(r"<Route\b[^>]*\bpath\s*=\s*[\"'{]([^\"'}]+)")
VUE_ROUTE = re.compile(r"\bpath\s*:\s*[\"']([^\"']+)[\"']")


def join_path(prefix, suffix):
    prefix = (prefix or "").strip("/")
    suffix = (suffix or "").strip("/")
    combined = "/".join(p for p in (prefix, suffix) if p)
    return "/" + combined if combined else "/"


def scan_python(path, lines, rel_path, api):
    for idx, line in enumerate(lines):
        m = PY_DECORATOR.search(line)
        if m:
            handler = next_def_name(lines, idx)
            api.append(_ep(m.group(1).upper(), m.group(2), handler, rel_path, idx + 1, "FastAPI/Flask"))
            continue
        fm = PY_FLASK_ROUTE.search(line)
        if fm:
            methods = fm.group(2)
            method_list = re.findall(r"[\"'](\w+)[\"']", methods) if methods else ["GET"]
            handler = next_def_name(lines, idx)
            for meth in method_list:
                api.append(_ep(meth.upper(), fm.group(1), handler, rel_path, idx + 1, "Flask"))
        dm = DJANGO_PATH.search(line)
        if dm and ("urls" in rel_path.lower()):
            api.append(_ep("ANY", "/" + dm.group(1).lstrip("/"), dm.group(2), rel_path, idx + 1, "Django"))


def scan_js(path, lines, rel_path, api):
    controller_prefix = ""
    for idx, line in enumerate(lines):
        cm = NEST_CONTROLLER.search(line)
        if cm:
            controller_prefix = cm.group(1)
        rm = JS_ROUTER.search(line)
        if rm:
            api.append(_ep(rm.group(1).upper(), rm.group(2), "(inline)", rel_path, idx + 1, "Express"))
            continue
        nm = NEST_METHOD.search(line)
        if nm and "@Controller" not in line:
            handler = next_def_name(lines, idx, js=True)
            full = join_path(controller_prefix, nm.group(2))
            api.append(_ep(nm.group(1).upper(), full, handler, rel_path, idx + 1, "NestJS"))


def scan_java(path, lines, rel_path, api):
    class_prefix = ""
    for idx, line in enumerate(lines):
        cm = SPRING_REQ_CLASS.search(line)
        if cm and ("class " in "\n".join(lines[idx:idx + 3]) or idx + 1 < len(lines)):
            class_prefix = cm.group(1)
        mm = SPRING_MAPPING.search(line)
        if mm:
            handler = next_java_method(lines, idx)
            full = join_path(class_prefix, mm.group(2))
            api.append(_ep(mm.group(1).upper(), full, handler, rel_path, idx + 1, "Spring"))


def scan_frontend(path, lines, rel_path, routes):
    is_vue_router = "router" in rel_path.lower() and rel_path.endswith((".js", ".ts"))
    for idx, line in enumerate(lines):
        rm = REACT_ROUTE.search(line)
        if rm:
            routes.append(_ep("VIEW", rm.group(1), "(component)", rel_path, idx + 1, "React Router"))
        if is_vue_router:
            vm = VUE_ROUTE.search(line)
            if vm:
                routes.append(_ep("VIEW", vm.group(1), "(component)", rel_path, idx + 1, "Vue Router"))


def scan_nextjs_files(root, routes):
    """Next.js routes the filesystem into URLs under pages/ or app/."""
    for path in detect.walk_files(root):
        rel_path = detect.rel(path, root)
        low = rel_path.replace(os.sep, "/").lower()
        base = os.path.basename(low)
        if not base.endswith((".js", ".jsx", ".ts", ".tsx")):
            continue
        for marker in ("pages/", "app/"):
            if marker in low:
                sub = low.split(marker, 1)[1]
                sub = re.sub(r"\.(js|jsx|ts|tsx)$", "", sub)
                if base.startswith(("page.", "route.")):
                    sub = sub.rsplit("/", 1)[0]
                if sub.endswith("index"):
                    sub = sub[:-5]
                if "_app" in sub or "_document" in sub or "components/" in sub:
                    continue
                url = "/" + sub.strip("/")
                routes.append(_ep("VIEW", url or "/", "(page)", rel_path, 1, "Next.js"))
                break


def next_def_name(lines, idx, js=False):
    for j in range(idx + 1, min(idx + 4, len(lines))):
        if js:
            m = re.search(r"\b(\w+)\s*\(", lines[j])
        else:
            m = re.search(r"def\s+(\w+)", lines[j])
        if m:
            return m.group(1)
    return "(handler)"


def next_java_method(lines, idx):
    for j in range(idx + 1, min(idx + 4, len(lines))):
        m = re.search(r"\b\w[\w<>\[\]]*\s+(\w+)\s*\(", lines[j])
        if m:
            return m.group(1)
    return "(handler)"


def _ep(method, path, handler, file, line, framework):
    if not path.startswith("/"):
        path = "/" + path
    return {"method": method.upper(), "path": path, "handler": handler,
            "file": file, "line": line, "framework": framework}


def build_routes(root):
    api, frontend = [], []
    for path, lang in detect.source_files(root):
        lines = detect.read_lines(path)
        rel_path = detect.rel(path, root)
        if lang == "python":
            scan_python(path, lines, rel_path, api)
        elif lang in ("javascript", "typescript"):
            scan_js(path, lines, rel_path, api)
            scan_frontend(path, lines, rel_path, frontend)
        elif lang in ("java", "kotlin"):
            scan_java(path, lines, rel_path, api)
    scan_nextjs_files(root, frontend)
    api = route_dedupe.dedupe_backend(dedupe(api))
    frontend = route_dedupe.dedupe_frontend(dedupe(frontend))
    return api, frontend


def dedupe(items):
    seen, out = set(), []
    for it in items:
        key = (it["method"], it["path"], it["file"], it["line"])
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return sorted(out, key=lambda x: (x["path"], x["method"]))


def print_table(api, frontend):
    print(f"API endpoints ({len(api)}):\n")
    if api:
        for e in api:
            print(f"  {e['method']:7} {e['path']:35} {e['handler']:20} {e['file']}:{e['line']}  [{e['framework']}]")
    else:
        print("  (none detected)")
    print(f"\nFrontend routes ({len(frontend)}):\n")
    if frontend:
        for e in frontend:
            print(f"  {e['method']:7} {e['path']:35} {e['file']}:{e['line']}  [{e['framework']}]")
    else:
        print("  (none detected)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="B2 API + frontend route map")
    ap.add_argument("repo")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.repo):
        print(f"error: not a directory: {args.repo}", file=sys.stderr)
        return 2
    api, frontend = build_routes(args.repo)
    if args.json:
        print(json.dumps({
            "repo": os.path.abspath(args.repo),
            "counts": {"api": len(api), "frontend": len(frontend)},
            "api": api, "frontend": frontend,
        }, indent=2))
    else:
        print_table(api, frontend)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

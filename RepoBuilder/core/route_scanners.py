"""Regex and AST route scanners for backend and frontend frameworks."""
from __future__ import annotations

import os
import re

from core.file_scanner import FileScanner
from core.route_ast import AstRoute, parse_routes_ast
from core.route_dedupe import dedupe_backend_routes, dedupe_frontend_routes

HTTP_METHODS = "get|post|put|patch|delete|head|options"

PY_DECORATOR = re.compile(
    rf"@(?:\w+)\.({HTTP_METHODS})\(\s*[\"']([^\"']+)[\"']", re.IGNORECASE
)
PY_FLASK_ROUTE = re.compile(
    r"@(?:\w+)\.route\(\s*[\"']([^\"']+)[\"'](?:.*?methods\s*=\s*\[([^\]]*)\])?",
    re.IGNORECASE | re.DOTALL,
)
JS_ROUTER = re.compile(
    rf"\b(?:app|router|api)\.({HTTP_METHODS})\(\s*[`\"']([^`\"']+)[`\"']", re.IGNORECASE
)
NEST_METHOD = re.compile(
    rf"@({HTTP_METHODS})\(\s*[`\"']?([^`\"')]*)[`\"']?\s*\)", re.IGNORECASE
)
NEST_CONTROLLER = re.compile(r"@Controller\(\s*[`\"']?([^`\"')]*)[`\"']?\s*\)")
SPRING_MAPPING = re.compile(
    r"@(Get|Post|Put|Patch|Delete)Mapping\(\s*(?:value\s*=\s*)?[\"']?([^\"')]*)[\"']?"
)
SPRING_REQ_CLASS = re.compile(r"@RequestMapping\(\s*(?:value\s*=\s*)?[\"']?([^\"',)]*)")

REACT_ROUTE = re.compile(r"<Route\b[^>]*\bpath\s*=\s*[\"'{]([^\"'}]+)")
CREATE_BROWSER_ROUTER = re.compile(r"createBrowserRouter\s*\(\s*\[", re.IGNORECASE)
USE_ROUTES = re.compile(r"useRoutes\s*\(\s*\[", re.IGNORECASE)
ROUTE_OBJECT_PATH = re.compile(r"\bpath\s*:\s*[\"']([^\"']+)[\"']")


def join_path(prefix: str, suffix: str) -> str:
    prefix = (prefix or "").strip("/")
    suffix = (suffix or "").strip("/")
    combined = "/".join(p for p in (prefix, suffix) if p)
    return "/" + combined if combined else "/"


def normalize_path(path: str) -> str:
    path = path.strip().strip("'\"`")
    if not path.startswith("/"):
        path = "/" + path
    return path or "/"


def _with_file(routes: list[AstRoute], rel_file: str) -> list[AstRoute]:
    return [
        AstRoute(
            method=r.method,
            path=r.path,
            line=r.line,
            framework=r.framework,
            file=rel_file,
            handler=r.handler,
        )
        for r in routes
    ]


def scan_repo(repo_path: str) -> tuple[list[AstRoute], list[AstRoute]]:
    """Return (backend_routes, frontend_routes) for a repository."""
    scanner = FileScanner()
    backend: list[AstRoute] = []
    frontend: list[AstRoute] = []

    for abs_path, lang in scanner.iter_source_files(repo_path):
        rel = os.path.relpath(abs_path, repo_path)
        found: list[AstRoute] = list(_regex_backend(abs_path, lang, rel, scanner))
        ast_routes = parse_routes_ast(abs_path, lang)
        if ast_routes:
            found.extend(_with_file(ast_routes, rel))
        backend.extend(found)

        if lang in ("javascript", "typescript"):
            frontend.extend(_with_file(_scan_frontend_file(abs_path, rel, scanner), rel))

    return dedupe_backend_routes(backend), dedupe_frontend_routes(frontend)


def _regex_backend(
    path: str, lang: str, rel_path: str, scanner: FileScanner
) -> list[AstRoute]:
    lines = scanner.read_lines(path)
    routes: list[AstRoute] = []
    controller_prefix = ""
    class_prefix = ""

    for idx, line in enumerate(lines):
        if lang == "python":
            m = PY_DECORATOR.search(line)
            if m:
                routes.append(
                    AstRoute(
                        m.group(1).upper(),
                        normalize_path(m.group(2)),
                        idx + 1,
                        "FastAPI",
                        rel_path,
                        _next_py_handler(lines, idx),
                    )
                )
                continue
            fm = PY_FLASK_ROUTE.search(line)
            if fm:
                methods = fm.group(2)
                method_list = re.findall(r"[\"'](\w+)[\"']", methods) if methods else ["GET"]
                for meth in method_list:
                    routes.append(
                        AstRoute(
                            meth.upper(),
                            normalize_path(fm.group(1)),
                            idx + 1,
                            "Flask",
                            rel_path,
                            _next_py_handler(lines, idx),
                        )
                    )
        elif lang in ("javascript", "typescript"):
            cm = NEST_CONTROLLER.search(line)
            if cm:
                controller_prefix = cm.group(1)
            rm = JS_ROUTER.search(line)
            if rm:
                routes.append(
                    AstRoute(
                        rm.group(1).upper(),
                        normalize_path(rm.group(2)),
                        idx + 1,
                        "Express",
                        rel_path,
                        "(inline)",
                    )
                )
                continue
            nm = NEST_METHOD.search(line)
            if nm and "@Controller" not in line:
                routes.append(
                    AstRoute(
                        nm.group(1).upper(),
                        normalize_path(join_path(controller_prefix, nm.group(2))),
                        idx + 1,
                        "NestJS",
                        rel_path,
                        _next_js_handler(lines, idx),
                    )
                )
        elif lang in ("java", "kotlin"):
            cm = SPRING_REQ_CLASS.search(line)
            if cm:
                class_prefix = cm.group(1)
            sm = SPRING_MAPPING.search(line)
            if sm:
                routes.append(
                    AstRoute(
                        sm.group(1).upper(),
                        normalize_path(join_path(class_prefix, sm.group(2))),
                        idx + 1,
                        "Spring Boot",
                        rel_path,
                        _next_java_handler(lines, idx),
                    )
                )
    return routes


def _scan_frontend_file(path: str, rel_path: str, scanner: FileScanner) -> list[AstRoute]:
    lines = scanner.read_lines(path)
    content = "\n".join(lines)
    routes: list[AstRoute] = []

    for idx, line in enumerate(lines):
        rm = REACT_ROUTE.search(line)
        if rm:
            routes.append(
                AstRoute("VIEW", normalize_path(rm.group(1)), idx + 1, "React Router", rel_path)
            )

    if CREATE_BROWSER_ROUTER.search(content) or USE_ROUTES.search(content):
        framework = (
            "createBrowserRouter"
            if CREATE_BROWSER_ROUTER.search(content)
            else "useRoutes"
        )
        for idx, line in enumerate(lines):
            pm = ROUTE_OBJECT_PATH.search(line)
            if pm:
                routes.append(
                    AstRoute(
                        "VIEW",
                        normalize_path(pm.group(1)),
                        idx + 1,
                        framework,
                        rel_path,
                    )
                )

    return routes


def _next_py_handler(lines: list[str], idx: int) -> str:
    for j in range(idx + 1, min(idx + 4, len(lines))):
        m = re.search(r"def\s+(\w+)", lines[j])
        if m:
            return m.group(1)
    return "(handler)"


def _next_js_handler(lines: list[str], idx: int) -> str:
    for j in range(idx + 1, min(idx + 4, len(lines))):
        m = re.search(r"\b(\w+)\s*\(", lines[j])
        if m:
            return m.group(1)
    return "(handler)"


def _next_java_handler(lines: list[str], idx: int) -> str:
    for j in range(idx + 1, min(idx + 4, len(lines))):
        m = re.search(r"\b\w[\w<>\[\]]*\s+(\w+)\s*\(", lines[j])
        if m:
            return m.group(1)
    return "(handler)"


def dedupe_routes(routes: list[AstRoute]) -> list[AstRoute]:
    """Exact dedupe by file+line; prefer canonical_dedupe for cross-file collisions."""
    seen = set()
    out: list[AstRoute] = []
    for r in sorted(routes, key=lambda x: (x.path, x.method, x.file, x.line)):
        key = (r.method, r.path, r.file, r.line, r.framework)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

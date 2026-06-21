"""Tree-sitter route extraction for backend decorators and Express-style calls."""
from __future__ import annotations

import re
from dataclasses import dataclass

from core.file_scanner import FileScanner
from core.inventory_ast import _PARSERS, _init_parsers, _node_text, _walk

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}

_PY_DECORATOR = re.compile(
    r"@\w+\.(get|post|put|patch|delete|head|options)\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
_PY_FLASK = re.compile(
    r"@\w+\.route\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
_JS_MEMBER = re.compile(
    r"\b(\w+)\.(get|post|put|patch|delete|head|options)\(\s*[`'\"]([^`'\"]+)[`'\"]",
    re.IGNORECASE,
)
_NEST_METHOD = re.compile(
    r"@(Get|Post|Put|Patch|Delete|Head|Options)\(\s*[`'\"]?(.*?)[`'\"]?\s*\)",
    re.IGNORECASE,
)
_SPRING = re.compile(
    r"@(Get|Post|Put|Patch|Delete)Mapping\(\s*(?:value\s*=\s*)?['\"]?(.*?)['\"]?\s*\)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AstRoute:
    method: str
    path: str
    line: int
    framework: str
    file: str = ""
    handler: str = ""


def parse_routes_ast(path: str, lang: str) -> list[AstRoute] | None:
    """Return routes from tree-sitter walk, or None if parser unavailable."""
    _init_parsers()
    key = "typescript" if lang == "typescript" else lang
    if lang == "javascript":
        key = "javascript"
    if key not in _PARSERS:
        return None

    scanner = FileScanner()
    lines = scanner.read_lines(path)
    if not lines:
        return None

    source = "\n".join(lines).encode("utf-8")
    parser, _ = _PARSERS[key]
    tree = parser.parse(source)
    root = tree.root_node

    if lang == "python":
        return _python_routes(source, root)
    if lang in ("javascript", "typescript"):
        return _js_routes(source, root, lang)
    if lang == "java":
        return _java_routes(source, root)
    return None


def _normalize_path(path: str) -> str:
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    return path or "/"


def _python_routes(source: bytes, root) -> list[AstRoute]:
    routes: list[AstRoute] = []

    def visit(node) -> None:
        if node.type != "decorated_definition":
            return
        dec_texts = [
            _node_text(source, c) for c in node.children if c.type == "decorator"
        ]
        def_node = next(
            (c for c in node.children if c.type in ("function_definition", "async_function_definition")),
            None,
        )
        handler = ""
        if def_node:
            name = def_node.child_by_field_name("name")
            if name:
                handler = _node_text(source, name)
        line = node.start_point[0] + 1
        for dec in dec_texts:
            m = _PY_DECORATOR.search(dec)
            if m:
                routes.append(
                    AstRoute(
                        method=m.group(1).upper(),
                        path=_normalize_path(m.group(2)),
                        line=line,
                        framework="FastAPI",
                        handler=handler,
                    )
                )
                continue
            fm = _PY_FLASK.search(dec)
            if fm:
                routes.append(
                    AstRoute(
                        method="GET",
                        path=_normalize_path(fm.group(1)),
                        line=line,
                        framework="Flask",
                        handler=handler,
                    )
                )

    _walk(root, visit)
    return routes


def _js_routes(source: bytes, root, lang: str) -> list[AstRoute]:
    routes: list[AstRoute] = []
    nest_prefix = ""

    def visit(node) -> None:
        nonlocal nest_prefix
        text = _node_text(source, node)
        if lang == "typescript" and "@Controller" in text:
            cm = re.search(r"@Controller\(\s*[`'\"]?(.*?)[`'\"]?\s*\)", text)
            if cm:
                nest_prefix = cm.group(1)
        if node.type == "call_expression":
            fn = node.child_by_field_name("function")
            if not fn:
                return
            fn_text = _node_text(source, fn)
            m = _JS_MEMBER.search(fn_text)
            if m and node.child_by_field_name("arguments"):
                args = node.child_by_field_name("arguments")
                if args and args.child_count > 0:
                    path_node = args.child(0)
                    path = _node_text(source, path_node).strip("`'\"")
                    routes.append(
                        AstRoute(
                            method=m.group(2).upper(),
                            path=_normalize_path(path),
                            line=node.start_point[0] + 1,
                            framework="Express",
                            handler="(inline)",
                        )
                    )
            nm = _NEST_METHOD.search(text)
            if nm and "@Controller" not in text:
                suffix = nm.group(2) or ""
                full = _join_prefix(nest_prefix, suffix)
                routes.append(
                    AstRoute(
                        method=nm.group(1).upper(),
                        path=_normalize_path(full),
                        line=node.start_point[0] + 1,
                        framework="NestJS",
                        handler="(method)",
                    )
                )

    _walk(root, visit)
    return routes


def _java_routes(source: bytes, root) -> list[AstRoute]:
    routes: list[AstRoute] = []
    class_prefix = ""

    def visit(node) -> None:
        nonlocal class_prefix
        text = _node_text(source, node)
        rm = re.search(
            r"@RequestMapping\(\s*(?:value\s*=\s*)?['\"]?(.*?)['\"]?\s*\)", text
        )
        if rm:
            class_prefix = rm.group(1)
        sm = _SPRING.search(text)
        if sm:
            full = _join_prefix(class_prefix, sm.group(2))
            routes.append(
                AstRoute(
                    method=sm.group(1).upper(),
                    path=_normalize_path(full),
                    line=node.start_point[0] + 1,
                    framework="Spring Boot",
                    handler="(method)",
                )
            )

    _walk(root, visit)
    return routes


def _join_prefix(prefix: str, suffix: str) -> str:
    prefix = (prefix or "").strip("/")
    suffix = (suffix or "").strip("/")
    combined = "/".join(p for p in (prefix, suffix) if p)
    return "/" + combined if combined else "/"

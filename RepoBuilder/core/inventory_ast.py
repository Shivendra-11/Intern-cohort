"""Tree-sitter AST extraction for inventory discovery.

Uses tree-sitter when language grammars are installed; otherwise returns None
so the inventory agent can fall back to regex heuristics.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from core.file_scanner import FileScanner

# Lazy-loaded parsers: lang_key -> (Parser, language_label)
_PARSERS: Dict[str, Tuple[object, str]] = {}
_INIT_ATTEMPTED = False


@dataclass(frozen=True)
class RawDefinition:
    """A syntactic definition extracted from source via AST or regex."""

    name: str
    syntactic_kind: str  # class | interface | function | enum | struct | trait | type
    line: int
    signature: str
    decorators: Tuple[str, ...] = ()


def _node_text(source: bytes, node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _init_parsers() -> None:
    global _INIT_ATTEMPTED
    if _INIT_ATTEMPTED:
        return
    _INIT_ATTEMPTED = True

    try:
        from tree_sitter import Language, Parser
    except ImportError:
        return

    specs = [
        ("python", "tree_sitter_python", "python"),
        ("javascript", "tree_sitter_javascript", "javascript"),
        ("typescript", "tree_sitter_typescript", "typescript"),
        ("java", "tree_sitter_java", "java"),
        ("go", "tree_sitter_go", "go"),
        ("rust", "tree_sitter_rust", "rust"),
    ]
    for key, module_name, lang_attr in specs:
        try:
            mod = __import__(module_name)
            lang_obj = getattr(mod, "language", None)
            if lang_obj is None:
                lang_obj = getattr(mod, lang_attr)
            language = Language(lang_obj() if callable(lang_obj) else lang_obj)
            _PARSERS[key] = (Parser(language), key)
        except Exception:
            continue


def available_parsers() -> List[str]:
    _init_parsers()
    return list(_PARSERS.keys())


def parse_definitions(path: str, lang: str) -> Optional[List[RawDefinition]]:
    """Parse a file with tree-sitter; return None if parser unavailable."""
    _init_parsers()
    parser_key = _lang_to_parser_key(lang)
    if parser_key not in _PARSERS:
        return None

    scanner = FileScanner()
    lines = scanner.read_lines(path)
    if not lines:
        return None

    source = "\n".join(lines).encode("utf-8")
    parser, _ = _PARSERS[parser_key]
    tree = parser.parse(source)
    extractor = _EXTRACTORS.get(parser_key)
    if not extractor:
        return None
    return extractor(source, tree.root_node)


def _lang_to_parser_key(lang: str) -> str:
    if lang == "typescript":
        return "typescript"
    if lang in ("javascript", "typescript"):
        return "javascript"
    return lang


def _walk(node, visit: Callable) -> None:
    visit(node)
    for child in node.children:
        _walk(child, visit)


# --- Python -----------------------------------------------------------------

def _extract_python(source: bytes, root) -> List[RawDefinition]:
    out: List[RawDefinition] = []

    def visit(node) -> None:
        if node.type == "decorated_definition":
            decs = [
                _node_text(source, c)
                for c in node.children
                if c.type == "decorator"
            ]
            for child in node.children:
                if child.type in ("class_definition", "function_definition"):
                    out.extend(_python_def(source, child, decs))
            return
        if node.type in ("class_definition", "function_definition"):
            if node.parent and node.parent.type == "decorated_definition":
                return
            out.extend(_python_def(source, node, ()))

    _walk(root, visit)
    return out


def _python_def(source: bytes, node, decorators: Tuple[str, ...]) -> List[RawDefinition]:
    name_node = node.child_by_field_name("name")
    if not name_node:
        return []
    name = _node_text(source, name_node)
    line = node.start_point[0] + 1
    sig = _node_text(source, node).split("\n", 1)[0][:160]
    kind = "class" if node.type == "class_definition" else "function"
    return [RawDefinition(name=name, syntactic_kind=kind, line=line, signature=sig, decorators=decorators)]


# --- JavaScript / TypeScript ------------------------------------------------

def _extract_js_ts(source: bytes, root, *, is_ts: bool) -> List[RawDefinition]:
    out: List[RawDefinition] = []

    def visit(node) -> None:
        if node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind="class",
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, node).split("\n", 1)[0][:160],
                    )
                )
        elif is_ts and node.type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind="interface",
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, node).split("\n", 1)[0][:160],
                    )
                )
        elif node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind="function",
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, node).split("\n", 1)[0][:160],
                    )
                )
        elif node.type == "lexical_declaration":
            # export const Foo = ...
            for child in node.children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value = child.child_by_field_name("value")
                    if name_node and value and value.type in ("arrow_function", "function"):
                        nm = _node_text(source, name_node)
                        if nm[:1].isupper():
                            out.append(
                                RawDefinition(
                                    name=nm,
                                    syntactic_kind="function",
                                    line=node.start_point[0] + 1,
                                    signature=_node_text(source, child).split("\n", 1)[0][:160],
                                )
                            )

    _walk(root, visit)
    return out


def _extract_javascript(source: bytes, root) -> List[RawDefinition]:
    return _extract_js_ts(source, root, is_ts=False)


def _extract_typescript(source: bytes, root) -> List[RawDefinition]:
    return _extract_js_ts(source, root, is_ts=True)


# --- Java -------------------------------------------------------------------

def _extract_java(source: bytes, root) -> List[RawDefinition]:
    out: List[RawDefinition] = []

    def visit(node) -> None:
        if node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind="class",
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, node).split("\n", 1)[0][:160],
                    )
                )
        elif node.type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind="interface",
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, node).split("\n", 1)[0][:160],
                    )
                )
        elif node.type == "annotation_type_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind="class",
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, node).split("\n", 1)[0][:160],
                        decorators=("@interface",),
                    )
                )

    _walk(root, visit)
    return out


# --- Go ---------------------------------------------------------------------

def _extract_go(source: bytes, root) -> List[RawDefinition]:
    out: List[RawDefinition] = []

    def visit(node) -> None:
        if node.type == "type_declaration":
            for spec in node.children:
                if spec.type != "type_spec":
                    continue
                name_node = spec.child_by_field_name("name")
                type_node = spec.child_by_field_name("type")
                if not name_node or not type_node:
                    continue
                kind = "class" if type_node.type == "struct_type" else "interface"
                if type_node.type == "interface_type":
                    kind = "interface"
                elif type_node.type != "struct_type":
                    continue
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind=kind,
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, spec).split("\n", 1)[0][:160],
                    )
                )

    _walk(root, visit)
    return out


# --- Rust -------------------------------------------------------------------

def _extract_rust(source: bytes, root) -> List[RawDefinition]:
    out: List[RawDefinition] = []

    def visit(node) -> None:
        mapping = {
            "struct_item": "struct",
            "trait_item": "trait",
            "enum_item": "enum",
        }
        if node.type in mapping:
            name_node = node.child_by_field_name("name")
            if name_node:
                sk = mapping[node.type]
                out.append(
                    RawDefinition(
                        name=_node_text(source, name_node),
                        syntactic_kind="trait" if sk == "trait" else "class",
                        line=node.start_point[0] + 1,
                        signature=_node_text(source, node).split("\n", 1)[0][:160],
                    )
                )

    _walk(root, visit)
    return out


_EXTRACTORS = {
    "python": _extract_python,
    "javascript": _extract_javascript,
    "typescript": _extract_typescript,
    "java": _extract_java,
    "go": _extract_go,
    "rust": _extract_rust,
}


def parser_for_file(path: str) -> Optional[str]:
    lang = FileScanner.language_of(path)
    if not lang:
        return None
    if lang == "typescript":
        return "typescript"
    if lang in ("javascript", "typescript"):
        return "javascript"
    return lang if lang in _EXTRACTORS else None

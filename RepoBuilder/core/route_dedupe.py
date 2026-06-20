"""Canonical route deduplication — collapse duplicate method+path across frameworks."""
from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, TypeVar

NOISE_PATH_PARTS = ("/test/", "/tests/", "/__tests__/", "/fixtures/", "/docs/", "/examples/")

FRAMEWORK_RANK = {
    "NestJS": 30,
    "FastAPI": 30,
    "Spring Boot": 25,
    "Spring": 25,
    "Flask": 10,
    "Express": 10,
    "Django": 10,
}

ENTRY_FILES = ("server.js", "main.py", "app.py", "main.ts", "app.ts")


def _file_path(route) -> str:
    if hasattr(route, "file"):
        return str(route.file)
    return str(route.get("file", ""))


def _handler(route) -> str:
    if hasattr(route, "handler"):
        return str(route.handler or "")
    return str(route.get("handler", ""))


def _framework(route) -> str:
    if hasattr(route, "framework"):
        return str(route.framework or "")
    return str(route.get("framework", ""))


def route_priority(route) -> tuple:
    """Higher tuple = preferred canonical route for a (method, path) pair."""
    file_low = "/" + _file_path(route).lower().replace("\\", "/")
    handler = _handler(route)
    framework = _framework(route)

    in_noise = any(part in file_low for part in NOISE_PATH_PARTS)
    inline = handler in ("(inline)", "(handler)", "(component)", "(page)")
    in_controller = "controller" in file_low
    in_entry = any(file_low.endswith("/" + name) for name in ENTRY_FILES)

    return (
        0 if in_noise else 1,
        0 if inline else 1,
        1 if in_controller else 0,
        FRAMEWORK_RANK.get(framework, 0),
        1 if in_entry else 0,
    )


T = TypeVar("T")


def canonical_dedupe(
    routes: Sequence[T],
    key_fn: Callable[[T], tuple],
) -> List[T]:
    """Keep one route per key_fn(route), choosing the highest route_priority."""
    best: dict[tuple, T] = {}
    for route in routes:
        key = key_fn(route)
        current = best.get(key)
        if current is None or route_priority(route) > route_priority(current):
            best[key] = route
    return sorted(best.values(), key=lambda r: key_fn(r))


def _route_method(route) -> str:
    if isinstance(route, dict):
        return route["method"]
    return route.method


def _route_path(route) -> str:
    if isinstance(route, dict):
        return route["path"]
    return route.path


def dedupe_backend_routes(routes: Sequence[T]) -> List[T]:
    return canonical_dedupe(routes, lambda r: (_route_method(r), _route_path(r)))


def dedupe_frontend_routes(routes: Sequence[T]) -> List[T]:
    return canonical_dedupe(routes, lambda r: (_route_path(r),))

#!/usr/bin/env python3
"""Reject imports that invert Steel Guitar Platform dependency direction."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable


RAG = "PRODUCT:RAG"
COMPANION = "PRODUCT:COMPANION"
SHARED = "PLATFORM:SHARED"
SERVICE = "SERVICE"

ALLOWED_INTERNAL_TARGETS = {
    RAG: frozenset({RAG, SHARED}),
    COMPANION: frozenset({COMPANION, SHARED}),
    SHARED: frozenset({SHARED}),
    SERVICE: frozenset({SERVICE, SHARED}),
}

SOURCE_SUFFIXES = frozenset({".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"})
JS_IMPORT_RE = re.compile(
    r"(?:\bfrom\s*|\bimport\s*(?:\(\s*)?|\brequire\s*\()\s*['\"]([^'\"]+)['\"]"
)


@dataclass(frozen=True)
class ImportReference:
    line: int
    specifier: str
    target_scope: str | None


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    source_scope: str
    target_scope: str
    specifier: str

    def render(self, root: Path) -> str:
        relative = self.path.relative_to(root)
        return (
            f"{relative}:{self.line}: {self.source_scope} may not depend on "
            f"{self.target_scope} via {self.specifier!r}"
        )


def _scope_for_parts(parts: tuple[str, ...]) -> str | None:
    if not parts:
        return None
    normalized = tuple(part.replace("-", "_") for part in parts)
    if normalized[0] == "steel_guitar_rag":
        return RAG
    if normalized[0] == "partner_companions":
        return COMPANION
    if normalized[0] == "packages":
        return SHARED
    if normalized[0] == "services":
        return SERVICE
    if len(normalized) >= 2 and normalized[0] == "apps":
        if normalized[1] == "steel_guitar_rag":
            return RAG
        if normalized[1] == "travis_companion":
            return COMPANION
    return None


def scope_for_path(path: Path, root: Path) -> str | None:
    try:
        return _scope_for_parts(path.relative_to(root).parts)
    except ValueError:
        return None


def _scope_for_module(module: str) -> str | None:
    if module.startswith("@steel-platform/"):
        return SHARED
    if module.startswith("@steel-guitar-rag/"):
        return RAG
    if module.startswith("@travis-companion/"):
        return COMPANION
    if module.startswith("@steel-services/"):
        return SERVICE
    return _scope_for_parts(tuple(part for part in module.split(".") if part))


def _python_package_parts(path: Path, root: Path) -> tuple[str, ...]:
    relative = path.relative_to(root)
    if relative.name == "__init__.py":
        return relative.parent.parts
    return relative.with_suffix("").parent.parts


def _python_target_scope(node: ast.ImportFrom, path: Path, root: Path) -> tuple[str | None, str]:
    module = node.module or ""
    if node.level == 0:
        return _scope_for_module(module), module

    package = list(_python_package_parts(path, root))
    parent_steps = max(0, node.level - 1)
    if parent_steps > len(package):
        return None, "." * node.level + module
    base = package[: len(package) - parent_steps]
    target_parts = tuple(base + [part for part in module.split(".") if part])
    return _scope_for_parts(target_parts), "." * node.level + module


def python_imports(path: Path, root: Path) -> Iterable[ImportReference]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot parse {path.relative_to(root)}: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield ImportReference(node.lineno, alias.name, _scope_for_module(alias.name))
        elif isinstance(node, ast.ImportFrom):
            target_scope, specifier = _python_target_scope(node, path, root)
            yield ImportReference(node.lineno, specifier, target_scope)


def _resolve_relative_js_import(path: Path, specifier: str, root: Path) -> str | None:
    if not specifier.startswith("."):
        return _scope_for_module(specifier.replace("/", "."))
    target = (path.parent / specifier).resolve()
    return scope_for_path(target, root.resolve())


def javascript_imports(path: Path, root: Path) -> Iterable[ImportReference]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"cannot decode {path.relative_to(root)}: {exc}") from exc
    for match in JS_IMPORT_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        specifier = match.group(1)
        yield ImportReference(line, specifier, _resolve_relative_js_import(path, specifier, root))


def check_repository(root: Path) -> tuple[list[Violation], int]:
    root = root.resolve()
    violations: list[Violation] = []
    scanned = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in {".git", ".venv", "node_modules"} for part in path.parts):
            continue
        source_scope = scope_for_path(path, root)
        if source_scope is None:
            continue
        scanned += 1
        imports = python_imports(path, root) if path.suffix == ".py" else javascript_imports(path, root)
        for reference in imports:
            target_scope = reference.target_scope
            if target_scope is None or target_scope in ALLOWED_INTERNAL_TARGETS[source_scope]:
                continue
            violations.append(
                Violation(path, reference.line, source_scope, target_scope, reference.specifier)
            )
    return violations, scanned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        violations, scanned = check_repository(args.root)
    except ValueError as exc:
        print(f"Platform boundary check failed: {exc}", file=sys.stderr)
        return 2
    if violations:
        print("Platform dependency boundary violations:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation.render(args.root.resolve())}", file=sys.stderr)
        return 1
    print(f"Platform dependency boundary check passed ({scanned} managed source files scanned).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

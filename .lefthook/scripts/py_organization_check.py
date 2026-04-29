#!/usr/bin/env python3
"""Guardrails for Python code organization on staged files."""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_LEFTHOOK_SCRIPTS = Path(__file__).resolve().parent
if str(_LEFTHOOK_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_LEFTHOOK_SCRIPTS))

from precommit_git_diff import git_diff_cached, git_repo_root, parse_staged_additions

MAX_FILE_LINES = 1500
MAX_CLASS_LINES = 1000
MIN_DUPLICATE_BODY_LINES = 8
MAX_INIT_LINES = 120
SRC_ROOT = Path("asset_generation/python/src").resolve()

# M901-04 packages legacy ``animated_build_options`` here; M901-06 will split schema/validate.
_LINE_COUNT_EXEMPT: Tuple[str, ...] = (
    "asset_generation/python/src/utils/build_options/animated_build_options.py",
    "asset_generation/python/src/utils/build_options/schema.py",
)

_FORBIDDEN_DYNAMIC_ACCESS: frozenset[str] = frozenset({"getattr", "setattr"})


def class_span(node: ast.ClassDef) -> Optional[int]:
    start = node.lineno
    end = node.end_lineno
    if start is None or end is None:
        return None
    return end - start + 1


def _call_dynamic_access_name(func: ast.expr) -> Optional[str]:
    if isinstance(func, ast.Name) and func.id in _FORBIDDEN_DYNAMIC_ACCESS:
        return func.id
    if isinstance(func, ast.Attribute) and func.attr in _FORBIDDEN_DYNAMIC_ACCESS:
        return func.attr
    return None


def _is_test_path(py_file: Path) -> bool:
    return "tests" in py_file.parts or py_file.name.startswith("test_")


def dynamic_access_errors(
    py_file: Path, tree: ast.AST, touched_lines: Optional[Set[int]]
) -> List[str]:
    """Forbid getattr/setattr outside tests.

    When ``touched_lines`` is ``None`` (no git repo), skip this rule.
    Otherwise only flag calls whose lineno appears in staged additions (incremental policy).
    """
    if _is_test_path(py_file):
        return []
    if not touched_lines:
        return []
    errors: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_dynamic_access_name(node.func)
        if name is None:
            continue
        lineno = node.lineno
        if lineno is None:
            continue
        if touched_lines is not None and lineno not in touched_lines:
            continue
        errors.append(
            f"{py_file}:{lineno}: avoid `{name}(...)` outside tests; "
            "use explicit attributes, typing.Protocol, or structured APIs"
        )
    return errors


def package_check(py_file: Path, errors: List[str]) -> None:
    try:
        resolved = py_file.resolve()
    except FileNotFoundError:
        return

    if resolved.is_relative_to(SRC_ROOT):
        parent = resolved.parent
        while parent != SRC_ROOT and parent != parent.parent:
            init_file = parent / "__init__.py"
            if not init_file.exists():
                errors.append(
                    f"{py_file}: missing package marker `{init_file.relative_to(Path.cwd())}`"
                )
            parent = parent.parent


def check_file(py_file: Path, touched_lines: Optional[Set[int]] = None) -> List[str]:
    errors: List[str] = []

    if not py_file.exists():
        return errors

    try:
        content = py_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"{py_file}: not valid UTF-8 text")
        return errors

    lines = content.count("\n") + (0 if content.endswith("\n") else 1)
    rel = py_file.as_posix()
    if lines > MAX_FILE_LINES and rel not in _LINE_COUNT_EXEMPT:
        errors.append(
            f"{py_file}: module is {lines} lines (max {MAX_FILE_LINES}); split into smaller modules"
        )

    try:
        tree = ast.parse(content, filename=str(py_file))
    except SyntaxError as exc:
        errors.append(f"{py_file}:{exc.lineno}: syntax error during organization checks: {exc.msg}")
        return errors

    errors.extend(init_module_minimal_errors(py_file, tree, lines))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            span = class_span(node)
            if span is not None and span > MAX_CLASS_LINES:
                errors.append(
                    f"{py_file}:{node.lineno}: class `{node.name}` is {span} lines "
                    f"(max {MAX_CLASS_LINES}); extract helper classes/modules"
                )
    errors.extend(private_import_errors(py_file, tree))
    errors.extend(dynamic_access_errors(py_file, tree, touched_lines))

    duplicate_groups = find_duplicate_function_bodies(tree, content)
    for funcs in duplicate_groups:
        refs = ", ".join(f"{name}@{line}" for name, line in funcs)
        errors.append(
            f"{py_file}: duplicated function bodies detected ({refs}); extract shared helper to keep DRY"
        )

    package_check(py_file, errors)
    return errors


def init_module_minimal_errors(py_file: Path, tree: ast.AST, lines: int) -> List[str]:
    errors: List[str] = []
    if py_file.name != "__init__.py":
        return errors

    if lines > MAX_INIT_LINES:
        errors.append(
            f"{py_file}: __init__.py is {lines} lines (max {MAX_INIT_LINES}); "
            "keep package __init__ minimal (imports/re-exports only)"
        )

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            errors.append(
                f"{py_file}:{node.lineno}: avoid defining {type(node).__name__.replace('Def', '').lower()} in __init__.py; "
                "move behavior to a module and re-export symbols here"
            )
    return errors


def private_import_errors(py_file: Path, tree: ast.AST) -> List[str]:
    errors: List[str] = []
    is_test_file = _is_test_path(py_file)
    is_dispatch_module = (
        py_file.name == "zone_geometry_extras_attach.py"
        or (py_file.name == "service.py" and "model_registry" in py_file.parts)
        or (py_file.name == "__init__.py" and "build_options" in py_file.parts)
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for alias in node.names:
                imported = alias.name
                if imported.startswith("_") and not imported.startswith("__"):
                    if not is_test_file and not is_dispatch_module:
                        errors.append(
                            f"{py_file}:{node.lineno}: imports private symbol `{imported}`; "
                            "depend on a public API instead (or promote it to a public symbol before reuse)"
                        )
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.rsplit(".", 1)[-1]
                if module_name.startswith("_") and not module_name.startswith("__"):
                    if not is_test_file and not is_dispatch_module:
                        errors.append(
                            f"{py_file}:{node.lineno}: imports private module `{alias.name}`; "
                            "depend on a public API instead (or promote it to a public module before reuse)"
                        )
    return errors


def normalized_body_lines(source: str, node: ast.AST) -> List[str]:
    segment = ast.get_source_segment(source, node) or ""
    out: List[str] = []
    for raw in segment.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(" ".join(line.split()))
    return out


def find_duplicate_function_bodies(
    tree: ast.AST, source: str
) -> List[List[tuple[str, int]]]:
    buckets: dict[tuple[str, ...], List[tuple[str, int]]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body_lines: List[str] = []
        for stmt in node.body:
            body_lines.extend(normalized_body_lines(source, stmt))
        if len(body_lines) < MIN_DUPLICATE_BODY_LINES:
            continue
        key = tuple(body_lines)
        buckets.setdefault(key, []).append((node.name, node.lineno))
    return [group for group in buckets.values() if len(group) > 1]


def function_body_key(node: ast.AST, source: str) -> Optional[Tuple[str, ...]]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    body_lines: List[str] = []
    for stmt in node.body:
        body_lines.extend(normalized_body_lines(source, stmt))
    if len(body_lines) < MIN_DUPLICATE_BODY_LINES:
        return None
    return tuple(body_lines)


def function_keys_for_file(py_file: Path) -> List[Tuple[Tuple[str, ...], str, int]]:
    if not py_file.exists():
        return []
    try:
        source = py_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    try:
        tree = ast.parse(source, filename=str(py_file))
    except SyntaxError:
        return []

    keys: List[Tuple[Tuple[str, ...], str, int]] = []
    for node in ast.walk(tree):
        key = function_body_key(node, source)
        if key is None:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            keys.append((key, node.name, node.lineno))
    return keys


def build_codebase_catalog(changed_files: List[Path]) -> Dict[Tuple[str, ...], List[Tuple[str, str, int]]]:
    changed_set = {p.resolve() for p in changed_files if p.exists()}
    catalog: Dict[Tuple[str, ...], List[Tuple[str, str, int]]] = {}
    for py_file in Path(".").rglob("*.py"):
        resolved = py_file.resolve()
        if resolved in changed_set:
            continue
        if ".venv" in py_file.parts:
            continue
        for key, func_name, lineno in function_keys_for_file(py_file):
            catalog.setdefault(key, []).append((py_file.as_posix(), func_name, lineno))
    return catalog


def codebase_dry_errors(
    changed_files: List[Path], catalog: Dict[Tuple[str, ...], List[Tuple[str, str, int]]]
) -> List[str]:
    errors: List[str] = []
    for py_file in changed_files:
        for key, func_name, lineno in function_keys_for_file(py_file):
            matches = catalog.get(key, [])
            if not matches:
                continue
            refs = ", ".join(f"{path}:{name}@{line}" for path, name, line in matches[:3])
            errors.append(
                f"{py_file}:{lineno}: function `{func_name}` duplicates existing code ({refs}); reuse existing logic to keep DRY"
            )
    return errors


def _repo_relative_posix(py_file: Path, repo: Optional[Path]) -> str:
    if repo is None:
        return py_file.as_posix()
    try:
        return py_file.resolve().relative_to(repo).as_posix()
    except ValueError:
        return py_file.as_posix()


def main(argv: List[str]) -> int:
    candidates = [Path(arg) for arg in argv[1:] if arg.endswith(".py")]
    if not candidates:
        return 0

    repo = git_repo_root()
    additions_map: dict[str, Set[int]] = {}
    if repo is not None:
        additions_map = {
            path: {ln for ln, _ in items}
            for path, items in parse_staged_additions(git_diff_cached(repo)).items()
        }

    all_errors: List[str] = []
    codebase_catalog = build_codebase_catalog(candidates)
    for path in candidates:
        rel = _repo_relative_posix(path, repo)
        touched: Optional[Set[int]] = additions_map.get(rel, set()) if repo is not None else None
        all_errors.extend(check_file(path, touched_lines=touched))
    all_errors.extend(codebase_dry_errors(candidates, codebase_catalog))

    if all_errors:
        print("pre-commit: Python organization check failed:")
        for err in all_errors:
            print(f" - {err}")
        return 1

    print("pre-commit: Python organization checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

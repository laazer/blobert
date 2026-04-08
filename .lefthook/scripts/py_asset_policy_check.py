#!/usr/bin/env python3
"""Pre-commit policy for asset_generation Python: lazy imports + unexplained literals on added lines."""

from __future__ import annotations

import ast
import math
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

from precommit_git_diff import git_diff_cached, git_repo_root, parse_staged_additions, staged_file_text

_PREV_LINE_OK = re.compile(
    r"^\s*#\s.*(?:import\s+cycle|circular\s+import|optional\s+depend|heavy\s+depend|lazy\s+import)",
    re.IGNORECASE,
)

# Wider than GDScript hook: small ints (indices, len checks) and common 0–1 tuning floats.
_EXEMPT_INTS_PY = frozenset(range(-1, 11))
_EXEMPT_FLOATS_PY = frozenset(
    {
        -1.0,
        0.0,
        0.05,
        0.08,
        0.12,
        0.25,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.75,
        0.8,
        1.0,
        2.0,
    }
)

_NUM_RE = re.compile(
    r"(?<![.\w])"
    r"(-?(?:\d+\.\d+(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?))"
    r"(?!\w)"
)

_SKIP_MAGIC_LINE = re.compile(
    r"^\s*(?:def\s|async\s+def\s|class\s|from\s|import\s|@|\.\.\.|#)"
)


class _LazyImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self._depth = 0
        self.hits: List[Tuple[int, int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_Import(self, node: ast.Import) -> None:
        if self._depth > 0:
            self.hits.append((node.lineno, node.col_offset or 0))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self._depth > 0:
            self.hits.append((node.lineno, node.col_offset or 0))
        self.generic_visit(node)


def _strip_py_strings(line: str) -> str:
    out: List[str] = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c in "\"'":
            quote = c
            out.append(" ")
            i += 1
            while i < n:
                if line[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if line[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def scan_py_added_line(line: str) -> List[str]:
    """Return disallowed numeric literal tokens on a single added source line."""
    stripped = line.strip()
    if not stripped:
        return []
    if stripped.startswith("#"):
        return []
    if stripped.startswith(("ruff:", "noqa:", "type:")):
        return []
    if _SKIP_MAGIC_LINE.match(line):
        return []

    no_strings = _strip_py_strings(line)
    if "#" in no_strings:
        no_strings = no_strings[: no_strings.index("#")]
    scan = no_strings.strip()
    if not scan:
        return []

    hits: List[str] = []
    for m in _NUM_RE.finditer(scan):
        raw = m.group(1)
        try:
            val = float(raw)
        except ValueError:
            continue
        if math.isfinite(val) and val == int(val):
            iv = int(val)
            if iv in _EXEMPT_INTS_PY:
                continue
        elif any(math.isclose(val, e, rel_tol=0.0, abs_tol=1e-9) for e in _EXEMPT_FLOATS_PY):
            continue
        hits.append(raw)
    return hits


def check_lazy_imports(relposix: str, source: str, added_lines: Set[int]) -> List[str]:
    errors: List[str] = []
    try:
        tree = ast.parse(source, filename=relposix)
    except SyntaxError as exc:
        return [f"{relposix}:{exc.lineno}: syntax error during lazy-import check: {exc.msg}"]

    visitor = _LazyImportVisitor()
    visitor.visit(tree)
    lines = source.splitlines()

    for ln, _col in visitor.hits:
        if ln not in added_lines:
            continue
        prev = lines[ln - 2] if ln >= 2 else ""
        if _PREV_LINE_OK.match(prev):
            continue
        errors.append(
            f"{relposix}:{ln}: import inside function — move to module level or add a comment "
            f"on the previous line documenting import cycle / optional dependency / lazy import; "
            f"see CLAUDE.md Code review agents → Python"
        )
    return errors


def check_magic_on_added_lines(relposix: str, added_pairs: List[Tuple[int, str]]) -> List[str]:
    errors: List[str] = []
    for ln, body in added_pairs:
        for token in scan_py_added_line(body):
            errors.append(
                f"{relposix}:{ln}: numeric literal `{token}` — name it at module/class scope "
                f"or use an @dataclass / settings field; see CLAUDE.md Code review agents → Python"
            )
    return errors


def main(argv: List[str]) -> int:
    repo = git_repo_root()
    if repo is None:
        print("pre-commit: py_asset_policy_check: not a git repo; skipping.")
        return 0

    paths = [Path(a) for a in argv[1:] if a.endswith(".py")]
    if not paths:
        return 0

    diff = git_diff_cached(repo)
    additions = parse_staged_additions(diff)

    errors: List[str] = []
    for p in paths:
        try:
            rel = p.resolve().relative_to(repo).as_posix()
        except ValueError:
            rel = p.as_posix()

        if not rel.startswith("asset_generation/"):
            continue
        # Test modules embed numeric fixtures and diff snippets; policy targets production code.
        if "/tests/" in rel.replace("\\", "/"):
            continue

        added_pairs = additions.get(rel)
        if not added_pairs:
            continue
        added_lines = {ln for ln, _ in added_pairs}
        text = staged_file_text(repo, rel)
        if text is None:
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")

        errors.extend(check_lazy_imports(rel, text, added_lines))
        errors.extend(check_magic_on_added_lines(rel, added_pairs))

    if errors:
        print("pre-commit: Python asset_generation policy failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("pre-commit: Python asset_generation policy passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

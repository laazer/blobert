#!/usr/bin/env python3
"""
Blender stub gap detector.

Parses one or more Python source files for mathutils API usage (Vector, Quaternion, Euler
attribute access and method calls) and reports any surface not present in blender_stubs.py.

Usage:
    python ci/scripts/blender_stub_check.py [file1.py file2.py ...]

    If no files are given, checks all .py files under asset_generation/python/src/enemies/
    and asset_generation/python/src/utils/ that import from blender_stubs or use mathutils.

Exit codes:
    0  — no gaps found
    1  — one or more missing stub members detected
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo root resolution
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = _SCRIPT_DIR.parent.parent
STUBS_PATH = REPO_ROOT / "asset_generation/python/src/utils/blender_stubs.py"
DEFAULT_SEARCH_DIRS = [
    REPO_ROOT / "asset_generation/python/src/enemies",
    REPO_ROOT / "asset_generation/python/src/utils",
]

# ---------------------------------------------------------------------------
# Known stub surface — derived by parsing blender_stubs.py at runtime
# ---------------------------------------------------------------------------

def _extract_stub_surface(stubs_path: Path) -> dict[str, set[str]]:
    """Return {class_name: {method_or_property_name, ...}} from blender_stubs.py."""
    src = stubs_path.read_text()
    tree = ast.parse(src)
    surface: dict[str, set[str]] = {}

    def _walk_class(node: ast.ClassDef) -> set[str]:
        members: set[str] = set()
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                members.add(item.name)
            elif isinstance(item, ast.AsyncFunctionDef):
                members.add(item.name)
            elif isinstance(item, (ast.Assign, ast.AnnAssign)):
                # class-level assignments like __slots__
                targets = item.targets if isinstance(item, ast.Assign) else [item.target]
                for t in targets:
                    if isinstance(t, ast.Name):
                        members.add(t.id)
        return members

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("_"):
            public_name = node.name.lstrip("_")  # _Vector → Vector
            surface[public_name] = _walk_class(node)

    return surface


# ---------------------------------------------------------------------------
# Usage patterns we grep for in source files
# ---------------------------------------------------------------------------

# Strategy: two complementary approaches, both targeted to mathutils surface only.
#
# 1. Regex on class-level usage: `Vector.something`, `Quaternion.something`
# 2. AST walk: find calls/attribute accesses on objects annotated or assigned as
#    mathutils types (e.g. `bc: Vector = ...`, `vec = mathutils.Vector(...)`)
#
# We do NOT match arbitrary lowercase variables — only confirmed mathutils contexts.

_MATHUTILS_TYPE_NAMES = {"Vector", "Quaternion", "Euler", "Matrix"}

# Match class-level attribute access: Vector.something or mathutils.Vector.something
_CLASS_ATTR_RE = re.compile(
    r"\b(?:mathutils\.)?(?:Vector|Quaternion|Euler)\b\s*\.\s*([a-zA-Z_][a-zA-Z0-9_]*)"
)

# The specific mathutils methods/properties we care about (the known required surface
# that trips up stubs). We only flag these, not arbitrary attribute names.
_TRACKED_ATTRS = {
    "dot", "cross", "normalize", "normalized", "to_euler", "rotation_difference",
    "length", "x", "y", "z", "w", "__iter__", "__add__", "__sub__", "__mul__",
    "__rmul__", "__truediv__", "__eq__", "to_matrix", "to_quaternion", "lerp",
    "slerp", "angle", "angle_signed", "project", "reflect", "orthogonal",
    "resize", "resized", "freeze", "copy",
}


def _collect_attr_usages_from_ast(src: str, filepath: Path) -> list[tuple[str, int]]:
    """
    Return [(attr_name, lineno), ...] for mathutils attribute accesses found in AST.

    Strategy: walk AST looking for:
      - Direct mathutils class attribute access: `mathutils.Vector.something`
      - Calls to mathutils constructors whose result is used: `mathutils.Vector(...).something`
      - Type annotations on function args/local vars that mention mathutils types,
        then track subsequent attribute accesses on those names
    """
    try:
        tree = ast.parse(src, filename=str(filepath))
    except SyntaxError:
        return []

    usages: list[tuple[str, int]] = []

    class _Visitor(ast.NodeVisitor):
        def __init__(self):
            self._mathutils_names: set[str] = set()

        def _is_mathutils_type(self, node: ast.expr) -> bool:
            """True if node refers to a mathutils type (Vector, Quaternion, etc.)."""
            if isinstance(node, ast.Name) and node.id in _MATHUTILS_TYPE_NAMES:
                return True
            if isinstance(node, ast.Attribute):
                if node.attr in _MATHUTILS_TYPE_NAMES:
                    return True
                if isinstance(node.value, ast.Name) and node.value.id == "mathutils":
                    return True
            return False

        def visit_AnnAssign(self, node: ast.AnnAssign):
            """Track: `var: Vector = ...` or `var: mathutils.Vector = ...`"""
            if self._is_mathutils_type(node.annotation) and isinstance(node.target, ast.Name):
                self._mathutils_names.add(node.target.id)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef):
            """Track annotated args: `def f(v: Vector)`"""
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if arg.annotation and self._is_mathutils_type(arg.annotation):
                    self._mathutils_names.add(arg.arg)
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute):
            if not isinstance(node.ctx, ast.Load):
                self.generic_visit(node)
                return

            attr = node.attr
            if attr not in _TRACKED_ATTRS:
                self.generic_visit(node)
                return

            val = node.value
            # Direct: `mathutils.Vector(...).<attr>` or chained call
            if self._is_mathutils_type(val):
                usages.append((attr, node.lineno))
            # Variable known to be mathutils type: `bc.dot(...)` where `bc: Vector`
            elif isinstance(val, ast.Name) and val.id in self._mathutils_names:
                usages.append((attr, node.lineno))
            # Direct call result: `mathutils.Vector(...).normalize()`
            elif isinstance(val, ast.Call) and self._is_mathutils_type(val.func):
                usages.append((attr, node.lineno))

            self.generic_visit(node)

    visitor = _Visitor()
    visitor.visit(tree)
    return usages


def _collect_usages_from_regex(src: str, filepath: Path) -> list[tuple[str, int]]:
    """Regex-based collection: catches `Vector.attr`, `Quaternion.attr` style class access."""
    usages: list[tuple[str, int]] = []
    for lineno, line in enumerate(src.splitlines(), start=1):
        for m in _CLASS_ATTR_RE.finditer(line):
            attr = m.group(1)
            if attr in _TRACKED_ATTRS:
                usages.append((attr, lineno))
    return usages


def _file_uses_mathutils(src: str) -> bool:
    return "mathutils" in src or "blender_stubs" in src or any(
        t in src for t in _MATHUTILS_TYPE_NAMES
    )


# ---------------------------------------------------------------------------
# Gap reporting
# ---------------------------------------------------------------------------

def check_file(
    filepath: Path, stub_surface: dict[str, set[str]]
) -> list[tuple[str, int, str]]:
    """
    Return list of (attr_name, lineno, hint) for attrs used but not in any stub class.
    hint is the stub class most likely expected to own the attr.
    """
    src = filepath.read_text()
    if not _file_uses_mathutils(src):
        return []

    # Aggregate all known stub members in a flat set for quick membership check
    all_stub_members: set[str] = set()
    for members in stub_surface.values():
        all_stub_members.update(members)

    # Collect usages (deduplicate by attr+line)
    seen: set[tuple[str, int]] = set()
    raw = _collect_attr_usages_from_ast(src, filepath)
    raw += _collect_usages_from_regex(src, filepath)

    gaps: list[tuple[str, int, str]] = []
    for attr, lineno in raw:
        key = (attr, lineno)
        if key in seen:
            continue
        seen.add(key)
        # Skip dunder-only attrs that are Python built-ins, not mathutils-specific
        if attr.startswith("__") and attr in {
            "__class__", "__init__", "__new__", "__doc__", "__module__",
            "__dict__", "__weakref__", "__slots__",
        }:
            continue
        if attr not in all_stub_members:
            # Guess which class should own it
            hint = "Vector"  # default
            if attr in {"w", "to_euler"}:
                hint = "Quaternion"
            gaps.append((attr, lineno, hint))

    return gaps


def run(files: list[Path]) -> int:
    if not STUBS_PATH.exists():
        print(f"ERROR: blender_stubs.py not found at {STUBS_PATH}", file=sys.stderr)
        return 2

    stub_surface = _extract_stub_surface(STUBS_PATH)
    all_known: set[str] = set()
    for members in stub_surface.values():
        all_known.update(members)

    if not files:
        # Auto-discover files that reference mathutils
        files = []
        for d in DEFAULT_SEARCH_DIRS:
            if d.exists():
                files.extend(d.rglob("*.py"))

    # Resolve all paths to absolute so relative_to(REPO_ROOT) works correctly
    files = [f.resolve() if not f.is_absolute() else f for f in files]

    total_gaps: list[tuple[Path, str, int, str]] = []
    checked = 0
    for f in sorted(files):
        if not f.exists():
            print(f"SKIP (not found): {f}", file=sys.stderr)
            continue
        gaps = check_file(f, stub_surface)
        checked += 1
        for attr, lineno, hint in gaps:
            total_gaps.append((f, attr, lineno, hint))

    # Print OK summary
    ok_attrs = sorted(all_known - {"__slots__"})
    print(f"Checked {checked} file(s). Stub surface ({len(ok_attrs)} members): "
          f"{', '.join(ok_attrs[:12])}{'...' if len(ok_attrs) > 12 else ''}")

    if not total_gaps:
        print("OK: no blender stub gaps detected.")
        return 0

    print(f"\nMISSING ({len(total_gaps)} gap(s)) — add to blender_stubs.py:\n")
    # Deduplicate by attr name for actionable output
    reported_attrs: set[str] = set()
    for filepath, attr, lineno, hint in total_gaps:
        rel = filepath.relative_to(REPO_ROOT)
        print(f"  MISSING: {hint}.{attr}  ({rel}:{lineno})")
        reported_attrs.add(f"{hint}.{attr}")

    print(f"\nFix: add the above method(s)/propert(ies) to the _{hint} class in "
          f"asset_generation/python/src/utils/blender_stubs.py")
    return 1


if __name__ == "__main__":
    file_args = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else []
    sys.exit(run(file_args))

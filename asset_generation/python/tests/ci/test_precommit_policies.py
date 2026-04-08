"""Unit tests for `.lefthook/scripts` pre-commit policy helpers (no git required)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_SCRIPTS = _REPO / ".lefthook" / "scripts"


def _load(name: str):
    path = _SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


precommit_git_diff = _load("precommit_git_diff")
gd_magic = _load("gd_magic_number_check")


def test_parse_staged_additions_simple_hunk():
    diff = """diff --git a/a.gd b/a.gd
--- a/a.gd
+++ b/a.gd
@@ -10 +10 @@
-foo
+bar
"""
    got = precommit_git_diff.parse_staged_additions(diff)
    assert got["a.gd"] == [(10, "bar")]


def test_parse_staged_additions_new_file():
    diff = """diff --git a/n.gd b/n.gd
new file mode 100644
--- /dev/null
+++ b/n.gd
@@ -0,0 +1,2 @@
+extends Node
+const X = 1
"""
    got = precommit_git_diff.parse_staged_additions(diff)
    assert got["n.gd"] == [(1, "extends Node"), (2, "const X = 1")]


def test_gd_magic_skips_const_line():
    assert gd_magic._scan_line_for_magic("const FOO: float = 3.14") == []


def test_gd_magic_flags_float_literal():
    assert gd_magic._scan_line_for_magic("var x := 3.14") == ["3.14"]


def test_gd_magic_exempt_small_int():
    assert gd_magic._scan_line_for_magic("if i == 2:") == []


def test_gd_magic_flags_larger_int():
    assert gd_magic._scan_line_for_magic("health = 100") == ["100"]


def test_gd_magic_ignores_string():
    assert gd_magic._scan_line_for_magic('print("100")') == []



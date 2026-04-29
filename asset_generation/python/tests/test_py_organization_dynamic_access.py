"""Contract tests for getattr/setattr guard in ``py_organization_check``."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

_ORG_CHECK_PATH = Path(__file__).resolve().parents[3] / ".lefthook/scripts/py_organization_check.py"


def _load_org_check():
    spec = importlib.util.spec_from_file_location(
        "py_organization_check",
        _ORG_CHECK_PATH,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def org():
    return _load_org_check()


def test_getattr_flagged_on_touched_line_prod(org, tmp_path: Path) -> None:
    src = tmp_path / "asset_generation/python/src/pkg"
    src.mkdir(parents=True)
    f = src / "mod.py"
    f.write_text("def f(x):\n    return getattr(x, 'a')\n", encoding="utf-8")
    tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
    err = org.dynamic_access_errors(f, tree, {2})
    assert len(err) == 1
    assert "getattr" in err[0]


def test_getattr_skipped_when_line_not_touched(org, tmp_path: Path) -> None:
    src = tmp_path / "asset_generation/python/src/pkg"
    src.mkdir(parents=True)
    f = src / "mod.py"
    f.write_text("def f(x):\n    return getattr(x, 'a')\n", encoding="utf-8")
    tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
    assert org.dynamic_access_errors(f, tree, {99}) == []


def test_getattr_allowed_under_tests_path(org, tmp_path: Path) -> None:
    tdir = tmp_path / "asset_generation/python/tests"
    tdir.mkdir(parents=True)
    f = tdir / "test_x.py"
    f.write_text("def test_a():\n    getattr(object(), 'x')\n", encoding="utf-8")
    tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
    assert org.dynamic_access_errors(f, tree, {2}) == []


def test_setattr_attribute_call_flagged(org, tmp_path: Path) -> None:
    src = tmp_path / "asset_generation/python/src/pkg"
    src.mkdir(parents=True)
    f = src / "mod.py"
    f.write_text(
        "def f(mp, x):\n    mp.setattr(x, 'a', 1)\n",
        encoding="utf-8",
    )
    tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
    err = org.dynamic_access_errors(f, tree, {2})
    assert len(err) == 1
    assert "setattr" in err[0]


def test_no_touched_lines_skips_dynamic_rule(org, tmp_path: Path) -> None:
    src = tmp_path / "asset_generation/python/src/pkg"
    src.mkdir(parents=True)
    f = src / "mod.py"
    f.write_text("def f(x):\n    return getattr(x, 'a')\n", encoding="utf-8")
    tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
    assert org.dynamic_access_errors(f, tree, set()) == []

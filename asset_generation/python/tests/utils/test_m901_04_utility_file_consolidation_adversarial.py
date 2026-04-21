"""
M901-04 — adversarial contracts: permutations, concurrency stress, boundary JSON/stem/float,
filesystem seams, R7 demo import audit, and wildcard-import guards.

# CHECKPOINT: Negative ``variant_index`` for ``animated_export_stem`` is unspecified; we freeze
# legacy ``export_naming`` f-string behavior (e.g. ``-3`` formats as ``-3``, not zero-padded).
"""

from __future__ import annotations

import itertools
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from tests.utils.m901_04_import_ast import (
    assert_build_options_package_no_star_from_src_utils,
    utils_demo_import_violations,
)
from tests.utils.m901_04_paths import (
    asset_generation_python_root,
    asset_generation_root,
    utils_src_dir,
)

_MODULES_FOR_PERMUTATION = (
    "utils.validation",
    "utils.materials",
    "utils.config",
    "utils.export",
    "utils.build_options",
)


def _src_on_path() -> Path:
    return asset_generation_python_root() / "src"


def _run_import_sequence(seq: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    lines = ["import sys", f"sys.path.insert(0, {str(_src_on_path())!r})"]
    for m in seq:
        lines.append(f"import {m}")
    code = "\n".join(lines)
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_adversarial_R1_all_import_permutations_acyclic() -> None:
    """Stress: every order of the five modules must import cleanly (catches cycle order-sensitivity)."""
    # CHECKPOINT: Full 5! graph; conservative assumption = spec DAG makes any order valid.
    for seq in itertools.permutations(_MODULES_FOR_PERMUTATION):
        proc = _run_import_sequence(seq)
        assert proc.returncode == 0, (seq, proc.stdout, proc.stderr)


def test_adversarial_R1_concurrent_fresh_interpreter_imports() -> None:
    """Concurrency: parallel subprocesses must not flake on import (no shared in-proc state)."""
    seq = _MODULES_FOR_PERMUTATION
    errors: list[str] = []

    def _task(_i: int) -> None:
        proc = _run_import_sequence(seq)
        if proc.returncode != 0:
            errors.append(f"{proc.stderr}\n{proc.stdout}")

    with ThreadPoolExecutor(max_workers=min(12, os.cpu_count() or 4)) as pool:
        futures = [pool.submit(_task, i) for i in range(24)]
        for f in as_completed(futures):
            f.result()
    assert not errors, "\n".join(errors[:5])


def test_adversarial_R3_validate_glb_path_directory_with_glb_suffix_raises(
    tmp_path: Path,
) -> None:
    from src.utils.export import validate_glb_path

    dir_named = tmp_path / "looks_like.glb"
    dir_named.mkdir()
    with pytest.raises(ValueError):
        validate_glb_path(dir_named)


def test_adversarial_R3_validate_glb_path_symlink_to_real_file_ok(tmp_path: Path) -> None:
    from src.utils.export import validate_glb_path

    real = tmp_path / "real.glb"
    real.write_bytes(b"glTF")
    link = tmp_path / "link.glb"
    try:
        os.symlink(real, link)
    except OSError:
        pytest.skip("symlinks not supported in this environment")
    out = validate_glb_path(link)
    assert isinstance(out, Path)
    assert validate_glb_path(link) == out


def test_adversarial_R3_validate_glb_path_idempotent_stress(tmp_path: Path) -> None:
    from src.utils.export import validate_glb_path

    p = tmp_path / "s.glb"
    p.write_bytes(b"x")
    for _ in range(500):
        assert validate_glb_path(p) == validate_glb_path(p)


def test_adversarial_R3_variant_start_index_env_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.utils.export import variant_start_index

    monkeypatch.delenv("BLOBERT_EXPORT_START_INDEX", raising=False)
    assert variant_start_index() == 0

    monkeypatch.setenv("BLOBERT_EXPORT_START_INDEX", "")
    assert variant_start_index() == 0

    monkeypatch.setenv("BLOBERT_EXPORT_START_INDEX", "not_a_number")
    assert variant_start_index() == 0

    monkeypatch.setenv("BLOBERT_EXPORT_START_INDEX", "-40")
    assert variant_start_index() == 0

    monkeypatch.setenv("BLOBERT_EXPORT_START_INDEX", "42")
    assert variant_start_index() == 42


def test_adversarial_R3_animated_export_stem_variants() -> None:
    from src.utils.export import animated_export_stem

    assert animated_export_stem("spider", 0) == "spider_animated_00"
    assert animated_export_stem("spider", 999) == "spider_animated_999"
    # CHECKPOINT: negative index — freeze prior formatting (see module docstring).
    assert animated_export_stem("x", -3) == "x_animated_-3"


def test_adversarial_R5_parse_build_options_json_malformed_and_non_dict() -> None:
    from src.utils.build_options import parse_build_options_json

    assert parse_build_options_json('{"a": 1}') == {"a": 1}
    assert parse_build_options_json("[]") == {}
    assert parse_build_options_json("null") == {}
    assert parse_build_options_json('"str"') == {}
    bloated = "{\n" + " " * 5000 + '"k": 1\n}'
    assert parse_build_options_json(bloated) == {"k": 1}


def test_adversarial_R5_options_for_enemy_deep_unicode_json_roundtrip() -> None:
    from src.utils.build_options import options_for_enemy, parse_build_options_json

    raw = '{"mesh": {"\u03b8": 0.5}, "eye_count": 2}'
    data = parse_build_options_json(raw)
    out = options_for_enemy("spider", data)
    assert isinstance(out, dict)
    assert "mesh" in out


def test_adversarial_R4_clamp01_numeric_extremes() -> None:
    from src.utils.validation import clamp01

    assert clamp01(float("inf")) == 1.0
    assert clamp01(float("-inf")) == 0.0
    # CHECKPOINT: NaN + ``min``/``max` in Python yields 1.0 (not NaN); freeze to catch reorder bugs.
    assert clamp01(float("nan")) == 1.0


def test_adversarial_R5_build_options_package_no_star_import_utils() -> None:
    assert_build_options_package_no_star_from_src_utils(utils_src_dir() / "build_options")


def test_adversarial_R7_no_demo_imports_in_src_tests_web() -> None:
    roots = (
        asset_generation_python_root() / "src",
        asset_generation_python_root() / "tests",
        asset_generation_root() / "web",
    )
    violations: list[str] = []
    for tree in roots:
        if not tree.is_dir():
            continue
        for path in tree.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if path.name == "m901_04_import_ast.py":
                continue
            violations.extend(utils_demo_import_violations(path))
    assert not violations, "\n".join(violations[:40])


def test_adversarial_R9_legacy_scan_helpers_remain_clean() -> None:
    from tests.utils.m901_04_import_ast import legacy_utils_import_violations

    ast_path = asset_generation_python_root() / "tests" / "utils" / "m901_04_import_ast.py"
    assert legacy_utils_import_violations(ast_path) == []
    assert utils_demo_import_violations(ast_path) == []

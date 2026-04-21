"""
M901-04 utility consolidation — behavior-first contracts (spec: m901_04_utility_file_consolidation_spec).

Maps: R1 import DAG + layout, R2 config surface, R3 export + validate_glb_path, R4 clamp01,
R5 build_options public API, R6 retained modules, R7 orphan removal, R8 utils.__init__,
R9 compileall + no legacy import paths.
"""

from __future__ import annotations

import compileall
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.utils.m901_04_import_ast import (
    assert_build_options_package_import_dag,
    assert_config_import_dag,
    assert_export_import_dag,
    assert_materials_import_dag,
    assert_validation_only_stdlib,
    legacy_utils_import_violations,
)
from tests.utils.m901_04_paths import (
    asset_generation_python_root,
    asset_generation_root,
    utils_src_dir,
)

# --- R2 slug/order parity (frozen; matches MAINT-ETRP + EnemyTypes registry) ---
_EXPECTED_ANIMATED_SLUGS = [
    "spider",
    "slug",
    "imp",
    "spitter",
    "claw_crawler",
    "carapace_husk",
]
_EXPECTED_STATIC_SLUGS = [
    "glue_drone",
    "melt_worm",
    "frost_jelly",
    "stone_burrower",
    "ferro_drone",
]


def _require_file(path: Path) -> Path:
    assert path.is_file(), f"M901-04 expected {path} to exist"
    return path


# --------------------------------------------------------------------------- R1
def test_R1_ast_import_dag_config_export_validation_materials_build_options() -> None:
    u = utils_src_dir()
    _require_file(u / "config.py")
    _require_file(u / "export.py")
    _require_file(u / "validation.py")
    _require_file(u / "materials.py")
    _require_file(u / "build_options" / "__init__.py")

    assert_config_import_dag(u / "config.py")
    assert_export_import_dag(u / "export.py")
    assert_validation_only_stdlib(u / "validation.py")
    assert_materials_import_dag(u / "materials.py")
    assert_build_options_package_import_dag(u / "build_options" / "__init__.py")


def test_R1_subprocess_import_order_variants_match_dag() -> None:
    """Fresh interpreter: several valid ``utils.*`` orderings all succeed (no cycles)."""
    root = asset_generation_python_root()
    src = root / "src"
    sequences = (
        (
            "utils.validation",
            "utils.materials",
            "utils.config",
            "utils.export",
            "utils.build_options",
        ),
        (
            "utils.materials",
            "utils.validation",
            "utils.config",
            "utils.export",
            "utils.build_options",
        ),
        (
            "utils.config",
            "utils.materials",
            "utils.validation",
            "utils.export",
            "utils.build_options",
        ),
    )
    for seq in sequences:
        lines = ["import sys", f"sys.path.insert(0, {str(src)!r})"]
        for m in seq:
            lines.append(f"import {m}")
        code = "\n".join(lines)
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert proc.returncode == 0, (seq, proc.stdout, proc.stderr)


# --------------------------------------------------------------------------- R2
def test_R2_config_exports_slug_registry_and_enemy_types_surface() -> None:
    from src.utils import config

    assert list(config.ANIMATED_SLUGS) == _EXPECTED_ANIMATED_SLUGS
    assert list(config.STATIC_SLUGS) == _EXPECTED_STATIC_SLUGS
    meta = config.animated_enemies_for_api()
    assert [e["slug"] for e in meta] == _EXPECTED_ANIMATED_SLUGS
    assert {e["slug"] for e in meta} == set(config.ANIMATED_ENEMY_LABELS.keys())

    assert config.EnemyTypes.get_animated() == _EXPECTED_ANIMATED_SLUGS
    assert config.EnemyTypes.get_static() == _EXPECTED_STATIC_SLUGS
    assert config.EnemyTypes.get_all() == _EXPECTED_ANIMATED_SLUGS + _EXPECTED_STATIC_SLUGS


def test_R2_config_reexports_body_families_symbols() -> None:
    from src.utils import config

    assert config.BoneNames is not None
    assert config.EnemyBodyTypes is not None


def test_R2_legacy_constants_and_slug_files_removed() -> None:
    u = utils_src_dir()
    assert not (u / "constants.py").is_file()
    assert not (u / "enemy_slug_registry.py").is_file()


# --------------------------------------------------------------------------- R3
def test_R3_export_stem_and_directories_preserve_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.utils.config import ExportConfig, LevelExportConfig, PlayerExportConfig
    from src.utils.export import (
        animated_export_directory,
        animated_export_stem,
        level_export_directory,
        player_export_directory,
        variant_start_index,
    )

    assert animated_export_stem("spider", 3) == "spider_animated_03"
    assert (
        animated_export_stem("spider", 3, prefab_name="Foo")
        == "spider_animated_prefab_Foo_03"
    )

    monkeypatch.delenv("BLOBERT_EXPORT_USE_DRAFT_SUBDIR", raising=False)
    monkeypatch.delenv("BLOBERT_EXPORT_START_INDEX", raising=False)

    assert animated_export_directory() == ExportConfig.ANIMATED_DIR
    assert player_export_directory() == PlayerExportConfig.PLAYER_DIR
    assert level_export_directory() == LevelExportConfig.LEVEL_DIR
    assert variant_start_index() == 0

    monkeypatch.setenv("BLOBERT_EXPORT_USE_DRAFT_SUBDIR", "1")
    assert animated_export_directory() == os.path.join(ExportConfig.ANIMATED_DIR, "draft")
    assert player_export_directory() == os.path.join(PlayerExportConfig.PLAYER_DIR, "draft")
    assert level_export_directory() == os.path.join(LevelExportConfig.LEVEL_DIR, "draft")

    monkeypatch.setenv("BLOBERT_EXPORT_START_INDEX", "5")
    assert variant_start_index() == 5


def test_R3_validate_glb_path_contract(tmp_path: Path) -> None:
    from src.utils.export import validate_glb_path

    missing = tmp_path / "nope.glb"
    with pytest.raises(ValueError):
        validate_glb_path(missing)

    wrong = tmp_path / "x.txt"
    wrong.write_bytes(b"x")
    with pytest.raises(ValueError):
        validate_glb_path(wrong)

    empty_glb = tmp_path / "empty.glb"
    empty_glb.write_bytes(b"")
    with pytest.raises(ValueError):
        validate_glb_path(empty_glb)

    ok_lower = tmp_path / "minimal.glb"
    ok_lower.write_bytes(b"glTF")
    out = validate_glb_path(ok_lower)
    assert isinstance(out, Path)
    assert validate_glb_path(ok_lower) == validate_glb_path(ok_lower)
    assert validate_glb_path(str(ok_lower)) == out

    ok_upper = tmp_path / "UPPER.GLB"
    ok_upper.write_bytes(b"glTF")
    validate_glb_path(ok_upper)

    with pytest.raises(ValueError):
        validate_glb_path("")


def test_R3_legacy_export_modules_removed() -> None:
    u = utils_src_dir()
    assert not (u / "export_naming.py").is_file()
    assert not (u / "export_subdir.py").is_file()


# --------------------------------------------------------------------------- R4
def test_R4_clamp01_single_canonical_definition() -> None:
    from src.utils.validation import clamp01

    from src.utils import placement_clustering

    assert placement_clustering.clamp01 is clamp01

    assert clamp01(0.25) == 0.25
    assert clamp01(2.0) == 1.0
    assert clamp01(-1.0) == 0.0
    assert clamp01("nope", 0.25) == 0.25


# --------------------------------------------------------------------------- R5
def test_R5_build_options_public_import_surface() -> None:
    from src.utils.build_options import (
        OFFSET_XYZ_MAX,
        OFFSET_XYZ_MIN,
        animated_build_controls_for_api,
        options_for_enemy,
        parse_build_options_json,
    )

    assert OFFSET_XYZ_MIN == -2.0
    assert OFFSET_XYZ_MAX == 2.0

    o = options_for_enemy("spider", {})
    assert o["eye_count"] == 2
    assert parse_build_options_json("") == {}
    assert parse_build_options_json("not json") == {}
    ctrl = animated_build_controls_for_api()
    assert "spider" in ctrl and "eye_count" in {c["key"] for c in ctrl["spider"]}


def test_R5_build_options_module_attributes_match_prior_surface() -> None:
    import src.utils.build_options as abo

    assert hasattr(abo, "_mouth_control_defs") and callable(abo._mouth_control_defs)
    assert hasattr(abo, "_tail_control_defs") and callable(abo._tail_control_defs)


def test_R5_no_animated_build_options_modules_at_utils_root() -> None:
    u = utils_src_dir()
    for p in u.glob("animated_build_options*.py"):
        assert False, f"unexpected legacy file at utils root: {p}"


# --------------------------------------------------------------------------- R6 / R7
def test_R6_retained_support_modules_present() -> None:
    u = utils_src_dir()
    for name in (
        "simple_viewer.py",
        "materials.py",
        "blender_stubs.py",
        "body_type_presets.py",
        "placement_clustering.py",
        "texture_asset_loader.py",
    ):
        assert (u / name).is_file(), f"R6 expected {name} to remain"


def test_R6_simple_viewer_non_trivial_and_blender_oriented() -> None:
    p = utils_src_dir() / "simple_viewer.py"
    txt = p.read_text(encoding="utf-8")
    assert len(txt) > 200
    assert "bpy" in txt or "Blender" in txt


def test_R7_demo_module_removed() -> None:
    assert not (utils_src_dir() / "demo.py").is_file()


# --------------------------------------------------------------------------- R8
def test_R8_utils_package_root_reexports_unchanged_names() -> None:
    import src.utils as u

    expected = {
        "EnemyTypes",
        "AnimationTypes",
        "EnemyBodyTypes",
        "BoneNames",
        "AnimationConfig",
        "ExportConfig",
        "MaterialColors",
        "MaterialNames",
        "MaterialThemes",
        "MaterialCategories",
        "BodyPartMaterials",
    }
    assert set(u.__all__) == expected
    for name in expected:
        assert hasattr(u, name), f"missing re-export: {name}"
    assert u.EnemyTypes.SPIDER == "spider"
    assert u.AnimationTypes.IDLE == "idle"
    assert u.ExportConfig.ANIMATED_DIR == "animated_exports"


def test_R8_utils_root_does_not_star_export_build_options() -> None:
    import src.utils as u

    assert "build_options" not in u.__all__


# --------------------------------------------------------------------------- R9
def test_R9_compileall_src_tree() -> None:
    root = asset_generation_python_root() / "src"
    assert compileall.compile_dir(str(root), quiet=1, force=True)


def test_R9_no_legacy_utils_import_paths_in_python_and_web_trees() -> None:
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
            if path.name == "test_m901_04_utility_file_consolidation.py":
                continue
            if path.name == "m901_04_import_ast.py":
                continue
            violations.extend(legacy_utils_import_violations(path))
    assert not violations, "\n".join(violations[:80])


def test_R9_ast_scan_skipped_files_are_self_consistent() -> None:
    """Guard: exclusions for this module must not hide legacy imports in helper files."""
    ast_root = asset_generation_python_root() / "tests" / "utils" / "m901_04_import_ast.py"
    assert legacy_utils_import_violations(ast_root) == []

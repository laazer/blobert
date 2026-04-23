"""
M901-06 animated build options consolidation — primary behavioral contracts.

Runtime-focused contracts only:
- package API compatibility for build-options consumers
- schema/validate module boundary and importability
- deterministic normalization/validation behavior
- legacy module retirement and import-path rewiring
"""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

from tests.utils.m901_04_paths import asset_generation_python_root, utils_src_dir

_LEGACY_MODULE_FILENAMES = (
    "animated_build_options.py",
    "animated_build_options_appendage_defs.py",
    "animated_build_options_mesh_controls.py",
    "animated_build_options_validate.py",
    "animated_build_options_zone_texture.py",
    "animated_build_options_spider_eye.py",
    "animated_build_options_part_feature_defs.py",
)

_REPO_IMPORT_SCAN_ROOTS = ("src", "tests")


def _src_on_path() -> Path:
    return asset_generation_python_root() / "src"


def _fresh_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_R1_schema_validate_and_package_import_in_any_order() -> None:
    src = _src_on_path()
    code_schema_first = "\n".join(
        (
            "import sys",
            f"sys.path.insert(0, {str(src)!r})",
            "import src.utils.build_options.schema",
            "import src.utils.build_options.validate",
            "import src.utils.build_options as bo",
            "assert callable(bo.options_for_enemy)",
        )
    )
    code_validate_first = "\n".join(
        (
            "import sys",
            f"sys.path.insert(0, {str(src)!r})",
            "import src.utils.build_options.validate",
            "import src.utils.build_options.schema",
            "import src.utils.build_options as bo",
            "assert callable(bo.options_for_enemy)",
        )
    )
    proc_schema_first = _fresh_python(code_schema_first)
    proc_validate_first = _fresh_python(code_validate_first)
    assert proc_schema_first.returncode == 0, (
        proc_schema_first.stdout,
        proc_schema_first.stderr,
    )
    assert proc_validate_first.returncode == 0, (
        proc_validate_first.stdout,
        proc_validate_first.stderr,
    )


def test_R2_legacy_animated_build_option_modules_deleted() -> None:
    build_options_dir = utils_src_dir() / "build_options"
    for filename in _LEGACY_MODULE_FILENAMES:
        assert not (build_options_dir / filename).exists(), (
            f"legacy module must be retired after consolidation: {filename}"
        )


def test_R3_package_boundary_exposes_public_api_contract() -> None:
    from src.utils.build_options import get_control_definitions, options_for_enemy

    controls = get_control_definitions()
    assert isinstance(controls, dict)
    assert "spider" in controls
    assert "claw_crawler" in controls
    spider_keys = {entry["key"] for entry in controls["spider"]}
    assert "eye_count" in spider_keys

    spider_default = options_for_enemy("spider", {})
    spider_custom = options_for_enemy("spider", {"eye_count": 4})
    assert set(spider_default.keys()) == set(spider_custom.keys())
    assert spider_default["eye_count"] == 2
    assert spider_custom["eye_count"] == 4


def test_R4_typed_schema_entries_are_runtime_dict_shapes() -> None:
    from src.utils.build_options import get_control_definitions

    controls = get_control_definitions()
    spider = controls["spider"]
    assert isinstance(spider, list)
    assert spider, "spider control definitions must be non-empty"
    eye_count = next(entry for entry in spider if entry["key"] == "eye_count")
    assert set(("key", "type", "default")).issubset(set(eye_count.keys()))
    assert isinstance(eye_count["key"], str)
    assert isinstance(eye_count["type"], str)


def test_R5_normalization_and_validation_are_deterministic() -> None:
    from src.utils.build_options import normalize_controls, validate_build_options

    raw = {
        "eye_count": 999,
        "extra_zone_body_kind": "spikes",
        "extra_zone_body_spike_count": "12",
    }
    first = normalize_controls("spider", raw)
    second = normalize_controls("spider", raw)
    assert first == second

    assert validate_build_options("spider", first) == validate_build_options(
        "spider", second
    )


def test_R5_invalid_values_fail_closed_via_public_normalization() -> None:
    from src.utils.build_options import normalize_controls

    normalized = normalize_controls(
        "slug",
        {
            "extra_zone_body_kind": "not_a_kind",
            "extra_zone_body_spike_count": -999,
            "extra_zone_body_spike_size": 999.0,
        },
    )
    body = normalized["zone_geometry_extras"]["body"]
    assert body["kind"] == "none"
    assert body["spike_count"] == 1
    assert body["spike_size"] == 3.0


def test_R5_normalization_does_not_mutate_input_payload() -> None:
    from src.utils.build_options import normalize_controls

    raw = {
        "extra_zone_body_kind": "spikes",
        "extra_zone_body_spike_count": "9",
        "extra_zone_body_spike_size": 2.5,
        "features": {"body": {"finish": "glossy", "hex": "abc123"}},
    }
    snapshot = copy.deepcopy(raw)
    normalize_controls("slug", raw)
    assert raw == snapshot


def test_R5_options_for_enemy_returns_fresh_nested_structures_per_call() -> None:
    from src.utils.build_options import options_for_enemy

    first = options_for_enemy("slug", {})
    # CHECKPOINT: assumes options_for_enemy must not leak mutable defaults across calls.
    first["zone_geometry_extras"]["body"]["kind"] = "spikes"
    first["features"]["body"]["finish"] = "metallic"
    first["mesh"]["LENGTH_BASE"] = 999.0

    second = options_for_enemy("slug", {})
    assert second["zone_geometry_extras"]["body"]["kind"] == "none"
    assert second["features"]["body"]["finish"] == "default"
    assert second["mesh"]["LENGTH_BASE"] != 999.0


def test_R5_validate_build_options_is_deterministic_for_corrupt_payload() -> None:
    from src.utils.build_options import validate_build_options

    payload = {
        "mesh": {"LENGTH_BASE": "not-a-float", "WIDTH_BASE": None},
        "zone_geometry_extras": {"body": {"kind": "spikes", "spike_count": "bad"}},
        "features": {"body": "not-a-dict"},
    }
    first = validate_build_options("slug", payload)
    second = validate_build_options("slug", payload)
    assert first == second


def test_R5_normalize_controls_ignores_non_mapping_enemy_envelope() -> None:
    from src.utils.build_options import normalize_controls

    normalized = normalize_controls(
        "spider",
        {
            "spider": "not-a-dict",
            "eye_count": 4,
            "mesh": {"BODY_BASE": 1.4},
        },
    )
    # CHECKPOINT: assumes non-dict enemy envelope is ignored instead of raising.
    assert normalized["eye_count"] == 4
    assert normalized["mesh"]["BODY_BASE"] == 1.4


def test_R7_no_runtime_imports_reference_legacy_build_option_modules() -> None:
    root = asset_generation_python_root()
    disallowed = (
        "utils.build_options.animated_build_options",
        "utils.build_options.animated_build_options_appendage_defs",
        "utils.build_options.animated_build_options_mesh_controls",
        "utils.build_options.animated_build_options_validate",
        "utils.build_options.animated_build_options_zone_texture",
        "utils.build_options.animated_build_options_spider_eye",
        "utils.build_options.animated_build_options_part_feature_defs",
    )
    violations: list[str] = []
    for rel in _REPO_IMPORT_SCAN_ROOTS:
        tree = root / rel
        if not tree.is_dir():
            continue
        for path in tree.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if path.name == "test_m901_06_animated_build_options_consolidation.py":
                continue
            text = path.read_text(encoding="utf-8")
            for needle in disallowed:
                if needle in text:
                    violations.append(f"{path}: {needle}")
    assert not violations, "\n".join(violations[:80])

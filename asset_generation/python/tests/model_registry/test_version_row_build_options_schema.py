"""
Registry version-row ``build_options`` manifest validation (FEAT-20260522).

Spec: R1 (schema allowlist, coerce, omit empty), R7 (size cap, patch preservation).
"""

from __future__ import annotations

import json

import pytest

from src.model_registry.schema import validate_manifest
from src.model_registry.service import (
    default_migrated_manifest,
    patch_enemy_version,
    save_manifest_atomic,
)
from src.utils.build_options import (
    coerce_validate_enemy_build_options,
    options_for_enemy,
)

_BUILD_OPTIONS_MAX_BYTES = 262_144


def _spider_snapshot(**overrides: object) -> dict[str, object]:
    merged = options_for_enemy("spider", dict(overrides))
    return coerce_validate_enemy_build_options("spider", merged)


def test_validate_manifest_accepts_version_row_with_build_options() -> None:
    snap = _spider_snapshot(eye_count=6)
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = snap
    out = validate_manifest(manifest)
    row = out["enemies"]["spider"]["versions"][0]
    assert row["build_options"]["eye_count"] == 6


def test_validate_manifest_rejects_build_options_non_object() -> None:
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = "not-an-object"
    with pytest.raises(ValueError, match="build_options"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_invalid_build_options_coercion() -> None:
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = {"mesh": "not-a-dict"}
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_validate_manifest_omits_empty_build_options_after_coercion() -> None:
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = {}
    out = validate_manifest(manifest)
    row = out["enemies"]["spider"]["versions"][0]
    assert "build_options" not in row


def test_validate_manifest_player_row_uses_player_slime_coercion() -> None:
    snap = coerce_validate_enemy_build_options("player_slime", options_for_enemy("player_slime", {}))
    manifest = default_migrated_manifest()
    manifest["player"]["versions"] = [
        {
            "id": "player_test_00",
            "path": "player_exports/player_test_00.glb",
            "draft": False,
            "in_use": True,
            "build_options": snap,
        },
    ]
    out = validate_manifest(manifest)
    assert "build_options" in out["player"]["versions"][0]


def test_validate_manifest_build_options_at_size_cap_minus_one_persists() -> None:
    snap = _spider_snapshot()
    serialized = json.dumps(snap, separators=(",", ":"), ensure_ascii=False)
    pad_key = "feat_body_texture_pattern_hex"
    pad_len = (
        _BUILD_OPTIONS_MAX_BYTES
        - len(serialized.encode("utf-8"))
        - len(f',"{pad_key}":"')
        - len('"}')
    )
    if pad_len > 0:
        snap = dict(snap)
        snap[pad_key] = "a" * pad_len
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = snap
    out = validate_manifest(manifest)
    assert "build_options" in out["enemies"]["spider"]["versions"][0]


def test_validate_manifest_build_options_over_size_cap_raises() -> None:
    snap = _spider_snapshot()
    snap = dict(snap)
    snap["feat_body_texture_pattern_hex"] = "f" * (_BUILD_OPTIONS_MAX_BYTES + 1)
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = snap
    with pytest.raises(ValueError, match="build_options too large"):
        validate_manifest(manifest)


def test_patch_enemy_version_preserves_build_options(tmp_path) -> None:
    snap = _spider_snapshot(eye_count=8)
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = snap
    save_manifest_atomic(tmp_path, validate_manifest(manifest))
    patch_enemy_version(tmp_path, "spider", "spider_animated_00", {"draft": True, "in_use": False})
    raw = json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))
    row = raw["enemies"]["spider"]["versions"][0]
    assert row["build_options"]["eye_count"] == 8

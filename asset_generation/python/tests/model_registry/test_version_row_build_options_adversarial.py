"""
Adversarial manifest validation for registry ``versions[].build_options``.

Spec: R1, R4, R7 — malformed types, coercion traps, PATCH key rejection, size boundary.
Traceability: FEAT-20260522 registry build-options snapshot.
"""

from __future__ import annotations

import json

import pytest

from src.model_registry.schema import validate_manifest
from src.model_registry.service import (
    default_migrated_manifest,
    patch_enemy_version,
    patch_player_version,
    save_manifest_atomic,
)
from src.utils.build_options import coerce_validate_enemy_build_options, options_for_enemy

_BUILD_OPTIONS_MAX_BYTES = 262_144


def _spider_snap(**overrides: object) -> dict[str, object]:
    return coerce_validate_enemy_build_options("spider", options_for_enemy("spider", dict(overrides)))


@pytest.mark.parametrize(
    "bad_value",
    [
        None,
        [],
        42,
        True,
        "string-snapshot",
    ],
    ids=["null", "list", "int", "bool", "str"],
)
def test_validate_manifest_rejects_non_object_build_options(bad_value: object) -> None:
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = bad_value
    with pytest.raises(ValueError, match="build_options"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_build_options_with_null_mesh() -> None:
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = {"mesh": None}
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_validate_manifest_player_row_rejects_invalid_player_slime_coercion() -> None:
    manifest = default_migrated_manifest()
    manifest["player"]["versions"] = [
        {
            "id": "player_adv_00",
            "path": "player_exports/player_adv_00.glb",
            "draft": False,
            "in_use": True,
            "build_options": {"mesh": "not-a-dict"},
        },
    ]
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_validate_manifest_enemy_and_player_snapshots_use_distinct_coercion_pipelines() -> None:
    spider_snap = _spider_snap(eye_count=6)
    player_snap = coerce_validate_enemy_build_options(
        "player_slime",
        options_for_enemy("player_slime", {"eye_count": 2}),
    )
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = spider_snap
    manifest["player"]["versions"] = [
        {
            "id": "player_adv_01",
            "path": "player_exports/player_adv_01.glb",
            "draft": False,
            "in_use": True,
            "build_options": player_snap,
        },
    ]
    out = validate_manifest(manifest)
    assert out["enemies"]["spider"]["versions"][0]["build_options"]["eye_count"] == 6
    assert out["player"]["versions"][0]["build_options"]["eye_count"] == 2


def test_validate_manifest_build_options_exactly_at_utf8_cap_persists() -> None:
    snap = _spider_snap()
    serialized = json.dumps(snap, separators=(",", ":"), ensure_ascii=False)
    pad_len = _BUILD_OPTIONS_MAX_BYTES - len(serialized.encode("utf-8")) - len(',"feat_body_hex":"') - len('"}')
    if pad_len > 0:
        snap = dict(snap)
        snap["feat_body_hex"] = "a" * max(0, pad_len)
    manifest = default_migrated_manifest()
    manifest["enemies"]["spider"]["versions"][0]["build_options"] = snap
    out = validate_manifest(manifest)
    row = out["enemies"]["spider"]["versions"][0]
    assert "build_options" in row
    assert len(json.dumps(row["build_options"], separators=(",", ":")).encode("utf-8")) <= _BUILD_OPTIONS_MAX_BYTES


def test_patch_enemy_version_rejects_client_build_options_key(tmp_path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    attacker = coerce_validate_enemy_build_options("imp", options_for_enemy("imp", {"eye_count": 99}))
    with pytest.raises(ValueError, match="unsupported patch keys"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"build_options": attacker})


def test_patch_player_version_rejects_client_build_options_key(tmp_path) -> None:
    manifest = default_migrated_manifest()
    manifest["player"]["versions"] = [
        {
            "id": "player_patch_adv",
            "path": "player_exports/player_patch_adv.glb",
            "draft": False,
            "in_use": True,
        },
    ]
    save_manifest_atomic(tmp_path, validate_manifest(manifest))
    with pytest.raises(ValueError, match="unsupported patch keys"):
        patch_player_version(tmp_path, "player_patch_adv", {"build_options": {"eye_count": 1}})

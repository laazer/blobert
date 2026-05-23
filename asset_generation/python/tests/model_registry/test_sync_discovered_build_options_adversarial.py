"""
Adversarial ``sync_discovered_*`` backfill when sidecars are corrupt or disagree (R4).

Missing registry + missing sidecar; semantically invalid JSON objects; player parity.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.model_registry.service import (
    default_migrated_manifest,
    load_effective_manifest,
    save_manifest_atomic,
    sync_discovered_animated_glb_versions,
    sync_discovered_player_glb_versions,
)
from src.utils.build_options import (
    coerce_validate_enemy_build_options,
    options_for_enemy,
)


def test_sync_discovered_row_without_registry_or_sidecar_has_no_build_options(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "imp_animated_no_bo"
    (export_dir / f"{stem}.glb").write_bytes(b"x")

    sync_discovered_animated_glb_versions(tmp_path, "imp")
    row = next(r for r in load_effective_manifest(tmp_path)["enemies"]["imp"]["versions"] if r["id"] == stem)
    assert "build_options" not in row


def test_sync_discovered_sidecar_empty_object_leaves_row_without_snapshot(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "imp_animated_empty_bo"
    (export_dir / f"{stem}.glb").write_bytes(b"x")
    (export_dir / f"{stem}.build_options.json").write_text("{}", encoding="utf-8")

    sync_discovered_animated_glb_versions(tmp_path, "imp")
    row = next(r for r in load_effective_manifest(tmp_path)["enemies"]["imp"]["versions"] if r["id"] == stem)
    assert "build_options" not in row


def test_sync_discovered_sidecar_json_array_treated_as_empty_parse(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "imp_animated_array_bo"
    (export_dir / f"{stem}.glb").write_bytes(b"x")
    (export_dir / f"{stem}.build_options.json").write_text("[1, 2]", encoding="utf-8")

    sync_discovered_animated_glb_versions(tmp_path, "imp")
    row = next(r for r in load_effective_manifest(tmp_path)["enemies"]["imp"]["versions"] if r["id"] == stem)
    assert "build_options" not in row


def test_sync_discovered_sidecar_valid_json_invalid_coercion_leaves_row_unchanged(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "imp_animated_bad_mesh"
    (export_dir / f"{stem}.glb").write_bytes(b"x")
    (export_dir / f"{stem}.build_options.json").write_text(
        json.dumps({"mesh": "not-a-dict"}),
        encoding="utf-8",
    )

    sync_discovered_animated_glb_versions(tmp_path, "imp")
    row = next(r for r in load_effective_manifest(tmp_path)["enemies"]["imp"]["versions"] if r["id"] == stem)
    assert "build_options" not in row


def test_sync_discovered_player_without_sidecar_or_registry_snapshot(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    pe = tmp_path / "player_exports"
    pe.mkdir(parents=True)
    stem = "player_no_bo_sidecar"
    (pe / f"{stem}.glb").write_bytes(b"p")

    sync_discovered_player_glb_versions(tmp_path)
    row = next(r for r in load_effective_manifest(tmp_path)["player"]["versions"] if r["id"] == stem)
    assert "build_options" not in row


def test_sync_discovered_player_malformed_sidecar_does_not_crash(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    pe = tmp_path / "player_exports"
    pe.mkdir(parents=True)
    stem = "player_bad_json"
    (pe / f"{stem}.glb").write_bytes(b"p")
    (pe / f"{stem}.build_options.json").write_text("{]", encoding="utf-8")

    sync_discovered_player_glb_versions(tmp_path)
    row = next(r for r in load_effective_manifest(tmp_path)["player"]["versions"] if r["id"] == stem)
    assert "build_options" not in row


def test_sync_discovered_player_backfill_matches_enemy_semantics(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    pe = tmp_path / "player_exports"
    pe.mkdir(parents=True)
    stem = "player_slime_blue_99"
    (pe / f"{stem}.glb").write_bytes(b"p")
    snap = coerce_validate_enemy_build_options(
        "player_slime",
        options_for_enemy("player_slime", {"mouth_shape": "grimace"}),
    )
    (pe / f"{stem}.build_options.json").write_text(json.dumps(snap), encoding="utf-8")

    out = sync_discovered_player_glb_versions(tmp_path)
    row = next(r for r in out["player"]["versions"] if r["id"] == stem)
    assert row["build_options"]["mouth_shape"] == "grimace"

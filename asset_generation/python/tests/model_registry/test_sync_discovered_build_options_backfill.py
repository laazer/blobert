"""
``sync_discovered_*`` idempotent ``build_options`` backfill from sidecars (FEAT-20260522).

Spec: R4.
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


def _write_sidecar(export_dir: Path, stem: str, family: str, **overrides: object) -> None:
    snap = coerce_validate_enemy_build_options(
        family if family != "player" else "player_slime",
        options_for_enemy(family if family != "player" else "player_slime", dict(overrides)),
    )
    (export_dir / f"{stem}.build_options.json").write_text(
        json.dumps(snap),
        encoding="utf-8",
    )


def test_sync_discovered_backfills_build_options_from_sidecar(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "spider_animated_01"
    (export_dir / f"{stem}.glb").write_bytes(b"x")
    _write_sidecar(export_dir, stem, "spider", eye_count=8)

    out = sync_discovered_animated_glb_versions(tmp_path, "spider")
    row = next(r for r in out["enemies"]["spider"]["versions"] if r["id"] == stem)
    assert row["build_options"]["eye_count"] == 8


def test_sync_discovered_does_not_overwrite_existing_registry_snapshot(tmp_path: Path) -> None:
    registry_snap = coerce_validate_enemy_build_options("spider", options_for_enemy("spider", {"eye_count": 3}))
    sidecar_snap = coerce_validate_enemy_build_options("spider", options_for_enemy("spider", {"eye_count": 99}))

    m = default_migrated_manifest()
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "spider_animated_01"
    path = f"animated_exports/{stem}.glb"
    m["enemies"]["spider"]["versions"].append(
        {
            "id": stem,
            "path": path,
            "draft": True,
            "in_use": False,
            "build_options": registry_snap,
        },
    )
    save_manifest_atomic(tmp_path, m)
    (export_dir / f"{stem}.glb").write_bytes(b"x")
    (export_dir / f"{stem}.build_options.json").write_text(
        json.dumps(sidecar_snap),
        encoding="utf-8",
    )

    out = sync_discovered_animated_glb_versions(tmp_path, "spider")
    row = next(r for r in out["enemies"]["spider"]["versions"] if r["id"] == stem)
    assert row["build_options"]["eye_count"] == 3


def test_sync_discovered_backfill_is_idempotent(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "spider_animated_01"
    (export_dir / f"{stem}.glb").write_bytes(b"x")
    _write_sidecar(export_dir, stem, "spider", eye_count=5)

    out1 = sync_discovered_animated_glb_versions(tmp_path, "spider")
    out2 = sync_discovered_animated_glb_versions(tmp_path, "spider")
    assert out1 == out2


def test_sync_discovered_player_backfills_from_build_options_sidecar(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    pe = tmp_path / "player_exports"
    pe.mkdir(parents=True)
    stem = "player_sync_bo_00"
    (pe / f"{stem}.glb").write_bytes(b"p")
    _write_sidecar(pe, stem, "player", mouth_enabled=True)

    out = sync_discovered_player_glb_versions(tmp_path)
    row = next(r for r in out["player"]["versions"] if r["id"] == stem)
    assert row["build_options"]["mouth_enabled"] is True


def test_sync_discovered_malformed_sidecar_leaves_row_without_snapshot(tmp_path: Path) -> None:
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    stem = "spider_animated_01"
    (export_dir / f"{stem}.glb").write_bytes(b"x")
    (export_dir / f"{stem}.build_options.json").write_text("not-json{{{", encoding="utf-8")

    sync_discovered_animated_glb_versions(tmp_path, "spider")
    reloaded = load_effective_manifest(tmp_path)
    row = next(r for r in reloaded["enemies"]["spider"]["versions"] if r["id"] == stem)
    assert "build_options" not in row

"""Adversarial tests for registry-fix-versions-slots-load (slots, sync, isolation)."""

from pathlib import Path

import pytest

from src.model_registry.service import (
    default_migrated_manifest,
    load_effective_manifest,
    patch_enemy_version,
    put_enemy_slots,
    put_player_slots,
    save_manifest_atomic,
    sync_discovered_animated_glb_versions,
    validate_manifest,
)


def test_put_enemy_slots_r2_all_placeholder_entries_non_empty_list_succeeds(tmp_path: Path):
    """registry-fix-versions-slots-load R2: structural validity for [\"\", \"\"] without assigned ids."""
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    out = put_enemy_slots(tmp_path, "imp", ["", ""])
    assert out["version_ids"] == ["", ""]
    assert out["resolved_paths"] == []
    assert load_effective_manifest(tmp_path)["enemies"]["imp"]["slots"] == ["", ""]


def test_put_enemy_slots_stress_many_placeholders_single_trailing_valid_id(tmp_path: Path):
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"].append(
        {
            "id": "imp_animated_01",
            "path": "animated_exports/imp_animated_01.glb",
            "draft": False,
            "in_use": True,
        },
    )
    save_manifest_atomic(tmp_path, validate_manifest(m))
    padding = [""] * 48
    payload = padding + ["imp_animated_01"]
    out = put_enemy_slots(tmp_path, "imp", payload)
    assert out["version_ids"] == payload
    assert out["resolved_paths"] == ["animated_exports/imp_animated_01.glb"]


def test_put_player_slots_r2_all_placeholders_and_reject_empty_list(tmp_path: Path):
    m = default_migrated_manifest()
    m["player"] = {
        "versions": [
            {"id": "pa", "path": "player_exports/pa.glb", "draft": False, "in_use": True},
        ],
        "slots": ["pa"],
    }
    save_manifest_atomic(tmp_path, validate_manifest(m))
    (tmp_path / "player_exports").mkdir(parents=True)
    (tmp_path / "player_exports" / "pa.glb").write_bytes(b"x")

    out = put_player_slots(tmp_path, ["", "", ""])
    assert out["version_ids"] == ["", "", ""]
    assert out["resolved_paths"] == []

    with pytest.raises(ValueError, match="must not be empty"):
        put_player_slots(tmp_path, [])


@pytest.mark.parametrize(
    ("version_ids", "error_type", "error_match"),
    [
        (["pa", "pa"], ValueError, "duplicate"),
        (["missing", "pa"], KeyError, "unknown player version"),
    ],
)
def test_put_player_slots_invalid_payload_never_partially_mutates_slots(
    tmp_path: Path,
    version_ids: list[str],
    error_type: type[Exception],
    error_match: str,
):
    m = default_migrated_manifest()
    m["player"] = {
        "versions": [
            {"id": "pa", "path": "player_exports/pa.glb", "draft": False, "in_use": True},
            {"id": "pb", "path": "player_exports/pb.glb", "draft": False, "in_use": True},
        ],
        "slots": ["pa", "pb"],
    }
    save_manifest_atomic(tmp_path, validate_manifest(m))
    pe = tmp_path / "player_exports"
    pe.mkdir(parents=True)
    (pe / "pa.glb").write_bytes(b"x")
    (pe / "pb.glb").write_bytes(b"x")

    # CHECKPOINT: invalid player slot PUT must not leave a half-written slot array.
    with pytest.raises(error_type, match=error_match):
        put_player_slots(tmp_path, version_ids)

    reloaded = load_effective_manifest(tmp_path)
    assert reloaded["player"]["slots"] == ["pa", "pb"]


def test_r1_sync_stress_appends_many_distinct_enemy_rows_without_dropping_prior(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    before_count = len(load_effective_manifest(tmp_path)["enemies"]["slug"]["versions"])
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    for i in range(1, 15):
        (export_dir / f"slug_animated_{i:02d}.glb").write_bytes(b"x")
    out = sync_discovered_animated_glb_versions(tmp_path, "slug")
    ids = {r["id"] for r in out["enemies"]["slug"]["versions"]}
    assert "slug_animated_00" in ids
    for i in range(1, 15):
        assert f"slug_animated_{i:02d}" in ids
    assert len(out["enemies"]["slug"]["versions"]) == before_count + 14


def test_patch_enemy_then_put_slots_order_preserves_other_family_slots(tmp_path: Path):
    """R1 + R2: mutating one family's slots does not touch another family's slot list."""
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"].append(
        {
            "id": "imp_animated_01",
            "path": "animated_exports/imp_animated_01.glb",
            "draft": False,
            "in_use": True,
        },
    )
    m["enemies"]["imp"]["slots"] = ["imp_animated_00"]
    m["enemies"]["slug"]["slots"] = ["slug_animated_00"]
    save_manifest_atomic(tmp_path, validate_manifest(m))
    patch_enemy_version(tmp_path, "imp", "imp_animated_01", {"name": "Sidecar"})
    put_enemy_slots(tmp_path, "imp", ["imp_animated_01", "", "imp_animated_00"])
    final = load_effective_manifest(tmp_path)
    assert final["enemies"]["slug"]["slots"] == ["slug_animated_00"]
    assert final["enemies"]["imp"]["slots"] == ["imp_animated_01", "", "imp_animated_00"]

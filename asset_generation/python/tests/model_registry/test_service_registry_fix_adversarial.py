"""Adversarial tests for registry-fix-versions-slots-load (slots, sync, isolation)."""

from pathlib import Path

import pytest

from src.model_registry.service import (
    default_migrated_manifest,
    load_effective_manifest,
    patch_enemy_version,
    patch_player_active_visual,
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


def test_save_manifest_atomic_validation_failure_keeps_existing_file_unchanged(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    before = (tmp_path / "model_registry.json").read_text(encoding="utf-8")

    invalid = default_migrated_manifest()
    invalid["unexpected"] = {"break": True}
    with pytest.raises(ValueError, match="unexpected top-level keys"):
        save_manifest_atomic(tmp_path, invalid)

    after = (tmp_path / "model_registry.json").read_text(encoding="utf-8")
    assert after == before


def test_load_effective_manifest_invalid_utf8_bytes_raise_decode_error(tmp_path: Path):
    (tmp_path / "model_registry.json").write_bytes(b"\xff\xfe\xfd")
    with pytest.raises(UnicodeDecodeError):
        load_effective_manifest(tmp_path)


def test_put_enemy_slots_whitespace_id_rejected_and_slots_unchanged(tmp_path: Path):
    m = default_migrated_manifest()
    m["enemies"]["imp"]["slots"] = ["imp_animated_00"]
    save_manifest_atomic(tmp_path, validate_manifest(m))

    with pytest.raises(KeyError, match="unknown version"):
        put_enemy_slots(tmp_path, "imp", [" ", "imp_animated_00"])

    reloaded = load_effective_manifest(tmp_path)
    assert reloaded["enemies"]["imp"]["slots"] == ["imp_animated_00"]


def test_sync_discovered_animated_accepts_uppercase_glb_extension(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    (export_dir / "imp_animated_03.GLB").write_bytes(b"x")

    # CHECKPOINT: conservative assumption — discovery treats GLB extension case-insensitively.
    out = sync_discovered_animated_glb_versions(tmp_path, "imp")
    ids = {r["id"] for r in out["enemies"]["imp"]["versions"]}
    assert "imp_animated_03" in ids


@pytest.mark.parametrize(
    "version_row",
    [
        {
            "id": "imp_animated_01",
            "path": "animated_exports/imp_animated_01.glb",
            "draft": True,
            "in_use": False,
        },
        {
            "id": "imp_animated_01",
            "path": "animated_exports/imp_animated_01.glb",
            "draft": False,
            "in_use": False,
        },
    ],
)
def test_put_enemy_slots_rejects_non_eligible_versions_without_partial_slot_write(
    tmp_path: Path,
    version_row: dict[str, object],
):
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"].append(version_row)
    m["enemies"]["imp"]["slots"] = ["imp_animated_00"]
    save_manifest_atomic(tmp_path, validate_manifest(m))

    # CHECKPOINT: conservative assumption — validator coercion preserves canonical
    # (draft=True, in_use=False) state and slot writes still fail atomically.
    with pytest.raises(ValueError, match="is draft and cannot be slotted"):
        put_enemy_slots(tmp_path, "imp", ["imp_animated_01"])

    reloaded = load_effective_manifest(tmp_path)
    assert reloaded["enemies"]["imp"]["slots"] == ["imp_animated_00"]


def test_patch_player_active_visual_duplicate_stem_path_keeps_existing_canonical_path(
    tmp_path: Path,
):
    m = default_migrated_manifest()
    m["player"] = {
        "versions": [
            {"id": "hero", "path": "player_exports/hero.glb", "draft": False, "in_use": True},
        ],
        "slots": ["hero"],
    }
    save_manifest_atomic(tmp_path, validate_manifest(m))

    out = patch_player_active_visual(tmp_path, path="player_exports/draft/hero.glb")
    player_versions = out["player"]["versions"]
    ids = [row["id"] for row in player_versions]
    assert "hero" in ids
    assert ids == ["hero"]
    # CHECKPOINT: conservative assumption — id collision resolves to existing canonical row.
    assert player_versions[0]["path"] == "player_exports/hero.glb"
    assert out["player"]["slots"][0] == "hero"


def test_patch_player_active_visual_path_only_preserves_existing_slot_order_tail(tmp_path: Path):
    m = default_migrated_manifest()
    m["player"] = {
        "versions": [
            {"id": "pa", "path": "player_exports/pa.glb", "draft": False, "in_use": True},
            {"id": "pb", "path": "player_exports/pb.glb", "draft": False, "in_use": True},
            {"id": "pc", "path": "player_exports/pc.glb", "draft": False, "in_use": True},
        ],
        "slots": ["pa", "pb", "pc"],
    }
    save_manifest_atomic(tmp_path, validate_manifest(m))

    out = patch_player_active_visual(tmp_path, path="player_exports/pb.glb")
    assert out["player"]["slots"] == ["pb", "pa", "pc"]

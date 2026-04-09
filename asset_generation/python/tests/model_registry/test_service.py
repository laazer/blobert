"""Tests for ``src.model_registry.service`` (MRVC persistence + spawn consumer)."""

import json
from pathlib import Path
from unittest import mock

import pytest

from src.model_registry.service import (
    default_migrated_manifest,
    get_enemy_slots,
    load_effective_manifest,
    patch_enemy_version,
    patch_player_active_visual,
    put_enemy_slots,
    registry_path,
    save_manifest_atomic,
    spawn_eligible_paths,
    sync_discovered_animated_glb_versions,
    validate_manifest,
)


def test_default_migrated_has_all_animated_slugs():
    m = default_migrated_manifest()
    assert m["schema_version"] == 1
    assert m["player_active_visual"] is None
    for slug in ("spider", "spitter", "claw_crawler"):
        assert slug in m["enemies"]
        vers = m["enemies"][slug]["versions"]
        assert len(vers) == 1
        assert vers[0]["draft"] is False
        assert vers[0]["in_use"] is True
        assert vers[0]["path"].startswith("animated_exports/")


def test_validate_rejects_traversal_path():
    base = default_migrated_manifest()
    base["enemies"]["spider"]["versions"][0]["path"] = "animated_exports/../secrets.glb"
    with pytest.raises(ValueError, match="invalid path"):
        validate_manifest(base)


def test_validate_normalizes_draft_and_in_use():
    base = default_migrated_manifest()
    base["enemies"]["imp"]["versions"][0]["draft"] = True
    base["enemies"]["imp"]["versions"][0]["in_use"] = True
    out = validate_manifest(base)
    assert out["enemies"]["imp"]["versions"][0]["in_use"] is False


def test_spawn_eligible_excludes_draft(tmp_path: Path):
    m = default_migrated_manifest()
    m["enemies"]["slug"]["versions"][0]["draft"] = True
    m["enemies"]["slug"]["versions"][0]["in_use"] = True
    m = validate_manifest(m)
    assert spawn_eligible_paths(m, "slug") == []


def test_spawn_eligible_excludes_not_in_use(tmp_path: Path):
    m = default_migrated_manifest()
    m["enemies"]["slug"]["versions"][0]["in_use"] = False
    m = validate_manifest(m)
    assert spawn_eligible_paths(m, "slug") == []


def test_load_effective_missing_file_uses_default(tmp_path: Path):
    m = load_effective_manifest(tmp_path)
    assert "spider" in m["enemies"]


def test_save_and_reload_round_trip(tmp_path: Path):
    m = default_migrated_manifest()
    save_manifest_atomic(tmp_path, m)
    path = tmp_path / "model_registry.json"
    assert path.is_file()
    again = load_effective_manifest(tmp_path)
    assert again["enemies"]["imp"]["versions"][0]["path"] == m["enemies"]["imp"]["versions"][0]["path"]


def test_patch_enemy_version_persists(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"draft": True, "in_use": False})
    raw = json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))
    row = raw["enemies"]["imp"]["versions"][0]
    assert row["draft"] is True
    assert row["in_use"] is False


def test_patch_unknown_family_raises(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError):
        patch_enemy_version(tmp_path, "nope_family", "v0", {"draft": True})


def test_validate_rejects_non_object():
    with pytest.raises(ValueError, match="must be a JSON object"):
        validate_manifest([])  # type: ignore[arg-type]


def test_validate_rejects_extra_top_level_key():
    m = default_migrated_manifest()
    m["extra_key"] = 1
    with pytest.raises(ValueError, match="unexpected top-level keys"):
        validate_manifest(m)


def test_validate_rejects_wrong_schema_version():
    m = default_migrated_manifest()
    m["schema_version"] = 99
    with pytest.raises(ValueError, match="unsupported schema_version"):
        validate_manifest(m)


def test_validate_enemies_must_be_object():
    m = default_migrated_manifest()
    m["enemies"] = []
    with pytest.raises(ValueError, match="enemies must be an object"):
        validate_manifest(m)


def test_validate_family_key_non_string():
    m = default_migrated_manifest()
    m["enemies"] = {"": {"versions": []}}
    with pytest.raises(ValueError, match="non-empty strings"):
        validate_manifest(m)


def test_validate_family_value_not_object():
    m = default_migrated_manifest()
    m["enemies"] = {"imp": []}
    with pytest.raises(ValueError, match="must be an object"):
        validate_manifest(m)


def test_validate_versions_not_array():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"] = {}
    with pytest.raises(ValueError, match="must be an array"):
        validate_manifest(m)


def test_validate_version_row_not_object():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"] = [[]]
    with pytest.raises(ValueError, match="must be an object"):
        validate_manifest(m)


def test_validate_version_missing_field():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"] = [{"id": "x", "path": "animated_exports/x.glb", "draft": False}]
    with pytest.raises(ValueError, match="missing"):
        validate_manifest(m)


def test_validate_version_id_not_string():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"] = [
        {"id": "", "path": "animated_exports/imp_animated_00.glb", "draft": False, "in_use": True},
    ]
    with pytest.raises(ValueError, match="id invalid"):
        validate_manifest(m)


def test_validate_duplicate_version_id():
    p = "animated_exports/imp_animated_00.glb"
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"] = [
        {"id": "same", "path": p, "draft": False, "in_use": True},
        {"id": "same", "path": p, "draft": True, "in_use": False},
    ]
    with pytest.raises(ValueError, match="duplicate version id"):
        validate_manifest(m)


def test_validate_draft_in_use_must_be_bool():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"][0]["draft"] = "no"
    with pytest.raises(ValueError, match="booleans"):
        validate_manifest(m)


def test_validate_player_active_visual_extra_keys():
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "player_exports/p_00.glb", "draft": False, "extra": 1}
    with pytest.raises(ValueError, match="only path and draft"):
        validate_manifest(m)


def test_validate_player_path_invalid():
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "bad/x.glb", "draft": False}
    with pytest.raises(ValueError, match="invalid player_active_visual.path"):
        validate_manifest(m)


def test_validate_player_draft_not_bool():
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "player_exports/p_00.glb", "draft": "x"}
    with pytest.raises(ValueError, match="draft must be boolean"):
        validate_manifest(m)


def test_validate_player_active_visual_not_object():
    m = default_migrated_manifest()
    m["player_active_visual"] = "nope"
    with pytest.raises(ValueError, match="null or an object"):
        validate_manifest(m)


def test_validate_player_branch_preserves_valid():
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "player_exports/p_00.glb", "draft": True}
    out = validate_manifest(m)
    assert out["player_active_visual"] == {"path": "player_exports/p_00.glb", "draft": True}


def test_load_effective_invalid_json(tmp_path: Path):
    registry_path(tmp_path).write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_effective_manifest(tmp_path)


def test_load_effective_root_not_object(tmp_path: Path):
    registry_path(tmp_path).write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_effective_manifest(tmp_path)


def test_save_atomic_unlinks_tmp_on_replace_failure(tmp_path: Path):
    m = validate_manifest(default_migrated_manifest())
    with mock.patch("src.model_registry.service.os.replace", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            save_manifest_atomic(tmp_path, m)


def test_patch_enemy_requires_flag(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="at least one patch field"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {})


def test_patch_enemy_unknown_version(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError, match="unknown version"):
        patch_enemy_version(tmp_path, "imp", "not_real", {"draft": True})


def test_patch_enemy_version_name_set_and_clear(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"name": "  Boss imp  "})
    raw = json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))
    assert raw["enemies"]["imp"]["versions"][0]["name"] == "Boss imp"
    patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"name": None})
    raw2 = json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))
    assert "name" not in raw2["enemies"]["imp"]["versions"][0]


def test_validate_version_name_too_long(tmp_path: Path):
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"][0]["name"] = "x" * 129
    with pytest.raises(ValueError, match="name exceeds max"):
        validate_manifest(m)


def test_validate_version_rejects_unknown_keys():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"][0]["extra_field"] = "nope"
    with pytest.raises(ValueError, match="unexpected keys"):
        validate_manifest(m)


def test_validate_version_optional_name_round_trip():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"][0]["name"] = "  Named imp  "
    out = validate_manifest(m)
    assert out["enemies"]["imp"]["versions"][0]["name"] == "Named imp"


def test_validate_version_name_wrong_type():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"][0]["name"] = 123  # type: ignore[assignment]
    with pytest.raises(ValueError, match="name must be a string"):
        validate_manifest(m)


def test_patch_enemy_version_rejects_unknown_keys(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="unsupported patch keys"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"draft": True, "bogus": 1})


def test_patch_enemy_version_draft_must_be_bool(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="patch draft must be boolean"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"draft": "yes"})


def test_patch_enemy_version_in_use_must_be_bool(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="patch in_use must be boolean"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"in_use": 1})


def test_patch_enemy_version_name_whitespace_clears(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"name": "keep"})
    patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"name": "   "})
    raw = json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))
    assert "name" not in raw["enemies"]["imp"]["versions"][0]


def test_patch_enemy_version_name_too_long_in_patch(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="exceeds max length"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"name": "x" * 129})


def test_patch_enemy_version_name_type_rejected(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="patch name must be string or null"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"name": 7})


def test_patch_player_requires_flag(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="at least one"):
        patch_player_active_visual(tmp_path)


def test_patch_player_when_null_requires_path(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="player_active_visual is unset"):
        patch_player_active_visual(tmp_path, draft=False)


def test_patch_player_initializes_from_null_with_path(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    out = patch_player_active_visual(tmp_path, path="player_exports/p_00.glb")
    assert out["player_active_visual"] == {"path": "player_exports/p_00.glb", "draft": False}


def test_patch_player_initializes_from_null_rejects_non_allowlisted_path(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="invalid player path"):
        patch_player_active_visual(tmp_path, path="outside/x.glb")
    raw = json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))
    assert raw.get("player_active_visual") is None


def test_patch_player_updates_path_and_draft(tmp_path: Path):
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "player_exports/old_00.glb", "draft": True}
    save_manifest_atomic(tmp_path, validate_manifest(m))
    out = patch_player_active_visual(
        tmp_path,
        draft=False,
        path="player_exports/new_00.glb",
    )
    assert out["player_active_visual"] == {"path": "player_exports/new_00.glb", "draft": False}


def test_patch_player_rejects_non_allowlisted_path(tmp_path: Path):
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "player_exports/p_00.glb", "draft": False}
    save_manifest_atomic(tmp_path, validate_manifest(m))
    with pytest.raises(ValueError, match="invalid player path"):
        patch_player_active_visual(tmp_path, path="outside/x.glb")


def test_patch_player_rejects_non_glb_path(tmp_path: Path):
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "player_exports/p_00.glb", "draft": False}
    save_manifest_atomic(tmp_path, validate_manifest(m))
    with pytest.raises(ValueError, match=r"must end with \.glb"):
        patch_player_active_visual(tmp_path, path="player_exports/p_00.gltf")


def test_get_enemy_slots_returns_empty_when_slots_missing(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    payload = get_enemy_slots(tmp_path, "imp")
    assert payload == {"family": "imp", "version_ids": [], "resolved_paths": []}


def test_get_enemy_slots_unknown_family_raises(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError, match="unknown family"):
        get_enemy_slots(tmp_path, "not_real")


def test_put_enemy_slots_persists_order_and_resolves_paths(tmp_path: Path):
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

    out = put_enemy_slots(tmp_path, "imp", ["imp_animated_01", "imp_animated_00"])
    assert out == {
        "family": "imp",
        "version_ids": ["imp_animated_01", "imp_animated_00"],
        "resolved_paths": [
            "animated_exports/imp_animated_01.glb",
            "animated_exports/imp_animated_00.glb",
        ],
    }

    reloaded = load_effective_manifest(tmp_path)
    assert reloaded["enemies"]["imp"]["slots"] == ["imp_animated_01", "imp_animated_00"]


def test_put_enemy_slots_rejects_empty_list(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="must not be empty"):
        put_enemy_slots(tmp_path, "imp", [])


def test_put_enemy_slots_rejects_duplicate_ids(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="duplicate"):
        put_enemy_slots(tmp_path, "imp", ["imp_animated_00", "imp_animated_00"])


def test_put_enemy_slots_rejects_unknown_version(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError, match="unknown version"):
        put_enemy_slots(tmp_path, "imp", ["missing"])


def test_put_enemy_slots_rejects_draft_version(tmp_path: Path):
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"][0]["draft"] = True
    m["enemies"]["imp"]["versions"][0]["in_use"] = False
    save_manifest_atomic(tmp_path, validate_manifest(m))
    with pytest.raises(ValueError, match="draft and cannot be slotted"):
        put_enemy_slots(tmp_path, "imp", ["imp_animated_00"])


def test_put_enemy_slots_rejects_not_in_use_version(tmp_path: Path):
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"][0]["in_use"] = False
    save_manifest_atomic(tmp_path, validate_manifest(m))
    with pytest.raises(ValueError, match="not in_use and cannot be slotted"):
        put_enemy_slots(tmp_path, "imp", ["imp_animated_00"])


def test_sync_discovered_animated_glb_versions_adds_on_disk_stems(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    (export_dir / "imp_animated_01.glb").write_bytes(b"x")
    out = sync_discovered_animated_glb_versions(tmp_path, "imp")
    ids = [row["id"] for row in out["enemies"]["imp"]["versions"]]
    assert "imp_animated_01" in ids
    row = next(r for r in out["enemies"]["imp"]["versions"] if r["id"] == "imp_animated_01")
    assert row == {
        "id": "imp_animated_01",
        "path": "animated_exports/imp_animated_01.glb",
        "draft": False,
        "in_use": False,
    }


def test_sync_discovered_animated_glb_versions_idempotent(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    out1 = sync_discovered_animated_glb_versions(tmp_path, "imp")
    out2 = sync_discovered_animated_glb_versions(tmp_path, "imp")
    assert out1 == out2


def test_sync_discovered_animated_glb_versions_unknown_family(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError, match="unknown family"):
        sync_discovered_animated_glb_versions(tmp_path, "not_a_family_slug")


@pytest.mark.parametrize(
    ("version_ids", "error_type", "error_match"),
    [
        (["imp_animated_00", "imp_animated_00", "missing"], ValueError, "duplicate"),
        (["missing", "imp_animated_00"], KeyError, "unknown version"),
        (["imp_animated_01", "imp_animated_00"], ValueError, "draft and cannot be slotted"),
        (["imp_animated_02", "imp_animated_00"], ValueError, "not in_use and cannot be slotted"),
    ],
)
def test_put_enemy_slots_rejected_payload_never_partially_mutates_slots(
    tmp_path: Path,
    version_ids: list[str],
    error_type: type[Exception],
    error_match: str,
):
    m = default_migrated_manifest()
    m["enemies"]["imp"]["versions"].append(
        {
            "id": "imp_animated_01",
            "path": "animated_exports/imp_animated_01.glb",
            "draft": True,
            "in_use": False,
        },
    )
    m["enemies"]["imp"]["versions"].append(
        {
            "id": "imp_animated_02",
            "path": "animated_exports/imp_animated_02.glb",
            "draft": False,
            "in_use": False,
        },
    )
    m["enemies"]["imp"]["slots"] = ["imp_animated_00"]
    save_manifest_atomic(tmp_path, validate_manifest(m))

    # CHECKPOINT: mixed-invalid payloads fail deterministically before any slot write.
    with pytest.raises(error_type, match=error_match):
        put_enemy_slots(tmp_path, "imp", version_ids)

    reloaded = load_effective_manifest(tmp_path)
    assert reloaded["enemies"]["imp"]["slots"] == ["imp_animated_00"]


def test_put_enemy_slots_mixed_invalid_precedence_prefers_duplicate_guard(tmp_path: Path):
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

    with pytest.raises(ValueError, match="duplicate"):
        put_enemy_slots(tmp_path, "imp", ["missing", "missing", "imp_animated_01"])


@pytest.mark.parametrize(
    "invalid_path",
    [
        "player_exports/new_00.GLB",
        "player_exports/new_00.glb ",
        "player_exports/new_00.glb?cache=1",
        "player_exports/new_00.glb/child",
    ],
)
def test_patch_player_rejects_malformed_allowlisted_non_glb_variants(
    tmp_path: Path,
    invalid_path: str,
):
    m = default_migrated_manifest()
    m["player_active_visual"] = {"path": "player_exports/original_00.glb", "draft": False}
    save_manifest_atomic(tmp_path, validate_manifest(m))

    with pytest.raises(ValueError, match=r"must end with \.glb"):
        patch_player_active_visual(tmp_path, path=invalid_path)

    reloaded = load_effective_manifest(tmp_path)
    assert reloaded["player_active_visual"] == {
        "path": "player_exports/original_00.glb",
        "draft": False,
    }


def test_validate_rejects_slots_duplicates_and_unknown_ids():
    m = default_migrated_manifest()
    m["enemies"]["imp"]["slots"] = ["imp_animated_00", "imp_animated_00"]
    with pytest.raises(ValueError, match="duplicate slot version id"):
        validate_manifest(m)

    m2 = default_migrated_manifest()
    m2["enemies"]["imp"]["slots"] = ["not_present"]
    with pytest.raises(ValueError, match="unknown slot version id"):
        validate_manifest(m2)


def test_spawn_eligible_unknown_family():
    m = validate_manifest(default_migrated_manifest())
    assert spawn_eligible_paths(m, "nonexistent_family") == []


def test_spawn_eligible_skips_non_string_path():
    manifest = {
        "enemies": {
            "imp": {"versions": [{"id": "i", "path": 99, "draft": False, "in_use": True}]},
        },
    }
    assert spawn_eligible_paths(manifest, "imp") == []

"""Tests for ``src.model_registry.service`` (MRVC persistence + spawn consumer)."""

import json
from pathlib import Path
from unittest import mock

import pytest

from src.model_registry.service import (
    default_migrated_manifest,
    load_effective_manifest,
    patch_enemy_version,
    patch_player_active_visual,
    registry_path,
    save_manifest_atomic,
    spawn_eligible_paths,
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
    patch_enemy_version(tmp_path, "imp", "imp_animated_00", draft=True, in_use=False)
    raw = json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))
    row = raw["enemies"]["imp"]["versions"][0]
    assert row["draft"] is True
    assert row["in_use"] is False


def test_patch_unknown_family_raises(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError):
        patch_enemy_version(tmp_path, "nope_family", "v0", draft=True)


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
    with pytest.raises(ValueError, match="at least one"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00")


def test_patch_enemy_unknown_version(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError, match="unknown version"):
        patch_enemy_version(tmp_path, "imp", "not_real", draft=True)


def test_patch_player_requires_flag(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(ValueError, match="at least one"):
        patch_player_active_visual(tmp_path)


def test_patch_player_when_null_raises(tmp_path: Path):
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    with pytest.raises(KeyError, match="player_active_visual is null"):
        patch_player_active_visual(tmp_path, draft=False)


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

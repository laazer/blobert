"""Tests for ``src.model_registry.service`` (MRVC persistence + spawn consumer)."""

import json
from pathlib import Path

import pytest

from src.model_registry.service import (
    default_migrated_manifest,
    load_effective_manifest,
    patch_enemy_version,
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

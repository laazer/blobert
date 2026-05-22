"""Registry version tag normalization."""

from __future__ import annotations

import pytest

from src.model_registry.schema import validate_manifest
from src.model_registry.service import (
    load_effective_manifest,
    patch_enemy_version,
    save_manifest_atomic,
)
from src.model_registry.tags import canonical_version_tags, normalize_tag_token


def test_normalize_tag_token_accepts_snake_case() -> None:
    assert normalize_tag_token("  Combat Ready  ") == "combat_ready"


def test_canonical_version_tags_injects_family_first() -> None:
    assert canonical_version_tags("acid_spitter", ["wip", "acid_spitter"]) == [
        "acid_spitter",
        "wip",
    ]


def test_validate_manifest_adds_family_tag_when_missing(tmp_path) -> None:
    raw = {
        "schema_version": 1,
        "enemies": {
            "spider": {
                "versions": [
                    {
                        "id": "spider_animated_00",
                        "path": "animated_exports/spider_animated_00.glb",
                        "draft": False,
                        "in_use": True,
                    }
                ]
            }
        },
        "player": {"versions": [], "slots": []},
        "player_active_visual": None,
    }
    out = validate_manifest(raw)
    row = out["enemies"]["spider"]["versions"][0]
    assert row["tags"] == ["spider"]


def test_patch_enemy_version_persists_tags(tmp_path) -> None:
    save_manifest_atomic(
        tmp_path,
        {
            "schema_version": 1,
            "enemies": {
                "imp": {
                    "versions": [
                        {
                            "id": "imp_animated_00",
                            "path": "animated_exports/imp_animated_00.glb",
                            "draft": False,
                            "in_use": True,
                        }
                    ]
                }
            },
            "player": {"versions": [], "slots": []},
            "player_active_visual": None,
        },
    )
    patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"tags": ["combat", "wip"]})
    loaded = load_effective_manifest(tmp_path)
    assert loaded["enemies"]["imp"]["versions"][0]["tags"] == ["imp", "combat", "wip"]


def test_patch_rejects_invalid_tag(tmp_path) -> None:
    save_manifest_atomic(
        tmp_path,
        {
            "schema_version": 1,
            "enemies": {
                "imp": {
                    "versions": [
                        {
                            "id": "imp_animated_00",
                            "path": "animated_exports/imp_animated_00.glb",
                            "draft": False,
                            "in_use": True,
                        }
                    ]
                }
            },
            "player": {"versions": [], "slots": []},
            "player_active_visual": None,
        },
    )
    with pytest.raises(ValueError, match="invalid"):
        patch_enemy_version(tmp_path, "imp", "imp_animated_00", {"tags": ["bad tag!"]})

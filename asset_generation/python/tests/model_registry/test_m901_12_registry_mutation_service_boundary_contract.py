from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from src.model_registry import service as registry_service


def _seed_manifest(tmp_path: Path) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "enemies": {
            "spider": {
                "slots": ["spider_live_00", "spider_live_01"],
                "versions": [
                    {
                        "id": "spider_live_00",
                        "path": "animated_exports/spider_live_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "spider_live_01",
                        "path": "animated_exports/spider_live_01.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "spider_draft_00",
                        "path": "animated_exports/spider_draft_00.glb",
                        "draft": True,
                        "in_use": False,
                    },
                ],
            },
            "slug": {
                "slots": ["slug_live_00"],
                "versions": [
                    {
                        "id": "slug_live_00",
                        "path": "animated_exports/slug_live_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                ],
            },
        },
        "player": {
            "versions": [
                {"id": "player_a", "path": "player_exports/player_a.glb", "draft": False, "in_use": True},
                {"id": "player_b", "path": "player_exports/player_b.glb", "draft": False, "in_use": True},
            ],
            "slots": ["player_a", "player_b"],
        },
        "player_active_visual": {"path": "player_exports/player_a.glb", "draft": False},
    }
    registry_service.save_manifest_atomic(tmp_path, payload)
    return payload


def _require_service_api(name: str) -> Callable[..., dict[str, Any]]:
    api = getattr(registry_service, name, None)
    assert callable(api), f"missing service API: {name}"
    return api


def _read_manifest(tmp_path: Path) -> dict[str, Any]:
    return json.loads((tmp_path / "model_registry.json").read_text(encoding="utf-8"))


def test_enemy_delete_rejects_missing_confirmation_without_mutation(tmp_path: Path) -> None:
    before = _seed_manifest(tmp_path)
    delete_enemy_version = _require_service_api("delete_enemy_version")

    with pytest.raises(ValueError):
        delete_enemy_version(
            tmp_path,
            family="spider",
            version_id="spider_draft_00",
            confirm=False,
            delete_files=True,
        )

    assert _read_manifest(tmp_path) == registry_service.validate_manifest(before)
    assert (tmp_path / "animated_exports" / "spider_draft_00.glb").exists() is False


def test_enemy_delete_success_removes_version_and_slot_and_unlinks_after_save(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_manifest(tmp_path)
    target_file = tmp_path / "animated_exports" / "spider_draft_00.glb"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_bytes(b"draft")
    delete_enemy_version = _require_service_api("delete_enemy_version")

    observed: dict[str, bool] = {"saved": False}
    original_save = registry_service.save_manifest_atomic

    def _save_spy(python_root: Path, manifest: dict[str, Any]) -> None:
        # Save must occur before file unlink side effect.
        assert target_file.exists()
        observed["saved"] = True
        original_save(python_root, manifest)

    monkeypatch.setattr(registry_service, "save_manifest_atomic", _save_spy)

    updated = delete_enemy_version(
        tmp_path,
        family="spider",
        version_id="spider_draft_00",
        confirm=True,
        delete_files=True,
    )

    ids = [row["id"] for row in updated["enemies"]["spider"]["versions"]]
    assert "spider_draft_00" not in ids
    assert "spider_draft_00" not in updated["enemies"]["spider"]["slots"]
    assert observed["saved"] is True
    assert target_file.exists() is False


def test_enemy_delete_rejects_sole_in_use_without_mutating_manifest_or_file(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)
    target_file = tmp_path / "animated_exports" / "slug_live_00.glb"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_bytes(b"live")
    before = _read_manifest(tmp_path)
    delete_enemy_version = _require_service_api("delete_enemy_version")

    with pytest.raises(RuntimeError):
        delete_enemy_version(
            tmp_path,
            family="slug",
            version_id="slug_live_00",
            confirm=True,
            confirm_text="delete in-use slug slug_live_00",
            delete_files=True,
        )

    assert _read_manifest(tmp_path) == before
    assert target_file.exists()


def test_enemy_delete_validation_failure_does_not_persist_manifest_or_delete_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_manifest(tmp_path)
    target_file = tmp_path / "animated_exports" / "spider_draft_00.glb"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_bytes(b"draft")
    before = _read_manifest(tmp_path)
    delete_enemy_version = _require_service_api("delete_enemy_version")

    def _raise_validation(_manifest: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("synthetic validation failure")

    monkeypatch.setattr(registry_service, "validate_manifest", _raise_validation)

    with pytest.raises(ValueError, match="synthetic validation failure"):
        delete_enemy_version(
            tmp_path,
            family="spider",
            version_id="spider_draft_00",
            confirm=True,
            delete_files=True,
        )

    assert _read_manifest(tmp_path) == before
    assert target_file.exists()


def test_player_active_delete_rejects_when_confirm_false_without_mutation(tmp_path: Path) -> None:
    before = _seed_manifest(tmp_path)
    delete_player_active_visual = _require_service_api("delete_player_active_visual")

    with pytest.raises(ValueError):
        delete_player_active_visual(tmp_path, confirm=False)

    assert _read_manifest(tmp_path) == registry_service.validate_manifest(before)


def test_player_active_delete_success_unslots_first_assigned_and_removes_key(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)
    delete_player_active_visual = _require_service_api("delete_player_active_visual")

    updated = delete_player_active_visual(tmp_path, confirm=True)

    assert "player_active_visual" not in updated
    assert updated["player"]["slots"] == ["", "player_b"]
    persisted = _read_manifest(tmp_path)
    assert "player_active_visual" not in persisted
    assert persisted["player"]["slots"] == ["", "player_b"]


def test_enemy_delete_rejects_target_path_mismatch_without_mutation(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)
    before = copy.deepcopy(_read_manifest(tmp_path))
    delete_enemy_version = _require_service_api("delete_enemy_version")

    with pytest.raises(ValueError):
        delete_enemy_version(
            tmp_path,
            family="spider",
            version_id="spider_draft_00",
            confirm=True,
            target_path="animated_exports/not_the_target.glb",
            delete_files=False,
        )

    assert _read_manifest(tmp_path) == before


def test_enemy_delete_rejects_in_use_without_exact_confirm_text_and_keeps_state(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)
    before = copy.deepcopy(_read_manifest(tmp_path))
    delete_enemy_version = _require_service_api("delete_enemy_version")

    with pytest.raises(ValueError):
        delete_enemy_version(
            tmp_path,
            family="spider",
            version_id="spider_live_00",
            confirm=True,
            confirm_text="delete in-use spider spider_live_00!",
            delete_files=False,
        )

    assert _read_manifest(tmp_path) == before


def test_enemy_delete_accepts_trimmed_in_use_confirm_text(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)
    delete_enemy_version = _require_service_api("delete_enemy_version")

    updated = delete_enemy_version(
        tmp_path,
        family="spider",
        version_id="spider_live_00",
        confirm=True,
        confirm_text="  delete in-use spider spider_live_00  ",
        delete_files=False,
    )

    persisted = _read_manifest(tmp_path)
    ids = [row["id"] for row in updated["enemies"]["spider"]["versions"]]
    assert "spider_live_00" not in ids
    assert persisted["enemies"]["spider"]["slots"] == ["", "spider_live_01"]


def test_enemy_delete_rejects_malformed_target_path_class_without_mutation(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)
    before = copy.deepcopy(_read_manifest(tmp_path))
    delete_enemy_version = _require_service_api("delete_enemy_version")

    with pytest.raises(ValueError):
        delete_enemy_version(
            tmp_path,
            family="spider",
            version_id="spider_draft_00",
            confirm=True,
            target_path="animated_exports/%2e%2e/spider_draft_00.glb",
            delete_files=False,
        )

    assert _read_manifest(tmp_path) == before


def test_player_active_delete_rejects_single_assigned_slot_with_empties(tmp_path: Path) -> None:
    seeded = _seed_manifest(tmp_path)
    seeded["player"]["slots"] = ["", "player_a", ""]
    registry_service.save_manifest_atomic(tmp_path, seeded)
    before = _read_manifest(tmp_path)
    delete_player_active_visual = _require_service_api("delete_player_active_visual")

    with pytest.raises(RuntimeError):
        delete_player_active_visual(tmp_path, confirm=True)

    assert _read_manifest(tmp_path) == before

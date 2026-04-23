from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException

import core.config as config_module
from routers import registry as registry_router


class _DeleteServiceSpy:
    def __init__(self) -> None:
        self.enemy_calls: list[dict[str, Any]] = []
        self.player_calls: list[dict[str, Any]] = []
        self.enemy_result: dict[str, str] = {"ok": "enemy-delete"}
        self.player_result: dict[str, str] = {"ok": "player-delete"}
        self.enemy_error: Exception | None = None
        self.player_error: Exception | None = None

    def delete_enemy_version(
        self,
        python_root: Path,
        *,
        family: str,
        version_id: str,
        confirm: bool,
        confirm_text: str | None = None,
        target_path: str | None = None,
        delete_files: bool = False,
    ) -> dict[str, str]:
        self.enemy_calls.append(
            {
                "python_root": python_root,
                "family": family,
                "version_id": version_id,
                "confirm": confirm,
                "confirm_text": confirm_text,
                "target_path": target_path,
                "delete_files": delete_files,
            },
        )
        if self.enemy_error is not None:
            raise self.enemy_error
        return self.enemy_result

    def delete_player_active_visual(self, python_root: Path, *, confirm: bool) -> dict[str, str]:
        self.player_calls.append({"python_root": python_root, "confirm": confirm})
        if self.player_error is not None:
            raise self.player_error
        return self.player_result

    def load_effective_manifest(self, _python_root: Path) -> dict[str, Any]:
        raise AssertionError("router should not call load_effective_manifest for delete endpoints")

    def validate_manifest(self, _manifest: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError("router should not call validate_manifest for delete endpoints")

    def save_manifest_atomic(self, _python_root: Path, _manifest: dict[str, Any]) -> None:
        raise AssertionError("router should not call save_manifest_atomic for delete endpoints")


@pytest.mark.asyncio
async def test_enemy_delete_endpoint_delegates_to_service_boundary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    spy = _DeleteServiceSpy()
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    body = registry_router.EnemyVersionDeleteRequest(
        confirm=True,
        delete_files=True,
        confirm_text="delete in-use spider spider_live_01",
        target_path="animated_exports/spider_live_01.glb",
    )
    response = await registry_router.delete_enemy_version_endpoint("spider", "spider_live_01", body)

    assert response.status_code == 200
    assert json.loads(response.body) == {"ok": "enemy-delete"}
    assert spy.enemy_calls == [
        {
            "python_root": tmp_path,
            "family": "spider",
            "version_id": "spider_live_01",
            "confirm": True,
            "confirm_text": "delete in-use spider spider_live_01",
            "target_path": "animated_exports/spider_live_01.glb",
            "delete_files": True,
        },
    ]


@pytest.mark.asyncio
async def test_player_delete_endpoint_delegates_to_service_boundary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    spy = _DeleteServiceSpy()
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    body = registry_router.PlayerActiveVisualDeleteRequest(confirm=True)
    response = await registry_router.delete_player_active_visual_endpoint(body)

    assert response.status_code == 200
    assert json.loads(response.body) == {"ok": "player-delete"}
    assert spy.player_calls == [{"python_root": tmp_path, "confirm": True}]


@pytest.mark.asyncio
async def test_enemy_delete_router_maps_service_unknown_target_to_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spy = _DeleteServiceSpy()
    spy.enemy_error = KeyError("unknown target")
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    with pytest.raises(HTTPException) as exc_info:
        await registry_router.delete_enemy_version_endpoint(
            "spider",
            "missing",
            registry_router.EnemyVersionDeleteRequest(confirm=True),
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_enemy_delete_router_maps_service_validation_failure_to_400(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spy = _DeleteServiceSpy()
    spy.enemy_error = ValueError("malformed confirmation text")
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    with pytest.raises(HTTPException) as exc_info:
        await registry_router.delete_enemy_version_endpoint(
            "spider",
            "spider_live_01",
            registry_router.EnemyVersionDeleteRequest(confirm=True, confirm_text="wrong"),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "malformed confirmation text"


@pytest.mark.asyncio
async def test_player_delete_router_maps_service_conflict_to_409(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spy = _DeleteServiceSpy()
    spy.player_error = RuntimeError("cannot delete sole active player visual")
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    with pytest.raises(HTTPException) as exc_info:
        await registry_router.delete_player_active_visual_endpoint(
            registry_router.PlayerActiveVisualDeleteRequest(confirm=True),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "cannot delete sole active player visual"


@pytest.mark.asyncio
async def test_enemy_delete_with_confirm_false_is_delegated_to_service_for_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spy = _DeleteServiceSpy()
    spy.enemy_error = ValueError("delete requires explicit confirmation")
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    with pytest.raises(HTTPException) as exc_info:
        await registry_router.delete_enemy_version_endpoint(
            "spider",
            "spider_draft_00",
            registry_router.EnemyVersionDeleteRequest(confirm=False),
        )

    assert exc_info.value.status_code == 400
    assert spy.enemy_calls == [
        {
            "python_root": tmp_path,
            "family": "spider",
            "version_id": "spider_draft_00",
            "confirm": False,
            "confirm_text": None,
            "target_path": None,
            "delete_files": False,
        },
    ]


@pytest.mark.asyncio
async def test_enemy_delete_router_maps_service_conflict_to_409(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spy = _DeleteServiceSpy()
    spy.enemy_error = RuntimeError("cannot delete sole in-use enemy version")
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    with pytest.raises(HTTPException) as exc_info:
        await registry_router.delete_enemy_version_endpoint(
            "slug",
            "slug_live_00",
            registry_router.EnemyVersionDeleteRequest(
                confirm=True,
                confirm_text="delete in-use slug slug_live_00",
            ),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "cannot delete sole in-use enemy version"


@pytest.mark.asyncio
async def test_player_delete_router_maps_service_unknown_target_to_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spy = _DeleteServiceSpy()
    spy.player_error = KeyError("unknown target")
    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: spy)

    with pytest.raises(HTTPException) as exc_info:
        await registry_router.delete_player_active_visual_endpoint(
            registry_router.PlayerActiveVisualDeleteRequest(confirm=True),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "unknown target"

"""
M902-25 — Pilot response models: shared fixture drift + route contracts.

Spec: project_board/specs/902_25_pydantic_zod_validation_spec.md (Requirement 09).

Run from asset_generation/web/backend/:
    python -m pytest tests/test_response_models_pilot.py -v
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Type
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from main import app

_FIXTURES_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "frontend"
    / "scripts"
    / "fixtures"
    / "dual_validation"
)


def _load_fixture(name: str) -> Any:
    path = _FIXTURES_DIR / name
    assert path.is_file(), f"missing drift fixture: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _import_response_models() -> tuple[type[BaseModel], ...]:
    from models.responses import (  # noqa: PLC0415 — import under test
        HealthResponse,
        MetaEnemiesResponse,
        ModelRegistryResponse,
    )

    return HealthResponse, ModelRegistryResponse, MetaEnemiesResponse


VALID_DRIFT_CASES: tuple[tuple[str, str], ...] = (
    ("health.ok.json", "HealthResponse"),
    ("registry.minimal.ok.json", "ModelRegistryResponse"),
    ("meta.ok.minimal.json", "MetaEnemiesResponse"),
    ("meta.fallback.ok.json", "MetaEnemiesResponse"),
)

INVALID_DRIFT_CASES: tuple[str, ...] = (
    "health.invalid.wrong_status.json",
    "health.invalid.empty.json",
    "health.invalid.extra_key.json",
    "registry.invalid.extra_top_key.json",
    "registry.invalid.schema_version.json",
    "registry.invalid.version_missing_draft.json",
    "registry.invalid.bad_path.json",
    "registry.invalid.pav_extra_key.json",
    "meta.invalid.backend.json",
    "meta.invalid.missing_slug.json",
    "meta.invalid.controls_not_object.json",
    "meta.invalid.control_missing_type.json",
    "meta.invalid.row_extra_key.json",
    "meta.invalid.fallback_missing_error.json",
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def response_models() -> dict[str, Type[BaseModel]]:
    health, registry, meta = _import_response_models()
    return {
        "HealthResponse": health,
        "ModelRegistryResponse": registry,
        "MetaEnemiesResponse": meta,
    }


@pytest.mark.parametrize(("fixture_name", "model_name"), VALID_DRIFT_CASES)
def test_valid_fixtures_model_validate_and_round_trip_json_keys(
    fixture_name: str,
    model_name: str,
    response_models: dict[str, Type[BaseModel]],
) -> None:
    payload = _load_fixture(fixture_name)
    model_cls = response_models[model_name]
    instance = model_cls.model_validate(payload)
    exclude_none = model_name == "MetaEnemiesResponse"
    dumped = instance.model_dump(mode="json", exclude_none=exclude_none)
    assert set(dumped.keys()) == set(payload.keys())
    assert model_cls.model_validate(dumped) == instance


@pytest.mark.parametrize("fixture_name", INVALID_DRIFT_CASES)
def test_invalid_fixtures_raise_validation_error(
    fixture_name: str,
    response_models: dict[str, Type[BaseModel]],
) -> None:
    payload = _load_fixture(fixture_name)
    if fixture_name.startswith("health."):
        model_cls = response_models["HealthResponse"]
    elif fixture_name.startswith("registry."):
        model_cls = response_models["ModelRegistryResponse"]
    else:
        model_cls = response_models["MetaEnemiesResponse"]

    with pytest.raises(ValidationError):
        model_cls.model_validate(payload)


def test_registry_response_accepts_empty_string_slot_placeholder(
    response_models: dict[str, Type[BaseModel]],
) -> None:
    """Manifest slots may use '' for unassigned positions (registry-fix-versions-slots-load)."""
    model_cls = response_models["ModelRegistryResponse"]
    payload = {
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
                ],
                "slots": [""],
            }
        },
        "player_active_visual": None,
    }
    instance = model_cls.model_validate(payload)
    assert instance.enemies["spider"].slots == [""]


def test_health_route_returns_valid_fixture(client: TestClient) -> None:
    expected = _load_fixture("health.ok.json")
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == expected


def test_registry_route_returns_mocked_minimal_fixture(client: TestClient) -> None:
    fixture = _load_fixture("registry.minimal.ok.json")
    service = MagicMock()
    service.load_effective_manifest.return_value = fixture

    with patch("routers.registry._load_service", return_value=service):
        response = client.get("/api/registry/model")

    assert response.status_code == 200
    assert response.json() == fixture


def test_registry_route_rejects_invalid_manifest_before_http_200(client: TestClient) -> None:
    """Handler must validate with ModelRegistryResponse before returning 200."""
    invalid = _load_fixture("registry.invalid.extra_top_key.json")
    service = MagicMock()
    service.load_effective_manifest.return_value = invalid

    with patch("routers.registry._load_service", return_value=service):
        response = client.get("/api/registry/model")

    assert response.status_code == 500


def test_meta_route_ok_branch_matches_minimal_fixture(client: TestClient) -> None:
    fixture = _load_fixture("meta.ok.minimal.json")
    build_options = MagicMock()
    build_options.animated_build_controls_for_api.return_value = fixture["animated_build_controls"]

    def _import_asset_module(name: str) -> MagicMock:
        if name == "src.utils.build_options":
            return build_options
        return MagicMock()

    with (
        patch("routers.meta.import_asset_module", side_effect=_import_asset_module),
        patch("routers.meta._get_canonical_enemies", return_value=fixture["enemies"]),
    ):
        response = client.get("/api/meta/enemies")

    assert response.status_code == 200
    body = response.json()
    assert body["meta_backend"] == "ok"
    assert body["enemies"] == fixture["enemies"]
    assert body["animated_build_controls"] == fixture["animated_build_controls"]
    assert "meta_error" not in body


def test_meta_route_fallback_branch_matches_fixture(client: TestClient) -> None:
    fixture = _load_fixture("meta.fallback.ok.json")

    def _raise_import(_name: str) -> MagicMock:
        raise ImportError("simulated")

    with (
        patch("routers.meta.import_asset_module", side_effect=_raise_import),
        patch(
            "routers.meta._get_canonical_enemies",
            return_value=fixture["enemies"],
        ),
    ):
        response = client.get("/api/meta/enemies")

    assert response.status_code == 200
    body = response.json()
    assert body["meta_backend"] == "fallback"
    assert body["meta_error"] == fixture["meta_error"]
    assert body["enemies"] == fixture["enemies"]
    assert body["animated_build_controls"] == {}

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import core.config as config_module
from routers import registry as registry_router
from services import registry_query


class _PolicySpy:
    def __init__(self, outcomes: dict[str, str | Exception] | None = None) -> None:
        self.calls: list[str] = []
        self._outcomes = outcomes or {}

    def normalize_registry_relative_glb_path(self, raw_path: str) -> str:
        self.calls.append(raw_path)
        outcome = self._outcomes.get(raw_path)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, str):
            return outcome
        if raw_path == "exports/Upper.GLB":
            return "exports/upper.glb"
        return raw_path


def test_candidates_delegate_normalization_to_service_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    policy = _PolicySpy()
    fake_service = SimpleNamespace(
        normalize_registry_relative_glb_path=policy.normalize_registry_relative_glb_path,
    )

    monkeypatch.setattr(registry_router, "_load_service", lambda: fake_service)
    monkeypatch.setattr(registry_query, "_load_model_registry_service", lambda: fake_service)
    monkeypatch.setattr(
        registry_query,
        "load_registry_json_unvalidated",
        lambda _python_root: {
            "enemies": {
                "imp": {
                    "versions": [
                        {
                            "id": "imp_live_00",
                            "path": "exports/Upper.GLB",
                            "draft": False,
                            "in_use": True,
                        },
                    ],
                },
            },
        },
    )

    rows = registry_query.load_existing_candidates_from_registry(Path("/unused"))
    assert rows == [
        {
            "kind": "enemy",
            "family": "imp",
            "version_id": "imp_live_00",
            "path": "exports/upper.glb",
        },
    ]
    assert policy.calls == ["exports/Upper.GLB"]


@pytest.mark.asyncio
async def test_open_path_delegates_to_service_policy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy = _PolicySpy()
    fake_service = SimpleNamespace(
        normalize_registry_relative_glb_path=policy.normalize_registry_relative_glb_path,
    )

    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: fake_service)
    monkeypatch.setattr(registry_query, "_load_model_registry_service", lambda: fake_service)
    monkeypatch.setattr(registry_router, "safe_is_file_under_python_root", lambda _root, _path: True)

    body = registry_router.LoadExistingOpenRequest(kind="path", path="exports/Upper.GLB")
    response = await registry_router.open_load_existing(body)

    assert response.status_code == 200
    assert response.body == b'{"kind":"path","path":"exports/upper.glb"}'
    assert policy.calls == ["exports/Upper.GLB"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("raw_path", "policy_error", "expected_status", "expected_detail"),
    [
        (
            "exports/%2e%2e/secret.glb",
            ValueError("malformed target path class: traversal"),
            400,
            "malformed target path class: traversal",
        ),
        (
            "exports%252f..%252fsecret.glb",
            ValueError("malformed target path class: traversal"),
            400,
            "malformed target path class: traversal",
        ),
        (
            "exports/valid.glb.exe",
            ValueError("malformed target path class: extension"),
            400,
            "malformed target path class: extension",
        ),
        (
            "/etc/passwd.glb",
            HTTPException(status_code=403, detail="forbidden target path class: absolute-path"),
            403,
            "forbidden target path class: absolute-path",
        ),
        (
            "res://unsafe.glb",
            HTTPException(status_code=403, detail="forbidden target path class: res-path"),
            403,
            "forbidden target path class: res-path",
        ),
        (
            "exports/%ZZ.glb",
            ValueError("malformed target path class: malformed-encoding"),
            400,
            "malformed target path class: malformed-encoding",
        ),
    ],
)
async def test_open_path_propagates_delegated_policy_rejections(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    raw_path: str,
    policy_error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    policy = _PolicySpy({raw_path: policy_error})
    fake_service = SimpleNamespace(
        normalize_registry_relative_glb_path=policy.normalize_registry_relative_glb_path,
    )

    monkeypatch.setattr(config_module.settings, "python_root", tmp_path)
    monkeypatch.setattr(registry_router, "_load_service", lambda: fake_service)
    monkeypatch.setattr(registry_query, "_load_model_registry_service", lambda: fake_service)
    monkeypatch.setattr(registry_router, "safe_is_file_under_python_root", lambda _root, _path: True)

    body = registry_router.LoadExistingOpenRequest(kind="path", path=raw_path)

    with pytest.raises(HTTPException) as exc_info:
        await registry_router.open_load_existing(body)

    assert exc_info.value.status_code == expected_status
    assert exc_info.value.detail == expected_detail
    assert policy.calls == [raw_path]


def test_candidates_filter_forbidden_classes_via_service_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    # CHECKPOINT: invalid path classes from registry rows are dropped, not surfaced.
    policy = _PolicySpy(
        {
            "exports/%2e%2e/secret.glb": ValueError("malformed target path class: traversal"),
            "exports/valid.glb.exe": ValueError("malformed target path class: extension"),
            "/etc/passwd.glb": HTTPException(
                status_code=403,
                detail="forbidden target path class: absolute-path",
            ),
            "res://unsafe.glb": HTTPException(
                status_code=403,
                detail="forbidden target path class: res-path",
            ),
        },
    )
    fake_service = SimpleNamespace(
        normalize_registry_relative_glb_path=policy.normalize_registry_relative_glb_path,
    )

    monkeypatch.setattr(registry_router, "_load_service", lambda: fake_service)
    monkeypatch.setattr(registry_query, "_load_model_registry_service", lambda: fake_service)
    monkeypatch.setattr(
        registry_query,
        "load_registry_json_unvalidated",
        lambda _python_root: {
            "enemies": {
                "imp": {
                    "versions": [
                        {"id": "ok", "path": "exports/ok.glb", "draft": False, "in_use": True},
                        {
                            "id": "trav",
                            "path": "exports/%2e%2e/secret.glb",
                            "draft": False,
                            "in_use": True,
                        },
                        {
                            "id": "ext",
                            "path": "exports/valid.glb.exe",
                            "draft": False,
                            "in_use": True,
                        },
                        {"id": "abs", "path": "/etc/passwd.glb", "draft": False, "in_use": True},
                        {"id": "res", "path": "res://unsafe.glb", "draft": False, "in_use": True},
                    ],
                },
            },
        },
    )

    rows = registry_query.load_existing_candidates_from_registry(Path("/unused"))

    assert rows == [
        {
            "kind": "enemy",
            "family": "imp",
            "version_id": "ok",
            "path": "exports/ok.glb",
        },
    ]
    assert policy.calls == [
        "exports/ok.glb",
        "exports/%2e%2e/secret.glb",
        "exports/valid.glb.exe",
        "/etc/passwd.glb",
        "res://unsafe.glb",
    ]

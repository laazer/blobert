# ruff: noqa: I001 — backend imports follow deliberate ``sys.path`` bootstrap.

from __future__ import annotations

import pathlib
import sys
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    import pydantic_core  # noqa: F401
except ImportError as exc:
    pytest.skip(
        f"pydantic_core failed to import ({exc!s}); recreate venv: "
        "cd asset_generation/python && uv sync --extra dev",
        allow_module_level=True,
    )

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[2].parent / "web" / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import core.config as config_module  # noqa: E402
from main import app  # noqa: E402
from tests.api.openapi_contract import OpenAPIContract, load_live_spec  # noqa: E402


@pytest.fixture(scope="session")
def live_spec() -> dict[str, Any]:
    return load_live_spec()


@pytest.fixture(scope="session")
def contract(live_spec: dict[str, Any]) -> OpenAPIContract:
    return OpenAPIContract(live_spec)


@pytest.fixture()
def python_root(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    root = tmp_path / "python"
    root.mkdir(parents=True)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest.fixture()
def src_tree(python_root: pathlib.Path) -> pathlib.Path:
    src = python_root / "src"
    src.mkdir(parents=True)
    (src / "module_a" / "sample.py").parent.mkdir(parents=True)
    (src / "module_a" / "sample.py").write_text("# contract fixture\n", encoding="utf-8")
    return src


@pytest.fixture()
def export_glb(python_root: pathlib.Path) -> str:
    export_dir = python_root / "exports"
    export_dir.mkdir(parents=True)
    rel = "exports/demo.glb"
    (python_root / rel).write_bytes(b"glTF\x00\x00\x00\x00")
    return rel


@pytest_asyncio.fixture()
async def async_client(python_root: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture()
def mock_process_manager() -> MagicMock:
    mgr = MagicMock()
    mgr.is_running = False
    mgr.run_id = None
    mgr.exit_code.return_value = 0
    mgr.start = AsyncMock(return_value="test-run-id")
    mgr.stream_output = AsyncMock(return_value=_async_empty())
    mgr.kill = AsyncMock()
    return mgr


async def _async_empty() -> AsyncIterator[str]:
    if False:  # pragma: no cover
        yield ""
    return


@pytest.fixture()
def patched_process_manager(mock_process_manager: MagicMock):
    with patch("routers.run.process_manager", mock_process_manager):
        yield mock_process_manager


@pytest.fixture()
def running_process_manager(mock_process_manager: MagicMock) -> MagicMock:
    mock_process_manager.is_running = True
    mock_process_manager.run_id = "busy-run"
    return mock_process_manager


@pytest.fixture()
def registry_with_player_version(python_root: pathlib.Path) -> dict[str, Any]:
    """Seed minimal player row + on-disk GLB for player slot / active-visual contracts."""
    import json

    from model_registry.migrations import default_migrated_manifest

    manifest = default_migrated_manifest()
    version_a = "player_test_00"
    version_b = "player_test_01"
    path_a = f"player_exports/{version_a}.glb"
    path_b = f"player_exports/{version_b}.glb"
    manifest["player"] = {
        "versions": [
            {"id": version_a, "path": path_a, "draft": False, "in_use": True},
            {"id": version_b, "path": path_b, "draft": False, "in_use": True},
        ],
        "slots": [version_a, version_b],
    }
    (python_root / "player_exports").mkdir(parents=True, exist_ok=True)
    (python_root / path_a).write_bytes(b"glTF\x00\x00\x00\x00")
    (python_root / path_b).write_bytes(b"glTF\x00\x00\x00\x00")
    (python_root / "model_registry.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest

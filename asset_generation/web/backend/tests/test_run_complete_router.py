"""
GET /api/run/complete — agent-oriented run completion (non-SSE).

Run from asset_generation/web/backend/:
    python -m pytest tests/test_run_complete_router.py -v
"""

from __future__ import annotations

import asyncio
import pathlib
from typing import Optional

import core.config as config_module
import pytest
from httpx import ASGITransport, AsyncClient
from main import app


def _repo_python_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent.parent.parent / "python"


class _FakeProcessManager:
    """Minimal stub matching ProcessManager surface for /complete tests."""

    def __init__(
        self,
        lines: list[str],
        *,
        exit_code: int = 0,
        hang_forever: bool = False,
        start_raises: Optional[Exception] = None,
    ) -> None:
        self._lines = lines
        self._exit = exit_code
        self._rid = "fake-run-id"
        self._after_start = False
        self._done = False
        self._hang = hang_forever
        self._start_raises = start_raises

    @property
    def is_running(self) -> bool:
        return self._after_start and not self._done

    @property
    def run_id(self) -> Optional[str]:
        return self._rid if self._after_start else None

    def exit_code(self) -> Optional[int]:
        if not self._done:
            return None
        return self._exit

    async def start(self, cmd: list[str], cwd: pathlib.Path, env: dict[str, str]) -> str:
        if self.is_running:
            raise RuntimeError("A process is already running")
        if self._start_raises is not None:
            raise self._start_raises
        self._after_start = True
        self._done = False
        return self._rid

    async def stream_output(self):
        if self._hang:
            await asyncio.sleep(3600.0)
            return
        for line in self._lines:
            yield line
        self._done = True

    async def kill(self) -> None:
        self._after_start = False
        self._done = True


@pytest.mark.asyncio
async def test_run_complete_rejects_unknown_cmd(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "python_root", _repo_python_root())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/run/complete?cmd=definitely_not_allowed")

    assert res.status_code == 400
    body = res.json()
    assert "detail" in body
    assert "Unknown command" in body["detail"]


@pytest.mark.asyncio
async def test_run_complete_conflict_when_process_running(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "python_root", _repo_python_root())

    class _Busy:
        is_running = True
        run_id = "busy-run-id"

    import routers.run as run_mod

    monkeypatch.setattr(run_mod, "process_manager", _Busy())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/run/complete?cmd=stats&enemy=spider")

    assert res.status_code == 409
    body = res.json()
    assert body.get("run_id") == "busy-run-id"
    assert "already running" in body.get("detail", "").lower()


@pytest.mark.asyncio
async def test_run_complete_happy_path_aggregates_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "python_root", _repo_python_root())
    fake = _FakeProcessManager(["alpha", "beta"], exit_code=0)
    import routers.run as run_mod

    monkeypatch.setattr(run_mod, "process_manager", fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/run/complete?cmd=stats&enemy=spider")

    assert res.status_code == 200
    data = res.json()
    assert data["exit_code"] == 0
    assert data["run_id"] == "fake-run-id"
    assert "alpha" in data["log_text"] and "beta" in data["log_text"]
    assert data.get("output_file") is None


@pytest.mark.asyncio
async def test_run_complete_spawn_failure_returns_negative_exit_in_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "python_root", _repo_python_root())
    fake = _FakeProcessManager([], start_raises=OSError("no such executable"))
    import routers.run as run_mod

    monkeypatch.setattr(run_mod, "process_manager", fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/run/complete?cmd=stats&enemy=spider")

    assert res.status_code == 200
    data = res.json()
    assert data["exit_code"] == -1
    assert "no such executable" in data.get("message", "")


@pytest.mark.asyncio
async def test_run_complete_max_wait_returns_504(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "python_root", _repo_python_root())
    fake = _FakeProcessManager([], hang_forever=True)
    import routers.run as run_mod

    monkeypatch.setattr(run_mod, "process_manager", fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/run/complete?cmd=stats&enemy=spider&max_wait_ms=40")

    assert res.status_code == 504
    data = res.json()
    assert data.get("timed_out") is True
    assert data.get("run_id") == "fake-run-id"

from __future__ import annotations

import importlib
import json
from typing import Optional

import pytest


def test_run_router_does_not_keep_local_command_and_prediction_builders() -> None:
    run_mod = importlib.import_module("routers.run")
    assert not hasattr(run_mod, "_build_command")
    assert not hasattr(run_mod, "_guess_output_file")


class _DoneProcessManager:
    def __init__(self) -> None:
        self.is_running = False
        self.run_id: Optional[str] = None

    async def start(self, cmd: list[str], cwd, env: dict[str, str]) -> str:
        self.run_id = "run-test-id"
        return "run-test-id"

    async def stream_output(self):
        if False:
            yield ""

    def exit_code(self) -> int:
        return 0


@pytest.mark.asyncio
async def test_run_stream_uses_contract_environment_and_output_prediction(monkeypatch: pytest.MonkeyPatch) -> None:
    run_mod = importlib.import_module("routers.run")
    fake_pm = _DoneProcessManager()
    monkeypatch.setattr(run_mod, "process_manager", fake_pm)

    observed: dict[str, object] = {}

    def _fake_prepare(**kwargs):
        observed["prepare_kwargs"] = kwargs
        return (["python", "main.py", "animated"], {"BLOBERT_EXPORT_START_INDEX": "9"}, 9)

    def _fake_predict(**kwargs):
        observed["predict_kwargs"] = kwargs
        return "animated_exports/spider_animated_09.glb"

    monkeypatch.setattr(run_mod.run_contract, "prepare_run_environment", _fake_prepare)
    monkeypatch.setattr(run_mod.run_contract, "predict_output_file", _fake_predict)

    events = []
    async for event in run_mod._run_stream(
        cmd="animated",
        enemy="spider",
        count=1,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options=None,
        output_draft=False,
        replace_variant_index=None,
    ):
        events.append(event)

    assert observed["prepare_kwargs"] == {
        "python_root": run_mod.settings.python_root,
        "cmd": "animated",
        "enemy": "spider",
        "count": 1,
        "description": None,
        "difficulty": None,
        "finish": None,
        "hex_color": None,
        "build_options": None,
        "output_draft": False,
        "replace_variant_index": None,
    }
    assert observed["predict_kwargs"] == {
        "cmd": "animated",
        "enemy": "spider",
        "count": 1,
        "start_index": 9,
        "output_draft": False,
    }
    assert events[-1]["event"] == "done"
    assert json.loads(events[-1]["data"])["output_file"] == "animated_exports/spider_animated_09.glb"


def test_run_router_exposes_shared_run_contract_module() -> None:
    # CHECKPOINT: conservative assumption is explicit module exposure for runtime
    # delegation so regressions cannot silently re-introduce duplicate helpers.
    run_mod = importlib.import_module("routers.run")
    assert hasattr(run_mod, "run_contract")

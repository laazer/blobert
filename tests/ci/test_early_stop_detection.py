"""Behavioral tests for early-stop detection (M902-22).

Validates `ci/scripts/early_stop_tracker.py` and middleware hook in
`ci/scripts/agent_invocation_middleware.py` per
`project_board/specs/902_22_early_stop_spec.md` Requirement 13 (T1–T10).

Assertions target JSON artifacts and `EarlyStopResult` fields — not ticket markdown.
Isolation: `tmp_path` checkpoints roots; `unittest.mock` for git subprocesses.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"

EMPTY_DIFF_HASH = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
_SCHEMA_VERSION = "1.0.0"

_LOOP_RUN_ID = "550e8400-e29b-41d4-a716-446655440000"
_LOOP_RUN_ID_B = "660e8400-e29b-41d4-a716-446655440001"

_RUN_001 = "run-001"
_RUN_002 = "run-002"
_RUN_003 = "run-003"
_RUN_004 = "run-004"
_RUN_005 = "run-005"

_SAME_ERROR = "ruff: E501 line too long"
_ALT_ERROR = "pytest: AssertionError"
_DIFF_HASH_A = "a" * 64
_DIFF_HASH_B = "b" * 64

_chdir_lock = threading.Lock()


def _ensure_ci_scripts_package() -> None:
    if "ci.scripts" in sys.modules:
        return
    ci_mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("ci", loader=None))
    scripts_mod = importlib.util.module_from_spec(
        importlib.util.spec_from_loader("ci.scripts", loader=None)
    )
    scripts_mod.__path__ = [str(_CI_SCRIPTS)]  # type: ignore[attr-defined]
    sys.modules["ci"] = ci_mod
    sys.modules["ci.scripts"] = scripts_mod


def _import_ci_script(module_name: str) -> Any:
    _ensure_ci_scripts_package()
    qualname = f"ci.scripts.{module_name}"
    if qualname in sys.modules:
        return sys.modules[qualname]
    path = _CI_SCRIPTS / f"{module_name}.py"
    if not path.is_file():
        raise ModuleNotFoundError(f"No module at {path}")
    if module_name == "agent_invocation_middleware":
        _import_ci_script("tool_category_manager")
    spec = importlib.util.spec_from_file_location(
        qualname,
        path,
        submodule_search_locations=[str(_CI_SCRIPTS)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {qualname} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualname] = module
    spec.loader.exec_module(module)
    return module


_tracker = _import_ci_script("early_stop_tracker")
record_iteration = _tracker.record_iteration
evaluate_early_stop = _tracker.evaluate_early_stop
normalize_error = _tracker.normalize_error
normalize_ticket_id = _tracker.normalize_ticket_id

if hasattr(_tracker, "EarlyStopConfig"):
    EarlyStopConfig = _tracker.EarlyStopConfig
else:
    EarlyStopConfig = None  # type: ignore[misc, assignment]


def _invoke_agent_with_category_filtering(*args: Any, **kwargs: Any) -> Any:
    middleware = _import_ci_script("agent_invocation_middleware")
    return middleware.invoke_agent_with_category_filtering(*args, **kwargs)


def _sandbox_checkpoints_root(checkpoints_root: Path) -> tuple[Path, str]:
    resolved = checkpoints_root.resolve()
    repo = _tracker.find_repo_root().resolve()
    for anchor in (repo, Path.cwd().resolve()):
        try:
            resolved.relative_to(anchor)
            rel = resolved.relative_to(anchor)
            return anchor, str(rel)
        except ValueError:
            continue
    return resolved.parent, resolved.name


def _iterations_path(checkpoints_root: Path, ticket_id: str) -> Path:
    normalized = normalize_ticket_id(ticket_id)
    return checkpoints_root / normalized / "agent_iterations.json"


def _events_path(checkpoints_root: Path, ticket_id: str) -> Path:
    normalized = normalize_ticket_id(ticket_id)
    return checkpoints_root / normalized / "early_stop_events.jsonl"


def _load_iterations(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ctx(
    *,
    error: str = "",
    diff_hash: str | None = None,
    modified_files: list[str] | None = None,
    tools_invoked: bool = False,
) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "error": error,
        "modified_files": modified_files if modified_files is not None else [],
        "tools_invoked": tools_invoked,
    }
    if diff_hash is not None:
        ctx["diff_hash"] = diff_hash
    return ctx


def _record(
    checkpoints_root: Path,
    ticket_id: str,
    *,
    agent_run_id: str,
    iteration_context: dict[str, Any],
    agent_type: str = "implementation",
    loop_run_id: str = _LOOP_RUN_ID,
    framework_result: Any | None = None,
) -> Path:
    sandbox_cwd, root_arg = _sandbox_checkpoints_root(checkpoints_root)
    with _chdir_lock:
        old_cwd = os.getcwd()
        try:
            os.chdir(sandbox_cwd)
            record_iteration(
                ticket_id,
                agent_type=agent_type,
                agent_run_id=agent_run_id,
                loop_run_id=loop_run_id,
                iteration_context=iteration_context,
                framework_result=framework_result,
                checkpoints_root=Path(root_arg),
            )
        finally:
            os.chdir(old_cwd)
    path = _iterations_path(checkpoints_root, ticket_id)
    assert path.is_file(), f"expected agent_iterations.json at {path}"
    return path


def _evaluate(
    checkpoints_root: Path,
    ticket_id: str,
    *,
    config: Any | None = None,
) -> dict[str, Any]:
    sandbox_cwd, root_arg = _sandbox_checkpoints_root(checkpoints_root)
    with _chdir_lock:
        old_cwd = os.getcwd()
        try:
            os.chdir(sandbox_cwd)
            kwargs: dict[str, Any] = {"checkpoints_root": Path(root_arg)}
            if config is not None:
                kwargs["config"] = config
            result = evaluate_early_stop(ticket_id, **kwargs)
        finally:
            os.chdir(old_cwd)
    if hasattr(result, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(result)
    if isinstance(result, dict):
        return result
    return dict(result)


# ---------------------------------------------------------------------------
# T1 — Append merges without clobber (Req 01, 05)
# ---------------------------------------------------------------------------


class TestRecordIterationAppend:
    """T1 / AC-01.2, AC-05.1: iterations append; loop_run_id merge semantics."""

    def test_second_iteration_appends_without_clobber(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_001,
            iteration_context=_ctx(error=_SAME_ERROR, diff_hash=_DIFF_HASH_A, modified_files=["a.py"]),
        )
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_002,
            iteration_context=_ctx(error=_ALT_ERROR, diff_hash=_DIFF_HASH_B, modified_files=["b.py"]),
        )
        data = _load_iterations(_iterations_path(root, "M902-22"))
        assert data["schema_version"] == _SCHEMA_VERSION
        assert data["ticket_id"] == "M902-22"
        assert len(data["iterations"]) == 2
        assert data["iterations"][0]["agent_run_id"] == _RUN_001
        assert data["iterations"][0]["error"] == _SAME_ERROR
        assert data["iterations"][1]["agent_run_id"] == _RUN_002
        assert data["rollup"]["iteration_count"] == 2

    def test_same_agent_run_id_replaces_not_duplicates(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_001,
            iteration_context=_ctx(error="first"),
        )
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_001,
            iteration_context=_ctx(error="second"),
        )
        data = _load_iterations(_iterations_path(root, "M902-22"))
        assert len(data["iterations"]) == 1
        assert data["iterations"][0]["error"] == "second"

    def test_new_loop_run_id_resets_iterations(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_001,
            loop_run_id=_LOOP_RUN_ID,
            iteration_context=_ctx(error="old loop"),
        )
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_002,
            loop_run_id=_LOOP_RUN_ID_B,
            iteration_context=_ctx(error="new loop"),
        )
        data = _load_iterations(_iterations_path(root, "M902-22"))
        assert data["loop_run_id"] == _LOOP_RUN_ID_B
        assert len(data["iterations"]) == 1
        assert data["iterations"][0]["iteration"] == 1


# ---------------------------------------------------------------------------
# T2 — Same error 3× → escalate repeated_error (Req 03, 06, 07)
# ---------------------------------------------------------------------------


class TestRepeatedErrorEscalation:
    """T2 / AC-06.1, AC-07.1: trailing identical normalized errors."""

    def test_three_same_errors_escalate_repeated_error(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        for run_id in (_RUN_001, _RUN_002, _RUN_003):
            _record(
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(
                    error=_SAME_ERROR,
                    diff_hash=_DIFF_HASH_A,
                    modified_files=["src/main.py"],
                    tools_invoked=True,
                ),
            )
        data = _load_iterations(_iterations_path(root, ticket))
        assert data["rollup"]["error_repeat_streak"] >= 3

        result = _evaluate(root, ticket)
        assert result["should_escalate"] is True
        assert result["break_loop"] is True
        assert result["reason"] == "repeated_error"
        assert result["recommended_handoff"] == "human"
        evidence = result["evidence"]
        assert len(evidence["errors"]) == 3
        assert evidence["errors"] == [_SAME_ERROR, _SAME_ERROR, _SAME_ERROR]
        assert result["incomplete_iterations"] is False


# ---------------------------------------------------------------------------
# T3 — Same diff_hash 3× → escalate repeated_diff (Req 04, 06)
# ---------------------------------------------------------------------------


class TestRepeatedDiffEscalation:
    """T3 / AC-06.2: stall on identical diff_hash with varying errors."""

    def test_three_same_diff_hash_escalate_repeated_diff(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        errors = ["err-a", "err-b", "err-c"]
        for run_id, err in zip((_RUN_001, _RUN_002, _RUN_003), errors, strict=True):
            _record(
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(
                    error=err,
                    diff_hash=_DIFF_HASH_A,
                    modified_files=["asset_generation/python/src/main.py"],
                ),
            )
        data = _load_iterations(_iterations_path(root, ticket))
        assert data["rollup"]["diff_repeat_streak"] >= 3

        result = _evaluate(root, ticket)
        assert result["should_escalate"] is True
        assert result["reason"] == "repeated_diff"
        assert len(result["evidence"]["diff_hashes"]) == 3


# ---------------------------------------------------------------------------
# T4 — No-op 2× flag only, no escalate (Req 06)
# ---------------------------------------------------------------------------


class TestNoOpDetection:
    """T4 / AC-06.3: tools invoked with empty modified_files."""

    def test_two_no_ops_flag_without_escalate(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        for run_id in (_RUN_001, _RUN_002):
            _record(
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(
                    tools_invoked=True,
                    modified_files=[],
                    diff_hash=EMPTY_DIFF_HASH,
                ),
            )
        data = _load_iterations(_iterations_path(root, ticket))
        assert data["rollup"]["no_op_streak"] == 2
        assert data["iterations"][-1].get("no_op_flag") is True

        result = _evaluate(root, ticket)
        assert result["should_escalate"] is False
        assert result["break_loop"] is False
        assert result["reason"] == ""
        assert result["no_op_streak"] == 2


# ---------------------------------------------------------------------------
# T5 — max_iterations default 5 (Req 06, 11)
# ---------------------------------------------------------------------------


class TestMaxIterations:
    """T5 / AC-06.4, AC-11.1: fifth iteration escalates without repetition."""

    def test_fifth_iteration_escalates_max_iterations(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        run_ids = [_RUN_001, _RUN_002, _RUN_003, _RUN_004, _RUN_005]
        for i, run_id in enumerate(run_ids, start=1):
            _record(
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(
                    error=f"unique-error-{i}",
                    diff_hash=f"{i:064x}"[:64],
                    modified_files=[f"file{i}.py"],
                ),
            )
        result = _evaluate(root, ticket)
        assert result["should_escalate"] is True
        assert result["reason"] == "max_iterations"
        assert result["break_loop"] is True

    def test_env_max_iterations_three_escalates_on_third(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EARLY_STOP_MAX_ITERATIONS", "3")
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        for i, run_id in enumerate((_RUN_001, _RUN_002, _RUN_003), start=1):
            _record(
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(
                    error=f"e-{run_id}",
                    diff_hash=f"{i:064x}"[:64],
                ),
            )
        result = _evaluate(root, ticket)
        assert result["should_escalate"] is True
        assert result["reason"] == "max_iterations"


# ---------------------------------------------------------------------------
# T6 — Vacuous first iteration (Req 06)
# ---------------------------------------------------------------------------


class TestVacuousFirstIteration:
    """T6 / AC-06.6: single iteration does not escalate."""

    def test_first_iteration_alone_no_escalate(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        _record(
            root,
            ticket,
            agent_run_id=_RUN_001,
            iteration_context=_ctx(error=_SAME_ERROR, diff_hash=_DIFF_HASH_A),
        )
        result = _evaluate(root, ticket)
        assert result["should_escalate"] is False
        assert result["reason"] == ""


# ---------------------------------------------------------------------------
# T7 — Alternating errors (Req 06)
# ---------------------------------------------------------------------------


class TestAlternatingErrors:
    """T7 / AC-06.5: A-B-A-B pattern does not trigger repeated_error."""

    def test_four_alternating_errors_no_repeated_error_escalate(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        pattern = [_SAME_ERROR, _ALT_ERROR, _SAME_ERROR, _ALT_ERROR]
        for i, (run_id, err) in enumerate(
            zip((_RUN_001, _RUN_002, _RUN_003, _RUN_004), pattern, strict=True),
            start=1,
        ):
            _record(
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(error=err, diff_hash=f"{i:064x}"[:64]),
            )
        data = _load_iterations(_iterations_path(root, ticket))
        assert data["rollup"]["error_repeat_streak"] == 1

        result = _evaluate(root, ticket)
        assert result["should_escalate"] is False
        assert result["reason"] != "repeated_error"


# ---------------------------------------------------------------------------
# T8 — Path-unsafe ticket_id (Req 01)
# ---------------------------------------------------------------------------


class TestPathSafety:
    """T8 / AC-01.3: invalid ticket_id rejected without writes."""

    def test_path_traversal_ticket_id_rejected(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        sandbox_cwd, root_arg = _sandbox_checkpoints_root(root)
        old_cwd = os.getcwd()
        try:
            os.chdir(sandbox_cwd)
            with pytest.raises(ValueError, match="invalid ticket_id|path"):
                record_iteration(
                    "../evil",
                    agent_type="implementation",
                    agent_run_id=_RUN_001,
                    loop_run_id=_LOOP_RUN_ID,
                    iteration_context=_ctx(),
                    checkpoints_root=Path(root_arg),
                )
        finally:
            os.chdir(old_cwd)
        assert not (root / "evil").exists()

    def test_ticket_id_underscore_normalized_to_hyphen(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902_22",
            agent_run_id=_RUN_001,
            iteration_context=_ctx(),
        )
        assert _iterations_path(root, "M902-22").is_file()
        data = _load_iterations(_iterations_path(root, "M902-22"))
        assert data["ticket_id"] == "M902-22"


# ---------------------------------------------------------------------------
# Error normalization (Req 03) — behavioral via normalize_error
# ---------------------------------------------------------------------------


class TestErrorNormalization:
    """AC-03.1–AC-03.3: normalize_error contract."""

    def test_whitespace_collapsed(self) -> None:
        assert normalize_error("  ruff:   E501  line too long  ") == "ruff: E501 line too long"

    def test_unix_path_segments_removed(self) -> None:
        raw = "Error at /Users/foo/bar/baz.py:10: E501"
        normalized = normalize_error(raw)
        assert "/Users/foo" not in normalized
        assert "E501" in normalized

    def test_long_error_truncated_with_suffix(self) -> None:
        raw = "x" * 3000
        normalized = normalize_error(raw)
        assert len(normalized) <= 2000
        assert normalized.endswith("…[truncated]")


# ---------------------------------------------------------------------------
# Diff hash contract (Req 04) — injected + mocked git
# ---------------------------------------------------------------------------


class TestDiffHashContract:
    """AC-04.1–AC-04.2: EMPTY_DIFF_HASH and injected hash round-trip."""

    def test_empty_modified_files_uses_empty_diff_hash(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_001,
            iteration_context=_ctx(modified_files=[]),
        )
        data = _load_iterations(_iterations_path(root, "M902-22"))
        assert data["iterations"][0]["diff_hash"] == EMPTY_DIFF_HASH

    def test_injected_diff_hash_round_trips(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902-22",
            agent_run_id=_RUN_001,
            iteration_context=_ctx(diff_hash=_DIFF_HASH_A, modified_files=["a.py"]),
        )
        data = _load_iterations(_iterations_path(root, "M902-22"))
        assert data["iterations"][0]["diff_hash"] == _DIFF_HASH_A

    def test_different_injected_hashes_differ_in_rollup(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        _record(
            root,
            ticket,
            agent_run_id=_RUN_001,
            iteration_context=_ctx(diff_hash=_DIFF_HASH_A),
        )
        _record(
            root,
            ticket,
            agent_run_id=_RUN_002,
            iteration_context=_ctx(diff_hash=_DIFF_HASH_B),
        )
        data = _load_iterations(_iterations_path(root, ticket))
        assert data["rollup"]["diff_repeat_streak"] == 1


# ---------------------------------------------------------------------------
# Evaluate — missing artifact (Req 07)
# ---------------------------------------------------------------------------


class TestEvaluateMissingArtifact:
    """AC-07.4: no file → incomplete_iterations, no escalate."""

    def test_missing_artifact_incomplete_no_escalate(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        result = _evaluate(root, "M902-NOFILE")
        assert result["incomplete_iterations"] is True
        assert result["should_escalate"] is False


# ---------------------------------------------------------------------------
# T9–T10 — Middleware integration (Req 08)
# ---------------------------------------------------------------------------


class TestMiddlewareEarlyStopHook:
    """T9–T10 / AC-08.1–AC-08.5: loop_mode gating and return preservation."""

    def test_loop_mode_true_creates_agent_iterations(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        env = {k: v for k, v in os.environ.items() if k != "EARLY_STOP_DETECTION"}
        env["EARLY_STOP_DETECTION"] = "1"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return {"status": "ok"}

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.dict(os.environ, env, clear=True):
                result = _invoke_agent_with_category_filtering(
                    agent_type="implementation",
                    prompt="fix lint",
                    all_tools=[],
                    framework_invocation_fn=_framework,
                    ticket_id="M902-22",
                    agent_run_id=_RUN_001,
                    loop_run_id=_LOOP_RUN_ID,
                    loop_mode=True,
                    iteration_context=_ctx(error=_SAME_ERROR, diff_hash=_DIFF_HASH_A),
                    checkpoints_root=Path("checkpoints"),
                )
        finally:
            os.chdir(old_cwd)

        assert result == {"status": "ok"}
        assert _iterations_path(root, "M902-22").is_file()

    def test_loop_mode_false_skips_agent_iterations(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return {"status": "ok"}

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.dict(os.environ, {"EARLY_STOP_DETECTION": "1"}, clear=False):
                _invoke_agent_with_category_filtering(
                    agent_type="spec",
                    prompt="write spec",
                    all_tools=[],
                    framework_invocation_fn=_framework,
                    ticket_id="M902-22",
                    agent_run_id=_RUN_001,
                    loop_mode=False,
                    checkpoints_root=Path("checkpoints"),
                )
        finally:
            os.chdir(old_cwd)

        assert not _iterations_path(root, "M902-22").exists()

    def test_early_stop_detection_zero_skips_write(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return {"status": "ok"}

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.dict(os.environ, {"EARLY_STOP_DETECTION": "0"}, clear=False):
                _invoke_agent_with_category_filtering(
                    agent_type="implementation",
                    prompt="loop",
                    all_tools=[],
                    framework_invocation_fn=_framework,
                    ticket_id="M902-22",
                    agent_run_id=_RUN_001,
                    loop_run_id=_LOOP_RUN_ID,
                    loop_mode=True,
                    checkpoints_root=Path("checkpoints"),
                )
        finally:
            os.chdir(old_cwd)

        assert not _iterations_path(root, "M902-22").exists()

    def test_framework_exception_does_not_create_iterations(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"

        def _fail(**_kwargs: Any) -> None:
            raise RuntimeError("framework failed")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.dict(os.environ, {"EARLY_STOP_DETECTION": "1"}, clear=False):
                with pytest.raises(RuntimeError, match="framework failed"):
                    _invoke_agent_with_category_filtering(
                        agent_type="implementation",
                        prompt="fail",
                        all_tools=[],
                        framework_invocation_fn=_fail,
                        ticket_id="M902-22",
                        agent_run_id=_RUN_001,
                        loop_run_id=_LOOP_RUN_ID,
                        loop_mode=True,
                        checkpoints_root=Path("checkpoints"),
                    )
        finally:
            os.chdir(old_cwd)

        assert not _iterations_path(root, "M902-22").exists()

    def test_middleware_return_value_unchanged(self, tmp_path: Path) -> None:
        payload = {"answer": 42, "nested": {"k": "v"}}

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return payload

        with patch.dict(os.environ, {"EARLY_STOP_DETECTION": "1"}, clear=False):
            out = _invoke_agent_with_category_filtering(
                agent_type="implementation",
                prompt="unchanged",
                all_tools=[],
                framework_invocation_fn=_framework,
                ticket_id="M902-22",
                agent_run_id=_RUN_001,
                loop_run_id=_LOOP_RUN_ID,
                loop_mode=True,
            )

        assert out is payload

    def test_on_early_stop_called_when_escalate(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        seen: list[dict[str, Any]] = []

        def _on_early_stop(result: Any) -> None:
            if hasattr(result, "__dataclass_fields__"):
                from dataclasses import asdict

                seen.append(asdict(result))
            elif isinstance(result, dict):
                seen.append(result)
            else:
                seen.append(dict(result))

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return {"status": "ok"}

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.dict(os.environ, {"EARLY_STOP_DETECTION": "1"}, clear=False):
                for run_id in (_RUN_001, _RUN_002, _RUN_003):
                    _invoke_agent_with_category_filtering(
                        agent_type="implementation",
                        prompt="repeat error",
                        all_tools=[],
                        framework_invocation_fn=_framework,
                        ticket_id="M902-22",
                        agent_run_id=run_id,
                        loop_run_id=_LOOP_RUN_ID,
                        loop_mode=True,
                        iteration_context=_ctx(error=_SAME_ERROR, diff_hash=_DIFF_HASH_A),
                        checkpoints_root=Path("checkpoints"),
                        on_early_stop=_on_early_stop,
                    )
        finally:
            os.chdir(old_cwd)

        assert len(seen) >= 1
        assert seen[-1]["should_escalate"] is True
        assert seen[-1]["reason"] == "repeated_error"


# ---------------------------------------------------------------------------
# Escalation side effects (Req 07, 10) — JSONL append on escalate
# ---------------------------------------------------------------------------


class TestEscalationSideEffects:
    """AC-07.2–AC-07.3, AC-10.2: break_loop parity and JSONL event."""

    def test_escalate_appends_jsonl_event(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        for run_id in (_RUN_001, _RUN_002, _RUN_003):
            _record(
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(error=_SAME_ERROR, diff_hash=_DIFF_HASH_A),
            )
        _evaluate(root, ticket)
        events_path = _events_path(root, ticket)
        assert events_path.is_file()
        lines = [ln for ln in events_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) >= 1
        event = json.loads(lines[-1])
        assert event["should_escalate"] is True
        assert event["reason"] == "repeated_error"

    def test_break_loop_matches_should_escalate(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        _record(root, ticket, agent_run_id=_RUN_001, iteration_context=_ctx())
        no_esc = _evaluate(root, ticket)
        assert no_esc["break_loop"] == no_esc["should_escalate"]

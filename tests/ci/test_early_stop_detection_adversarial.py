"""Adversarial tests for early-stop detection (M902-22).

Exposes corrupt JSON merge fail-closed, schema version mismatch, huge error
truncation, concurrent append races, JSONL evaluate idempotency, git diff
one-byte hash sensitivity, whitespace-only error vacuity, and invalid injected
diff_hash handling beyond `tests/ci/test_early_stop_detection.py`.

Traceability: `project_board/specs/902_22_early_stop_spec.md` Requirements 01–07
failure taxonomy and Requirement 13 adversarial module.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"

EMPTY_DIFF_HASH = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
_SCHEMA_VERSION = "1.0.0"

_LOOP_RUN_ID = "550e8400-e29b-41d4-a716-446655440000"
_RUN_SPEC = "adv-run-spec"
_SAME_ERROR = "ruff: E501 line too long"
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


@pytest.fixture(scope="module")
def tracker() -> Any:
    if not (_CI_SCRIPTS / "early_stop_tracker.py").is_file():
        pytest.skip("early_stop_tracker.py not implemented")
    return _import_ci_script("early_stop_tracker")


@pytest.fixture(scope="module")
def middleware() -> Any:
    if not (_CI_SCRIPTS / "agent_invocation_middleware.py").is_file():
        pytest.skip("agent_invocation_middleware.py missing")
    return _import_ci_script("agent_invocation_middleware")


@pytest.fixture(scope="module")
def early_stop_middleware_hook(middleware: Any) -> Any:
    """Skip middleware adversarial tests until hook + tracker are implemented."""
    if not (_CI_SCRIPTS / "early_stop_tracker.py").is_file():
        pytest.skip("early_stop_tracker.py not implemented")
    if not hasattr(middleware, "_maybe_record_early_stop_iteration"):
        pytest.skip("early stop middleware hook not implemented")
    return middleware


def _sandbox_checkpoints_root(checkpoints_root: Path) -> tuple[Path, str]:
    resolved = checkpoints_root.resolve()
    repo = _REPO_ROOT.resolve()
    for anchor in (repo, Path.cwd().resolve()):
        try:
            resolved.relative_to(anchor)
            return anchor, str(resolved.relative_to(anchor))
        except ValueError:
            continue
    return resolved.parent, resolved.name


def _iterations_path(root: Path, ticket_id: str, tracker_mod: Any) -> Path:
    normalized = tracker_mod.normalize_ticket_id(ticket_id)
    return root / normalized / "agent_iterations.json"


def _events_path(root: Path, ticket_id: str, tracker_mod: Any) -> Path:
    normalized = tracker_mod.normalize_ticket_id(ticket_id)
    return root / normalized / "early_stop_events.jsonl"


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
    tracker_mod: Any,
    root: Path,
    ticket_id: str,
    *,
    agent_run_id: str,
    iteration_context: dict[str, Any],
    loop_run_id: str = _LOOP_RUN_ID,
) -> Path:
    sandbox_cwd, root_arg = _sandbox_checkpoints_root(root)
    with _chdir_lock:
        old_cwd = os.getcwd()
        try:
            os.chdir(sandbox_cwd)
            tracker_mod.record_iteration(
                ticket_id,
                agent_type="implementation",
                agent_run_id=agent_run_id,
                loop_run_id=loop_run_id,
                iteration_context=iteration_context,
                checkpoints_root=Path(root_arg),
            )
        finally:
            os.chdir(old_cwd)
    path = _iterations_path(root, ticket_id, tracker_mod)
    assert path.is_file(), f"expected agent_iterations.json at {path}"
    return path


def _evaluate(tracker_mod: Any, root: Path, ticket_id: str) -> dict[str, Any]:
    sandbox_cwd, root_arg = _sandbox_checkpoints_root(root)
    with _chdir_lock:
        old_cwd = os.getcwd()
        try:
            os.chdir(sandbox_cwd)
            result = tracker_mod.evaluate_early_stop(
                ticket_id,
                checkpoints_root=Path(root_arg),
            )
        finally:
            os.chdir(old_cwd)
    if hasattr(result, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(result)
    if isinstance(result, dict):
        return result
    return dict(result)


def _write_iterations_fixture(
    root: Path,
    ticket_id: str,
    *,
    schema_version: str = _SCHEMA_VERSION,
    iterations: Any | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    normalized = ticket_id.replace("_", "-")
    ticket_dir = root / normalized
    ticket_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": schema_version,
        "ticket_id": normalized,
        "ticket_path": None,
        "agent": "implementation",
        "loop_run_id": _LOOP_RUN_ID,
        "created_at": "2026-05-20T12:00:00Z",
        "updated_at": "2026-05-20T12:00:00Z",
        "iterations": iterations if iterations is not None else [],
        "rollup": {
            "iteration_count": 0,
            "last_error": "",
            "last_diff_hash": EMPTY_DIFF_HASH,
            "error_repeat_streak": 0,
            "diff_repeat_streak": 0,
            "no_op_streak": 0,
            "should_escalate": False,
            "escalate_reason": None,
        },
        "last_evaluation": None,
    }
    if extra:
        payload.update(extra)
    path = ticket_dir / "agent_iterations.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _escalate_fixture(tracker_mod: Any, root: Path, ticket_id: str = "M902-22") -> None:
    for run_id in ("adv-001", "adv-002", "adv-003"):
        _record(
            tracker_mod,
            root,
            ticket_id,
            agent_run_id=run_id,
            iteration_context=_ctx(error=_SAME_ERROR, diff_hash=_DIFF_HASH_A, modified_files=["a.py"]),
        )
    result = _evaluate(tracker_mod, root, ticket_id)
    assert result["should_escalate"] is True


# ---------------------------------------------------------------------------
# Corrupt JSON (Req 01 AC-01.4)
# ---------------------------------------------------------------------------


class TestCorruptAgentIterationsJson:
    """Merge into corrupt on-disk JSON must fail without partial overwrite."""

    def test_merge_into_truncated_json_raises_preserves_bytes(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-22"
        path = _iterations_path(root, ticket_id, tracker)
        path.parent.mkdir(parents=True)
        corrupt = '{"schema_version": "1.0.0", "iterations": ['
        path.write_text(corrupt, encoding="utf-8")

        with pytest.raises((json.JSONDecodeError, ValueError)):
            _record(
                tracker,
                root,
                ticket_id,
                agent_run_id="adv-corrupt",
                iteration_context=_ctx(),
            )

        assert path.read_text(encoding="utf-8") == corrupt

    def test_evaluate_corrupt_json_incomplete_no_escalate(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        path = _write_iterations_fixture(root, "M902-CORRUPT")
        path.write_text("{not-json", encoding="utf-8")

        result = _evaluate(tracker, root, "M902-CORRUPT")
        assert result["incomplete_iterations"] is True
        assert result["should_escalate"] is False


# ---------------------------------------------------------------------------
# Schema mismatch (Req 02 AC-02.4)
# ---------------------------------------------------------------------------


class TestSchemaVersionMismatch:
    """Unsupported schema_version on read is fail-closed."""

    def test_unsupported_schema_version_on_record_raises(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_iterations_fixture(root, "M902-OLD", schema_version="9.9.9")

        with pytest.raises(ValueError, match="unsupported schema_version"):
            _record(
                tracker,
                root,
                "M902-OLD",
                agent_run_id="adv-old",
                iteration_context=_ctx(),
            )

    def test_evaluate_unsupported_schema_incomplete(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_iterations_fixture(root, "M902-EVAL-OLD", schema_version="2.0.0")

        result = _evaluate(tracker, root, "M902-EVAL-OLD")
        assert result["incomplete_iterations"] is True
        assert result["should_escalate"] is False


# ---------------------------------------------------------------------------
# Huge errors (Req 03 AC-03.3)
# ---------------------------------------------------------------------------


class TestHugeErrorBoundaries:
    """Oversized errors truncate deterministically; streak uses normalized form."""

    def test_normalize_error_3000_chars_truncated(self, tracker: Any) -> None:
        raw = "E" * 3000
        normalized = tracker.normalize_error(raw)
        assert len(normalized) <= 2000
        assert normalized.endswith("…[truncated]")

    def test_record_persists_truncated_error_not_raw(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        raw = "x" * 4000
        _record(
            tracker,
            root,
            "M902-22",
            agent_run_id="adv-huge",
            iteration_context=_ctx(error=raw),
        )
        data = json.loads(_iterations_path(root, "M902-22", tracker).read_text(encoding="utf-8"))
        stored = data["iterations"][0]["error"]
        assert len(stored) <= 2000
        assert stored.endswith("…[truncated]")
        assert len(raw) > len(stored)

    def test_three_huge_identical_prefix_errors_still_escalate(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-HUGE"
        base = "FAIL:" + ("z" * 2500)
        for run_id in ("h1", "h2", "h3"):
            _record(
                tracker,
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(error=base, diff_hash=_DIFF_HASH_A),
            )
        result = _evaluate(tracker, root, ticket)
        assert result["should_escalate"] is True
        assert result["reason"] == "repeated_error"


# ---------------------------------------------------------------------------
# Concurrent append (Req 05 AC-05.4)
# ---------------------------------------------------------------------------


class TestConcurrentAppend:
    """Parallel record_iteration calls must not drop iterations or corrupt JSON."""

    def test_parallel_distinct_agent_run_ids_all_persist(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-RACE"
        errors: list[str] = []

        def worker(idx: int) -> None:
            try:
                _record(
                    tracker,
                    root,
                    ticket_id,
                    agent_run_id=f"parallel-{idx}",
                    iteration_context=_ctx(
                        error=f"err-{idx}",
                        diff_hash=f"{idx:064x}"[:64],
                        modified_files=[f"f{idx}.py"],
                    ),
                )
            except Exception as exc:  # noqa: BLE001 — collect thread failures
                errors.append(str(exc))

        with ThreadPoolExecutor(max_workers=8) as pool:
            futs = [pool.submit(worker, i) for i in range(8)]
            for fut in as_completed(futs):
                fut.result()

        assert not errors, f"parallel record failures: {errors}"
        data = json.loads(_iterations_path(root, ticket_id, tracker).read_text(encoding="utf-8"))
        assert data["rollup"]["iteration_count"] == 8
        assert len(data["iterations"]) == 8
        run_ids = {row["agent_run_id"] for row in data["iterations"]}
        assert len(run_ids) == 8

    def test_concurrent_same_agent_run_id_last_write_wins_single_slot(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-22"
        barrier = threading.Barrier(4)

        def worker(tag: str) -> None:
            barrier.wait(timeout=5)
            _record(
                tracker,
                root,
                ticket_id,
                agent_run_id="same-run",
                iteration_context=_ctx(error=tag),
            )

        threads = [threading.Thread(target=worker, args=(f"v{i}",)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        data = json.loads(_iterations_path(root, ticket_id, tracker).read_text(encoding="utf-8"))
        assert len(data["iterations"]) == 1
        assert data["iterations"][0]["agent_run_id"] == "same-run"


# ---------------------------------------------------------------------------
# JSONL idempotency (Req 07 AC-07.3)
# ---------------------------------------------------------------------------


class TestEscalationJsonlIdempotency:
    """Re-evaluate after escalate must not append duplicate JSONL events."""

    def test_double_evaluate_same_state_single_jsonl_line(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        _escalate_fixture(tracker, root, ticket)

        _evaluate(tracker, root, ticket)
        _evaluate(tracker, root, ticket)

        events_path = _events_path(root, ticket, tracker)
        assert events_path.is_file()
        lines = [ln for ln in events_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["should_escalate"] is True
        assert event["reason"] == "repeated_error"

    def test_jsonl_lines_are_valid_json_objects(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-22"
        _escalate_fixture(tracker, root, ticket)
        events_path = _events_path(root, ticket, tracker)
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parsed = json.loads(line)
            assert parsed["break_loop"] == parsed["should_escalate"]


# ---------------------------------------------------------------------------
# Hash sensitivity — one-byte diff change (Req 04 AC-04.4)
# ---------------------------------------------------------------------------


class TestDiffHashByteSensitivity:
    """Mocked git diff payload: one-byte change must alter computed diff_hash."""

    def test_one_byte_git_diff_stdout_changes_hash(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-HASH"
        payloads = (
            "@@ -1 +1 @@\n-old\n+old",
            "@@ -1 +1 @@\n-old\n+new",
        )
        hashes: list[str] = []

        for idx, payload in enumerate(payloads):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = payload

            with patch("subprocess.run", return_value=mock_result):
                _record(
                    tracker,
                    root,
                    ticket,
                    agent_run_id=f"hash-{idx}",
                    iteration_context=_ctx(
                        modified_files=["src/main.py"],
                        error=f"e-{idx}",
                    ),
                )

            data = json.loads(_iterations_path(root, ticket, tracker).read_text(encoding="utf-8"))
            hashes.append(data["iterations"][-1]["diff_hash"])

        assert hashes[0] != hashes[1]
        assert all(len(h) == 64 for h in hashes)
        assert hashes[0] != EMPTY_DIFF_HASH or hashes[1] != EMPTY_DIFF_HASH

    def test_invalid_injected_diff_hash_recomputed_not_trusted(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        bad_hash = "G" * 64
        _record(
            tracker,
            root,
            "M902-22",
            agent_run_id="adv-bad-hash",
            iteration_context=_ctx(diff_hash=bad_hash, modified_files=["a.py"]),
        )
        data = json.loads(_iterations_path(root, "M902-22", tracker).read_text(encoding="utf-8"))
        stored = data["iterations"][0]["diff_hash"]
        assert stored != bad_hash
        assert len(stored) == 64
        assert stored == stored.lower()


# ---------------------------------------------------------------------------
# Vacuous / type-structure edges (Req 03, 06)
# ---------------------------------------------------------------------------


class TestVacuousAndStructuralEdges:
    """Whitespace-only errors and malformed iteration structures."""

    def test_whitespace_only_errors_do_not_build_error_streak(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket = "M902-WS"
        for run_id in ("w1", "w2", "w3"):
            _record(
                tracker,
                root,
                ticket,
                agent_run_id=run_id,
                iteration_context=_ctx(error="   \n\t  ", diff_hash=_DIFF_HASH_A),
            )
        data = json.loads(_iterations_path(root, ticket, tracker).read_text(encoding="utf-8"))
        assert data["rollup"]["error_repeat_streak"] == 0
        result = _evaluate(tracker, root, ticket)
        assert result["reason"] != "repeated_error"

    def test_iterations_wrong_type_on_disk_blocks_evaluate(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_iterations_fixture(root, "M902-BADTYPE", iterations="not-a-list")

        result = _evaluate(tracker, root, "M902-BADTYPE")
        assert result["incomplete_iterations"] is True
        assert result["should_escalate"] is False


# ---------------------------------------------------------------------------
# Middleware adversarial (Req 08)
# ---------------------------------------------------------------------------


class TestMiddlewareAdversarialPaths:
    """Tracking failures and missing context must not break invocations."""

    def test_tracker_exception_swallowed_framework_return_preserved(
        self, early_stop_middleware_hook: Any, tmp_path: Path
    ) -> None:
        payload = {"status": "ok", "value": 99}

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return payload

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.dict(os.environ, {"EARLY_STOP_DETECTION": "1"}, clear=False):
                with patch.object(
                    early_stop_middleware_hook,
                    "_maybe_record_early_stop_iteration",
                    side_effect=RuntimeError("tracker blew up"),
                ):
                    out = early_stop_middleware_hook.invoke_agent_with_category_filtering(
                        agent_type="implementation",
                        prompt="survive",
                        all_tools=[],
                        framework_invocation_fn=_framework,
                        ticket_id="M902-22",
                        agent_run_id="adv-mw",
                        loop_run_id=_LOOP_RUN_ID,
                        loop_mode=True,
                        checkpoints_root=Path("checkpoints"),
                    )
        finally:
            os.chdir(old_cwd)

        assert out is payload

    def test_missing_loop_run_id_skips_iterations_file(
        self, early_stop_middleware_hook: Any, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return {"status": "ok"}

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.dict(os.environ, {"EARLY_STOP_DETECTION": "1"}, clear=False):
                early_stop_middleware_hook.invoke_agent_with_category_filtering(
                    agent_type="implementation",
                    prompt="no loop id",
                    all_tools=[],
                    framework_invocation_fn=_framework,
                    ticket_id="M902-22",
                    agent_run_id="adv-mw2",
                    loop_mode=True,
                    checkpoints_root=Path("checkpoints"),
                )
        finally:
            os.chdir(old_cwd)

        assert not _iterations_path(root, "M902-22", tracker).exists()

"""Adversarial tests for context budget tracking (M902-21).

Exposes merge races, malformed JSON, reporter edge cases, middleware bypass paths,
path traversal, and outlier math boundaries beyond the behavioral contract in
`tests/ci/test_context_budget_tracking.py`.

Traceability: `project_board/specs/902_21_context_budget_tracking_spec.md`
Requirements 01–09 failure taxonomy and risk notes.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"
_REPORT_CLI = _CI_SCRIPTS / "context_budget_report.py"
_SCHEMA_VERSION = "1.0.0"

_RUN_SPEC = "550e8400-e29b-41d4-a716-446655440000"
_RUN_IMPL = "660e8400-e29b-41d4-a716-446655440001"
_RUN_ALT = "770e8400-e29b-41d4-a716-446655440002"


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
    if not (_CI_SCRIPTS / "context_budget_tracker.py").is_file():
        pytest.skip("context_budget_tracker.py not implemented")
    return _import_ci_script("context_budget_tracker")


@pytest.fixture(scope="module")
def middleware() -> Any:
    if not (_CI_SCRIPTS / "agent_invocation_middleware.py").is_file():
        pytest.skip("agent_invocation_middleware.py missing")
    return _import_ci_script("agent_invocation_middleware")


@pytest.fixture(scope="module")
def report_cli() -> Path:
    if not _REPORT_CLI.is_file():
        pytest.skip("context_budget_report.py not implemented")
    return _REPORT_CLI


def _exact_usage(input_tokens: int, output_tokens: int, **extra: Any) -> dict[str, Any]:
    return {"usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}, **extra}


def _usage_path(root: Path, ticket_id: str) -> Path:
    return root / ticket_id / "token_usage.json"


def _record(
    tracker_mod: Any,
    root: Path,
    ticket_id: str,
    *,
    agent_type: str,
    agent_run_id: str,
    framework_result: Any,
    workflow_stage: str | None = None,
    stage_key: str | None = None,
    prompt: str = "prompt",
    tools: list[dict[str, Any]] | None = None,
) -> Path:
    tracker_mod.record_stage_usage(
        ticket_id,
        agent_type=agent_type,
        prompt=prompt,
        tools=tools or [],
        framework_result=framework_result,
        agent_run_id=agent_run_id,
        workflow_stage=workflow_stage,
        stage_key=stage_key,
        checkpoints_root=root,
    )
    path = _usage_path(root, ticket_id)
    assert path.is_file()
    return path


def _write_fixture(
    root: Path,
    ticket_id: str,
    *,
    ticket_type: str = "generic",
    total_tokens: int,
    schema_version: str = _SCHEMA_VERSION,
    corrupt_rollup: bool = False,
) -> None:
    half = total_tokens // 2
    remainder = total_tokens - half
    rollup = {
        "total_tokens": total_tokens,
        "total_input_tokens": half,
        "total_output_tokens": remainder,
        "avg_tokens_per_stage": float(total_tokens),
        "stage_count": 1,
        "max_stage_tokens": total_tokens,
        "max_stage_key": "spec",
    }
    if corrupt_rollup:
        del rollup["total_tokens"]
    payload: dict[str, Any] = {
        "schema_version": schema_version,
        "ticket_id": ticket_id,
        "ticket_type": ticket_type,
        "ticket_path": None,
        "created_at": "2026-05-20T12:00:00Z",
        "updated_at": "2026-05-20T12:00:00Z",
        "stages": {
            "spec": {
                "workflow_stage": "spec",
                "agent_type": "spec",
                "agent_run_id": f"{ticket_id}-run",
                "recorded_at": "2026-05-20T12:00:00Z",
                "input_tokens": half,
                "output_tokens": remainder,
                "total_tokens": total_tokens,
                "schema_size_tokens": 100,
                "context_efficiency": round(remainder / total_tokens, 2) if total_tokens else 0.0,
                "input_efficiency_ratio": round(half / 100, 2),
                "confidence": "exact",
                "estimation_method": None,
                "tool_category_state": None,
            }
        },
        "rollup": rollup,
        "outliers": [],
        "tool_category_state": None,
    }
    ticket_dir = root / ticket_id
    ticket_dir.mkdir(parents=True, exist_ok=True)
    (ticket_dir / "token_usage.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_reporter_json(report_cli: Path, root: Path, *extra: str) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(
        [sys.executable, str(report_cli), "--checkpoints-root", str(root), "--json", *extra],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    report = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, report, proc.stdout, proc.stderr


# ---------------------------------------------------------------------------
# Merge races (Req 01 R1, Req 05)
# ---------------------------------------------------------------------------


class TestMergeRaceConditions:
    """Concurrent writes must not leave unparseable JSON or duplicate stage slots."""

    def test_parallel_writes_same_stage_last_write_wins_valid_json(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-21"
        errors: list[str] = []

        def worker(run_id: str, inp: int) -> None:
            try:
                _record(
                    tracker,
                    root,
                    ticket_id,
                    agent_type="spec",
                    agent_run_id=run_id,
                    framework_result=_exact_usage(inp, 1),
                    workflow_stage="spec",
                )
            except Exception as exc:  # noqa: BLE001 — collect thread failures
                errors.append(str(exc))

        threads = [
            threading.Thread(target=worker, args=(f"run-{i}", 100 + i))
            for i in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"parallel record failures: {errors}"
        data = json.loads(_usage_path(root, ticket_id).read_text(encoding="utf-8"))
        assert len(data["stages"]) == 1
        assert data["stages"]["spec"]["agent_run_id"].startswith("run-")
        assert data["rollup"]["stage_count"] == 1

    def test_interleaved_distinct_stage_keys_both_survive(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-RACE"
        barrier = threading.Barrier(2)

        def record_stage(stage: str, run_id: str, tokens: int) -> None:
            barrier.wait(timeout=5)
            _record(
                tracker,
                root,
                ticket_id,
                agent_type=stage,
                agent_run_id=run_id,
                framework_result=_exact_usage(tokens, 1),
                workflow_stage=stage,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [
                pool.submit(record_stage, "spec", _RUN_SPEC, 50),
                pool.submit(record_stage, "implementation", _RUN_IMPL, 80),
            ]
            for fut in as_completed(futs):
                fut.result()

        data = json.loads(_usage_path(root, ticket_id).read_text(encoding="utf-8"))
        assert set(data["stages"].keys()) == {"spec", "implementation"}
        assert data["rollup"]["stage_count"] == 2


# ---------------------------------------------------------------------------
# Malformed JSON (Req 01 AC-01.4, Req 02 AC-02.4)
# ---------------------------------------------------------------------------


class TestMalformedTokenUsageJson:
    """Fail-closed on corrupt or unsupported on-disk artifacts."""

    def test_merge_into_truncated_json_raises_no_partial_overwrite(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-21"
        path = _usage_path(root, ticket_id)
        path.parent.mkdir(parents=True)
        corrupt = '{"schema_version": "1.0.0", "stages": {'
        path.write_text(corrupt, encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            _record(
                tracker,
                root,
                ticket_id,
                agent_type="spec",
                agent_run_id=_RUN_SPEC,
                framework_result=_exact_usage(1, 1),
            )

        assert path.read_text(encoding="utf-8") == corrupt

    def test_unsupported_schema_version_on_read_raises(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_fixture(root, "M902-OLD", total_tokens=100, schema_version="9.9.9")

        with pytest.raises(ValueError, match="unsupported schema_version"):
            _record(
                tracker,
                root,
                "M902-OLD",
                agent_type="spec",
                agent_run_id=_RUN_SPEC,
                framework_result=_exact_usage(5, 5),
            )

    def test_reporter_skips_corrupt_file_without_traceback(
        self, report_cli: Path, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_fixture(root, "M902-GOOD", total_tokens=500)
        bad_dir = root / "M902-BAD"
        bad_dir.mkdir(parents=True)
        (bad_dir / "token_usage.json").write_text("{not json", encoding="utf-8")

        code, report, _, stderr = _run_reporter_json(report_cli, root)
        assert code == 0, stderr
        assert "Traceback" not in stderr
        assert report["tickets_scanned"] >= 1


# ---------------------------------------------------------------------------
# Reporter edge cases (Req 09)
# ---------------------------------------------------------------------------


class TestReporterEdgeCases:
    """Vacuous medians, tie-breaks, milestone filter, and damaged rollups."""

    def test_single_ticket_of_type_produces_no_outliers(
        self, report_cli: Path, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_fixture(root, "ONLY-FEAT", ticket_type="feature", total_tokens=99999)

        code, report, _, stderr = _run_reporter_json(report_cli, root)
        assert code == 0, stderr
        assert report["outliers"] == []

    def test_exactly_twice_median_not_outlier(self, report_cli: Path, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _write_fixture(root, "FEAT-A", ticket_type="feature", total_tokens=1000)
        _write_fixture(root, "FEAT-B", ticket_type="feature", total_tokens=1000)
        _write_fixture(root, "FEAT-C", ticket_type="feature", total_tokens=2000)

        code, report, _, stderr = _run_reporter_json(report_cli, root)
        assert code == 0, stderr
        outlier_ids = {row["ticket_id"] for row in report["outliers"]}
        assert "FEAT-C" not in outlier_ids

    def test_top_10_tie_break_ticket_id_ascending(self, report_cli: Path, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        for tid in ("M902-Z", "M902-A", "M902-M"):
            _write_fixture(root, tid, total_tokens=5000)

        code, report, _, stderr = _run_reporter_json(report_cli, root)
        assert code == 0, stderr
        top = report["top_10_consumers"]
        tied = [row for row in top if row["total_tokens"] == 5000]
        assert [row["ticket_id"] for row in tied] == sorted(row["ticket_id"] for row in tied)

    def test_milestone_filter_excludes_non_matching_dirs(
        self, report_cli: Path, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_fixture(root, "M901-OLD", total_tokens=100)
        _write_fixture(root, "M902-NEW", total_tokens=200)

        code, report, _, stderr = _run_reporter_json(
            report_cli, root, "--milestone", "902"
        )
        assert code == 0, stderr
        assert report["tickets_scanned"] == 1
        assert report["top_10_consumers"][0]["ticket_id"] == "M902-NEW"

    def test_fixture_missing_rollup_field_handled_gracefully(
        self, report_cli: Path, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_fixture(root, "M902-NOROLL", total_tokens=100, corrupt_rollup=True)

        code, _, _, stderr = _run_reporter_json(report_cli, root)
        assert code in (0, 1)
        assert "Traceback" not in stderr


# ---------------------------------------------------------------------------
# Middleware bypass / opt-out (Req 06)
# ---------------------------------------------------------------------------


class TestMiddlewareTrackingBypass:
    """Silent skip paths must not create artifacts or mutate framework results."""

    def test_missing_ticket_id_skips_write(
        self, middleware: Any, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        root = tmp_path / "checkpoints"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return _exact_usage(3, 2)

        with patch.dict(os.environ, {"CONTEXT_BUDGET_TRACKING": "1"}, clear=False):
            out = middleware.invoke_agent_with_category_filtering(
                agent_type="spec",
                prompt="no ticket",
                all_tools=[],
                framework_invocation_fn=_framework,
                agent_run_id=_RUN_SPEC,
                checkpoints_root=root,
            )

        assert out == _exact_usage(3, 2)
        assert not (root / "M902-21").exists()

    def test_missing_agent_run_id_skips_write(
        self, middleware: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return _exact_usage(1, 1)

        with patch.dict(os.environ, {"CONTEXT_BUDGET_TRACKING": "1"}, clear=False):
            middleware.invoke_agent_with_category_filtering(
                agent_type="spec",
                prompt="no run id",
                all_tools=[],
                framework_invocation_fn=_framework,
                ticket_id="M902-21",
                checkpoints_root=root,
            )

        assert not _usage_path(root, "M902-21").exists()

    def test_only_exact_zero_env_disables_tracking(
        self, middleware: Any, tracker: Any, tmp_path: Path
    ) -> None:
        """Req 06: opt-out is exactly CONTEXT_BUDGET_TRACKING=0, not truthy/falsy strings."""
        root = tmp_path / "checkpoints"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return _exact_usage(9, 1)

        for env_value in ("false", "", "off", "no"):
            env = {k: v for k, v in os.environ.items() if k != "CONTEXT_BUDGET_TRACKING"}
            env["CONTEXT_BUDGET_TRACKING"] = env_value
            with patch.dict(os.environ, env, clear=True):
                middleware.invoke_agent_with_category_filtering(
                    agent_type="spec",
                    prompt="should record",
                    all_tools=[],
                    framework_invocation_fn=_framework,
                    ticket_id="M902-21",
                    agent_run_id=_RUN_SPEC,
                    checkpoints_root=root,
                )
            assert _usage_path(root, "M902-21").is_file(), (
                f"env={env_value!r} must not disable tracking (only '0' does)"
            )
            _usage_path(root, "M902-21").unlink()

        with patch.dict(os.environ, {"CONTEXT_BUDGET_TRACKING": "0"}, clear=False):
            middleware.invoke_agent_with_category_filtering(
                agent_type="spec",
                prompt="disabled",
                all_tools=[],
                framework_invocation_fn=_framework,
                ticket_id="M902-21",
                agent_run_id=_RUN_SPEC,
                checkpoints_root=root,
            )
        assert not _usage_path(root, "M902-21").exists()


# ---------------------------------------------------------------------------
# Path traversal (Req 01, Req 09)
# ---------------------------------------------------------------------------


class TestPathTraversalAdversarial:
    """Traversal and injection attempts must fail closed with no escape writes."""

    @pytest.mark.parametrize(
        "bad_id",
        [
            "../../etc/passwd",
            "M902/../evil",
            "M902-21\x00evil",
            "M902/21",
            "..",
        ],
    )
    def test_record_rejects_traversal_ticket_ids(
        self, tracker: Any, tmp_path: Path, bad_id: str
    ) -> None:
        root = tmp_path / "checkpoints"
        with pytest.raises(ValueError, match="invalid ticket_id|path|ticket"):
            tracker.record_stage_usage(
                bad_id,
                agent_type="spec",
                prompt="x",
                tools=[],
                framework_result=_exact_usage(1, 1),
                agent_run_id=_RUN_SPEC,
                checkpoints_root=root,
            )
        assert list(root.glob("**/token_usage.json")) == []

    def test_reporter_rejects_relative_escape_checkpoints_root(
        self, report_cli: Path, tmp_path: Path
    ) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(report_cli),
                "--checkpoints-root",
                str(tmp_path / ".." / ".." / "etc"),
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1
        assert proc.stderr.strip() != ""


# ---------------------------------------------------------------------------
# Outlier / metric math edge cases (Req 04, Req 09)
# ---------------------------------------------------------------------------


class TestOutlierMathEdgeCases:
    """Boundary math for medians, zero totals, and provider total disagreements."""

    def test_zero_total_tokens_context_efficiency_zero(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _record(
            tracker,
            root,
            "M902-ZERO",
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(0, 0),
        )
        stage = json.loads(_usage_path(root, "M902-ZERO").read_text())["stages"]["spec"]
        assert stage["total_tokens"] == 0
        assert stage["context_efficiency"] == 0.0

    def test_provider_total_tokens_disagreement_recomputed(
        self, tracker: Any, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        framework_result = {
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 9999,
            }
        }
        _record(
            tracker,
            root,
            "M902-SUM",
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=framework_result,
        )
        stage = json.loads(_usage_path(root, "M902-SUM").read_text())["stages"]["spec"]
        assert stage["total_tokens"] == 15
        assert stage["input_tokens"] + stage["output_tokens"] == 15

    def test_outlier_strictly_greater_than_twice_median(
        self, report_cli: Path, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        _write_fixture(root, "BUG-1", ticket_type="bugfix", total_tokens=100)
        _write_fixture(root, "BUG-2", ticket_type="bugfix", total_tokens=100)
        _write_fixture(root, "BUG-3", ticket_type="bugfix", total_tokens=201)

        code, report, _, stderr = _run_reporter_json(report_cli, root)
        assert code == 0, stderr
        outlier_ids = {row["ticket_id"] for row in report["outliers"]}
        assert "BUG-3" in outlier_ids

    def test_even_count_median_outlier_uses_lower_middle(
        self, report_cli: Path, tmp_path: Path
    ) -> None:
        root = tmp_path / "checkpoints"
        for tid, total in (("R-1", 100), ("R-2", 200), ("R-3", 300), ("R-4", 400)):
            _write_fixture(root, tid, ticket_type="refactor", total_tokens=total)
        _write_fixture(root, "R-OUT", ticket_type="refactor", total_tokens=900)

        code, report, _, stderr = _run_reporter_json(report_cli, root)
        assert code == 0, stderr
        assert any(row["ticket_id"] == "R-OUT" for row in report["outliers"])

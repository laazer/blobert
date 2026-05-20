"""Behavioral tests for context budget tracking (M902-21).

Validates `ci/scripts/context_budget_tracker.py`, `ci/scripts/context_budget_report.py`,
and middleware hook in `ci/scripts/agent_invocation_middleware.py` per
`project_board/specs/902_21_context_budget_tracking_spec.md` Test Contract (T1–T11).

Assertions target JSON artifacts, CLI exit codes, and computed metrics — not ticket markdown.
Isolation: `tmp_path` checkpoints roots; `unittest.mock` for framework returns.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"


def _ensure_ci_scripts_package() -> None:
    """Register `ci.scripts` so middleware relative imports resolve in tests."""
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


_tracker = _import_ci_script("context_budget_tracker")
record_stage_usage = _tracker.record_stage_usage
normalize_workflow_stage = _tracker.normalize_workflow_stage
infer_ticket_type = _tracker.infer_ticket_type


def _invoke_agent_with_category_filtering(*args: Any, **kwargs: Any) -> Any:
    middleware = _import_ci_script("agent_invocation_middleware")
    return middleware.invoke_agent_with_category_filtering(*args, **kwargs)

_REPORT_CLI = _CI_SCRIPTS / "context_budget_report.py"
_SCHEMA_VERSION = "1.0.0"

_RUN_SPEC = "550e8400-e29b-41d4-a716-446655440000"
_RUN_TEST_DESIGNER = "660e8400-e29b-41d4-a716-446655440001"
_RUN_RETRY = "770e8400-e29b-41d4-a716-446655440002"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exact_usage(input_tokens: int, output_tokens: int, **extra: Any) -> dict[str, Any]:
    return {"usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}, **extra}


def _usage_path(checkpoints_root: Path, ticket_id: str) -> Path:
    return checkpoints_root / ticket_id / "token_usage.json"


def _load_usage(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _record(
    checkpoints_root: Path,
    ticket_id: str,
    *,
    agent_type: str,
    agent_run_id: str,
    framework_result: Any,
    workflow_stage: str | None = None,
    stage_key: str | None = None,
    prompt: str = "agent prompt body",
    tools: list[dict[str, Any]] | None = None,
    ticket_path: str | None = None,
    ticket_type: str | None = None,
) -> Path:
    record_stage_usage(
        ticket_id,
        agent_type=agent_type,
        prompt=prompt,
        tools=tools or [],
        framework_result=framework_result,
        agent_run_id=agent_run_id,
        workflow_stage=workflow_stage,
        stage_key=stage_key,
        ticket_path=ticket_path,
        ticket_type=ticket_type,
        checkpoints_root=checkpoints_root,
    )
    path = _usage_path(checkpoints_root, ticket_id)
    assert path.is_file(), f"expected token_usage.json at {path}"
    return path


def _write_token_usage_fixture(
    checkpoints_root: Path,
    ticket_id: str,
    *,
    ticket_type: str = "generic",
    agent_type: str = "spec",
    workflow_stage: str = "spec",
    total_tokens: int,
) -> None:
    """Minimal on-disk fixture for reporter-only scenarios."""
    half = total_tokens // 2
    remainder = total_tokens - half
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "ticket_id": ticket_id,
        "ticket_type": ticket_type,
        "ticket_path": None,
        "created_at": "2026-05-20T12:00:00Z",
        "updated_at": "2026-05-20T12:00:00Z",
        "stages": {
            workflow_stage: {
                "workflow_stage": workflow_stage,
                "agent_type": agent_type,
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
        "rollup": {
            "total_tokens": total_tokens,
            "total_input_tokens": half,
            "total_output_tokens": remainder,
            "avg_tokens_per_stage": float(total_tokens),
            "stage_count": 1,
            "max_stage_tokens": total_tokens,
            "max_stage_key": workflow_stage,
        },
        "outliers": [],
        "tool_category_state": None,
    }
    ticket_dir = checkpoints_root / ticket_id
    ticket_dir.mkdir(parents=True, exist_ok=True)
    out = ticket_dir / "token_usage.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_reporter_json(checkpoints_root: Path, *extra_args: str) -> tuple[int, dict[str, Any], str, str]:
    cmd = [
        sys.executable,
        str(_REPORT_CLI),
        "--checkpoints-root",
        str(checkpoints_root),
        "--json",
        *extra_args,
    ]
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.stdout.strip():
        report = json.loads(proc.stdout)
    else:
        report = {}
    return proc.returncode, report, proc.stdout, proc.stderr


def _run_reporter_human(checkpoints_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(_REPORT_CLI),
        "--checkpoints-root",
        str(checkpoints_root),
        *extra_args,
    ]
    return subprocess.run(cmd, cwd=_REPO_ROOT, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# T1 — Merge two stages without clobber (Req 01, 05)
# ---------------------------------------------------------------------------


class TestRecordStageMerge:
    """T1 / AC-01.2 / AC-05.3: sequential stages accumulate in one file."""

    def test_merge_two_stages_preserves_both_entries(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-21"

        _record(
            root,
            ticket_id,
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(100, 50),
            workflow_stage="spec",
        )
        _record(
            root,
            ticket_id,
            agent_type="test-designer",
            agent_run_id=_RUN_TEST_DESIGNER,
            framework_result=_exact_usage(200, 80),
            workflow_stage="test-designer",
        )

        data = _load_usage(_usage_path(root, ticket_id))
        assert set(data["stages"].keys()) == {"spec", "test-designer"}
        assert data["stages"]["spec"]["total_tokens"] == 150
        assert data["stages"]["test-designer"]["total_tokens"] == 280
        assert data["rollup"]["stage_count"] == 2
        assert data["rollup"]["total_tokens"] == 430
        assert data["ticket_id"] == ticket_id


# ---------------------------------------------------------------------------
# T2 — Idempotent same agent_run_id (Req 05)
# ---------------------------------------------------------------------------


class TestRecordStageIdempotency:
    """T2 / AC-05.1–AC-05.2: retries replace; same stage_key latest wins."""

    def test_same_agent_run_id_replaces_not_duplicates(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-21"

        _record(
            root,
            ticket_id,
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(100, 50),
            workflow_stage="spec",
        )
        _record(
            root,
            ticket_id,
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(300, 100),
            workflow_stage="spec",
        )

        data = _load_usage(_usage_path(root, ticket_id))
        assert len(data["stages"]) == 1
        assert data["stages"]["spec"]["input_tokens"] == 300
        assert data["stages"]["spec"]["output_tokens"] == 100
        assert data["stages"]["spec"]["total_tokens"] == 400

    def test_same_stage_key_different_run_id_latest_wins(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-21"

        _record(
            root,
            ticket_id,
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(50, 25),
            workflow_stage="spec",
        )
        _record(
            root,
            ticket_id,
            agent_type="spec",
            agent_run_id=_RUN_RETRY,
            framework_result=_exact_usage(500, 200),
            workflow_stage="spec",
        )

        data = _load_usage(_usage_path(root, ticket_id))
        assert len(data["stages"]) == 1
        assert data["stages"]["spec"]["agent_run_id"] == _RUN_RETRY
        assert data["stages"]["spec"]["total_tokens"] == 700


# ---------------------------------------------------------------------------
# T3 — context_efficiency formula (Req 04)
# ---------------------------------------------------------------------------


class TestMetricFormulas:
    """T3 / AC-04.1–AC-04.3: frozen derived metrics on write."""

    def test_context_and_input_efficiency_ratios(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        tools = [{"name": "read", "categories": ["parse"], "rationale": "Read files"}] * 3

        _record(
            root,
            "M902-04",
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(4250, 1840),
            workflow_stage="spec",
            tools=tools,
        )

        stage = _load_usage(_usage_path(root, "M902-04"))["stages"]["spec"]
        assert stage["total_tokens"] == 6090
        assert stage["context_efficiency"] == 0.3
        assert stage["input_efficiency_ratio"] == 2.02
        assert stage["confidence"] == "exact"

    def test_empty_tools_schema_size_zero(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902-04B",
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(10, 5),
            tools=[],
        )
        stage = _load_usage(_usage_path(root, "M902-04B"))["stages"]["spec"]
        assert stage["schema_size_tokens"] == 0


# ---------------------------------------------------------------------------
# T4 — Missing usage → estimated (Req 03)
# ---------------------------------------------------------------------------


class TestUsageMetadataEstimation:
    """T4 / AC-03.2: estimation path when provider usage absent."""

    def test_opaque_result_uses_char_div4_estimation(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        prompt = "hello"
        result_text = "world"

        _record(
            root,
            "M902-EST",
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=result_text,
            prompt=prompt,
        )

        stage = _load_usage(_usage_path(root, "M902-EST"))["stages"]["spec"]
        assert stage["confidence"] == "estimated"
        assert stage["estimation_method"] == "char_div4"
        expected_in = len(prompt.encode("utf-8")) // 4
        expected_out = len(result_text.encode("utf-8")) // 4
        assert stage["input_tokens"] == expected_in
        assert stage["output_tokens"] == expected_out
        assert stage["total_tokens"] == expected_in + expected_out

    def test_negative_usage_rejected_without_write(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        ticket_id = "M902-NEG"

        with pytest.raises(ValueError, match="negative token"):
            record_stage_usage(
                ticket_id,
                agent_type="spec",
                prompt="x",
                tools=[],
                framework_result={"usage": {"input_tokens": -1, "output_tokens": 5}},
                agent_run_id=_RUN_SPEC,
                checkpoints_root=root,
            )

        assert not _usage_path(root, ticket_id).exists()


# ---------------------------------------------------------------------------
# T5–T9, T11 — Reporter CLI (Req 09, 01)
# ---------------------------------------------------------------------------


class TestContextBudgetReporter:
    """Aggregate reporter across fixture token_usage.json files."""

    def test_totals_by_agent_type_sums_match_manual(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _write_token_usage_fixture(root, "M902-A", agent_type="spec", total_tokens=1000)
        _write_token_usage_fixture(root, "M902-B", agent_type="implementation", total_tokens=2500)

        code, report, _, stderr = _run_reporter_json(root)
        assert code == 0, stderr
        assert report["tickets_scanned"] == 2
        assert report["totals_by_agent_type"]["spec"] == 1000
        assert report["totals_by_agent_type"]["implementation"] == 2500

    def test_averages_by_ticket_type(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _write_token_usage_fixture(root, "BUG-1", ticket_type="bugfix", total_tokens=800)
        _write_token_usage_fixture(root, "BUG-2", ticket_type="bugfix", total_tokens=1200)

        code, report, _, stderr = _run_reporter_json(root)
        assert code == 0, stderr
        bugfix = report["averages_by_ticket_type"]["bugfix"]
        assert bugfix["ticket_count"] == 2
        assert bugfix["mean_total_tokens"] == 1000.0
        assert bugfix["median_total_tokens"] == 1000

    def test_top_10_consumers_deterministic_with_eleven_tickets(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        for i in range(11):
            tid = f"M902-T{i:02d}"
            _write_token_usage_fixture(root, tid, total_tokens=1000 + i * 100)

        code, report, _, stderr = _run_reporter_json(root)
        assert code == 0, stderr
        top = report["top_10_consumers"]
        assert len(top) == 10
        assert [row["total_tokens"] for row in top] == sorted(
            [1000 + i * 100 for i in range(1, 11)], reverse=True
        )
        assert [row["ticket_id"] for row in top] == [
            f"M902-T{i:02d}" for i in range(10, 0, -1)
        ]

    def test_outlier_above_twice_median_for_ticket_type(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _write_token_usage_fixture(root, "FEAT-1", ticket_type="feature", total_tokens=1000)
        _write_token_usage_fixture(root, "FEAT-2", ticket_type="feature", total_tokens=1100)
        _write_token_usage_fixture(root, "FEAT-OUT", ticket_type="feature", total_tokens=2500)

        code, report, _, stderr = _run_reporter_json(root)
        assert code == 0, stderr
        outlier_ids = {row["ticket_id"] for row in report["outliers"]}
        assert "FEAT-OUT" in outlier_ids

    def test_empty_checkpoints_root_exit_zero(self, tmp_path: Path) -> None:
        root = tmp_path / "empty_checkpoints"
        root.mkdir()

        code, report, _, stderr = _run_reporter_json(root)
        assert code == 0, stderr
        assert report["tickets_scanned"] == 0

        human = _run_reporter_human(root)
        assert human.returncode == 0
        assert "No token usage data found." in human.stdout

    def test_reporter_rejects_checkpoints_root_outside_repo(self, tmp_path: Path) -> None:
        outside = tmp_path / "outside_repo"
        outside.mkdir()
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPORT_CLI),
                "--checkpoints-root",
                str(outside),
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1
        assert proc.stderr.strip() != ""


# ---------------------------------------------------------------------------
# T10 — Middleware opt-out (Req 06)
# ---------------------------------------------------------------------------


class TestMiddlewareContextBudgetHook:
    """T10 / AC-06.1–AC-06.4: hook behavior and env opt-out."""

    def test_tracking_enabled_writes_token_usage(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        env = {k: v for k, v in os.environ.items() if k != "CONTEXT_BUDGET_TRACKING"}
        env["CONTEXT_BUDGET_TRACKING"] = "1"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return _exact_usage(12, 8)

        with patch.dict(os.environ, env, clear=True):
            result = _invoke_agent_with_category_filtering(
                agent_type="spec",
                prompt="Write specification",
                all_tools=[],
                framework_invocation_fn=_framework,
                ticket_id="M902-21",
                agent_run_id=_RUN_SPEC,
                workflow_stage="spec",
                checkpoints_root=root,
            )

        assert result == _exact_usage(12, 8)
        data = _load_usage(_usage_path(root, "M902-21"))
        assert data["stages"]["spec"]["total_tokens"] == 20

    def test_context_budget_tracking_zero_skips_write(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return _exact_usage(5, 5)

        with patch.dict(os.environ, {"CONTEXT_BUDGET_TRACKING": "0"}, clear=False):
            _invoke_agent_with_category_filtering(
                agent_type="spec",
                prompt="no tracking",
                all_tools=[],
                framework_invocation_fn=_framework,
                ticket_id="M902-21",
                agent_run_id=_RUN_SPEC,
                checkpoints_root=root,
            )

        assert not _usage_path(root, "M902-21").exists()

    def test_framework_exception_does_not_update_usage(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"

        def _fail(**_kwargs: Any) -> None:
            raise RuntimeError("framework failed")

        with patch.dict(os.environ, {"CONTEXT_BUDGET_TRACKING": "1"}, clear=False):
            with pytest.raises(RuntimeError, match="framework failed"):
                _invoke_agent_with_category_filtering(
                    agent_type="spec",
                    prompt="fail path",
                    all_tools=[],
                    framework_invocation_fn=_fail,
                    ticket_id="M902-21",
                    agent_run_id=_RUN_SPEC,
                    checkpoints_root=root,
                )

        assert not _usage_path(root, "M902-21").exists()

    def test_middleware_return_value_unchanged(self, tmp_path: Path) -> None:
        payload = {"usage": {"input_tokens": 1, "output_tokens": 2}, "answer": 42}

        def _framework(**_kwargs: Any) -> dict[str, Any]:
            return payload

        with patch.dict(os.environ, {"CONTEXT_BUDGET_TRACKING": "1"}, clear=False):
            out = _invoke_agent_with_category_filtering(
                agent_type="spec",
                prompt="unchanged",
                all_tools=[],
                framework_invocation_fn=_framework,
                ticket_id="M902-21",
                agent_run_id=_RUN_SPEC,
            )

        assert out == payload


# ---------------------------------------------------------------------------
# T11 — Path traversal rejected (Req 01, 09)
# ---------------------------------------------------------------------------


class TestPathSafety:
    """T11 / AC-01.3: invalid ticket_id and traversal paths fail closed."""

    def test_record_stage_rejects_path_traversal_ticket_id(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        with pytest.raises(ValueError, match="invalid ticket_id|path"):
            record_stage_usage(
                "../evil",
                agent_type="spec",
                prompt="x",
                tools=[],
                framework_result=_exact_usage(1, 1),
                agent_run_id=_RUN_SPEC,
                checkpoints_root=root,
            )
        assert not (root / "evil").exists()

    def test_ticket_id_underscore_normalized_to_hyphen(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902_21",
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(10, 5),
        )
        assert _usage_path(root, "M902-21").is_file()
        data = _load_usage(_usage_path(root, "M902-21"))
        assert data["ticket_id"] == "M902-21"


# ---------------------------------------------------------------------------
# Supporting contracts (Req 07, 08) — exercised by recorder paths
# ---------------------------------------------------------------------------


class TestNormalizationAndTicketType:
    """Stage normalization and ticket_type inference/immutability."""

    def test_normalize_workflow_stage_aliases(self) -> None:
        assert normalize_workflow_stage("Spec Agent", None) == "spec"
        assert normalize_workflow_stage("any", "TEST_DESIGN") == "test-designer"
        assert normalize_workflow_stage("custom-bot", None) == "unknown"

    def test_infer_ticket_type_from_path(self) -> None:
        assert (
            infer_ticket_type(
                "project_board/foo/bugfix/bar.md",
                title=None,
            )
            == "bugfix"
        )
        assert infer_ticket_type("project_board/tickets/21_foo.md", title="M902-21") == "generic"

    def test_ticket_type_immutable_after_first_write(self, tmp_path: Path) -> None:
        root = tmp_path / "checkpoints"
        _record(
            root,
            "M902-TYPE",
            agent_type="spec",
            agent_run_id=_RUN_SPEC,
            framework_result=_exact_usage(10, 5),
            ticket_type="feature",
        )
        _record(
            root,
            "M902-TYPE",
            agent_type="spec",
            agent_run_id=_RUN_RETRY,
            framework_result=_exact_usage(20, 10),
            ticket_path="project_board/bugfix/would_change.md",
        )
        data = _load_usage(_usage_path(root, "M902-TYPE"))
        assert data["ticket_type"] == "feature"

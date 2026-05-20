"""Behavioral tests for TodoWrite checkpoint validation gate (M902-20).

Validates `validate_todos` and `run()` in `ci/scripts/gates/todo_validation_check.py` against
`project_board/specs/902_20_todo_validation_spec.md` (Req 01–08, scenarios T1–T7).

Tests use `tmp_path` fixtures with `todos-latest.json` under checkpoint ticket dirs.
No assertions on ticket markdown prose.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any
import pytest

CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(CI_SCRIPTS))

from gates.todo_validation_check import run as gate_run
from gates.todo_validation_check import validate_todos

GATE_NAME = "todo_validation_check"
TICKET_ID = "M902-20"
SPEC_AGENT = "Spec Agent"
PLANNER_AGENT = "Planner Agent"


# ---------------------------------------------------------------------------
# Fixture helpers (Requirement 02 TodoSnapshot contract)
# ---------------------------------------------------------------------------


def _todo(
    todo_id: str,
    content: str,
    status: str,
    *,
    agent: str | None = None,
    active_form: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": todo_id,
        "content": content,
        "status": status,
    }
    if agent is not None:
        record["agent"] = agent
    if active_form is not None:
        record["activeForm"] = active_form
    return record


def _snapshot(
    todos: list[dict[str, Any]],
    *,
    ticket_id: str = TICKET_ID,
    agent: str = SPEC_AGENT,
    schema_version: str = "1.0",
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "ticket_id": ticket_id,
        "agent": agent,
        "captured_at": "2026-05-20T18:00:00Z",
        "todos": todos,
    }


def _write_todos_latest(ticket_dir: Path, snapshot: dict[str, Any]) -> Path:
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / "todos-latest.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    return path


def _repo_layout(tmp_path: Path, ticket_id: str = TICKET_ID) -> Path:
    """Return ticket checkpoint dir under faux repo root (cwd = tmp_path)."""
    return tmp_path / "project_board" / "checkpoints" / ticket_id


def _checkpoints_parent(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


def _assert_gate_envelope(result: dict[str, Any]) -> None:
    assert result["version"] == "0.1.0"
    assert result["gate"] == GATE_NAME
    assert result["ticket_id"] == TICKET_ID
    assert result["status"] in ("PASS", "FAIL")
    assert isinstance(result["message"], str)
    assert isinstance(result["violations"], list)
    assert isinstance(result["remediation_hints"], list)
    assert isinstance(result["incomplete_tasks"], list)
    assert isinstance(result["duration_ms"], int)
    assert "timestamp" in result


def _run_with_checkpoints(
    tmp_path: Path,
    *,
    expected_agent: str = SPEC_AGENT,
    ticket_id: str = TICKET_ID,
    extra_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inputs: dict[str, Any] = {
        "ticket_id": ticket_id,
        "expected_agent": expected_agent,
        "checkpoints_dir": str(_checkpoints_parent(tmp_path)),
    }
    if extra_inputs:
        inputs.update(extra_inputs)
    result = gate_run(inputs)
    _assert_gate_envelope(result)
    return result


# ---------------------------------------------------------------------------
# T1–T7 core scenarios (Requirement 08)
# ---------------------------------------------------------------------------


class TestTodoValidationT1AllCompleted:
    """T1: All attributed todos completed → PASS (AC-01.1, AC-03.1)."""

    def test_validate_todos_all_completed_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        _write_todos_latest(
            ticket_dir,
            _snapshot(
                [
                    _todo("t1", "Draft acceptance criteria", "completed"),
                    _todo("t2", "Map test scenarios", "completed"),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        _assert_gate_envelope(result)
        assert result["status"] == "PASS"
        assert result["incomplete_tasks"] == []
        assert result["violations"] == []

    def test_run_all_completed_passes(self, tmp_path: Path) -> None:
        ticket_dir = _checkpoints_parent(tmp_path) / TICKET_ID
        _write_todos_latest(
            ticket_dir,
            _snapshot(
                [
                    _todo("t1", "Draft acceptance criteria", "completed"),
                    _todo("t2", "Map test scenarios", "completed"),
                ],
            ),
        )
        result = _run_with_checkpoints(tmp_path)
        assert result["status"] == "PASS"
        assert "completed" in result["message"].lower() or "All todos" in result["message"]


class TestTodoValidationT2OneIncomplete:
    """T2: One in_progress for expected agent → FAIL with one incomplete (AC-01.2)."""

    def test_validate_todos_one_in_progress_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        _write_todos_latest(
            ticket_dir,
            _snapshot(
                [
                    _todo("t1", "Draft acceptance criteria", "in_progress"),
                    _todo("t2", "Map test scenarios", "completed"),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert len(result["incomplete_tasks"]) == 1
        assert result["incomplete_tasks"][0]["id"] == "t1"
        assert result["incomplete_tasks"][0]["status"] == "in_progress"
        assert result["incomplete_tasks"][0]["agent_key"] == "spec"
        assert len(result["violations"]) == 1
        assert result["violations"][0]["rule"] == "todo_incomplete"
        assert len(result["remediation_hints"]) >= 3

    def test_fail_message_includes_task_count(self, tmp_path: Path) -> None:
        ticket_dir = _checkpoints_parent(tmp_path) / TICKET_ID
        _write_todos_latest(
            ticket_dir,
            _snapshot([_todo("t1", "Draft acceptance criteria", "in_progress")]),
        )
        result = _run_with_checkpoints(tmp_path)
        assert result["status"] == "FAIL"
        assert "1 task" in result["message"] or "1 task(s)" in result["message"]


class TestTodoValidationT3MultipleIncomplete:
    """T3: Multiple in_progress → FAIL lists all, stable sort (AC-01.3)."""

    def test_validate_todos_three_in_progress_sorted(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        _write_todos_latest(
            ticket_dir,
            _snapshot(
                [
                    _todo("c", "Map test scenarios", "in_progress"),
                    _todo("a", "Draft acceptance criteria", "in_progress"),
                    _todo("b", "Review spec exit gate", "in_progress"),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert len(result["incomplete_tasks"]) == 3
        ids = [t["id"] for t in result["incomplete_tasks"]]
        assert ids == sorted(ids)
        assert len(result["violations"]) == 3
        for violation in result["violations"]:
            assert violation["rule"] == "todo_incomplete"
            assert violation["severity"] == "ERROR"


class TestTodoValidationT4NoArtifacts:
    """T4: No snapshot files → vacuous PASS (AC-01.4, AC-03.5)."""

    def test_validate_todos_no_artifacts_vacuous_pass(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"
        assert result["incomplete_tasks"] == []
        assert "no todo" in result["message"].lower()

    def test_run_no_artifacts_vacuous_pass(self, tmp_path: Path) -> None:
        (_checkpoints_parent(tmp_path) / TICKET_ID).mkdir(parents=True)
        result = _run_with_checkpoints(tmp_path)
        assert result["status"] == "PASS"
        assert "no todo" in result["message"].lower()


class TestTodoValidationT5EmptyList:
    """T5: Snapshot with empty todos array → vacuous PASS (AC-01.5, AC-03.4)."""

    def test_validate_todos_empty_todos_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(_repo_layout(tmp_path), _snapshot([]))
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"
        assert result["incomplete_tasks"] == []
        assert "empty" in result["message"].lower() or "vacuous" in result["message"].lower()


class TestTodoValidationT6PriorAgentRegression:
    """T6: Prior-agent in_progress does not fail current agent (AC-01.6, AC-04.2)."""

    def test_planner_in_progress_spec_completed_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        _write_todos_latest(
            ticket_dir,
            _snapshot(
                [
                    _todo("p1", "Decompose milestone", "in_progress", agent=PLANNER_AGENT),
                    _todo("s1", "Draft acceptance criteria", "completed"),
                    _todo("s2", "Map test scenarios", "completed"),
                ],
                agent=SPEC_AGENT,
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"
        assert result["incomplete_tasks"] == []


class TestTodoValidationT7MalformedArtifact:
    """T7: Invalid JSON → FAIL todo_artifact_invalid (AC-01.7)."""

    def test_invalid_json_fails_closed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        (ticket_dir / "todos-latest.json").write_text("{not valid json", encoding="utf-8")
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert result["incomplete_tasks"] == []
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])


# ---------------------------------------------------------------------------
# Requirement 03 — non-blocking statuses
# ---------------------------------------------------------------------------


class TestTodoValidationNonBlockingStatuses:
    """pending/cancelled must not fail when no in_progress (AC-03.3)."""

    @pytest.mark.parametrize(
        "status",
        ["pending", "cancelled"],
    )
    def test_pending_and_cancelled_pass(
        self, tmp_path: Path, status: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Deferred work", status)]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# Requirement 04 — agent attribution and normalization
# ---------------------------------------------------------------------------


class TestTodoValidationAgentAttribution:
    """Agent matching, envelope inheritance, unattributed exclusion (Req 04)."""

    def test_envelope_agent_case_insensitive_match(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Task", "completed")], agent="spec agent"),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_per_todo_agent_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [
                    _todo("t1", "Planner task", "in_progress", agent=PLANNER_AGENT),
                    _todo("t2", "Spec task", "completed", agent=SPEC_AGENT),
                ],
                agent=SPEC_AGENT,
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_unattributed_todo_excluded(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        snapshot = _snapshot([_todo("t1", "Orphan task", "in_progress")])
        del snapshot["agent"]
        _write_todos_latest(_repo_layout(tmp_path), snapshot)
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_implementation_agent_generalist_alias(self, tmp_path: Path) -> None:
        ticket_dir = _checkpoints_parent(tmp_path) / TICKET_ID
        _write_todos_latest(
            ticket_dir,
            _snapshot(
                [_todo("t1", "Ship feature", "in_progress")],
                agent="Implementation Agent (Generalist)",
            ),
        )
        result = _run_with_checkpoints(tmp_path, expected_agent="Implementation Agent (Generalist)")
        assert result["status"] == "FAIL"
        assert result["incomplete_tasks"][0]["agent_key"] == "implementation"


# ---------------------------------------------------------------------------
# Requirement 02 — discovery and schema validation
# ---------------------------------------------------------------------------


class TestTodoSnapshotDiscovery:
    """Snapshot precedence and schema fail-closed rules (Req 02)."""

    def test_todos_latest_preferred_over_older_run_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        older = ticket_dir / "todos-2026-05-19T-planning.json"
        older.write_text(
            json.dumps(_snapshot([_todo("old", "Stale in progress", "in_progress")])),
            encoding="utf-8",
        )
        time.sleep(0.02)
        _write_todos_latest(ticket_dir, _snapshot([_todo("new", "Fresh completed", "completed")]))
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_wrong_schema_version_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Task", "completed")], schema_version="2.0"),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])

    def test_duplicate_todo_ids_fail(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [
                    _todo("dup", "First", "completed"),
                    _todo("dup", "Second", "completed"),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])

    def test_unknown_status_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Task", "blocked")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])

    def test_ticket_id_normalization(self, tmp_path: Path) -> None:
        ticket_dir = _checkpoints_parent(tmp_path) / "M902-20"
        _write_todos_latest(
            ticket_dir,
            _snapshot([_todo("t1", "Task", "completed")]),
        )
        result = _run_with_checkpoints(tmp_path, ticket_id="M902_20")
        assert result["ticket_id"] == "M902-20"
        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# Requirement 05 — run() contract
# ---------------------------------------------------------------------------


class TestTodoValidationRunContract:
    """run() inputs, gate name, missing required fields (Req 05)."""

    def test_run_sets_gate_name(self, tmp_path: Path) -> None:
        (_checkpoints_parent(tmp_path) / TICKET_ID).mkdir(parents=True)
        result = _run_with_checkpoints(tmp_path)
        assert result["gate"] == GATE_NAME

    def test_run_missing_ticket_id_fails(self, tmp_path: Path) -> None:
        result = gate_run({"expected_agent": SPEC_AGENT, "checkpoints_dir": str(_checkpoints_parent(tmp_path))})
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "missing_required_input" for v in result["violations"])

    def test_run_missing_expected_agent_fails(self, tmp_path: Path) -> None:
        result = gate_run({"ticket_id": TICKET_ID, "checkpoints_dir": str(_checkpoints_parent(tmp_path))})
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "missing_required_input" for v in result["violations"])

    def test_run_echoes_upstream_downstream_mode(self, tmp_path: Path) -> None:
        (_checkpoints_parent(tmp_path) / TICKET_ID).mkdir(parents=True)
        result = _run_with_checkpoints(
            tmp_path,
            extra_inputs={
                "upstream_agent": SPEC_AGENT,
                "downstream_agent": "Test Designer Agent",
                "mode": "shadow",
            },
        )
        assert result.get("upstream_agent") == SPEC_AGENT
        assert result.get("downstream_agent") == "Test Designer Agent"
        assert result.get("mode") == "shadow"


# ---------------------------------------------------------------------------
# Requirement 06 — FAIL payload shape
# ---------------------------------------------------------------------------


class TestTodoValidationFailPayload:
    """incomplete_tasks ↔ violations parity and remediation (Req 06)."""

    def test_incomplete_tasks_match_violations_count(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [
                    _todo("t1", "Alpha", "in_progress", active_form="Doing alpha"),
                    _todo("t2", "Beta", "in_progress"),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert len(result["incomplete_tasks"]) == len(result["violations"])
        assert result["incomplete_tasks"][0]["activeForm"] == "Doing alpha"
        assert result["incomplete_tasks"][1]["activeForm"] == "Beta"

    def test_checkpoint_files_not_mutated_on_fail(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        path = _write_todos_latest(
            ticket_dir,
            _snapshot([_todo("t1", "Still open", "in_progress")]),
        )
        before = path.read_bytes()
        validate_todos(TICKET_ID, SPEC_AGENT)
        assert path.read_bytes() == before


# ---------------------------------------------------------------------------
# NFR-3 — path traversal rejection
# ---------------------------------------------------------------------------


class TestTodoValidationPathSecurity:
    """Reject traversal in ticket_id and checkpoints_dir (NFR-3)."""

    def test_ticket_id_with_dotdot_rejected(self, tmp_path: Path) -> None:
        result = gate_run(
            {
                "ticket_id": "../etc",
                "expected_agent": SPEC_AGENT,
                "checkpoints_dir": str(_checkpoints_parent(tmp_path)),
            }
        )
        assert result["status"] == "FAIL"
        assert any(
            v.get("rule") in ("path_traversal", "todo_artifact_invalid", "missing_required_input")
            for v in result["violations"]
        )

    def test_checkpoints_dir_traversal_rejected(self, tmp_path: Path) -> None:
        result = gate_run(
            {
                "ticket_id": TICKET_ID,
                "expected_agent": SPEC_AGENT,
                "checkpoints_dir": str(tmp_path / ".." / "secrets"),
            }
        )
        assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Requirement 07 — registry contract (red until Task 5)
# ---------------------------------------------------------------------------


class TestTodoValidationRegistry:
    """Registry entry todo_validation_check (AC-07.1)."""

    def test_gate_registry_contains_todo_validation_check(self, gate_registry: Path) -> None:
        entries = json.loads(gate_registry.read_text(encoding="utf-8"))
        names = {e["name"] for e in entries}
        assert GATE_NAME in names
        entry = next(e for e in entries if e["name"] == GATE_NAME)
        assert entry["module"] == "todo_validation_check"
        assert "ticket_id" in entry["required_inputs"]
        assert "expected_agent" in entry["required_inputs"]
        assert entry.get("default_mode") == "shadow"
        assert entry.get("category") == "workflow"


# ---------------------------------------------------------------------------
# Determinism (NFR-1)
# ---------------------------------------------------------------------------


class TestTodoValidationDeterminism:
    """Same bytes + agent → identical outcome (NFR-1)."""

    def test_validate_todos_deterministic(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Task", "in_progress")]),
        )
        first = validate_todos(TICKET_ID, SPEC_AGENT)
        second = validate_todos(TICKET_ID, SPEC_AGENT)
        stable_keys = ("status", "gate", "ticket_id", "message", "incomplete_tasks", "violations")
        assert {k: first[k] for k in stable_keys} == {k: second[k] for k in stable_keys}

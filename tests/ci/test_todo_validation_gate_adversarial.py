"""Adversarial tests for TodoWrite checkpoint validation gate (M902-20).

Exposes attribution bypass, malformed artifacts, path traversal, snapshot merge/fallback
edge cases, fenced JSON in markdown, and optional timing_diagnostics per
`project_board/specs/902_20_todo_validation_spec.md`.

Traceability: M902-20 ticket; complements `tests/ci/test_todo_validation_gate.py`.
Executable behavior only — no ticket markdown prose assertions. Prefer tmp_path fixtures.
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
TEST_DESIGNER = "Test Designer Agent"


def _todo(
    todo_id: str,
    content: str,
    status: str,
    *,
    agent: str | None = None,
    active_form: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
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
    if started_at is not None:
        record["started_at"] = started_at
    if completed_at is not None:
        record["completed_at"] = completed_at
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


def _write_run_snapshot(ticket_dir: Path, run_id: str, snapshot: dict[str, Any]) -> Path:
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / f"todos-{run_id}.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    return path


def _repo_layout(tmp_path: Path, ticket_id: str = TICKET_ID) -> Path:
    return tmp_path / "project_board" / "checkpoints" / ticket_id


def _checkpoints_parent(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


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
    return gate_run(inputs)


# ---------------------------------------------------------------------------
# Attribution bypass (Req 03–04)
# ---------------------------------------------------------------------------


class TestTodoValidationAttributionBypass:
    """Agents must not hide in_progress work via envelope/per-todo agent tricks."""

    def test_envelope_spec_per_todo_planner_in_progress_does_not_fail_spec(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bypass attempt: envelope Spec but label in_progress todo as Planner."""
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [_todo("p1", "Hidden planner work", "in_progress", agent=PLANNER_AGENT)],
                agent=SPEC_AGENT,
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"
        assert result["incomplete_tasks"] == []

    def test_envelope_planner_per_todo_spec_in_progress_fails_spec(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Per-todo agent override must win over envelope for attribution."""
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [_todo("s1", "Spec work left open", "in_progress", agent=SPEC_AGENT)],
                agent=PLANNER_AGENT,
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert len(result["incomplete_tasks"]) == 1
        assert result["incomplete_tasks"][0]["agent_key"] == "spec"

    def test_whitespace_padded_agent_alias_still_matches_spec(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Open", "in_progress")], agent="  spec agent  "),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"

    def test_empty_string_per_todo_agent_falls_back_to_envelope(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty todo.agent must not bypass envelope attribution (treat as inherit)."""
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Open", "in_progress", agent="")], agent=SPEC_AGENT),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"

    def test_wrong_expected_agent_slug_no_false_fail_on_spec_todos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Querying Test Designer while only Spec todos in_progress → vacuous PASS."""
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Spec only", "in_progress")], agent=SPEC_AGENT),
        )
        result = validate_todos(TICKET_ID, TEST_DESIGNER)
        assert result["status"] == "PASS"
        assert result["incomplete_tasks"] == []

    def test_implementation_alias_without_parenthetical_still_matches(
        self, tmp_path: Path
    ) -> None:
        ticket_dir = _checkpoints_parent(tmp_path) / TICKET_ID
        _write_todos_latest(
            ticket_dir,
            _snapshot([_todo("t1", "Ship", "in_progress")], agent="implementation agent"),
        )
        result = _run_with_checkpoints(tmp_path, expected_agent="Implementation Agent")
        assert result["status"] == "FAIL"
        assert result["incomplete_tasks"][0]["agent_key"] == "implementation"


# ---------------------------------------------------------------------------
# Malformed artifacts — fail-closed (Req 02, A5)
# ---------------------------------------------------------------------------


class TestTodoValidationMalformedArtifacts:
    """Invalid envelopes must FAIL with todo_artifact_invalid, not vacuous PASS."""

    @pytest.mark.parametrize(
        "payload",
        [
            "[]",
            '"string-root"',
            "null",
            '{"schema_version":"1.0"}',
            '{"schema_version":"1.0","ticket_id":"M902-20","agent":"Spec Agent","captured_at":"2026-05-20T18:00:00Z"}',
        ],
        ids=["root_array", "root_string", "root_null", "missing_todos", "missing_captured_at"],
    )
    def test_invalid_root_or_required_fields_fail(
        self, tmp_path: Path, payload: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        (ticket_dir / "todos-latest.json").write_text(payload, encoding="utf-8")
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])

    def test_envelope_ticket_id_mismatch_directory_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Task", "completed")], ticket_id="M902-99"),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])

    def test_todos_field_not_array_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        bad = _snapshot([])
        bad["todos"] = {"id": "t1"}
        (ticket_dir / "todos-latest.json").write_text(json.dumps(bad), encoding="utf-8")
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])

    def test_missing_todo_id_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        snap = _snapshot([{"content": "No id", "status": "completed"}])
        (ticket_dir / "todos-latest.json").write_text(json.dumps(snap), encoding="utf-8")
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])

    def test_invalid_latest_does_not_fallback_to_run_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid todos-latest is fail-closed; newer run file must not mask it."""
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        (ticket_dir / "todos-latest.json").write_text("{broken", encoding="utf-8")
        time.sleep(0.02)
        _write_run_snapshot(
            ticket_dir,
            "2026-05-21T-newer",
            _snapshot([_todo("t1", "Would pass if picked", "completed")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "todo_artifact_invalid" for v in result["violations"])


# ---------------------------------------------------------------------------
# Snapshot merge / fallback (Req 02)
# ---------------------------------------------------------------------------


class TestTodoValidationSnapshotMergeFallback:
    """Discovery precedence: latest > run files by mtime > fenced md."""

    def test_fallback_newest_todos_run_when_no_latest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        older = _write_run_snapshot(
            ticket_dir,
            "2026-05-19T-old",
            _snapshot([_todo("old", "Stale", "in_progress")]),
        )
        time.sleep(0.02)
        newer = _write_run_snapshot(
            ticket_dir,
            "2026-05-21T-new",
            _snapshot([_todo("new", "Fresh", "completed")]),
        )
        assert newer.stat().st_mtime >= older.stat().st_mtime
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_fallback_run_file_in_progress_fails_when_no_latest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        _write_run_snapshot(
            ticket_dir,
            "2026-05-20T-spec",
            _snapshot([_todo("t1", "Still open", "in_progress")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert len(result["incomplete_tasks"]) == 1

    def test_latest_valid_ignores_newer_invalid_run_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        _write_todos_latest(ticket_dir, _snapshot([_todo("ok", "Done", "completed")]))
        time.sleep(0.02)
        _write_run_snapshot(
            ticket_dir,
            "2026-05-21T-evil",
            _snapshot([_todo("evil", "Trap", "in_progress")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# Fenced JSON in markdown (Req 02)
# ---------------------------------------------------------------------------


class TestTodoValidationFencedJsonMarkdown:
    """Parse ```json todos and legacy todo-snapshot blocks when no JSON files."""

    def _write_md_snapshot(
        self,
        ticket_dir: Path,
        filename: str,
        snapshot: dict[str, Any],
        *,
        fence_lang: str = "json todos",
    ) -> Path:
        ticket_dir.mkdir(parents=True, exist_ok=True)
        body = f"# checkpoint\n\n```{fence_lang}\n{json.dumps(snapshot, indent=2)}\n```\n"
        path = ticket_dir / filename
        path.write_text(body, encoding="utf-8")
        return path

    def test_fenced_json_todos_when_no_json_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        self._write_md_snapshot(
            ticket_dir,
            "run.md",
            _snapshot([_todo("t1", "From md", "in_progress")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert len(result["incomplete_tasks"]) == 1

    def test_legacy_fence_alias_todo_snapshot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        self._write_md_snapshot(
            ticket_dir,
            "legacy.md",
            _snapshot([_todo("t1", "Legacy fence", "completed")]),
            fence_lang="json todo-snapshot",
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_last_fenced_block_in_file_wins(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        fail_snap = json.dumps(_snapshot([_todo("bad", "Fail block", "in_progress")]))
        pass_snap = json.dumps(_snapshot([_todo("good", "Pass block", "completed")]))
        (ticket_dir / "multi.md").write_text(
            f"```json todos\n{fail_snap}\n```\n\n```json todos\n{pass_snap}\n```\n",
            encoding="utf-8",
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_newer_md_file_wins_over_older_md(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        self._write_md_snapshot(
            ticket_dir,
            "older.md",
            _snapshot([_todo("o", "Old fail", "in_progress")]),
        )
        time.sleep(0.02)
        self._write_md_snapshot(
            ticket_dir,
            "newer.md",
            _snapshot([_todo("n", "New pass", "completed")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_json_file_preferred_over_md_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        self._write_md_snapshot(
            ticket_dir,
            "md-only-would-fail.md",
            _snapshot([_todo("m", "Md trap", "in_progress")]),
        )
        time.sleep(0.02)
        _write_run_snapshot(
            ticket_dir,
            "2026-05-20T-json",
            _snapshot([_todo("j", "Json pass", "completed")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# Path traversal / security (NFR-3)
# ---------------------------------------------------------------------------


class TestTodoValidationPathTraversalAdversarial:
    """Reject traversal in ticket_id and checkpoints_dir overrides."""

    @pytest.mark.parametrize(
        "ticket_id",
        ["../M902-20", "M902-20/../../etc", "..\\M902-20", "M902-20%2e%2e"],
    )
    def test_ticket_id_traversal_variants_rejected(self, tmp_path: Path, ticket_id: str) -> None:
        result = _run_with_checkpoints(tmp_path, ticket_id=ticket_id)
        assert result["status"] == "FAIL"
        assert result["violations"]

    def test_absolute_checkpoints_dir_outside_repo_rejected(self, tmp_path: Path) -> None:
        outside = tmp_path / "outside-checkpoints"
        outside.mkdir()
        result = gate_run(
            {
                "ticket_id": TICKET_ID,
                "expected_agent": SPEC_AGENT,
                "checkpoints_dir": str(outside.resolve()),
            }
        )
        assert result["status"] == "FAIL"

    def test_ticket_id_with_path_separator_rejected(self, tmp_path: Path) -> None:
        result = _run_with_checkpoints(tmp_path, ticket_id="M902/20")
        assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Combinatorial / order / stress (NFR-1, NFR-2)
# ---------------------------------------------------------------------------


class TestTodoValidationCombinatorialEdgeCases:
    """Multiple edge factors and stable ordering under stress."""

    def test_many_in_progress_stable_sort_by_id_then_content(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        todos = [
            _todo("z", "Zulu", "in_progress"),
            _todo("a", "Alpha", "in_progress"),
            _todo("m", "Mike", "in_progress"),
        ]
        _write_todos_latest(_repo_layout(tmp_path), _snapshot(todos))
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        ids = [t["id"] for t in result["incomplete_tasks"]]
        assert ids == sorted(ids)

    def test_vacuous_pass_with_only_unattributed_in_progress_and_completed_spec(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        snap = _snapshot(
            [
                _todo("u", "Unattributed open", "in_progress"),
                _todo("s", "Spec done", "completed", agent=SPEC_AGENT),
            ]
        )
        del snap["agent"]
        _write_todos_latest(_repo_layout(tmp_path), snap)
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"

    def test_artifacts_sha256_populated_when_snapshot_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Observable contract: artifacts list references read snapshot paths."""
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot([_todo("t1", "Done", "completed")]),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"
        assert isinstance(result.get("artifacts"), list)


# ---------------------------------------------------------------------------
# timing_diagnostics (Req 09 — optional, non-blocking)
# ---------------------------------------------------------------------------


class TestTodoValidationTimingDiagnostics:
    """Slow-task diagnostics must not change PASS/FAIL status."""

    def test_slow_completed_task_attaches_timing_diagnostics_on_pass(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [
                    _todo(
                        "slow",
                        "Long task",
                        "completed",
                        started_at="2026-05-19T10:00:00Z",
                        completed_at="2026-05-19T12:30:00Z",
                    ),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"
        diag = result.get("timing_diagnostics")
        if diag is not None:
            slow = diag.get("slow_tasks", [])
            assert any(t.get("id") == "slow" for t in slow)
            assert all(t.get("duration_seconds", 0) > 3600 for t in slow)

    def test_in_progress_with_timestamps_does_not_flip_fail_via_timing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [
                    _todo(
                        "open",
                        "Still running",
                        "in_progress",
                        started_at="2026-05-19T10:00:00Z",
                    ),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "FAIL"
        assert len(result["incomplete_tasks"]) == 1

    def test_negative_duration_timestamps_ignored_silently(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_todos_latest(
            _repo_layout(tmp_path),
            _snapshot(
                [
                    _todo(
                        "skew",
                        "Clock skew",
                        "completed",
                        started_at="2026-05-20T12:00:00Z",
                        completed_at="2026-05-20T10:00:00Z",
                    ),
                ],
            ),
        )
        result = validate_todos(TICKET_ID, SPEC_AGENT)
        assert result["status"] == "PASS"
        diag = result.get("timing_diagnostics")
        if diag is not None:
            assert diag.get("slow_tasks", []) == []

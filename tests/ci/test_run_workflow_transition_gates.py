"""Behavioral tests for mandatory workflow transition gate runner (M902-20 + M902-23)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(CI_SCRIPTS))

from run_workflow_transition_gates import run_transition_gates  # noqa: E402

TICKET_ID = "M902-23"
PLANNER_AGENT = "Planner Agent"


def _repo_layout(tmp_path: Path) -> Path:
    return tmp_path / "project_board" / "checkpoints" / TICKET_ID


def _write_todos_latest(ticket_dir: Path) -> None:
    ticket_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "schema_version": "1.0",
        "ticket_id": TICKET_ID,
        "agent": PLANNER_AGENT,
        "captured_at": "2026-05-20T18:00:00Z",
        "todos": [
            {
                "id": "p1",
                "content": "Plan ticket",
                "status": "completed",
                "agent": PLANNER_AGENT,
            }
        ],
    }
    (ticket_dir / "todos-latest.json").write_text(json.dumps(snapshot), encoding="utf-8")


def _write_execution_plan(tmp_path: Path) -> str:
    rel = f"project_board/execution_plans/{TICKET_ID}_transition_gate.md"
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Execution Plan\n\nRevision: 1\n\nEstimated Effort: 3 runs\n\n"
        "## Dependency Matrix\n\n| Dep | State |\n|-----|-------|\n| none | ok |\n",
        encoding="utf-8",
    )
    return rel


def _write_planner_handoff(ticket_dir: Path, tmp_path: Path) -> None:
    plan_path = _write_execution_plan(tmp_path)
    yaml_text = f"""handoff:
  schema_version: "1.0"
  ticket_id: {TICKET_ID}
  from_agent: planner
  to_agent: spec
  validated_at: "2026-05-20T18:00:00Z"
  required_items_met: 3
  total_required_items: 3
  checklist:
    - item_key: planner_ticket_decomposed
      item: "Ticket decomposed into execution plan tasks"
      required: true
      status: complete
      evidence: "{plan_path}"
      evidence_type: path
    - item_key: planner_dependencies_clear
      item: "Dependencies clear (acyclic or documented WARN)"
      required: true
      status: complete
      evidence: "{plan_path} section Dependency Matrix"
    - item_key: planner_timeline_estimated
      item: "Timeline estimated"
      required: true
      status: complete
      evidence: "{plan_path}"
      evidence_type: path
"""
    ticket_dir.mkdir(parents=True, exist_ok=True)
    (ticket_dir / "handoff-latest.yaml").write_text(yaml_text, encoding="utf-8")


class TestRunWorkflowTransitionGates:
    def test_unknown_transition_returns_exit_2(self, tmp_path: Path) -> None:
        code, summary = run_transition_gates(
            TICKET_ID,
            "not_a_transition",
            checkpoints_dir=str(tmp_path / "project_board" / "checkpoints"),
        )
        assert code == 2
        assert "error" in summary

    def test_planner_to_spec_passes_with_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        _write_todos_latest(ticket_dir)
        _write_planner_handoff(ticket_dir, tmp_path)
        code, summary = run_transition_gates(
            TICKET_ID,
            "planner_to_spec",
            checkpoints_dir="project_board/checkpoints",
        )
        assert code == 0
        assert summary["todo_validation_check"]["status"] == "PASS"
        assert summary["handoff_validation_check"]["status"] == "PASS"
        assert summary["todo_validation_check"].get("mode") == "blocking"
        assert summary["handoff_validation_check"].get("mode") == "blocking"

    def test_planner_to_spec_fails_when_artifacts_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _repo_layout(tmp_path).mkdir(parents=True, exist_ok=True)
        code, summary = run_transition_gates(
            TICKET_ID,
            "planner_to_spec",
            checkpoints_dir="project_board/checkpoints",
        )
        assert code == 1
        statuses = {
            summary["todo_validation_check"]["status"],
            summary["handoff_validation_check"]["status"],
        }
        assert "FAIL" in statuses


def test_cli_main_unknown_transition_exits_2(tmp_path: Path) -> None:
    import subprocess

    script = CI_SCRIPTS / "run_workflow_transition_gates.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--ticket-id",
            TICKET_ID,
            "--transition",
            "bogus_transition",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 2

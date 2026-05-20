"""Behavioral tests for atomic handoff YAML validation gate (M902-23).

Validates `validate_handoff_checklist` and `run()` in `ci/scripts/gates/handoff_validation_check.py`
against `project_board/specs/902_23_atomic_handoff_spec.md` (Req 01–04, 18; scenarios H1–H9, V1–V3).

Tests use `tmp_path` fixtures with `handoff-latest.yaml` under checkpoint ticket dirs.
No assertions on ticket markdown prose.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(CI_SCRIPTS))

from gates.handoff_validation_check import run as gate_run
from gates.handoff_validation_check import validate_handoff_checklist

GATE_NAME = "handoff_validation_check"
TICKET_ID = "M902-23"
HANDOFF_SCHEMA_VERSION = "1.0"
VALIDATED_AT = "2026-05-20T18:00:00Z"

# Frozen catalog labels (Req 05–11) — must match spec verbatim.
LABELS: dict[str, str] = {
    "planner_ticket_decomposed": "Ticket decomposed into execution plan tasks",
    "planner_dependencies_clear": "Dependencies clear (acyclic or documented WARN)",
    "planner_timeline_estimated": "Timeline estimated",
    "spec_acceptance_criteria": "Acceptance criteria defined",
    "spec_test_strategy": "Test strategy documented",
    "spec_edge_cases": "Edge cases listed",
    "test_suite_complete": "Test suite complete per spec test plan",
    "test_coverage_threshold": "Coverage threshold met (>80% proxy)",
    "test_all_runnable": "All tests runnable",
    "breaker_gaps_documented": "All discovered gaps documented",
    "breaker_impl_notes": "Implementation notes created",
    "impl_ac_complete": "All acceptance criteria implemented",
    "impl_tests_passing": "All tests passing",
    "impl_linter_clean": "No linter violations",
    "impl_checkpoint_logged": "Checkpoint logged",
    "impl_docstrings": "Docstrings/comments on complex logic",
    "review_feedback_incorporated": "Feedback incorporated",
    "review_code_reviewed": "Code reviewed",
    "review_merge_ready": "Merge-ready",
    "learning_insights_documented": "Insights documented",
    "learning_rationale_recorded": "Decision rationale recorded",
    "learning_checklist_validated": "Handoff checklist validated",
}


# ---------------------------------------------------------------------------
# Fixture helpers (Requirement 02 HandoffDocument contract)
# ---------------------------------------------------------------------------


def _checklist_item(
    item_key: str,
    *,
    status: str = "complete",
    required: bool = True,
    evidence: str = "attestation: satisfied",
    evidence_type: str | None = None,
    defer_reason: str | None = None,
    block_reason: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "item_key": item_key,
        "item": LABELS[item_key],
        "required": required,
        "status": status,
        "evidence": evidence,
    }
    if evidence_type is not None:
        item["evidence_type"] = evidence_type
    if defer_reason is not None:
        item["defer_reason"] = defer_reason
    if block_reason is not None:
        item["block_reason"] = block_reason
    return item


def _handoff_root(
    checklist: list[dict[str, Any]],
    *,
    from_agent: str,
    to_agent: str,
    ticket_id: str = TICKET_ID,
    required_items_met: int | None = None,
    total_required_items: int | None = None,
) -> dict[str, Any]:
    required_count = sum(1 for i in checklist if i.get("required"))
    met = sum(
        1
        for i in checklist
        if i.get("required") and i.get("status") == "complete"
    )
    return {
        "handoff": {
            "schema_version": HANDOFF_SCHEMA_VERSION,
            "ticket_id": ticket_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "validated_at": VALIDATED_AT,
            "checklist": checklist,
            "required_items_met": required_items_met if required_items_met is not None else met,
            "total_required_items": (
                total_required_items if total_required_items is not None else required_count
            ),
        }
    }


def _yaml_dump(handoff: dict[str, Any]) -> str:
    """Minimal YAML serializer for fixtures (no PyYAML dependency in tests)."""

    def _quote(s: str) -> str:
        if any(c in s for c in ':"\\#\n'):
            escaped = s.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return s

    lines: list[str] = ["handoff:"]
    root = handoff["handoff"]
    for key in (
        "schema_version",
        "ticket_id",
        "from_agent",
        "to_agent",
        "validated_at",
        "required_items_met",
        "total_required_items",
    ):
        val = root[key]
        if isinstance(val, str):
            lines.append(f"  {key}: {_quote(val)}")
        else:
            lines.append(f"  {key}: {val}")
    lines.append("  checklist:")
    for entry in root["checklist"]:
        lines.append(f"    - item_key: {entry['item_key']}")
        lines.append(f"      item: {_quote(str(entry['item']))}")
        lines.append(f"      required: {str(entry['required']).lower()}")
        lines.append(f"      status: {entry['status']}")
        lines.append(f"      evidence: {_quote(str(entry.get('evidence', '')))}")
        if entry.get("evidence_type"):
            lines.append(f"      evidence_type: {entry['evidence_type']}")
        if entry.get("defer_reason"):
            lines.append(f"      defer_reason: {_quote(str(entry['defer_reason']))}")
        if entry.get("block_reason"):
            lines.append(f"      block_reason: {_quote(str(entry['block_reason']))}")
    return "\n".join(lines) + "\n"


def _write_handoff_latest(ticket_dir: Path, handoff: dict[str, Any]) -> Path:
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / "handoff-latest.yaml"
    path.write_text(_yaml_dump(handoff), encoding="utf-8")
    return path


def _repo_layout(tmp_path: Path, ticket_id: str = TICKET_ID) -> Path:
    return tmp_path / "project_board" / "checkpoints" / ticket_id


def _checkpoints_parent(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


def _gap_item_keys(result: dict[str, Any]) -> set[str]:
    gaps = result.get("gaps") or result.get("missing_items") or []
    keys: set[str] = set()
    for entry in gaps:
        if isinstance(entry, dict) and entry.get("item_key"):
            keys.add(str(entry["item_key"]))
    return keys


def _assert_gate_envelope(result: dict[str, Any]) -> None:
    assert result["version"] == "0.1.0"
    assert result["gate"] == GATE_NAME
    assert result["ticket_id"] == TICKET_ID
    assert result["status"] in ("PASS", "FAIL")
    assert isinstance(result["message"], str)
    assert isinstance(result["violations"], list)
    assert isinstance(result["remediation_hints"], list)
    assert "gaps" in result or "missing_items" in result
    gaps = result.get("gaps") or result.get("missing_items")
    assert isinstance(gaps, list)
    assert isinstance(result["duration_ms"], int)
    assert "timestamp" in result
    assert "from_agent" in result
    assert "to_agent" in result


def _run_with_checkpoints(
    tmp_path: Path,
    *,
    from_agent: str,
    to_agent: str,
    ticket_id: str = TICKET_ID,
    extra_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        _checkpoints_parent(tmp_path).mkdir(parents=True, exist_ok=True)
        inputs: dict[str, Any] = {
            "ticket_id": ticket_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "checkpoints_dir": "checkpoints",
        }
        if extra_inputs:
            inputs.update(extra_inputs)
        result = gate_run(inputs)
    finally:
        os.chdir(old_cwd)
    _assert_gate_envelope(result)
    return result


def _write_execution_plan(tmp_path: Path, ticket_id: str = TICKET_ID) -> str:
    rel = f"project_board/execution_plans/{ticket_id}_atomic_handoff.md"
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Execution Plan\n\nRevision: 1\n\nEstimated Effort: 9 agent runs\n\n"
        "## Dependency Matrix\n\n| Dep | State |\n|-----|-------|\n| M902-01 | done |\n",
        encoding="utf-8",
    )
    return rel


def _write_spec_file(tmp_path: Path, ticket_id: str = TICKET_ID) -> str:
    rel = f"project_board/specs/{ticket_id}_handoff_fixture_spec.md"
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Fixture Spec\n\n### 2. Acceptance Criteria\n\nAC listed.\n\n"
        "## Test strategy\n\npytest modules.\n\n## Risk & Ambiguity\n\nEdge cases.\n",
        encoding="utf-8",
    )
    return rel


def _planner_spec_checklist(tmp_path: Path) -> list[dict[str, Any]]:
    plan_path = _write_execution_plan(tmp_path)
    return [
        _checklist_item(
            "planner_ticket_decomposed",
            evidence=plan_path,
            evidence_type="path",
        ),
        _checklist_item(
            "planner_dependencies_clear",
            evidence=f"{plan_path} section Dependency Matrix",
        ),
        _checklist_item(
            "planner_timeline_estimated",
            evidence=plan_path,
            evidence_type="path",
        ),
    ]


def _spec_test_designer_checklist(
    tmp_path: Path,
    *,
    edge_status: str = "complete",
) -> list[dict[str, Any]]:
    spec_path = _write_spec_file(tmp_path)
    return [
        _checklist_item(
            "spec_acceptance_criteria",
            evidence=spec_path,
            evidence_type="path",
        ),
        _checklist_item(
            "spec_test_strategy",
            evidence=f"{spec_path} section Test strategy",
        ),
        _checklist_item(
            "spec_edge_cases",
            status=edge_status,
            evidence="" if edge_status != "complete" else f"{spec_path} Risk & Ambiguity",
        ),
    ]


def _test_designer_test_breaker_checklist(tmp_path: Path) -> list[dict[str, Any]]:
    test_rel = "tests/ci/test_handoff_validation_gate.py"
    test_path = tmp_path / test_rel
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text("# fixture\n", encoding="utf-8")
    return [
        _checklist_item(
            "test_suite_complete",
            evidence=test_rel,
            evidence_type="path",
        ),
        _checklist_item(
            "test_coverage_threshold",
            evidence="coverage: 85",
        ),
        _checklist_item(
            "test_all_runnable",
            evidence="pytest collection PASS 2026-05-20T18:00:00Z",
        ),
    ]


def _test_breaker_implementation_checklist(tmp_path: Path) -> list[dict[str, Any]]:
    gap_rel = f"project_board/checkpoints/{TICKET_ID}/2026-05-20T-test-break-run.md"
    gap_path = tmp_path / gap_rel
    gap_path.parent.mkdir(parents=True, exist_ok=True)
    gap_path.write_text("# gaps\n", encoding="utf-8")
    return [
        _checklist_item(
            "breaker_gaps_documented",
            evidence=gap_rel,
            evidence_type="path",
        ),
        _checklist_item(
            "breaker_impl_notes",
            evidence="execution plan task notes for implementation",
        ),
    ]


def _implementation_static_qa_checklist(
    tmp_path: Path,
    *,
    tests_status: str = "complete",
    include_optional_deferred: bool = False,
) -> list[dict[str, Any]]:
    gate_rel = f"project_board/checkpoints/{TICKET_ID}/gate-results/static_analysis_2026-05-20.json"
    gate_path = tmp_path / gate_rel
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text("{}", encoding="utf-8")
    cp_rel = f"project_board/checkpoints/{TICKET_ID}/2026-05-20T-impl-run.md"
    cp_path = tmp_path / cp_rel
    cp_path.write_text("# impl checkpoint\n", encoding="utf-8")
    items = [
        _checklist_item("impl_ac_complete", evidence="AC-01.1, AC-09.3"),
        _checklist_item(
            "impl_tests_passing",
            status=tests_status,
            evidence="timeout 300 ci/scripts/run_tests.sh PASS 2026-05-20T14:30:00Z",
            block_reason="tests still failing" if tests_status == "blocked" else None,
        ),
        _checklist_item(
            "impl_linter_clean",
            evidence=gate_rel,
            evidence_type="path",
        ),
        _checklist_item(
            "impl_checkpoint_logged",
            evidence=cp_rel,
            evidence_type="path",
        ),
    ]
    if include_optional_deferred:
        items.append(
            _checklist_item(
                "impl_docstrings",
                required=False,
                status="deferred",
                evidence="",
                defer_reason="Defer doc pass to M903",
            )
        )
    return items


# ---------------------------------------------------------------------------
# H1–H9 core scenarios (Requirement 18)
# ---------------------------------------------------------------------------


class TestHandoffValidationH1AllRequiredComplete:
    """H1: All required complete — planner → spec → PASS."""

    def test_validate_handoff_planner_spec_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _planner_spec_checklist(tmp_path),
                from_agent="planner",
                to_agent="spec",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "planner", "spec")
        _assert_gate_envelope(result)
        assert result["status"] == "PASS"
        assert result["from_agent"] == "planner"
        assert result["to_agent"] == "spec"
        assert _gap_item_keys(result) == set()
        assert result["violations"] == []


class TestHandoffValidationH2OneRequiredIncomplete:
    """H2: One required incomplete — spec → test_designer → FAIL handoff_item_missing."""

    def test_validate_handoff_spec_edge_cases_incomplete_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "Spec Agent", "Test Designer Agent")
        assert result["status"] == "FAIL"
        assert "spec_edge_cases" in _gap_item_keys(result)
        assert any(v.get("rule") == "handoff_item_missing" for v in result["violations"])
        assert len(result["remediation_hints"]) >= 3

    def test_run_spec_incomplete_fails(self, tmp_path: Path) -> None:
        _write_spec_file(tmp_path)
        ticket_dir = _checkpoints_parent(tmp_path) / TICKET_ID
        _write_handoff_latest(
            ticket_dir,
            _handoff_root(
                _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = _run_with_checkpoints(
            tmp_path,
            from_agent="spec",
            to_agent="test_designer",
        )
        assert result["status"] == "FAIL"


class TestHandoffValidationH3RequiredBlocked:
    """H3: Required blocked — implementation → static_qa → FAIL handoff_blocked."""

    def test_validate_handoff_impl_tests_blocked_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _implementation_static_qa_checklist(tmp_path, tests_status="blocked"),
                from_agent="implementation",
                to_agent="static_qa",
            ),
        )
        result = validate_handoff_checklist(
            TICKET_ID, "implementation", "Code Reviewer"
        )
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_blocked" for v in result["violations"])
        assert "impl_tests_passing" in _gap_item_keys(result) or any(
            v.get("rule") == "handoff_blocked" for v in result["violations"]
        )


class TestHandoffValidationH4OptionalDeferred:
    """H4: Optional deferred with reason — implementation → static_qa → PASS."""

    def test_validate_handoff_optional_docstrings_deferred_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _implementation_static_qa_checklist(
                    tmp_path, include_optional_deferred=True
                ),
                from_agent="implementation",
                to_agent="static_qa",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "implementation", "static_qa")
        assert result["status"] == "PASS"
        assert result["violations"] == []


class TestHandoffValidationH5PairMismatch:
    """H5: Pair mismatch in file — FAIL handoff_pair_mismatch."""

    def test_validate_handoff_wrong_to_agent_in_file_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_breaker",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_pair_mismatch" for v in result["violations"])


class TestHandoffValidationH6MissingArtifact:
    """H6: Missing artifact — FAIL handoff_artifact_missing (fail-closed)."""

    def test_validate_handoff_missing_artifact_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (_repo_layout(tmp_path)).mkdir(parents=True, exist_ok=True)
        result = validate_handoff_checklist(TICKET_ID, "planner", "spec")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_missing" for v in result["violations"])

    def test_handoff_optional_vacuous_pass_when_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (_repo_layout(tmp_path)).mkdir(parents=True, exist_ok=True)
        result = validate_handoff_checklist(
            TICKET_ID, "planner", "spec", handoff_optional=True
        )
        assert result["status"] == "PASS"


class TestHandoffValidationH7MalformedYaml:
    """H7: Malformed YAML — FAIL handoff_artifact_invalid."""

    def test_invalid_yaml_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        (ticket_dir / "handoff-latest.yaml").write_text("handoff: [not: valid: yaml", encoding="utf-8")
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_invalid" for v in result["violations"])


class TestHandoffValidationH8CounterMismatch:
    """H8: Inflated required_items_met — test_breaker → implementation → FAIL."""

    def test_validate_handoff_counter_mismatch_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        checklist = _test_breaker_implementation_checklist(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                checklist,
                from_agent="test_breaker",
                to_agent="implementation",
                required_items_met=99,
                total_required_items=2,
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "test_breaker", "implementation")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_counter_mismatch" for v in result["violations"])


class TestHandoffValidationH9RunAndGateRunnerSmoke:
    """H9: run() + gate_runner smoke — spec → test_designer."""

    def test_run_spec_pair_passes(self, tmp_path: Path) -> None:
        ticket_dir = _checkpoints_parent(tmp_path) / TICKET_ID
        _write_spec_file(tmp_path)
        _write_handoff_latest(
            ticket_dir,
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = _run_with_checkpoints(
            tmp_path,
            from_agent="Spec Agent",
            to_agent="Test Designer Agent",
            extra_inputs={"mode": "shadow"},
        )
        assert result["status"] == "PASS"
        assert result.get("mode") == "shadow"

    def test_gate_runner_handoff_validation_smoke(
        self, gate_runner: Path, tmp_path: Path
    ) -> None:
        registry_path = CI_SCRIPTS / "gate_registry.json"
        if not registry_path.exists():
            pytest.skip("gate_registry.json not found")
        entries = json.loads(registry_path.read_text(encoding="utf-8"))
        if not any(e.get("name") == GATE_NAME for e in entries):
            pytest.skip(f"{GATE_NAME} not registered yet")

        ticket_dir = tmp_path / "checkpoints" / TICKET_ID
        _write_spec_file(tmp_path)
        _write_handoff_latest(
            ticket_dir,
            _handoff_root(
                _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        out_dir = tmp_path / "gate-results"
        out_dir.mkdir()
        proc = subprocess.run(
            [
                sys.executable,
                str(gate_runner),
                GATE_NAME,
                "--mode",
                "shadow",
                "--ticket-id",
                TICKET_ID,
                "--output-dir",
                str(out_dir),
                "--upstream-agent",
                "Spec Agent",
                "--downstream-agent",
                "Test Designer Agent",
                "--input",
                json.dumps(
                    {
                        "ticket_id": TICKET_ID,
                        "from_agent": "spec",
                        "to_agent": "test_designer",
                        "checkpoints_dir": "checkpoints",
                    }
                ),
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert proc.returncode == 0, proc.stderr
        result_files = list(out_dir.glob(f"{GATE_NAME}_*.json"))
        assert result_files, f"expected gate result under {out_dir}"
        payload = json.loads(result_files[0].read_text(encoding="utf-8"))
        assert payload["status"] == "FAIL"
        assert payload["gate"] == GATE_NAME


# ---------------------------------------------------------------------------
# V1–V3 distinct pair vectors (Requirement 18)
# ---------------------------------------------------------------------------


class TestHandoffValidationVectorV1SpecToTestDesigner:
    """V1: spec → test_designer — pair-specific key spec_edge_cases."""

    def test_pass_includes_spec_edge_cases_complete(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "PASS"

    def test_fail_gap_lists_spec_edge_cases(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert "spec_edge_cases" in _gap_item_keys(result)


class TestHandoffValidationVectorV2TestBreakerToImplementation:
    """V2: test_breaker → implementation — pair-specific breaker_gaps_documented."""

    def test_pass_requires_breaker_gaps_documented(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _test_breaker_implementation_checklist(tmp_path),
                from_agent="test_breaker",
                to_agent="implementation",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "test_breaker", "implementation")
        assert result["status"] == "PASS"

    def test_fail_when_breaker_gaps_missing_from_checklist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        only_notes = [
            _checklist_item(
                "breaker_impl_notes",
                evidence="notes only",
            ),
        ]
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                only_notes,
                from_agent="test_breaker",
                to_agent="implementation",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "test_breaker", "implementation")
        assert result["status"] == "FAIL"
        assert "breaker_gaps_documented" in _gap_item_keys(result)


class TestHandoffValidationVectorV3ImplementationToStaticQa:
    """V3: implementation → static_qa — pair-specific impl_linter_clean."""

    def test_pass_with_impl_linter_clean_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _implementation_static_qa_checklist(tmp_path),
                from_agent="implementation",
                to_agent="static_qa",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "implementation", "static_qa")
        assert result["status"] == "PASS"

    def test_fail_when_linter_path_missing_on_disk(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        items = _implementation_static_qa_checklist(tmp_path)
        for item in items:
            if item["item_key"] == "impl_linter_clean":
                item["evidence"] = "project_board/checkpoints/M902-23/gate-results/missing.json"
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                items,
                from_agent="implementation",
                to_agent="static_qa",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "implementation", "static_qa")
        assert result["status"] == "FAIL"
        assert "impl_linter_clean" in _gap_item_keys(result) or any(
            v.get("rule") in ("handoff_evidence_missing", "handoff_item_missing")
            for v in result["violations"]
        )


# ---------------------------------------------------------------------------
# Requirement 13 — run() contract
# ---------------------------------------------------------------------------


class TestHandoffValidationRunContract:
    """run() inputs, gate name, missing required fields (Req 13)."""

    def test_run_sets_gate_name(self, tmp_path: Path) -> None:
        ticket_dir = _checkpoints_parent(tmp_path) / TICKET_ID
        _write_handoff_latest(
            ticket_dir,
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        _write_spec_file(tmp_path)
        result = _run_with_checkpoints(
            tmp_path,
            from_agent="spec",
            to_agent="test_designer",
        )
        assert result["gate"] == GATE_NAME

    def test_run_missing_ticket_id_fails(self, tmp_path: Path) -> None:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = gate_run(
                {
                    "from_agent": "spec",
                    "to_agent": "test_designer",
                    "checkpoints_dir": "checkpoints",
                }
            )
        finally:
            os.chdir(old_cwd)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "missing_required_input" for v in result["violations"])

    def test_run_missing_from_agent_fails(self, tmp_path: Path) -> None:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = gate_run(
                {
                    "ticket_id": TICKET_ID,
                    "to_agent": "test_designer",
                    "checkpoints_dir": "checkpoints",
                }
            )
        finally:
            os.chdir(old_cwd)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "missing_required_input" for v in result["violations"])

    def test_fail_payload_has_gaps_and_violations(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        gaps = result.get("gaps") or result.get("missing_items") or []
        assert len(gaps) >= 1
        assert len(result["violations"]) >= 1


# ---------------------------------------------------------------------------
# Discovery, normalization, read-only (Req 02, 04, NFR)
# ---------------------------------------------------------------------------


class TestHandoffValidationDiscovery:
    """handoff-latest.yaml precedence and agent alias normalization."""

    def test_handoff_latest_preferred_over_older_run_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        stale = ticket_dir / "handoff-2026-05-19T-stale.yaml"
        stale.write_text(
            _yaml_dump(
                _handoff_root(
                    _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                    from_agent="spec",
                    to_agent="test_designer",
                )
            ),
            encoding="utf-8",
        )
        time.sleep(0.02)
        _write_handoff_latest(
            ticket_dir,
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        _write_spec_file(tmp_path)
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "PASS"

    def test_mixed_case_agent_labels_normalize(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_execution_plan(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _planner_spec_checklist(tmp_path),
                from_agent="planner",
                to_agent="spec",
            ),
        )
        result = validate_handoff_checklist(
            TICKET_ID, "Planner Agent", "Spec Agent"
        )
        assert result["status"] == "PASS"
        assert result["from_agent"] == "planner"
        assert result["to_agent"] == "spec"

    def test_checkpoint_files_not_mutated_on_fail(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        path = _write_handoff_latest(
            ticket_dir,
            _handoff_root(
                _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        before = path.read_bytes()
        validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert path.read_bytes() == before


class TestHandoffValidationPathSecurity:
    """Reject traversal in ticket_id and checkpoints_dir (NFR-3)."""

    def test_ticket_id_with_dotdot_rejected(self, tmp_path: Path) -> None:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = gate_run(
                {
                    "ticket_id": "../etc",
                    "from_agent": "spec",
                    "to_agent": "test_designer",
                    "checkpoints_dir": "checkpoints",
                }
            )
        finally:
            os.chdir(old_cwd)
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "path_traversal" for v in result["violations"])

    def test_checkpoints_dir_traversal_rejected(self, tmp_path: Path) -> None:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = gate_run(
                {
                    "ticket_id": TICKET_ID,
                    "from_agent": "spec",
                    "to_agent": "test_designer",
                    "checkpoints_dir": str(tmp_path / ".." / "secrets"),
                }
            )
        finally:
            os.chdir(old_cwd)
        assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Requirement 14 — registry contract (red until implementation registers gate)
# ---------------------------------------------------------------------------


class TestHandoffValidationRegistry:
    """Registry entry handoff_validation_check (AC-14.1)."""

    def test_gate_registry_contains_handoff_validation_check(self, gate_registry: Path) -> None:
        entries = json.loads(gate_registry.read_text(encoding="utf-8"))
        names = {e["name"] for e in entries}
        assert GATE_NAME in names
        entry = next(e for e in entries if e["name"] == GATE_NAME)
        assert entry["module"] == "handoff_validation_check"
        assert "ticket_id" in entry["required_inputs"]
        assert "from_agent" in entry["required_inputs"]
        assert "to_agent" in entry["required_inputs"]
        assert entry.get("default_mode") == "shadow"
        assert entry.get("category") == "workflow"


# ---------------------------------------------------------------------------
# Determinism (NFR-1)
# ---------------------------------------------------------------------------


class TestHandoffValidationDeterminism:
    """Same bytes + pair → identical outcome (NFR-1)."""

    def test_validate_handoff_deterministic(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path, edge_status="incomplete"),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        first = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        second = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        stable_keys = (
            "status",
            "gate",
            "ticket_id",
            "message",
            "violations",
            "from_agent",
            "to_agent",
        )
        assert {k: first[k] for k in stable_keys} == {k: second[k] for k in stable_keys}
        gaps_a = first.get("gaps") or first.get("missing_items")
        gaps_b = second.get("gaps") or second.get("missing_items")
        assert gaps_a == gaps_b

"""Adversarial tests for atomic handoff YAML validation gate (M902-23).

Exposes bypass attempts, symlink escape, concurrent/partial writes, empty evidence,
wrong schema_version, duplicate keys, fenced-YAML vs file precedence, path traversal,
and threshold/counter tricks per `project_board/specs/902_23_atomic_handoff_spec.md`.

Traceability: M902-23 ticket; complements `tests/ci/test_handoff_validation_gate.py`.
Executable behavior only — no ticket markdown prose assertions. Prefer tmp_path fixtures.
"""

from __future__ import annotations

import os
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
}


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
    schema_version: str = HANDOFF_SCHEMA_VERSION,
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
            "schema_version": schema_version,
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
    def _quote(s: str) -> str:
        if not s.strip() or any(c in s for c in ':"\\#\n\t'):
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
        lines.append(f"      evidence: {_quote(str(entry.get('evidence', '')))}")  # always quoted (tabs/empty)
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


def _write_handoff_run(ticket_dir: Path, run_id: str, handoff: dict[str, Any]) -> Path:
    ticket_dir.mkdir(parents=True, exist_ok=True)
    path = ticket_dir / f"handoff-{run_id}.yaml"
    path.write_text(_yaml_dump(handoff), encoding="utf-8")
    return path


def _repo_layout(tmp_path: Path, ticket_id: str = TICKET_ID) -> Path:
    return tmp_path / "project_board" / "checkpoints" / ticket_id


def _checkpoints_parent(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


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
        return gate_run(inputs)
    finally:
        os.chdir(old_cwd)


def _write_spec_file(tmp_path: Path) -> str:
    rel = f"project_board/specs/{TICKET_ID}_handoff_fixture_spec.md"
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Fixture Spec\n\n### 2. Acceptance Criteria\n\nAC listed.\n\n"
        "## Test strategy\n\npytest modules.\n\n## Risk & Ambiguity\n\nEdge cases.\n",
        encoding="utf-8",
    )
    return rel


def _spec_test_designer_checklist(tmp_path: Path) -> list[dict[str, Any]]:
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
            evidence=f"{spec_path} Risk & Ambiguity",
        ),
    ]


def _gap_item_keys(result: dict[str, Any]) -> set[str]:
    gaps = result.get("gaps") or result.get("missing_items") or []
    return {
        str(entry["item_key"])
        for entry in gaps
        if isinstance(entry, dict) and entry.get("item_key")
    }


# ---------------------------------------------------------------------------
# Evidence / status bypass (Req 03)
# ---------------------------------------------------------------------------


class TestHandoffValidationEvidenceBypass:
    """Agents must not PASS with empty evidence or threshold inflation."""

    def test_complete_with_empty_evidence_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        items = _spec_test_designer_checklist(tmp_path)
        for item in items:
            if item["item_key"] == "spec_edge_cases":
                item["evidence"] = ""
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(items, from_agent="spec", to_agent="test_designer"),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(
            v.get("rule") in ("handoff_evidence_missing", "handoff_item_missing")
            for v in result["violations"]
        )

    def test_complete_with_whitespace_only_evidence_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        items = _spec_test_designer_checklist(tmp_path)
        for item in items:
            if item["item_key"] == "spec_test_strategy":
                item["evidence"] = "   \t  "
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(items, from_agent="spec", to_agent="test_designer"),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_evidence_missing" for v in result["violations"])

    def test_coverage_75_does_not_bypass_threshold(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bypass: claim complete with coverage: 75 (Req 07 AC-07.2)."""
        monkeypatch.chdir(tmp_path)
        test_rel = "tests/ci/test_handoff_validation_gate_adversarial.py"
        test_path = tmp_path / test_rel
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("# fixture\n", encoding="utf-8")
        checklist = [
            _checklist_item(
                "test_suite_complete",
                evidence=test_rel,
                evidence_type="path",
            ),
            _checklist_item(
                "test_coverage_threshold",
                evidence="coverage: 75",
            ),
            _checklist_item(
                "test_all_runnable",
                evidence="pytest collection PASS 2026-05-20T18:00:00Z",
            ),
        ]
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                checklist,
                from_agent="test_designer",
                to_agent="test_breaker",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "test_designer", "test_breaker")
        assert result["status"] == "FAIL"
        assert "test_coverage_threshold" in _gap_item_keys(result)


# ---------------------------------------------------------------------------
# Deferral / counter bypass
# ---------------------------------------------------------------------------


class TestHandoffValidationDeferralAndCounterBypass:
    """Required deferrals and counter tricks must fail closed."""

    def test_required_deferred_without_deferrable_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        items = _spec_test_designer_checklist(tmp_path)
        for item in items:
            if item["item_key"] == "spec_acceptance_criteria":
                item["status"] = "deferred"
                item["defer_reason"] = "Will finish later"
                item["evidence"] = ""
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(items, from_agent="spec", to_agent="test_designer"),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_deferred_not_allowed" for v in result["violations"])

    def test_deflated_required_items_met_fails_counter_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bypass: under-report counters while items look complete."""
        monkeypatch.chdir(tmp_path)
        checklist = _spec_test_designer_checklist(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                checklist,
                from_agent="spec",
                to_agent="test_designer",
                required_items_met=0,
                total_required_items=3,
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_counter_mismatch" for v in result["violations"])


# ---------------------------------------------------------------------------
# Malformed artifacts — fail-closed (Req 02)
# ---------------------------------------------------------------------------


class TestHandoffValidationMalformedArtifacts:
    """Invalid envelopes must FAIL; handoff_optional must not mask parse errors."""

    def test_wrong_schema_version_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
                schema_version="2.0",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_invalid" for v in result["violations"])

    def test_empty_checklist_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root([], from_agent="spec", to_agent="test_designer"),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_invalid" for v in result["violations"])

    def test_duplicate_item_key_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        dup = _spec_test_designer_checklist(tmp_path)
        dup.append(_checklist_item("spec_edge_cases", evidence="duplicate key row"))
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(dup, from_agent="spec", to_agent="test_designer"),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_invalid" for v in result["violations"])

    def test_handoff_optional_does_not_mask_invalid_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        (ticket_dir / "handoff-latest.yaml").write_text("{not yaml", encoding="utf-8")
        monkeypatch.setenv("BLOBERT_ALLOW_GATE_OPT_OUT", "1")
        result = validate_handoff_checklist(
            TICKET_ID,
            "spec",
            "test_designer",
            handoff_optional=True,
        )
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_invalid" for v in result["violations"])

    def test_yaml_merge_anchor_in_handoff_root_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """YAML alias/merge tricks must not yield vacuous PASS (Req 02 risk)."""
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        anchor_yaml = (
            "handoff: &root\n"
            "  <<: *root\n"
            "  schema_version: '1.0'\n"
            "  ticket_id: M902-23\n"
            "  from_agent: spec\n"
            "  to_agent: test_designer\n"
            "  validated_at: '2026-05-20T18:00:00Z'\n"
            "  checklist: []\n"
            "  required_items_met: 0\n"
            "  total_required_items: 0\n"
        )
        (ticket_dir / "handoff-latest.yaml").write_text(anchor_yaml, encoding="utf-8")
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert result["violations"]


# ---------------------------------------------------------------------------
# Discovery / stale artifact bypass (Req 02)
# ---------------------------------------------------------------------------


class TestHandoffValidationDiscoveryBypass:
    """Precedence: latest > run mtime > fenced md; invalid latest is fail-closed."""

    def test_stale_run_file_wrong_pair_does_not_override_latest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Newer run file with wrong pair must not beat handoff-latest."""
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        _write_handoff_run(
            ticket_dir,
            "2026-05-21T-evil",
            _handoff_root(
                [
                    _checklist_item("spec_edge_cases", status="incomplete", evidence=""),
                ],
                from_agent="spec",
                to_agent="test_breaker",
            ),
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
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "PASS"

    def test_invalid_latest_does_not_fallback_to_newer_run_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        (ticket_dir / "handoff-latest.yaml").write_text("handoff: [", encoding="utf-8")
        time.sleep(0.02)
        _write_handoff_run(
            ticket_dir,
            "2026-05-21T-would-pass",
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_invalid" for v in result["violations"])

    def test_yaml_file_preferred_over_fenced_md_trap(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        fail_block = _yaml_dump(
            _handoff_root(
                [
                    _checklist_item(
                        "spec_edge_cases",
                        status="incomplete",
                        evidence="",
                    ),
                ],
                from_agent="spec",
                to_agent="test_designer",
            )
        )
        (ticket_dir / "trap.md").write_text(
            f"# checkpoint\n\n```yaml handoff\n{fail_block}```\n",
            encoding="utf-8",
        )
        time.sleep(0.02)
        _write_handoff_run(
            ticket_dir,
            "2026-05-20T-json-pass",
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "PASS"

    def test_fenced_md_used_when_no_standalone_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        block = _yaml_dump(
            _handoff_root(
                [
                    _checklist_item(
                        "spec_edge_cases",
                        status="incomplete",
                        evidence="",
                    ),
                ],
                from_agent="spec",
                to_agent="test_designer",
            )
        )
        (ticket_dir / "only-md.md").write_text(
            f"```yaml handoff-checklist\n{block}```\n",
            encoding="utf-8",
        )
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert "spec_edge_cases" in _gap_item_keys(result)


# ---------------------------------------------------------------------------
# Path traversal / symlink (NFR-3)
# ---------------------------------------------------------------------------


class TestHandoffValidationPathTraversalAdversarial:
    """Reject traversal in ticket_id and unsafe checkpoints_dir."""

    @pytest.mark.parametrize(
        "ticket_id",
        ["../M902-23", "M902-23/../../etc", "..\\M902-23", "M902-23%2e%2e"],
    )
    def test_ticket_id_traversal_variants_rejected(
        self, tmp_path: Path, ticket_id: str
    ) -> None:
        result = _run_with_checkpoints(
            tmp_path,
            from_agent="spec",
            to_agent="test_designer",
            ticket_id=ticket_id,
        )
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "path_traversal" for v in result["violations"])

    def test_symlink_handoff_latest_outside_ticket_dir_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Symlink escape: handoff-latest points outside checkpoints tree."""
        monkeypatch.chdir(tmp_path)
        outside = tmp_path / "outside-handoff.yaml"
        outside.write_text(
            _yaml_dump(
                _handoff_root(
                    _spec_test_designer_checklist(tmp_path),
                    from_agent="spec",
                    to_agent="test_designer",
                )
            ),
            encoding="utf-8",
        )
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        link = ticket_dir / "handoff-latest.yaml"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("symlink not supported in this environment")
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert result["violations"]


# ---------------------------------------------------------------------------
# Concurrent / torn writes (Req 02 risk)
# ---------------------------------------------------------------------------


class TestHandoffValidationConcurrentWrites:
    """Partial or torn YAML must fail closed, not vacuous PASS."""

    def test_truncated_handoff_latest_mid_document_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        ticket_dir = _repo_layout(tmp_path)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        full = _yaml_dump(
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="spec",
                to_agent="test_designer",
            )
        )
        torn = full[: max(20, len(full) // 2)]
        (ticket_dir / "handoff-latest.yaml").write_text(torn, encoding="utf-8")
        result = validate_handoff_checklist(TICKET_ID, "spec", "test_designer")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_artifact_invalid" for v in result["violations"])


# ---------------------------------------------------------------------------
# Pair / agent bypass (Req 04)
# ---------------------------------------------------------------------------


class TestHandoffValidationPairBypass:
    """Unknown pairs and wrong gate queries must not false-PASS blocked work."""

    def test_unknown_handoff_pair_fails_before_catalog(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(
                _spec_test_designer_checklist(tmp_path),
                from_agent="ac_gatekeeper",
                to_agent="planner",
            ),
        )
        result = validate_handoff_checklist(TICKET_ID, "ac_gatekeeper", "planner")
        assert result["status"] == "FAIL"
        assert any(v.get("rule") == "handoff_pair_unknown" for v in result["violations"])

    def test_query_planner_spec_while_file_is_spec_test_designer_incomplete_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Wrong pair query must not PASS on a different pair's incomplete artifact."""
        monkeypatch.chdir(tmp_path)
        incomplete = _spec_test_designer_checklist(tmp_path)
        for item in incomplete:
            if item["item_key"] == "spec_edge_cases":
                item["status"] = "incomplete"
                item["evidence"] = ""
        _write_handoff_latest(
            _repo_layout(tmp_path),
            _handoff_root(incomplete, from_agent="spec", to_agent="test_designer"),
        )
        result = validate_handoff_checklist(TICKET_ID, "planner", "spec")
        assert result["status"] == "FAIL"
        assert any(
            v.get("rule") in ("handoff_artifact_missing", "handoff_pair_mismatch")
            for v in result["violations"]
        )

"""
Atomic handoff YAML validation gate (M902-23).

Specification: project_board/specs/902_23_atomic_handoff_spec.md
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

import yaml

logger = logging.getLogger(__name__)

GATE_NAME = "handoff_validation_check"
GATE_VERSION = "0.1.0"
DEFAULT_CHECKPOINTS_DIR = "project_board/checkpoints"
HANDOFF_SCHEMA_VERSION = "1.0"
VALID_STATUSES = frozenset({"complete", "incomplete", "deferred", "blocked"})

AGENT_ALIAS_MAP: dict[str, str] = {
    "planner agent": "planner",
    "planner": "planner",
    "spec agent": "spec",
    "specification agent": "spec",
    "test designer agent": "test_designer",
    "test designer": "test_designer",
    "test-designer": "test_designer",
    "test breaker agent": "test_breaker",
    "test breaker": "test_breaker",
    "implementation agent": "implementation",
    "implementation agent generalist": "implementation",
    "implementation agent (generalist)": "implementation",
    "generalist": "implementation",
    "static qa": "static_qa",
    "code reviewer": "static_qa",
    "python-reviewer": "static_qa",
    "learning agent": "learning",
    "ac gatekeeper": "ac_gatekeeper",
    "acceptance criteria gatekeeper": "ac_gatekeeper",
    "acceptance criteria gatekeeper agent": "ac_gatekeeper",
}

VALID_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("planner", "spec"),
        ("spec", "test_designer"),
        ("test_designer", "test_breaker"),
        ("test_breaker", "implementation"),
        ("implementation", "static_qa"),
        ("static_qa", "learning"),
        ("learning", "ac_gatekeeper"),
    }
)

FAIL_REMEDIATION_HINTS = [
    "Complete all required checklist items with status: complete and non-empty evidence.",
    "Write or refresh project_board/checkpoints/<ticket_id>/handoff-latest.yaml before handoff.",
    "Re-run: python ci/scripts/gate_runner.py handoff_validation_check --input '{\"ticket_id\":\"<id>\",\"from_agent\":\"<from>\",\"to_agent\":\"<to>\"}'",
]


class CatalogItem:
    """Frozen catalog row for a handoff pair."""

    __slots__ = ("item_key", "item", "required", "deferrable", "evidence_type")

    def __init__(
        self,
        item_key: str,
        item: str,
        required: bool,
        deferrable: bool = False,
        evidence_type: str = "attestation",
    ) -> None:
        self.item_key = item_key
        self.item = item
        self.required = required
        self.deferrable = deferrable
        self.evidence_type = evidence_type


def _catalog(*entries: CatalogItem) -> dict[str, CatalogItem]:
    return {e.item_key: e for e in entries}


PAIR_CATALOGS: dict[tuple[str, str], dict[str, CatalogItem]] = {
    ("planner", "spec"): _catalog(
        CatalogItem(
            "planner_ticket_decomposed",
            "Ticket decomposed into execution plan tasks",
            True,
            evidence_type="path",
        ),
        CatalogItem(
            "planner_dependencies_clear",
            "Dependencies clear (acyclic or documented WARN)",
            True,
        ),
        CatalogItem(
            "planner_timeline_estimated",
            "Timeline estimated",
            True,
            evidence_type="path",
        ),
    ),
    ("spec", "test_designer"): _catalog(
        CatalogItem("spec_acceptance_criteria", "Acceptance criteria defined", True, evidence_type="path"),
        CatalogItem("spec_test_strategy", "Test strategy documented", True),
        CatalogItem("spec_edge_cases", "Edge cases listed", True),
    ),
    ("test_designer", "test_breaker"): _catalog(
        CatalogItem(
            "test_suite_complete",
            "Test suite complete per spec test plan",
            True,
            evidence_type="path",
        ),
        CatalogItem("test_coverage_threshold", "Coverage threshold met (>80% proxy)", True),
        CatalogItem("test_all_runnable", "All tests runnable", True),
    ),
    ("test_breaker", "implementation"): _catalog(
        CatalogItem(
            "breaker_gaps_documented",
            "All discovered gaps documented",
            True,
            evidence_type="path",
        ),
        CatalogItem("breaker_impl_notes", "Implementation notes created", True),
    ),
    ("implementation", "static_qa"): _catalog(
        CatalogItem("impl_ac_complete", "All acceptance criteria implemented", True),
        CatalogItem("impl_tests_passing", "All tests passing", True),
        CatalogItem("impl_linter_clean", "No linter violations", True, evidence_type="path"),
        CatalogItem("impl_checkpoint_logged", "Checkpoint logged", True, evidence_type="path"),
        CatalogItem(
            "impl_docstrings",
            "Docstrings/comments on complex logic",
            False,
            deferrable=True,
        ),
    ),
    ("static_qa", "learning"): _catalog(
        CatalogItem("review_feedback_incorporated", "Feedback incorporated", True),
        CatalogItem("review_code_reviewed", "Code reviewed", True),
        CatalogItem("review_merge_ready", "Merge-ready", True),
    ),
    ("learning", "ac_gatekeeper"): _catalog(
        CatalogItem(
            "learning_insights_documented",
            "Insights documented",
            True,
            evidence_type="path",
        ),
        CatalogItem("learning_rationale_recorded", "Decision rationale recorded", True),
        CatalogItem("learning_checklist_validated", "Handoff checklist validated", True),
    ),
}


class GateResult(TypedDict, total=False):
    version: str
    status: str
    gate: str
    ticket_id: str
    timestamp: str
    message: str
    violations: list[dict[str, Any]]
    remediation_hints: list[str]
    gaps: list[dict[str, Any]]
    missing_items: list[dict[str, Any]]
    from_agent: str
    to_agent: str
    artifacts: list[dict[str, str]]
    duration_ms: int
    upstream_agent: str
    downstream_agent: str
    mode: str


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_ticket_id(ticket_id: str) -> str:
    cleaned = ticket_id.upper().replace("_", "-").strip()
    match = re.search(r"(M\d{3}-\d+)", cleaned)
    if match:
        return match.group(1)
    return cleaned


def _normalize_agent_name(agent: str) -> str:
    raw = agent.strip()
    key = re.sub(r"\([^)]*\)", "", raw).strip()
    key_lower = key.lower()
    if key_lower in AGENT_ALIAS_MAP:
        return AGENT_ALIAS_MAP[key_lower]
    return re.sub(r"\s+", "_", key_lower)


def _is_unsafe_ticket_id(ticket_id: str) -> bool:
    if not ticket_id or not ticket_id.strip():
        return True
    lowered = ticket_id.lower()
    if ".." in ticket_id or "/" in ticket_id or "\\" in ticket_id:
        return True
    if "%2e" in lowered:
        return True
    return False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_checkpoints_root(checkpoints_dir: str) -> Path:
    path = Path(checkpoints_dir)
    if path.is_absolute():
        return path.resolve()
    cwd_candidate = (Path.cwd() / path).resolve()
    try:
        cwd_candidate.relative_to(Path.cwd().resolve())
        return cwd_candidate
    except ValueError:
        pass
    return (_repo_root() / path).resolve()


def _checkpoints_dir_allowed(checkpoints_dir: str) -> bool:
    if ".." in checkpoints_dir:
        return False
    resolved = _resolve_checkpoints_root(checkpoints_dir)
    for anchor in (_repo_root().resolve(), Path.cwd().resolve()):
        try:
            resolved.relative_to(anchor)
            return True
        except ValueError:
            continue
    return False


def _artifact_entry(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def _make_violation(
    *,
    file: str,
    rule: str,
    message: str,
    severity: str = "ERROR",
    line: int | None = None,
) -> dict[str, Any]:
    return {
        "file": file,
        "line": line,
        "rule": rule,
        "message": message,
        "severity": severity,
    }


def _base_result(ticket_id: str, start_time: float) -> dict[str, Any]:
    return {
        "version": GATE_VERSION,
        "gate": GATE_NAME,
        "ticket_id": ticket_id,
        "timestamp": _utc_timestamp(),
        "violations": [],
        "remediation_hints": [],
        "gaps": [],
        "missing_items": [],
        "artifacts": [],
        "duration_ms": int((time.perf_counter() - start_time) * 1000),
    }


def _gap_entry(
    item_key: str,
    item: str,
    *,
    status: str,
    required: bool,
) -> dict[str, Any]:
    return {
        "item_key": item_key,
        "item": item,
        "status": status,
        "required": required,
    }


_FENCE_RE = re.compile(
    r"```ya?ml\s+handoff(?:-checklist)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def _discover_handoff_source(ticket_dir: Path) -> tuple[Path | None, str]:
    """Return (source path, inline YAML payload). Payload empty when reading from a file."""
    latest = ticket_dir / "handoff-latest.yaml"
    if latest.is_file():
        return latest, ""

    candidates = [
        p
        for p in ticket_dir.glob("handoff-*.yaml")
        if p.name != "handoff-latest.yaml" and p.is_file()
    ]
    if candidates:
        newest = max(candidates, key=lambda p: p.stat().st_mtime)
        return newest, ""

    md_files = sorted(ticket_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        blocks = list(_FENCE_RE.finditer(text))
        if blocks:
            return md_path, blocks[-1].group(1)
    return None, ""


def _load_handoff_document(
    source: Path | None,
    raw_yaml: str,
    *,
    source_label: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        parsed = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        return None, [
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message=f"Invalid YAML: {exc}",
            )
        ]

    if parsed is None:
        return None, [
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message="Empty handoff document",
            )
        ]

    if not isinstance(parsed, dict) or "handoff" not in parsed:
        return None, [
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message="Root key 'handoff' required",
            )
        ]

    handoff = parsed["handoff"]
    if not isinstance(handoff, dict):
        return None, [
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message="handoff must be a mapping",
            )
        ]

    return parsed, []


def _validate_handoff_structure(
    handoff: dict[str, Any],
    *,
    expected_ticket_id: str,
    source_label: str,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []

    schema_raw = handoff.get("schema_version")
    schema_str = str(schema_raw) if schema_raw is not None else ""
    if schema_str not in (HANDOFF_SCHEMA_VERSION, "1", "1.0"):
        violations.append(
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message=(
                    f"Unsupported schema_version: {schema_raw!r} "
                    f"(expected {HANDOFF_SCHEMA_VERSION!r})"
                ),
            )
        )

    doc_ticket = handoff.get("ticket_id")
    if not isinstance(doc_ticket, str) or _normalize_ticket_id(doc_ticket) != expected_ticket_id:
        violations.append(
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message=f"ticket_id mismatch: expected {expected_ticket_id!r}",
            )
        )

    for field in (
        "from_agent",
        "to_agent",
        "checklist",
        "required_items_met",
        "total_required_items",
        "validated_at",
    ):
        if field not in handoff:
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_artifact_invalid",
                    message=f"Missing required field: handoff.{field}",
                )
            )

    checklist = handoff.get("checklist")
    if checklist is None:
        violations.append(
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message="handoff.checklist is required",
            )
        )
    elif not isinstance(checklist, list) or not checklist:
        violations.append(
            _make_violation(
                file=source_label,
                rule="handoff_artifact_invalid",
                message="handoff.checklist must be a non-empty list",
            )
        )
    else:
        seen: set[str] = set()
        for entry in checklist:
            if not isinstance(entry, dict):
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_artifact_invalid",
                        message="Each checklist entry must be a mapping",
                    )
                )
                continue
            key = entry.get("item_key")
            if isinstance(key, str):
                if key in seen:
                    violations.append(
                        _make_violation(
                            file=source_label,
                            rule="handoff_artifact_invalid",
                            message=f"Duplicate item_key: {key}",
                        )
                    )
                seen.add(key)
            status = entry.get("status")
            if status not in VALID_STATUSES:
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_artifact_invalid",
                        message=f"Invalid status: {status!r}",
                    )
                )

    return violations


def _resolve_repo_path(evidence: str) -> Path:
    path = Path(evidence.strip())
    if path.is_absolute():
        return path.resolve()
    cwd_target = (Path.cwd() / path).resolve()
    if cwd_target.is_file():
        return cwd_target
    repo_target = (_repo_root() / path).resolve()
    return repo_target


def _path_exists(evidence: str) -> bool:
    try:
        return _resolve_repo_path(evidence).is_file()
    except OSError:
        return False


def _validate_item_evidence(
    entry: dict[str, Any],
    catalog: CatalogItem,
    *,
    source_label: str,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    evidence = entry.get("evidence", "")
    if not isinstance(evidence, str):
        evidence = str(evidence)

    item_key = catalog.item_key
    evidence_type = entry.get("evidence_type") or catalog.evidence_type

    if evidence_type == "path":
        if not evidence.strip() or not _path_exists(evidence):
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_evidence_missing",
                    message=f"Path evidence missing or not found for {item_key}: {evidence!r}",
                )
            )
            return violations

        path = Path.cwd() / evidence.strip() if (Path.cwd() / evidence.strip()).is_file() else _resolve_repo_path(evidence)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            content = ""

        if item_key == "planner_timeline_estimated":
            if "Estimated Effort" not in content:
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_evidence_missing",
                        message="Execution plan must contain Estimated Effort",
                    )
                )
        if item_key == "spec_acceptance_criteria":
            if "Acceptance Criteria" not in content and "### 2. Acceptance Criteria" not in content:
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_evidence_missing",
                        message="Spec file must contain Acceptance Criteria section",
                    )
                )

    if not evidence.strip():
        violations.append(
            _make_violation(
                file=source_label,
                rule="handoff_evidence_missing",
                message=f"Evidence required for {item_key}",
            )
        )
        return violations

    if item_key == "test_coverage_threshold":
        lowered = evidence.lower()
        if "docs-only:n/a" in lowered.replace(" ", ""):
            return violations
        match = re.search(r"coverage:\s*(\d+)", evidence, re.I)
        if match:
            if int(match.group(1)) < 80:
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_item_missing",
                        message=f"Coverage below threshold: {match.group(1)}",
                    )
                )
            return violations
        if "diff_cover_preflight pass" in lowered:
            return violations
        if re.search(r"gate-results/.*\.json", evidence, re.I) and _path_exists(evidence):
            return violations
        violations.append(
            _make_violation(
                file=source_label,
                rule="handoff_item_missing",
                message="test_coverage_threshold evidence must include coverage: >=80 or diff_cover_preflight PASS",
            )
        )

    return violations


def _handoff_opt_out_forbidden(result: dict[str, Any], handoff_optional: bool) -> bool:
    """Return True when handoff_optional is used without break-glass env (result is FAIL)."""
    if not handoff_optional or os.environ.get("BLOBERT_ALLOW_GATE_OPT_OUT") == "1":
        return False
    result["status"] = "FAIL"
    result["message"] = (
        "handoff_optional is forbidden unless BLOBERT_ALLOW_GATE_OPT_OUT=1 (tests only)"
    )
    result["violations"] = [
        _make_violation(
            file="",
            rule="handoff_opt_out_forbidden",
            message=(
                "Orchestrators must use run_workflow_transition_gates.py "
                "without handoff_optional"
            ),
        )
    ]
    return True


def _load_handoff_artifact(
    result: dict[str, Any],
    ticket_dir: Path,
    source: Path | None,
    payload: str,
    *,
    handoff_optional: bool,
) -> tuple[dict[str, Any] | None, str, list[dict[str, Any]]] | None:
    """Load handoff document; return None if result was set for early exit."""
    if source is None and not payload:
        if handoff_optional:
            result["status"] = "PASS"
            result["message"] = "No handoff artifact; vacuous PASS (handoff_optional)."
            return None
        result["status"] = "FAIL"
        result["message"] = "Handoff artifact missing"
        result["violations"] = [
            _make_violation(
                file=str(ticket_dir),
                rule="handoff_artifact_missing",
                message="No handoff-latest.yaml or fenced handoff block found",
            )
        ]
        result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
        return None

    if source is not None and payload == "":
        if source.is_symlink():
            result["status"] = "FAIL"
            result["message"] = "Handoff artifact must not be a symlink"
            result["violations"] = [
                _make_violation(
                    file=str(source),
                    rule="path_traversal",
                    message="handoff-latest.yaml symlink is not allowed",
                )
            ]
            result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
            return None
        resolved_source = source.resolve()
        raw = resolved_source.read_text(encoding="utf-8")
        source_label = str(source)
        doc, parse_violations = _load_handoff_document(source, raw, source_label=source_label)
        result["artifacts"] = [_artifact_entry(resolved_source)]
        return doc, source_label, parse_violations

    if payload:
        source_label = str(source) if source else str(ticket_dir)
        doc, parse_violations = _load_handoff_document(None, payload, source_label=source_label)
        if source is not None and source.is_file():
            try:
                result["artifacts"] = [_artifact_entry(source)]
            except OSError:
                pass
        return doc, source_label, parse_violations

    return None, str(ticket_dir), []


def _checklist_entries_by_key(handoff: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    checklist_raw = handoff.get("checklist") or []
    if isinstance(checklist_raw, list):
        for entry in checklist_raw:
            if isinstance(entry, dict) and isinstance(entry.get("item_key"), str):
                by_key[entry["item_key"]] = entry
    return by_key


def _audit_catalog_checklist_entries(
    catalog: dict[str, CatalogItem],
    by_key: dict[str, dict[str, Any]],
    *,
    source_label: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    violations: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    for item_key, cat in catalog.items():
        entry = by_key.get(item_key)
        if entry is None:
            if cat.required:
                gaps.append(_gap_entry(item_key, cat.item, status="incomplete", required=True))
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_item_missing",
                        message=f"Missing required item_key: {item_key}",
                    )
                )
            continue

        if entry.get("item") != cat.item:
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_artifact_invalid",
                    message=f"Item label mismatch for {item_key}",
                )
            )

        required_flag = bool(entry.get("required", cat.required))
        if required_flag != cat.required:
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_artifact_invalid",
                    message=f"required flag mismatch for {item_key}",
                )
            )

        if item_key not in catalog and item_key in by_key:
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_unknown_item",
                    message=f"Unknown item_key for pair: {item_key}",
                )
            )

        status = entry.get("status")
        if status == "blocked" and cat.required:
            gaps.append(_gap_entry(item_key, cat.item, status="blocked", required=True))
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_blocked",
                    message=f"Required item blocked: {item_key}",
                )
            )
            continue

        if status == "deferred":
            if cat.required and not cat.deferrable:
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_deferred_not_allowed",
                        message=f"Required item cannot be deferred: {item_key}",
                    )
                )
                gaps.append(_gap_entry(item_key, cat.item, status="deferred", required=True))
            continue

        if status != "complete":
            if cat.required:
                gaps.append(_gap_entry(item_key, cat.item, status=str(status), required=True))
                violations.append(
                    _make_violation(
                        file=source_label,
                        rule="handoff_item_missing",
                        message=f"Required item not complete: {item_key} ({status})",
                    )
                )
            continue

        evidence = entry.get("evidence", "")
        if not isinstance(evidence, str) or not evidence.strip():
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_evidence_missing",
                    message=f"Complete item missing evidence: {item_key}",
                )
            )
            if cat.required:
                gaps.append(_gap_entry(item_key, cat.item, status="incomplete", required=True))
            continue

        item_violations = _validate_item_evidence(entry, cat, source_label=source_label)
        violations.extend(item_violations)
        if cat.required and item_violations:
            gaps.append(_gap_entry(item_key, cat.item, status="incomplete", required=True))

    for extra_key in by_key:
        if extra_key not in catalog:
            violations.append(
                _make_violation(
                    file=source_label,
                    rule="handoff_unknown_item",
                    message=f"Unknown item_key: {extra_key}",
                )
            )

    return violations, gaps


def _audit_handoff_required_counters(
    handoff: dict[str, Any],
    catalog: dict[str, CatalogItem],
    by_key: dict[str, dict[str, Any]],
    gaps: list[dict[str, Any]],
    *,
    source_label: str,
) -> list[dict[str, Any]]:
    required_total = sum(1 for c in catalog.values() if c.required)
    failing_keys = {
        g["item_key"]
        for g in gaps
        if isinstance(g.get("item_key"), str)
    }
    met_computed = sum(
        1
        for key, cat in catalog.items()
        if cat.required
        and key not in failing_keys
        and (entry := by_key.get(key))
        and entry.get("status") == "complete"
        and isinstance(entry.get("evidence"), str)
        and entry.get("evidence", "").strip()
    )

    declared_met = handoff.get("required_items_met")
    declared_total = handoff.get("total_required_items")
    if declared_met != met_computed or declared_total != required_total:
        return [
            _make_violation(
                file=source_label,
                rule="handoff_counter_mismatch",
                message=(
                    f"Counters mismatch: declared {declared_met}/{declared_total}, "
                    f"computed {met_computed}/{required_total}"
                ),
            )
        ]
    return []


def _audit_handoff_catalog(
    handoff: dict[str, Any],
    catalog: dict[str, CatalogItem],
    *,
    source_label: str,
    from_key: str,
    to_key: str,
    normalized_ticket: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    violations: list[dict[str, Any]] = []
    violations.extend(
        _validate_handoff_structure(handoff, expected_ticket_id=normalized_ticket, source_label=source_label)
    )

    doc_from = _normalize_agent_name(str(handoff.get("from_agent", "")))
    doc_to = _normalize_agent_name(str(handoff.get("to_agent", "")))
    if doc_from != from_key or doc_to != to_key:
        violations.append(
            _make_violation(
                file=source_label,
                rule="handoff_pair_mismatch",
                message=(
                    f"Document pair {doc_from}→{doc_to} does not match "
                    f"requested {from_key}→{to_key}"
                ),
            )
        )

    by_key = _checklist_entries_by_key(handoff)
    entry_violations, gaps = _audit_catalog_checklist_entries(
        catalog, by_key, source_label=source_label
    )
    violations.extend(entry_violations)
    violations.extend(
        _audit_handoff_required_counters(
            handoff, catalog, by_key, gaps, source_label=source_label
        )
    )
    return violations, gaps


def _evaluate_handoff_pair_checklist(
    result: dict[str, Any],
    *,
    normalized_ticket: str,
    from_key: str,
    to_key: str,
    pair: tuple[str, str],
    checkpoints_dir: str,
    handoff_optional: bool,
) -> dict[str, Any]:
    catalog = PAIR_CATALOGS[pair]
    root = _resolve_checkpoints_root(checkpoints_dir)
    ticket_dir = root / normalized_ticket
    source, payload = _discover_handoff_source(ticket_dir)

    loaded = _load_handoff_artifact(
        result, ticket_dir, source, payload, handoff_optional=handoff_optional
    )
    if loaded is None:
        return result

    doc, source_label, parse_violations = loaded
    violations: list[dict[str, Any]] = list(parse_violations)
    if doc is None:
        result["status"] = "FAIL"
        result["message"] = "Handoff artifact invalid"
        result["violations"] = violations
        result["gaps"] = []
        result["missing_items"] = []
        result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
        return result

    catalog_violations, gaps = _audit_handoff_catalog(
        doc["handoff"],
        catalog,
        source_label=source_label,
        from_key=from_key,
        to_key=to_key,
        normalized_ticket=normalized_ticket,
    )
    violations.extend(catalog_violations)
    result["gaps"] = gaps
    result["missing_items"] = gaps

    if violations:
        result["status"] = "FAIL"
        result["message"] = f"Handoff validation failed for {from_key}→{to_key} ({len(gaps)} gap(s))"
        result["violations"] = violations
        result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
        logger.info(
            "FAIL: handoff %s→%s ticket %s (%d violations)",
            from_key,
            to_key,
            normalized_ticket,
            len(violations),
        )
        return result

    result["status"] = "PASS"
    result["message"] = f"Handoff checklist valid for {from_key}→{to_key}."
    logger.info("PASS: handoff %s→%s ticket %s", from_key, to_key, normalized_ticket)
    return result


def validate_handoff_checklist(
    ticket_id: str,
    from_agent: str,
    to_agent: str,
    *,
    checkpoints_dir: str = DEFAULT_CHECKPOINTS_DIR,
    handoff_optional: bool = False,
) -> GateResult:
    start = time.perf_counter()
    normalized_ticket = _normalize_ticket_id(ticket_id)
    result: dict[str, Any] = _base_result(normalized_ticket, start)
    from_key = _normalize_agent_name(from_agent)
    to_key = _normalize_agent_name(to_agent)
    result["from_agent"] = from_key
    result["to_agent"] = to_key

    if _handoff_opt_out_forbidden(result, handoff_optional):
        return result  # type: ignore[return-value]

    if _is_unsafe_ticket_id(ticket_id):
        result["status"] = "FAIL"
        result["message"] = "Invalid ticket_id"
        result["violations"] = [
            _make_violation(file="", rule="path_traversal", message="Unsafe ticket_id")
        ]
        result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
        return result  # type: ignore[return-value]

    if not _checkpoints_dir_allowed(checkpoints_dir):
        result["status"] = "FAIL"
        result["message"] = "checkpoints_dir not allowed"
        result["violations"] = [
            _make_violation(
                file="",
                rule="path_traversal",
                message="checkpoints_dir must resolve under repository or cwd",
            )
        ]
        return result  # type: ignore[return-value]

    if from_key not in AGENT_ALIAS_MAP.values() and from_key == _normalize_agent_name(from_agent):
        if from_agent.strip().lower() not in AGENT_ALIAS_MAP:
            pass
    pair = (from_key, to_key)
    if pair not in VALID_PAIRS:
        result["status"] = "FAIL"
        result["message"] = f"Unknown handoff pair: {from_key} → {to_key}"
        result["violations"] = [
            _make_violation(
                file="",
                rule="handoff_pair_unknown",
                message=f"Pair ({from_key}, {to_key}) is not in the frozen pair table",
            )
        ]
        result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
        return result  # type: ignore[return-value]

    return _evaluate_handoff_pair_checklist(  # type: ignore[return-value]
        result,
        normalized_ticket=normalized_ticket,
        from_key=from_key,
        to_key=to_key,
        pair=pair,
        checkpoints_dir=checkpoints_dir,
        handoff_optional=handoff_optional,
    )


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute handoff validation gate via gate_runner."""
    ticket_id = inputs.get("ticket_id")
    from_agent = inputs.get("from_agent")
    to_agent = inputs.get("to_agent")
    checkpoints_dir = inputs.get("checkpoints_dir", DEFAULT_CHECKPOINTS_DIR)
    handoff_optional = bool(inputs.get("handoff_optional", False))

    if not ticket_id:
        result = _base_result("", time.perf_counter())
        result["status"] = "FAIL"
        result["message"] = "Missing required input: ticket_id"
        result["violations"] = [
            _make_violation(
                file="",
                rule="missing_required_input",
                message="ticket_id is required but was not provided.",
            )
        ]
        return result

    if not from_agent or not to_agent:
        normalized = _normalize_ticket_id(str(ticket_id))
        result = _base_result(normalized, time.perf_counter())
        result["status"] = "FAIL"
        result["message"] = "Missing required input: from_agent and to_agent"
        result["violations"] = [
            _make_violation(
                file="",
                rule="missing_required_input",
                message="from_agent and to_agent are required.",
            )
        ]
        return result

    result = validate_handoff_checklist(
        str(ticket_id),
        str(from_agent),
        str(to_agent),
        checkpoints_dir=str(checkpoints_dir),
        handoff_optional=handoff_optional,
    )
    result["gate"] = GATE_NAME

    if "upstream_agent" in inputs:
        result["upstream_agent"] = inputs["upstream_agent"]
    elif from_agent:
        result["upstream_agent"] = from_agent

    if "downstream_agent" in inputs:
        result["downstream_agent"] = inputs["downstream_agent"]
    elif to_agent:
        result["downstream_agent"] = to_agent

    if "mode" in inputs:
        result["mode"] = inputs["mode"]

    return result

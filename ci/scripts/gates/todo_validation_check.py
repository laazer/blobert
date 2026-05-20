"""
TodoWrite checkpoint validation gate (M902-20).

Specification: project_board/specs/902_20_todo_validation_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/20_todo_validation_gates.md

Validates TodoWrite checkpoint snapshots under project_board/checkpoints/<ticket_id>/
and blocks handoff when todos attributed to the finishing agent remain in_progress.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

logger = logging.getLogger(__name__)

GATE_NAME = "todo_validation_check"
GATE_VERSION = "0.1.0"
DEFAULT_CHECKPOINTS_DIR = "project_board/checkpoints"
SCHEMA_VERSION = "1.0"
SLOW_TASK_THRESHOLD_SECONDS = 3600

VALID_STATUSES = frozenset({"pending", "in_progress", "completed", "cancelled"})

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
    "integration agent": "integration",
    "documenter": "integration",
    "learning agent": "learning",
    "ac gatekeeper": "ac_gatekeeper",
    "acceptance criteria gatekeeper": "ac_gatekeeper",
    "acceptance criteria gatekeeper agent": "ac_gatekeeper",
}

FENCE_PATTERN = re.compile(
    r"```json\s+(todos|todo-snapshot)\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)

FAIL_REMEDIATION_HINTS = [
    "Run TodoWrite to move completed tasks to 'completed' status before handing off.",
    "For deferred work use 'pending' or 'cancelled' — do not leave finished work in 'in_progress'.",
    "Update project_board/checkpoints/<ticket_id>/todos-latest.json then re-run todo_validation_check.",
]


class GateResult(TypedDict, total=False):
    """Gate result conforming to M902-01 schema."""

    version: str
    status: str
    gate: str
    ticket_id: str
    timestamp: str
    message: str
    violations: list[dict[str, Any]]
    remediation_hints: list[str]
    incomplete_tasks: list[dict[str, Any]]
    artifacts: list[dict[str, str]]
    duration_ms: int
    upstream_agent: str
    downstream_agent: str
    mode: str
    timing_diagnostics: dict[str, Any]
    remediation: str


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_ticket_id(ticket_id: str) -> str:
    cleaned = ticket_id.upper().replace("_", "-").strip()
    match = re.search(r"(M\d{3}-\d{2})", cleaned)
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


def _is_unsafe_checkpoints_dir(checkpoints_dir: str) -> bool:
    if ".." in checkpoints_dir:
        return True
    return False


def _checkpoints_dir_allowed(checkpoints_dir: str) -> bool:
    if checkpoints_dir == DEFAULT_CHECKPOINTS_DIR:
        return True
    if _is_unsafe_checkpoints_dir(checkpoints_dir):
        return False
    path = Path(checkpoints_dir)
    if path.is_absolute() and path.name != "checkpoints":
        return False
    return True


def _artifact_entry(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


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
        "incomplete_tasks": [],
        "artifacts": [],
        "duration_ms": int((time.perf_counter() - start_time) * 1000),
    }


def _resolve_todo_agent(todo: dict[str, Any], envelope_agent: str | None) -> str | None:
    todo_agent = todo.get("agent")
    if isinstance(todo_agent, str) and todo_agent.strip():
        return todo_agent.strip()
    if envelope_agent and envelope_agent.strip():
        return envelope_agent.strip()
    return None


def _parse_snapshot_json(
    raw: str,
    *,
    source_path: str,
    expected_ticket_id: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [
            _make_violation(
                file=source_path,
                rule="todo_artifact_invalid",
                message=f"Invalid JSON in todo snapshot: {exc}",
            )
        ]

    if not isinstance(parsed, dict):
        return None, [
            _make_violation(
                file=source_path,
                rule="todo_artifact_invalid",
                message="Todo snapshot root must be a JSON object",
            )
        ]

    violations: list[dict[str, Any]] = []

    schema_version = parsed.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        violations.append(
            _make_violation(
                file=source_path,
                rule="todo_artifact_invalid",
                message=f"Unsupported schema_version: {schema_version!r} (expected {SCHEMA_VERSION!r})",
            )
        )

    for field in ("ticket_id", "captured_at", "todos"):
        if field not in parsed:
            violations.append(
                _make_violation(
                    file=source_path,
                    rule="todo_artifact_invalid",
                    message=f"Missing required field: {field}",
                )
            )

    envelope_ticket = parsed.get("ticket_id")
    if isinstance(envelope_ticket, str):
        if _normalize_ticket_id(envelope_ticket) != expected_ticket_id:
            violations.append(
                _make_violation(
                    file=source_path,
                    rule="todo_artifact_invalid",
                    message=(
                        f"Envelope ticket_id {envelope_ticket!r} does not match "
                        f"expected {_normalize_ticket_id(expected_ticket_id)!r}"
                    ),
                )
            )

    todos = parsed.get("todos")
    if todos is not None and not isinstance(todos, list):
        violations.append(
            _make_violation(
                file=source_path,
                rule="todo_artifact_invalid",
                message="Field 'todos' must be an array",
            )
        )
        todos = None

    if isinstance(todos, list):
        seen_ids: set[str] = set()
        for index, todo in enumerate(todos):
            if not isinstance(todo, dict):
                violations.append(
                    _make_violation(
                        file=source_path,
                        rule="todo_artifact_invalid",
                        message=f"Todo record at index {index} must be an object",
                    )
                )
                continue
            for req in ("id", "content", "status"):
                if req not in todo:
                    violations.append(
                        _make_violation(
                            file=source_path,
                            rule="todo_artifact_invalid",
                            message=f"Todo record missing required field: {req}",
                        )
                    )
            todo_id = todo.get("id")
            if isinstance(todo_id, str):
                if todo_id in seen_ids:
                    violations.append(
                        _make_violation(
                            file=source_path,
                            rule="todo_artifact_invalid",
                            message=f"Duplicate todo id: {todo_id}",
                        )
                    )
                seen_ids.add(todo_id)
            status = todo.get("status")
            if isinstance(status, str) and status not in VALID_STATUSES:
                violations.append(
                    _make_violation(
                        file=source_path,
                        rule="todo_artifact_invalid",
                        message=f"Unknown todo status: {status!r}",
                    )
                )

    if violations:
        return None, violations
    return parsed, []


def _discover_snapshot(
    ticket_dir: Path,
    expected_ticket_id: str,
) -> tuple[dict[str, Any] | None, Path | None, list[dict[str, Any]]]:
    latest_path = ticket_dir / "todos-latest.json"
    if latest_path.exists():
        logger.info("Using primary snapshot: %s", latest_path)
        raw = latest_path.read_text(encoding="utf-8")
        snapshot, violations = _parse_snapshot_json(
            raw,
            source_path=str(latest_path),
            expected_ticket_id=expected_ticket_id,
        )
        return snapshot, latest_path if snapshot else latest_path, violations

    run_files = sorted(
        ticket_dir.glob("todos-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    run_files = [p for p in run_files if p.name != "todos-latest.json"]
    if run_files:
        chosen = run_files[0]
        logger.warning("Falling back to run snapshot: %s", chosen)
        raw = chosen.read_text(encoding="utf-8")
        snapshot, violations = _parse_snapshot_json(
            raw,
            source_path=str(chosen),
            expected_ticket_id=expected_ticket_id,
        )
        return snapshot, chosen if snapshot else chosen, violations

    md_files = sorted(ticket_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        blocks = list(FENCE_PATTERN.finditer(content))
        if not blocks:
            continue
        logger.warning("Falling back to fenced JSON in markdown: %s", md_file)
        last_block = blocks[-1].group(2)
        snapshot, violations = _parse_snapshot_json(
            last_block,
            source_path=str(md_file),
            expected_ticket_id=expected_ticket_id,
        )
        return snapshot, md_file if snapshot else md_file, violations

    logger.info("No todo snapshots found under %s", ticket_dir)
    return None, None, []


def _compute_timing_diagnostics(todos: list[dict[str, Any]]) -> dict[str, Any] | None:
    slow_tasks: list[dict[str, Any]] = []
    for todo in todos:
        started = todo.get("started_at")
        completed = todo.get("completed_at")
        if not isinstance(started, str) or not isinstance(completed, str):
            continue
        try:
            start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            duration_seconds = (end_dt - start_dt).total_seconds()
        except ValueError:
            continue
        if duration_seconds < 0:
            continue
        if duration_seconds > SLOW_TASK_THRESHOLD_SECONDS:
            slow_tasks.append(
                {
                    "id": todo.get("id", ""),
                    "content": todo.get("content", ""),
                    "duration_seconds": duration_seconds,
                }
            )
    if not slow_tasks:
        return None
    return {"slow_tasks": slow_tasks}


def validate_todos(
    ticket_id: str,
    expected_agent: str,
    *,
    checkpoints_dir: str = DEFAULT_CHECKPOINTS_DIR,
) -> dict[str, Any]:
    """Validate todo snapshots for a ticket and expected finishing agent."""
    start_time = time.perf_counter()

    if _is_unsafe_ticket_id(ticket_id):
        normalized_ticket = _normalize_ticket_id(ticket_id)
        result = _base_result(normalized_ticket, start_time)
        result["status"] = "FAIL"
        result["message"] = f"Unsafe ticket_id rejected: {ticket_id!r}"
        result["violations"] = [
            _make_violation(
                file=str(Path(checkpoints_dir) / normalized_ticket),
                rule="path_traversal",
                message=f"ticket_id contains unsafe path segments: {ticket_id!r}",
            )
        ]
        return result

    if _is_unsafe_checkpoints_dir(checkpoints_dir):
        normalized_ticket = _normalize_ticket_id(ticket_id)
        result = _base_result(normalized_ticket, start_time)
        result["status"] = "FAIL"
        result["message"] = f"Unsafe checkpoints_dir rejected: {checkpoints_dir!r}"
        result["violations"] = [
            _make_violation(
                file=checkpoints_dir,
                rule="path_traversal",
                message=f"checkpoints_dir contains path traversal: {checkpoints_dir!r}",
            )
        ]
        return result

    if not _checkpoints_dir_allowed(checkpoints_dir):
        normalized_ticket = _normalize_ticket_id(ticket_id)
        result = _base_result(normalized_ticket, start_time)
        result["status"] = "FAIL"
        result["message"] = f"checkpoints_dir outside repository root: {checkpoints_dir!r}"
        result["violations"] = [
            _make_violation(
                file=checkpoints_dir,
                rule="path_traversal",
                message=f"checkpoints_dir must be under repository root: {checkpoints_dir!r}",
            )
        ]
        return result

    normalized_ticket = _normalize_ticket_id(ticket_id)
    result = _base_result(normalized_ticket, start_time)
    checkpoints_root = Path(checkpoints_dir)

    ticket_dir = checkpoints_root / normalized_ticket
    expected_key = _normalize_agent_name(expected_agent)

    snapshot, source_path, parse_violations = _discover_snapshot(ticket_dir, normalized_ticket)
    if parse_violations:
        result["status"] = "FAIL"
        result["message"] = "Todo snapshot artifact is invalid"
        result["violations"] = parse_violations
        result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
        return result

    if snapshot is None:
        result["status"] = "PASS"
        result["message"] = f"No todo snapshots found for {normalized_ticket}; vacuous PASS."
        return result

    if source_path is not None:
        result["artifacts"] = [_artifact_entry(source_path)]

    todos = snapshot.get("todos", [])
    envelope_agent = snapshot.get("agent")
    if isinstance(envelope_agent, str):
        envelope_agent = envelope_agent.strip()
    else:
        envelope_agent = None

    if not todos:
        result["status"] = "PASS"
        result["message"] = "Empty todo list; vacuous PASS."
        timing = _compute_timing_diagnostics(todos)
        if timing:
            result["timing_diagnostics"] = timing
        return result

    incomplete: list[dict[str, Any]] = []
    for todo in todos:
        if not isinstance(todo, dict):
            continue
        display_agent = _resolve_todo_agent(todo, envelope_agent)
        if display_agent is None:
            continue
        if _normalize_agent_name(display_agent) != expected_key:
            continue
        if todo.get("status") == "in_progress":
            agent_key = _normalize_agent_name(display_agent)
            incomplete.append(
                {
                    "id": todo.get("id", ""),
                    "content": todo.get("content", ""),
                    "activeForm": todo.get("activeForm") or todo.get("content", ""),
                    "status": "in_progress",
                    "agent": display_agent,
                    "agent_key": agent_key,
                }
            )

    incomplete.sort(key=lambda t: (t.get("id", ""), t.get("content", "")))

    timing = _compute_timing_diagnostics(todos)
    if timing:
        result["timing_diagnostics"] = timing

    artifact_file = str(source_path) if source_path else str(ticket_dir)

    if incomplete:
        result["status"] = "FAIL"
        count = len(incomplete)
        result["message"] = (
            f"{count} task(s) remain in_progress for {expected_agent}. "
            "Agent should complete or explicitly move to pending/cancelled."
        )
        result["incomplete_tasks"] = incomplete
        result["violations"] = [
            _make_violation(
                file=artifact_file,
                rule="todo_incomplete",
                message=f"Todo still in_progress: {item['content']} (agent={item['agent']})",
            )
            for item in incomplete
        ]
        result["remediation_hints"] = list(FAIL_REMEDIATION_HINTS)
        result["remediation"] = FAIL_REMEDIATION_HINTS[0]
        logger.info(
            "FAIL: %d incomplete todos for agent %s (ticket %s)",
            count,
            expected_agent,
            normalized_ticket,
        )
        return result

    result["status"] = "PASS"
    result["message"] = f"All todos completed for {expected_agent}."
    logger.info("PASS: all todos completed for agent %s (ticket %s)", expected_agent, normalized_ticket)
    return result


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute todo validation gate via gate_runner."""
    ticket_id = inputs.get("ticket_id")
    expected_agent = inputs.get("expected_agent")
    checkpoints_dir = inputs.get("checkpoints_dir", DEFAULT_CHECKPOINTS_DIR)

    if not ticket_id:
        normalized = ""
        result = _base_result(normalized, time.perf_counter())
        result["status"] = "FAIL"
        result["message"] = "Missing required input: ticket_id"
        result["violations"] = [
            _make_violation(
                file="",
                rule="missing_required_input",
                message="ticket_id is required but was not provided.",
            )
        ]
        result["gate"] = GATE_NAME
        return result

    if not expected_agent:
        normalized = _normalize_ticket_id(str(ticket_id))
        result = _base_result(normalized, time.perf_counter())
        result["status"] = "FAIL"
        result["message"] = "Missing required input: expected_agent"
        result["violations"] = [
            _make_violation(
                file="",
                rule="missing_required_input",
                message="expected_agent is required but was not provided.",
            )
        ]
        result["gate"] = GATE_NAME
        return result

    result = validate_todos(str(ticket_id), str(expected_agent), checkpoints_dir=str(checkpoints_dir))
    result["gate"] = GATE_NAME

    if "upstream_agent" in inputs:
        result["upstream_agent"] = inputs["upstream_agent"]
    elif expected_agent:
        result["upstream_agent"] = expected_agent

    if "downstream_agent" in inputs:
        result["downstream_agent"] = inputs["downstream_agent"]

    if "mode" in inputs:
        result["mode"] = inputs["mode"]

    return result

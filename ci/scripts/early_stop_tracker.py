"""Early-stop tracker — detect agent loop stagnation (M902-22).

Persists iterations at ``project_board/checkpoints/<ticket_id>/agent_iterations.json``.
Escalation events append to ``early_stop_events.jsonl``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .context_budget_tracker import (
    _lock_for,
    _resolve_checkpoints_root,
    find_repo_root,
    normalize_ticket_id,
)

SCHEMA_VERSION = "1.0.0"
EMPTY_DIFF_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
_ERROR_TRUNCATE_LEN = 2000
_TRUNCATE_SUFFIX = " …[truncated]"

_UNIX_PATH_RE = re.compile(r"(?:/Users/|/home/|/tmp/)[^\s:]+")
_WIN_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s:]+")
_DIFF_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

_logger = logging.getLogger(__name__)
_git_warning_logged = False
_last_jsonl_event_key: dict[str, str] = {}
_jsonl_key_guard = threading.Lock()


@dataclass
class EarlyStopConfig:
    max_iterations: int = 5
    error_threshold: int = 3
    diff_threshold: int = 3
    noop_threshold: int = 2
    handoff_override: str = ""


@dataclass
class EarlyStopResult:
    should_escalate: bool = False
    break_loop: bool = False
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    no_op_streak: int = 0
    recommended_handoff: str = ""
    incomplete_iterations: bool = False


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_positive_int(env_name: str, default: int, minimum: int = 1) -> int:
    raw = os.environ.get(env_name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        _logger.warning("%s invalid (%r); using default %s", env_name, raw, default)
        return default
    if value < minimum:
        _logger.warning("%s below minimum (%s); using default %s", env_name, minimum, default)
        return default
    return value


def config_from_env() -> EarlyStopConfig:
    return EarlyStopConfig(
        max_iterations=_parse_positive_int("EARLY_STOP_MAX_ITERATIONS", 5),
        error_threshold=_parse_positive_int("EARLY_STOP_ERROR_THRESHOLD", 3, minimum=2),
        diff_threshold=_parse_positive_int("EARLY_STOP_DIFF_THRESHOLD", 3, minimum=2),
        noop_threshold=_parse_positive_int("EARLY_STOP_NOOP_THRESHOLD", 2, minimum=2),
    )


def normalize_error(text: str) -> str:
    if not text:
        return ""
    collapsed = re.sub(r"\s+", " ", text.strip())
    collapsed = _UNIX_PATH_RE.sub("", collapsed)
    collapsed = _WIN_PATH_RE.sub("", collapsed)
    collapsed = re.sub(r"\s+", " ", collapsed).strip()
    if len(collapsed) <= _ERROR_TRUNCATE_LEN:
        return collapsed
    limit = _ERROR_TRUNCATE_LEN - len(_TRUNCATE_SUFFIX)
    return collapsed[:limit] + _TRUNCATE_SUFFIX


def extract_error(
    iteration_context: dict[str, Any],
    framework_result: Any | None = None,
    framework_kwargs: dict[str, Any] | None = None,
) -> str:
    ctx = iteration_context or {}
    for key in ("error", "error_message"):
        val = ctx.get(key)
        if isinstance(val, str) and val.strip():
            return normalize_error(val)

    if isinstance(framework_result, dict):
        for key in ("error", "stderr", "message"):
            val = framework_result.get(key)
            if isinstance(val, str) and val.strip():
                return normalize_error(val)

    fk = framework_kwargs or {}
    for key in ("last_error", "stderr"):
        val = fk.get(key)
        if isinstance(val, str) and val.strip():
            return normalize_error(val)
    return ""


def _normalize_modified_files(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    paths: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            paths.append(item.strip().replace("\\", "/"))
    return sorted(set(paths))


def _git_porcelain_paths(repo_root: Path) -> list[str]:
    global _git_warning_logged  # noqa: PLW0603
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        if not _git_warning_logged:
            _logger.warning("git status failed: %s", exc)
            _git_warning_logged = True
        return []
    if proc.returncode != 0:
        if not _git_warning_logged:
            _logger.warning("git status exit %s: %s", proc.returncode, proc.stderr)
            _git_warning_logged = True
        return []
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path_part = line[3:].strip()
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1].strip()
        if path_part:
            paths.append(path_part.replace("\\", "/"))
    return sorted(set(paths))


def discover_modified_files(
    iteration_context: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> list[str]:
    ctx = iteration_context or {}
    if "modified_files" in ctx:
        return _normalize_modified_files(ctx.get("modified_files"))
    root = repo_root or find_repo_root()
    return _git_porcelain_paths(root)


def compute_diff_hash(
    modified_files: list[str],
    iteration_context: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> str:
    ctx = iteration_context or {}
    injected = ctx.get("diff_hash")
    if isinstance(injected, str) and _DIFF_HASH_RE.fullmatch(injected):
        return injected

    if not modified_files:
        return EMPTY_DIFF_HASH

    root = repo_root or find_repo_root()
    try:
        proc = subprocess.run(
            ["git", "diff", "HEAD", "--", *modified_files],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        payload = proc.stdout if proc.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        payload = ""

    if not payload:
        return EMPTY_DIFF_HASH
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _iterations_file(checkpoints_root: Path, ticket_id: str) -> Path:
    return checkpoints_root / ticket_id / "agent_iterations.json"


def _events_file(checkpoints_root: Path, ticket_id: str) -> Path:
    return checkpoints_root / ticket_id / "early_stop_events.jsonl"


def _load_document(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {version!r}")
    return data


def _tail_streak(iterations: list[dict[str, Any]], field_name: str, *, non_empty_only: bool = False) -> int:
    if not iterations:
        return 0
    streak = 0
    target = iterations[-1].get(field_name)
    if non_empty_only and not target:
        return 0
    for item in reversed(iterations):
        val = item.get(field_name)
        if non_empty_only and not val:
            break
        if val == target:
            streak += 1
        else:
            break
    return streak


def _compute_rollup(iterations: list[dict[str, Any]], config: EarlyStopConfig) -> dict[str, Any]:
    error_streak = _tail_streak(iterations, "error", non_empty_only=True)
    diff_streak = _tail_streak(iterations, "diff_hash")
    noop_streak = 0
    for item in reversed(iterations):
        if item.get("no_op_flag"):
            noop_streak += 1
        else:
            break

    should_escalate = False
    escalate_reason: str | None = None
    if error_streak >= config.error_threshold:
        should_escalate = True
        escalate_reason = "repeated_error"
    elif diff_streak >= config.diff_threshold:
        should_escalate = True
        escalate_reason = "repeated_diff"
    elif len(iterations) >= config.max_iterations:
        should_escalate = True
        escalate_reason = "max_iterations"

    last = iterations[-1] if iterations else {}
    return {
        "iteration_count": len(iterations),
        "last_error": last.get("error", ""),
        "last_diff_hash": last.get("diff_hash", EMPTY_DIFF_HASH),
        "error_repeat_streak": error_streak,
        "diff_repeat_streak": diff_streak,
        "no_op_streak": noop_streak,
        "should_escalate": should_escalate,
        "escalate_reason": escalate_reason,
    }


def _build_iteration_record(
    *,
    iteration: int,
    agent_run_id: str,
    error: str,
    diff_hash: str,
    modified_files: list[str],
    tools_invoked: bool,
) -> dict[str, Any]:
    no_op = bool(tools_invoked) and len(modified_files) == 0
    record: dict[str, Any] = {
        "iteration": iteration,
        "agent_run_id": agent_run_id,
        "recorded_at": _utc_now_iso(),
        "error": error,
        "diff_hash": diff_hash,
        "modified_files": modified_files,
        "tools_invoked": tools_invoked,
    }
    if no_op:
        record["no_op_flag"] = True
    return record


def record_iteration(
    ticket_id: str,
    *,
    agent_type: str,
    agent_run_id: str,
    loop_run_id: str,
    iteration_context: dict[str, Any],
    framework_result: Any | None = None,
    checkpoints_root: Path | None = None,
    ticket_path: str | None = None,
    framework_kwargs: dict[str, Any] | None = None,
) -> None:
    if not loop_run_id:
        raise ValueError("loop_run_id is required")
    if not agent_run_id:
        raise ValueError("agent_run_id is required")

    normalized_id = normalize_ticket_id(ticket_id)
    root = _resolve_checkpoints_root(checkpoints_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _iterations_file(root, normalized_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    ctx = iteration_context or {}
    error = extract_error(ctx, framework_result, framework_kwargs)
    modified_files = discover_modified_files(ctx)
    diff_hash = compute_diff_hash(modified_files, ctx)
    tools_invoked = bool(ctx.get("tools_invoked", False))

    now = _utc_now_iso()
    with _lock_for(path):
        existing = _load_document(path) if path.is_file() else {}
        if existing:
            doc = existing
            if doc.get("loop_run_id") != loop_run_id:
                doc["iterations"] = []
                doc["loop_run_id"] = loop_run_id
            doc["updated_at"] = now
            doc["agent"] = agent_type
            if ticket_path:
                doc["ticket_path"] = ticket_path
        else:
            doc = {
                "schema_version": SCHEMA_VERSION,
                "ticket_id": normalized_id,
                "ticket_path": ticket_path,
                "agent": agent_type,
                "loop_run_id": loop_run_id,
                "created_at": now,
                "updated_at": now,
                "iterations": [],
                "rollup": {},
                "last_evaluation": None,
            }

        iterations: list[dict[str, Any]] = list(doc.get("iterations") or [])
        new_record = _build_iteration_record(
            iteration=0,
            agent_run_id=agent_run_id,
            error=error,
            diff_hash=diff_hash,
            modified_files=modified_files,
            tools_invoked=tools_invoked,
        )

        replaced = False
        for idx, item in enumerate(iterations):
            if item.get("agent_run_id") == agent_run_id:
                new_record["iteration"] = item.get("iteration", idx + 1)
                iterations[idx] = new_record
                replaced = True
                break
        if not replaced:
            new_record["iteration"] = len(iterations) + 1
            iterations.append(new_record)

        doc["iterations"] = iterations
        config = config_from_env()
        doc["rollup"] = _compute_rollup(iterations, config)

        if doc["rollup"]["no_op_streak"] >= config.noop_threshold:
            _logger.warning(
                "early stop no-op streak ticket_id=%s no_op_streak=%s iteration=%s",
                normalized_id,
                doc["rollup"]["no_op_streak"],
                new_record["iteration"],
            )

        path.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def _build_evidence(doc: dict[str, Any], reason: str, config: EarlyStopConfig) -> dict[str, Any]:
    iterations: list[dict[str, Any]] = doc.get("iterations") or []
    rollup = doc.get("rollup") or {}
    if reason == "repeated_error":
        n = int(rollup.get("error_repeat_streak", config.error_threshold))
    elif reason == "repeated_diff":
        n = int(rollup.get("diff_repeat_streak", config.diff_threshold))
    else:
        n = int(rollup.get("iteration_count", config.max_iterations))
    n = max(n, 1)
    tail = iterations[-n:]
    return {
        "ticket_id": doc.get("ticket_id", ""),
        "iteration_indices": [int(it.get("iteration", 0)) for it in tail],
        "errors": [it.get("error", "") for it in tail],
        "diff_hashes": [it.get("diff_hash", EMPTY_DIFF_HASH) for it in tail],
        "modified_files_union": sorted(
            {p for it in tail for p in (it.get("modified_files") or []) if isinstance(p, str)}
        ),
        "agent": doc.get("agent", ""),
        "loop_run_id": doc.get("loop_run_id", ""),
    }


def _handoff_for_reason(reason: str, config: EarlyStopConfig) -> str:
    if config.handoff_override:
        return config.handoff_override
    if reason in ("repeated_error", "repeated_diff", "max_iterations"):
        return "human"
    return ""


def _jsonl_dedupe_key(
    checkpoints_root: Path,
    ticket_id: str,
    doc: dict[str, Any],
    reason: str,
) -> str:
    rollup = doc.get("rollup") or {}
    return (
        f"{checkpoints_root.resolve()}:{ticket_id}:{doc.get('loop_run_id')}:"
        f"{rollup.get('iteration_count')}:{reason}"
    )


def _append_jsonl_event(path: Path, payload: dict[str, Any]) -> None:
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _mark_last_iteration_escalation(path: Path, reason: str) -> None:
    with _lock_for(path):
        doc = _load_document(path)
        iterations = doc.get("iterations") or []
        if not iterations:
            return
        iterations[-1]["escalation_triggered"] = True
        iterations[-1]["reason"] = reason
        doc["iterations"] = iterations
        path.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def evaluate_early_stop(
    ticket_id: str,
    *,
    config: EarlyStopConfig | None = None,
    checkpoints_root: Path | None = None,
) -> EarlyStopResult:
    cfg = config or config_from_env()
    normalized_id = normalize_ticket_id(ticket_id)
    root = _resolve_checkpoints_root(checkpoints_root)
    path = _iterations_file(root, normalized_id)

    if not path.is_file():
        return EarlyStopResult(incomplete_iterations=True)

    try:
        doc = _load_document(path)
    except (json.JSONDecodeError, ValueError):
        return EarlyStopResult(incomplete_iterations=True)

    raw_iterations = doc.get("iterations")
    if not isinstance(raw_iterations, list):
        return EarlyStopResult(incomplete_iterations=True)
    iterations: list[dict[str, Any]] = raw_iterations
    rollup = _compute_rollup(iterations, cfg)
    doc["rollup"] = rollup

    should = bool(rollup.get("should_escalate"))
    reason = rollup.get("escalate_reason") or ""
    if should and not reason:
        reason = "max_iterations"

    result = EarlyStopResult(
        should_escalate=should,
        break_loop=should,
        reason=reason if should else "",
        evidence=_build_evidence(doc, reason, cfg) if should else {},
        no_op_streak=int(rollup.get("no_op_streak", 0)),
        recommended_handoff=_handoff_for_reason(reason, cfg) if should else "",
        incomplete_iterations=False,
    )

    doc["last_evaluation"] = asdict(result)
    events_path = _events_file(root, normalized_id)

    if should:
        _logger.info(
            "early stop escalate ticket_id=%s reason=%s iteration_count=%s "
            "error_repeat_streak=%s diff_repeat_streak=%s no_op_streak=%s "
            "diff_hash_prefixes=%s",
            normalized_id,
            reason,
            rollup.get("iteration_count"),
            rollup.get("error_repeat_streak"),
            rollup.get("diff_repeat_streak"),
            rollup.get("no_op_streak"),
            [str(h)[:8] for h in (result.evidence.get("diff_hashes") or [])[-3:]],
        )
        dedupe_key = _jsonl_dedupe_key(root, normalized_id, doc, reason)
        with _jsonl_key_guard:
            if _last_jsonl_event_key.get(str(root.resolve())) != dedupe_key:
                event_payload = {**asdict(result), "logged_at": _utc_now_iso()}
                events_path.parent.mkdir(parents=True, exist_ok=True)
                _append_jsonl_event(events_path, event_payload)
                _last_jsonl_event_key[str(root.resolve())] = dedupe_key
        _mark_last_iteration_escalation(path, reason)

    with _lock_for(path):
        path.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return result

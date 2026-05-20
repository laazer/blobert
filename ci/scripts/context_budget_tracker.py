"""Context budget tracker — record LLM token usage per agent stage (M902-21).

Persists merged usage at ``project_board/checkpoints/<ticket_id>/token_usage.json``.
Forecasting remains in ``ci/scripts/token_budget_analyzer.py`` (unchanged).
"""

from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
CHARS_PER_TOKEN = 4
ALLOWED_TICKET_TYPES = frozenset({"feature", "bugfix", "refactor", "generic"})

_logger = logging.getLogger(__name__)
_file_locks: dict[str, threading.Lock] = {}
_file_locks_guard = threading.Lock()

_STAGE_ALIASES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(planner|planning)$", re.I), "planning"),
    (re.compile(r"^(spec|specification|spec agent)$", re.I), "spec"),
    (re.compile(r"^(test-designer|test_designer|test design|test_design)$", re.I), "test-designer"),
    (re.compile(r"^(test-breaker|test_breaker|test break)$", re.I), "test-breaker"),
    (re.compile(r"^(implementation|implementation-generalist|implementation agent)$", re.I), "implementation"),
    (re.compile(r"^(implementation-backend|backend)$", re.I), "implementation-backend"),
    (re.compile(r"^(implementation-frontend|frontend)$", re.I), "implementation-frontend"),
    (re.compile(r"^(static-qa|static_qa|reviewer|python-reviewer|code-reviewer)$", re.I), "review"),
    (re.compile(r"^integration$", re.I), "integration"),
    (re.compile(r"^(ac-gatekeeper|acceptance|gatekeeper)$", re.I), "acceptance"),
    (re.compile(r"^learning$", re.I), "learning"),
    (re.compile(r"^deployment$", re.I), "deployment"),
]


def find_repo_root() -> Path:
    """Return repository root (directory containing ``.git``)."""
    current = Path.cwd().resolve()
    while True:
        if (current / ".git").is_dir():
            return current
        if current.parent == current:
            return Path(__file__).resolve().parents[2]
        current = current.parent


def normalize_ticket_id(ticket_id: str) -> str:
    """Normalize ticket id and reject path-unsafe values."""
    if not ticket_id or not isinstance(ticket_id, str):
        raise ValueError("invalid ticket_id: empty")
    if "\x00" in ticket_id:
        raise ValueError("invalid ticket_id: path unsafe")
    normalized = ticket_id.strip().replace("_", "-")
    if ".." in normalized or "/" in normalized or "\\" in normalized:
        raise ValueError("invalid ticket_id: path unsafe")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\-]*", normalized):
        raise ValueError("invalid ticket_id: path unsafe")
    return normalized.upper() if re.fullmatch(r"M\d{3}-\d+", normalized, re.I) else normalized


def normalize_workflow_stage(agent_type: str, workflow_stage: str | None) -> str:
    """Map raw agent/stage strings to stable workflow stage keys."""
    if workflow_stage:
        raw = workflow_stage.strip()
        for pattern, stage in _STAGE_ALIASES:
            if pattern.match(raw):
                return stage
        return "unknown"
    raw = agent_type.strip()
    for pattern, stage in _STAGE_ALIASES:
        if pattern.match(raw):
            return stage
    return "unknown"


def infer_ticket_type(ticket_path: str | None, *, title: str | None = None) -> str:
    """Infer ticket_type from path/title (first match wins)."""
    path_lower = (ticket_path or "").lower()
    title_lower = (title or "").lower()
    if "bugfix" in path_lower or "bugfix" in title_lower or "fix:" in title_lower:
        return "bugfix"
    if "refactor" in path_lower or "refactor" in title_lower:
        return "refactor"
    if "/feature/" in path_lower or title_lower.startswith("feat:") or "feature" in title_lower:
        return "feature"
    return "generic"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _lock_for(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _file_locks_guard:
        if key not in _file_locks:
            _file_locks[key] = threading.Lock()
        return _file_locks[key]


def checkpoints_root_allowed(resolved: Path, raw: str | None = None) -> bool:
    """NFR-3: checkpoints root must resolve under repository root or cwd."""
    if raw is not None and ".." in Path(raw).parts:
        return False
    repo_root = find_repo_root().resolve()
    cwd = Path.cwd().resolve()
    for anchor in (repo_root, cwd):
        try:
            resolved.relative_to(anchor)
            return True
        except ValueError:
            continue
    return False


def _resolve_checkpoints_root(checkpoints_root: Path | None) -> Path:
    if checkpoints_root is not None:
        resolved = checkpoints_root.resolve()
        if not checkpoints_root_allowed(resolved):
            raise ValueError("checkpoints root must resolve inside repository or cwd")
        return resolved
    return (find_repo_root() / "project_board" / "checkpoints").resolve()


def _usage_file_path(checkpoints_root: Path, ticket_id: str) -> Path:
    return checkpoints_root / ticket_id / "token_usage.json"


def schema_size_tokens(tools: list[dict[str, Any]]) -> int:
    payload = json.dumps(tools, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return len(payload) // CHARS_PER_TOKEN


def context_efficiency(output_tokens: int, total_tokens: int) -> float:
    if total_tokens <= 0:
        return 0.0
    return round(output_tokens / total_tokens, 2)


def input_efficiency_ratio(input_tokens: int, schema_tokens: int) -> float:
    return round(input_tokens / max(schema_tokens, 1), 2)


def _coerce_non_negative_int(value: Any, field: str) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid token field {field}") from exc
    if n < 0:
        raise ValueError("negative token count")
    return n


def _usage_from_object(obj: Any) -> tuple[int, int] | None:
    usage = getattr(obj, "usage", None)
    if usage is None:
        usage = getattr(obj, "usage_metadata", None)
    if usage is None:
        return None
    if isinstance(usage, dict):
        inp = usage.get("input_tokens", usage.get("prompt_tokens"))
        out = usage.get("output_tokens", usage.get("completion_tokens"))
    else:
        inp = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None)
        out = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None)
    if inp is None or out is None:
        return None
    return _coerce_non_negative_int(inp, "input_tokens"), _coerce_non_negative_int(out, "output_tokens")


def extract_token_usage(prompt: str, framework_result: Any) -> tuple[int, int, str, str | None]:
    """Return (input_tokens, output_tokens, confidence, estimation_method)."""
    if isinstance(framework_result, dict):
        for key in ("usage", "usage_metadata"):
            nested = framework_result.get(key)
            if isinstance(nested, dict):
                inp = nested.get("input_tokens", nested.get("prompt_tokens"))
                out = nested.get("output_tokens", nested.get("completion_tokens"))
                if inp is not None and out is not None:
                    return (
                        _coerce_non_negative_int(inp, "input_tokens"),
                        _coerce_non_negative_int(out, "output_tokens"),
                        "exact",
                        None,
                    )
        if "input_tokens" in framework_result and "output_tokens" in framework_result:
            return (
                _coerce_non_negative_int(framework_result["input_tokens"], "input_tokens"),
                _coerce_non_negative_int(framework_result["output_tokens"], "output_tokens"),
                "exact",
                None,
            )

    from_object = _usage_from_object(framework_result)
    if from_object is not None:
        return from_object[0], from_object[1], "exact", None

    input_tokens = len(prompt.encode("utf-8")) // CHARS_PER_TOKEN
    if isinstance(framework_result, (dict, list)):
        response_text = json.dumps(framework_result, separators=(",", ":"), sort_keys=True)
    else:
        response_text = str(framework_result)
    output_tokens = len(response_text.encode("utf-8")) // CHARS_PER_TOKEN
    return input_tokens, output_tokens, "estimated", "char_div4"


def _compute_rollup(stages: dict[str, Any]) -> dict[str, Any]:
    total_tokens = sum(int(s.get("total_tokens", 0)) for s in stages.values())
    total_input = sum(int(s.get("input_tokens", 0)) for s in stages.values())
    total_output = sum(int(s.get("output_tokens", 0)) for s in stages.values())
    stage_count = len(stages)
    max_stage_key = ""
    max_stage_tokens = 0
    for key, stage in stages.items():
        stage_total = int(stage.get("total_tokens", 0))
        if stage_total >= max_stage_tokens:
            max_stage_tokens = stage_total
            max_stage_key = key
    avg = round(total_tokens / max(stage_count, 1), 2)
    return {
        "total_tokens": total_tokens,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "avg_tokens_per_stage": avg,
        "stage_count": stage_count,
        "max_stage_tokens": max_stage_tokens,
        "max_stage_key": max_stage_key,
    }


def _empty_document(
    ticket_id: str,
    *,
    ticket_type: str,
    ticket_path: str | None,
    now: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ticket_id": ticket_id,
        "ticket_type": ticket_type,
        "ticket_path": ticket_path,
        "created_at": now,
        "updated_at": now,
        "stages": {},
        "rollup": _compute_rollup({}),
        "outliers": [],
        "tool_category_state": None,
    }


def _load_existing(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {version!r}")
    return data


def record_stage_usage(
    ticket_id: str,
    *,
    agent_type: str,
    prompt: str,
    tools: list[dict[str, Any]],
    framework_result: Any,
    agent_run_id: str,
    workflow_stage: str | None = None,
    stage_key: str | None = None,
    ticket_path: str | None = None,
    ticket_type: str | None = None,
    checkpoints_root: Path | None = None,
    tool_category_state: dict[str, Any] | None = None,
) -> None:
    """Record one stage invocation and merge into ``token_usage.json``."""
    normalized_id = normalize_ticket_id(ticket_id)
    if not agent_run_id:
        raise ValueError("agent_run_id is required")

    if ticket_type is not None:
        if ticket_type not in ALLOWED_TICKET_TYPES:
            raise ValueError(f"invalid ticket_type: {ticket_type!r}")
        resolved_type = ticket_type
    else:
        resolved_type = infer_ticket_type(ticket_path)

    normalized_stage = normalize_workflow_stage(agent_type, workflow_stage)
    resolved_stage_key = stage_key or normalized_stage

    input_tokens, output_tokens, confidence, estimation_method = extract_token_usage(
        prompt, framework_result
    )
    total_tokens = input_tokens + output_tokens
    schema_tokens = schema_size_tokens(tools)

    stage_record = {
        "workflow_stage": normalized_stage,
        "agent_type": agent_type,
        "agent_run_id": agent_run_id,
        "recorded_at": _utc_now_iso(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "schema_size_tokens": schema_tokens,
        "context_efficiency": context_efficiency(output_tokens, total_tokens),
        "input_efficiency_ratio": input_efficiency_ratio(input_tokens, schema_tokens),
        "confidence": confidence,
        "estimation_method": estimation_method,
        "tool_category_state": tool_category_state,
    }

    root = _resolve_checkpoints_root(checkpoints_root)
    root.mkdir(parents=True, exist_ok=True)
    usage_path = _usage_file_path(root, normalized_id)
    usage_path.parent.mkdir(parents=True, exist_ok=True)

    now = _utc_now_iso()
    with _lock_for(usage_path):
        existing = _load_existing(usage_path)
        if existing:
            doc = existing
            resolved_type = doc.get("ticket_type", resolved_type)
            doc["updated_at"] = now
            if ticket_path and not doc.get("ticket_path"):
                doc["ticket_path"] = ticket_path
        else:
            doc = _empty_document(
                normalized_id,
                ticket_type=resolved_type,
                ticket_path=ticket_path,
                now=now,
            )

        stages: dict[str, Any] = doc.setdefault("stages", {})
        stages[resolved_stage_key] = stage_record
        doc["rollup"] = _compute_rollup(stages)
        doc["outliers"] = doc.get("outliers") or []

        usage_path.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

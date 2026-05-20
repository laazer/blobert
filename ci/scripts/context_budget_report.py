#!/usr/bin/env python3
"""Aggregate context budget usage across checkpoint ``token_usage.json`` files (M902-21)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from context_budget_tracker import checkpoints_root_allowed, find_repo_root  # noqa: E402

DEFAULT_CHECKPOINTS_ROOT = "project_board/checkpoints"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _median_total_tokens(values: list[int]) -> int:
    """Median for outlier baselines: average of two when n==2, else lower-middle for even n."""
    if not values:
        return 0
    ordered = sorted(values)
    n = len(ordered)
    if n % 2 == 1:
        return ordered[n // 2]
    if n == 2:
        return int(round((ordered[0] + ordered[1]) / 2))
    return ordered[n // 2 - 1]


def _checkpoints_root_allowed(resolved: Path, raw: str) -> bool:
    return checkpoints_root_allowed(resolved, raw)


def _resolve_checkpoints_root(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        resolved = path.resolve()
    else:
        cwd_candidate = (Path.cwd() / path).resolve()
        try:
            cwd_candidate.relative_to(Path.cwd().resolve())
            resolved = cwd_candidate
        except ValueError:
            resolved = (find_repo_root() / path).resolve()
    if not _checkpoints_root_allowed(resolved, raw):
        raise ValueError("checkpoints root must resolve inside repository or cwd")
    return resolved


def _ticket_rollup_total(data: dict[str, Any]) -> int | None:
    rollup = data.get("rollup")
    if not isinstance(rollup, dict):
        return None
    total = rollup.get("total_tokens")
    if total is None:
        return None
    try:
        return int(total)
    except (TypeError, ValueError):
        return None


def _collect_usage_files(root: Path, milestone: str | None) -> list[Path]:
    files: list[Path] = []
    if not root.is_dir():
        return files
    for usage_file in sorted(root.rglob("token_usage.json")):
        if milestone:
            parent_chain = "/".join(usage_file.relative_to(root).parts[:-1]).lower()
            if milestone.lower() not in parent_chain and milestone.lower() not in usage_file.parent.name.lower():
                continue
        files.append(usage_file)
    return files


def build_report(checkpoints_root: Path, *, milestone: str | None = None) -> dict[str, Any]:
    totals_by_agent: dict[str, int] = {}
    totals_by_stage: dict[str, int] = {}
    tickets: list[dict[str, Any]] = []
    context_efficiencies: list[float] = []
    input_efficiencies: list[float] = []
    with_cat: list[int] = []
    without_cat: list[int] = []

    for usage_file in _collect_usage_files(checkpoints_root, milestone):
        try:
            data = json.loads(usage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        ticket_id = data.get("ticket_id") or usage_file.parent.name
        ticket_type = data.get("ticket_type") or "generic"
        total = _ticket_rollup_total(data)
        if total is None:
            continue

        rollup = data.get("rollup") or {}
        tickets.append(
            {
                "ticket_id": ticket_id,
                "ticket_type": ticket_type,
                "total_tokens": total,
                "max_stage_key": rollup.get("max_stage_key") or "",
            }
        )

        for stage in (data.get("stages") or {}).values():
            if not isinstance(stage, dict):
                continue
            agent = str(stage.get("agent_type", "unknown"))
            workflow = str(stage.get("workflow_stage", "unknown"))
            stage_total = int(stage.get("total_tokens", 0))
            totals_by_agent[agent] = totals_by_agent.get(agent, 0) + stage_total
            totals_by_stage[workflow] = totals_by_stage.get(workflow, 0) + stage_total
            if "context_efficiency" in stage:
                context_efficiencies.append(float(stage["context_efficiency"]))
            if "input_efficiency_ratio" in stage:
                input_efficiencies.append(float(stage["input_efficiency_ratio"]))
            tool_state = stage.get("tool_category_state")
            if isinstance(tool_state, dict) and tool_state.get("categorization_active"):
                with_cat.append(stage_total)
            else:
                without_cat.append(stage_total)

    averages_by_type: dict[str, dict[str, Any]] = {}
    by_type: dict[str, list[int]] = {}
    for row in tickets:
        by_type.setdefault(row["ticket_type"], []).append(row["total_tokens"])
    for ttype, values in by_type.items():
        averages_by_type[ttype] = {
            "median_total_tokens": _median_total_tokens(values),
            "mean_total_tokens": round(sum(values) / len(values), 2),
            "ticket_count": len(values),
        }

    outliers: list[dict[str, Any]] = []
    for row in tickets:
        type_stats = averages_by_type.get(row["ticket_type"])
        if not type_stats or type_stats["ticket_count"] < 2:
            continue
        median = type_stats["median_total_tokens"]
        if row["total_tokens"] > 2 * median:
            outliers.append(row)

    top_10 = sorted(
        tickets,
        key=lambda r: (-r["total_tokens"], r["ticket_id"]),
    )[:10]

    tool_category_impact: dict[str, Any] | None = None
    if with_cat:
        with_avg = round(sum(with_cat) / len(with_cat), 2)
        without_avg = round(sum(without_cat) / max(len(without_cat), 1), 2)
        reduction = 0.0
        if without_avg > 0:
            reduction = round(100.0 * (without_avg - with_avg) / without_avg, 2)
        tool_category_impact = {
            "with_categorization_avg": with_avg,
            "without_categorization_avg": without_avg,
            "reduction_percent": reduction,
        }

    mean_context = (
        round(sum(context_efficiencies) / len(context_efficiencies), 2)
        if context_efficiencies
        else 0.0
    )
    mean_input = (
        round(sum(input_efficiencies) / len(input_efficiencies), 2)
        if input_efficiencies
        else 0.0
    )

    total_tokens_all = sum(row["total_tokens"] for row in tickets)

    return {
        "generated_at": _utc_now_iso(),
        "tickets_scanned": len(tickets),
        "total_tokens_all": total_tokens_all,
        "totals_by_agent_type": totals_by_agent,
        "totals_by_workflow_stage": totals_by_stage,
        "averages_by_ticket_type": averages_by_type,
        "top_10_consumers": top_10,
        "efficiency_summary": {
            "mean_context_efficiency": mean_context,
            "mean_input_efficiency_ratio": mean_input,
        },
        "outliers": outliers,
        "tool_category_impact": tool_category_impact,
    }


def format_human_summary(report: dict[str, Any], *, run_id: str = "run") -> str:
    lines = [f"Context Budget Summary — {run_id}"]
    total_tokens = report.get("total_tokens_all")
    if total_tokens is None:
        total_tokens = sum(row["total_tokens"] for row in report.get("top_10_consumers", []))
    lines.append(f"Totals: {total_tokens} tokens across {report.get('tickets_scanned', 0)} ticket(s)")
    stage_totals = report.get("totals_by_workflow_stage") or {}
    top_stages = sorted(stage_totals.items(), key=lambda kv: -kv[1])[:3]
    if top_stages:
        lines.append("Top stages: " + ", ".join(f"{k}={v}" for k, v in top_stages))
    top_tickets = report.get("top_10_consumers", [])[:5]
    if top_tickets:
        lines.append(
            "Top tickets: "
            + ", ".join(f"{r['ticket_id']}({r['total_tokens']})" for r in top_tickets)
        )
    outlier_ids = [r["ticket_id"] for r in report.get("outliers", [])]
    lines.append(f"Outliers: {', '.join(outlier_ids) if outlier_ids else 'None'}")
    impact = report.get("tool_category_impact")
    if impact:
        lines.append(
            f"Tool categorization: {impact.get('reduction_percent', 0)}% reduction "
            f"(with={impact.get('with_categorization_avg')}, without={impact.get('without_categorization_avg')})"
        )
    else:
        lines.append("Tool categorization: N/A (M902-18 inactive)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate token usage checkpoints")
    parser.add_argument(
        "--checkpoints-root",
        default=DEFAULT_CHECKPOINTS_ROOT,
        help="Root directory to scan for token_usage.json",
    )
    parser.add_argument(
        "--milestone",
        default=None,
        help="Only include tickets whose checkpoint path contains this substring",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report to stdout")
    parser.add_argument("--run-id", default="run", help="Run id for human summary header")

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    try:
        root = _resolve_checkpoints_root(args.checkpoints_root)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = build_report(root, milestone=args.milestone)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if report["tickets_scanned"] == 0:
            print("No token usage data found.")
        else:
            print(format_human_summary(report, run_id=args.run_id))

    return 0


if __name__ == "__main__":
    sys.exit(main())

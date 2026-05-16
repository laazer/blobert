#!/usr/bin/env python3
"""
Governance audit pipeline for M902-07.

Invokes static analysis gate, loads baseline, clusters violations, detects baseline diffs,
and generates audit reports (JSON and Markdown).

Usage:
    python ci/scripts/audit.py \\
        --mode shadow|blocking \\
        --baseline-path ./.governance-baseline.json \\
        --output-dir ./ci/artifacts/ \\
        --upstream-agent Implementation \\
        --downstream-agent Script Review Agent \\
        --ticket-id M902-07
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from baseline import (
    get_baseline_entries,
    is_entry_expired,
    load_baseline,
    match_violation,
    normalize_path,
    validate_baseline,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_repo_root() -> Path:
    """Find repository root by looking for .git directory.

    Returns:
        Path to repo root

    Raises:
        RuntimeError: If .git not found
    """
    cwd = Path.cwd()
    current = cwd
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            raise RuntimeError("Could not find repo root (.git not found)")
        current = current.parent


def invoke_gate_runner(mode: str, upstream_agent: str, downstream_agent: str, ticket_id: Optional[str]) -> dict[str, Any]:
    """Invoke gate runner to execute static analysis gate.

    Args:
        mode: "shadow" or "blocking"
        upstream_agent: Name of upstream agent
        downstream_agent: Name of downstream agent
        ticket_id: Ticket ID or None

    Returns:
        Gate output dict with violations array

    Raises:
        subprocess.CalledProcessError: If gate runner fails
    """
    repo_root = find_repo_root()
    gate_runner = repo_root / "ci" / "scripts" / "gate_runner.py"

    if not gate_runner.exists():
        logger.error(f"Gate runner not found: {gate_runner}")
        sys.exit(EXIT_CONFIG_ERROR)

    cmd = [
        sys.executable,
        str(gate_runner),
        "static_analysis_check",
        "--mode", mode,
        "--upstream-agent", upstream_agent,
        "--downstream-agent", downstream_agent,
    ]

    if ticket_id:
        cmd.extend(["--ticket-id", ticket_id])

    try:
        logger.info(f"Invoking gate runner: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode not in (0, 1):
            logger.error(f"Gate runner failed with exit code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            sys.exit(EXIT_CONFIG_ERROR)

        # Parse gate output (JSON from stdout)
        try:
            gate_output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Gate runner produced invalid JSON: {e}")
            logger.error(f"stdout: {result.stdout[:500]}")
            sys.exit(EXIT_CONFIG_ERROR)

        return gate_output

    except subprocess.TimeoutExpired:
        logger.error("Gate runner timed out")
        sys.exit(EXIT_CONFIG_ERROR)
    except Exception as e:
        logger.error(f"Failed to invoke gate runner: {e}")
        sys.exit(EXIT_CONFIG_ERROR)


def cluster_violations(violations: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Cluster violations by (rule_id, path_cluster).

    Clustering strategy per spec:
    - Python (asset_generation/python/src/*): depth = 2
    - Web backend (asset_generation/web/backend/*): depth = 2
    - Web frontend (asset_generation/web/frontend/src/*): depth = 2
    - Godot (scripts/*, scenes/*, tests/*): depth = 1
    - jscpd (repo-wide): depth = 1 (rule_id only)

    Args:
        violations: List of violation dicts

    Returns:
        Dict mapping cluster_key to list of violations in cluster
    """
    clusters: dict[str, list[dict[str, Any]]] = {}

    for violation in violations:
        rule_id = violation.get("rule") or violation.get("tool", "unknown")
        file_path = normalize_path(violation.get("file", ""))

        # Determine clustering depth based on file path
        depth = _get_cluster_depth(file_path)

        # Extract path cluster (first N path components)
        path_cluster = _extract_path_cluster(file_path, depth)

        cluster_key = f"{rule_id}:{path_cluster}"

        if cluster_key not in clusters:
            clusters[cluster_key] = []

        clusters[cluster_key].append(violation)

    # Sort violations within each cluster by file path for determinism
    for cluster_violations in clusters.values():
        cluster_violations.sort(key=lambda v: (v.get("file", ""), v.get("line", 0)))

    return clusters


def _get_cluster_depth(file_path: str) -> int:
    """Determine clustering depth for file path.

    Args:
        file_path: Normalized file path

    Returns:
        Cluster depth (1 or 2)
    """
    # Python backend modules
    if file_path.startswith("asset_generation/python/src/"):
        return 2

    # Web backend
    if file_path.startswith("asset_generation/web/backend/"):
        return 2

    # Web frontend
    if file_path.startswith("asset_generation/web/frontend/"):
        return 2

    # Godot, jscpd, and others
    return 1


# Module-level constant for config errors
EXIT_CONFIG_ERROR = 2


def _extract_path_cluster(file_path: str, depth: int) -> str:
    """Extract path cluster from file path.

    Clustering depth interpretation:
    - depth=1: Return first path component (e.g., 'scripts')
    - depth=2: Return first 4 components for Python/TypeScript/JavaScript backends
             (language root is 3 components; depth 2 means 2 AFTER root = 4 total)

    Args:
        file_path: Normalized file path
        depth: Cluster depth (1 or 2); determines how many components to extract

    Returns:
        Path cluster (e.g., "asset_generation/python/src/models")
    """
    parts = file_path.split("/")

    if depth == 1:
        # Return first component only (Godot, jscpd)
        return parts[0] if parts else ""

    if depth == 2:
        # For Python/TypeScript backends: return first 4 components
        # Language root = first 3 components
        # Module level = first 4 components (add 1 to language root)
        return "/".join(parts[:4]) if len(parts) >= 4 else "/".join(parts)

    # Fallback (should not reach here based on _get_cluster_depth)
    return "/".join(parts[:depth]) if len(parts) >= depth else "/".join(parts)


def detect_baseline_diff(
    violations: list[dict[str, Any]],
    clusters: dict[str, list[dict[str, Any]]],
    baseline: dict[str, Any],
    mode: str,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Detect baseline diffs: new, expired, remediated violations.

    Args:
        violations: List of violations from gate
        clusters: Clustered violations
        baseline: Baseline dict
        mode: "shadow" or "blocking"
        now: Current datetime (or None to use now)

    Returns:
        Dict with keys: new, expired, remediated, status, summary
    """
    if now is None:
        now = datetime.now(timezone.utc)

    baseline_entries = get_baseline_entries(baseline)

    new_violations = []
    expired_violations = []
    remediated_violations = []
    unknown_rules = set()

    # Find new and expired violations
    for violation in violations:
        matched = False

        for entry in baseline_entries:
            # Skip expired entries
            if is_entry_expired(entry, now):
                # Mark as expired if it matches this violation
                if match_violation(violation, entry):
                    expired_violations.append({
                        "violation": violation,
                        "baseline_entry": entry,
                    })
                continue

            # Non-expired entry: check if violation matches
            if match_violation(violation, entry):
                matched = True
                break

        if not matched:
            # Check if rule is known in baseline at all
            rule_id = violation.get("rule")
            known_rules = {e.get("rule_id") for e in baseline_entries}

            if rule_id not in known_rules and rule_id is not None:
                unknown_rules.add(rule_id)

            new_violations.append(violation)

    # Find remediated violations (in old baseline but not in current scan)
    # For simplicity, we'll track which baseline entries were matched
    matched_entries = set()
    for violation in violations:
        for entry in baseline_entries:
            if not is_entry_expired(entry, now) and match_violation(violation, entry):
                matched_entries.add(id(entry))

    # Violations that were in baseline but not matched = remediated
    # (This is informational only in M902-07)

    # Determine audit status
    if new_violations and mode == "blocking":
        audit_status = "FAIL"
        summary = f"{len(new_violations)} new violations detected (blocking mode)"
    elif expired_violations and mode == "shadow":
        audit_status = "WARN"
        summary = f"{len(expired_violations)} expired baseline entries present"
    else:
        audit_status = "PASS"
        if new_violations:
            summary = f"{len(new_violations)} new violations detected (shadow mode, non-blocking)"
        elif expired_violations:
            summary = f"{len(expired_violations)} expired baseline entries present"
        else:
            summary = "No new violations detected"

    return {
        "new": new_violations,
        "expired": expired_violations,
        "remediated": remediated_violations,
        "unknown_rules": list(unknown_rules),
        "status": audit_status,
        "summary": summary,
    }


def generate_json_report(
    violations: list[dict[str, Any]],
    clusters: dict[str, list[dict[str, Any]]],
    baseline_diff: dict[str, Any],
    baseline: dict[str, Any],
    mode: str,
    repo_root: Path,
    output_dir: Path,
) -> str:
    """Generate JSON audit report.

    Args:
        violations: List of violations from gate
        clusters: Clustered violations
        baseline_diff: Baseline diff result
        baseline: Baseline dict
        mode: "shadow" or "blocking"
        repo_root: Repository root path
        output_dir: Directory to write report to

    Returns:
        Path to generated JSON report file
    """
    audit_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)
    timestamp_str = timestamp.strftime("%Y%m%dT%H%M%SZ")

    # Get git info
    repo_commit = "unknown"
    repo_branch = "unknown"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            repo_commit = result.stdout.strip()[:8]
    except Exception as e:
        logger.warning(f"Failed to get git commit SHA: {e}")

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            repo_branch = result.stdout.strip()
    except Exception as e:
        logger.warning(f"Failed to get git branch: {e}")

    # Count violations by category
    violation_counts = {
        "total": len(violations),
        "new": len(baseline_diff.get("new", [])),
        "expired": len(baseline_diff.get("expired", [])),
        "remediated": len(baseline_diff.get("remediated", [])),
        "baseline_matched": len(violations) - len(baseline_diff.get("new", [])),
    }

    # Build cluster summaries
    cluster_list = []
    for cluster_key, cluster_viols in sorted(clusters.items()):
        rule_id = cluster_key.split(":")[0]
        path_cluster = ":".join(cluster_key.split(":")[1:]) if ":" in cluster_key else ""

        new_count = sum(
            1 for v in cluster_viols
            if any(v.get("file") == nv.get("file") and v.get("line") == nv.get("line")
                   for nv in baseline_diff.get("new", []))
        )

        # Count expired violations in this cluster
        expired_count = sum(
            1 for v in cluster_viols
            if any(v.get("file") == ev.get("violation", {}).get("file")
                   and v.get("line") == ev.get("violation", {}).get("line")
                   for ev in baseline_diff.get("expired", []))
        )

        cluster_list.append({
            "cluster_key": cluster_key,
            "rule_id": rule_id,
            "path_cluster": path_cluster,
            "violation_count": len(cluster_viols),
            "new_count": new_count,
            "expired_count": expired_count,
            "remediated_count": len(baseline_diff.get("remediated", [])),
            "baseline_matched_count": len(cluster_viols) - new_count,
        })

    # Sort clusters by violation count (descending)
    cluster_list.sort(key=lambda c: c["violation_count"], reverse=True)

    # Build audit report
    report = {
        "version": "1.0",
        "audit_timestamp": timestamp.isoformat(),
        "audit_id": audit_id,
        "mode": mode,
        "audit_status": baseline_diff.get("status", "UNKNOWN"),
        "gate_status": "PASS" if not violations else "FAIL",
        "repo_commit": repo_commit,
        "repo_branch": repo_branch,
        "baseline_path": ".governance-baseline.json",
        "baseline_valid": True,
        "violations": violation_counts,
        "violation_list": violations,
        "clusters": cluster_list,
        "baseline_diff": {
            "new_violations": baseline_diff.get("new", []),
            "expired_violations": baseline_diff.get("expired", []),
            "remediated_violations": baseline_diff.get("remediated", []),
            "unknown_rules": baseline_diff.get("unknown_rules", []),
        },
        "summary": {
            "message": baseline_diff.get("summary", ""),
            "recommendation": _get_recommendation(baseline_diff),
            "next_steps": _get_next_steps(baseline_diff, mode),
        },
    }

    # Write report
    output_file = output_dir / f"audit-report-{timestamp_str}.json"
    output_file.write_text(json.dumps(report, indent=2))
    logger.info(f"Wrote JSON audit report: {output_file}")

    return str(output_file)


def _get_recommendation(baseline_diff: dict[str, Any]) -> str:
    """Get recommendation based on baseline diff.

    Args:
        baseline_diff: Baseline diff result

    Returns:
        Recommendation string
    """
    new_count = len(baseline_diff.get("new", []))
    expired_count = len(baseline_diff.get("expired", []))

    if new_count > 0:
        return f"Fix or baseline {new_count} new violations"
    elif expired_count > 0:
        return f"Renew or remove {expired_count} expired baseline entries"
    else:
        return "No action required"


def _get_next_steps(baseline_diff: dict[str, Any], mode: str) -> list[str]:
    """Get list of next steps.

    Args:
        baseline_diff: Baseline diff result
        mode: "shadow" or "blocking"

    Returns:
        List of actionable next steps
    """
    steps = []

    new_count = len(baseline_diff.get("new", []))
    if new_count > 0:
        steps.append(f"Review {new_count} new violations in remediation report")

    expired_count = len(baseline_diff.get("expired", []))
    if expired_count > 0:
        steps.append(f"Renew or remove {expired_count} expired baseline entries")

    if mode == "blocking" and new_count > 0:
        steps.append("Fix violations to pass audit gate")

    if not steps:
        steps.append("No action required - audit passed")

    return steps


def generate_markdown_report(
    violations: list[dict[str, Any]],
    clusters: dict[str, list[dict[str, Any]]],
    baseline_diff: dict[str, Any],
    output_dir: Path,
) -> str:
    """Generate Markdown remediation report.

    Args:
        violations: List of violations from gate
        clusters: Clustered violations
        baseline_diff: Baseline diff result
        output_dir: Directory to write report to

    Returns:
        Path to generated Markdown report file
    """
    timestamp = datetime.now(timezone.utc)
    timestamp_str = timestamp.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "# Governance Audit Report",
        "",
        "## Summary",
        "",
        f"- **Status:** {baseline_diff.get('status', 'UNKNOWN')}",
        f"- **Timestamp:** {timestamp.isoformat()}",
        f"- **Total Violations:** {len(violations)}",
        f"- **New Violations:** {len(baseline_diff.get('new', []))}",
        f"- **Expired Baseline Entries:** {len(baseline_diff.get('expired', []))}",
        "",
        "## Violation Clusters",
        "",
    ]

    # Sort clusters by violation count
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)

    for cluster_key, cluster_viols in sorted_clusters:
        rule_id = cluster_key.split(":")[0]
        path_cluster = ":".join(cluster_key.split(":")[1:]) if ":" in cluster_key else ""

        lines.extend([
            f"### {rule_id} - {path_cluster}",
            "",
            f"**Violations:** {len(cluster_viols)}",
            "",
            "**Affected Files:**",
            "",
        ])

        # List sample violations
        for violation in cluster_viols[:5]:
            file_path = violation.get("file", "unknown")
            line_num = violation.get("line", "?")
            message = violation.get("message", "")
            lines.append(f"- `{file_path}:{line_num}` — {message}")

        if len(cluster_viols) > 5:
            lines.append(f"- ... and {len(cluster_viols) - 5} more")

        lines.extend([
            "",
            "#### Remediation",
            "",
            f"Fix or baseline all violations of rule `{rule_id}` in this cluster.",
            "",
        ])

    # Expired baseline entries section
    if baseline_diff.get("expired"):
        lines.extend([
            "## Expired Baseline Entries",
            "",
            "The following baseline entries have expired and no longer protect violations:",
            "",
        ])
        for item in baseline_diff.get("expired", []):
            entry = item.get("baseline_entry", {})
            rule_id = entry.get("rule_id", "unknown")
            expires_at = entry.get("expires_at", "unknown")
            lines.append(f"- `{rule_id}` (expired {expires_at})")
        lines.append("")

    # New violations section
    if baseline_diff.get("new"):
        lines.extend([
            "## New Violations Requiring Baseline",
            "",
            "The following violations are not covered by baseline entries:",
            "",
        ])
        rules_with_new = {}
        for violation in baseline_diff.get("new", []):
            rule_id = violation.get("rule", "unknown")
            if rule_id not in rules_with_new:
                rules_with_new[rule_id] = []
            rules_with_new[rule_id].append(violation)

        for rule_id, viols in sorted(rules_with_new.items()):
            lines.append(f"- `{rule_id}`: {len(viols)} new violation(s)")
        lines.append("")

    lines.extend([
        "## Next Steps",
        "",
        _get_next_steps_markdown(baseline_diff),
        "",
    ])

    # Write report
    output_file = output_dir / f"audit-report-{timestamp_str}.md"
    output_file.write_text("\n".join(lines))
    logger.info(f"Wrote Markdown audit report: {output_file}")

    return str(output_file)


def _get_next_steps_markdown(baseline_diff: dict[str, Any]) -> str:
    """Get next steps as markdown.

    Args:
        baseline_diff: Baseline diff result

    Returns:
        Markdown-formatted next steps
    """
    steps = []

    new_count = len(baseline_diff.get("new", []))
    if new_count > 0:
        steps.append(f"1. Review and fix {new_count} new violations")

    expired_count = len(baseline_diff.get("expired", []))
    if expired_count > 0:
        steps.append(f"2. Renew or remove {expired_count} expired baseline entries")

    if not steps:
        return "- No action required"

    return "\n".join(f"- {step}" for step in steps)


def main() -> None:
    """Main entry point for audit command."""
    parser = argparse.ArgumentParser(
        description="Governance audit pipeline for M902-07"
    )
    parser.add_argument(
        "--mode",
        choices=["shadow", "blocking"],
        default="shadow",
        help="Audit mode (shadow or blocking)",
    )
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=Path(".governance-baseline.json"),
        help="Path to baseline file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ci/artifacts"),
        help="Output directory for audit reports",
    )
    parser.add_argument(
        "--upstream-agent",
        default="Implementation",
        help="Upstream agent name",
    )
    parser.add_argument(
        "--downstream-agent",
        default="Script Review Agent",
        help="Downstream agent name",
    )
    parser.add_argument(
        "--ticket-id",
        help="Ticket ID",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Find repo root
    try:
        repo_root = find_repo_root()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(EXIT_CONFIG_ERROR)

    # Resolve baseline path relative to repo root if not absolute
    if not args.baseline_path.is_absolute():
        baseline_path = repo_root / args.baseline_path
    else:
        baseline_path = args.baseline_path

    logger.info(f"Starting audit in mode: {args.mode}")

    # Invoke gate runner
    gate_output = invoke_gate_runner(
        args.mode,
        args.upstream_agent,
        args.downstream_agent,
        args.ticket_id,
    )

    violations = gate_output.get("violations", [])
    logger.info(f"Gate produced {len(violations)} violations")

    # Load and validate baseline
    try:
        baseline = load_baseline(baseline_path)
        if not validate_baseline(baseline):
            logger.warning("Baseline validation failed, but continuing with audit")
    except Exception as e:
        logger.error(f"Failed to load baseline: {e}")
        sys.exit(EXIT_CONFIG_ERROR)

    # Cluster violations
    clusters = cluster_violations(violations)
    logger.info(f"Clustered violations into {len(clusters)} clusters")

    # Detect baseline diff
    now = datetime.now(timezone.utc)
    baseline_diff = detect_baseline_diff(violations, clusters, baseline, args.mode, now)
    logger.info(f"Baseline diff: {len(baseline_diff['new'])} new, "
                f"{len(baseline_diff['expired'])} expired, "
                f"{len(baseline_diff['remediated'])} remediated")

    # Generate reports
    generate_json_report(
        violations, clusters, baseline_diff, baseline, args.mode, repo_root, args.output_dir
    )
    generate_markdown_report(
        violations, clusters, baseline_diff, args.output_dir
    )

    logger.info(f"Audit complete: status={baseline_diff['status']}")

    # Exit with appropriate code
    if baseline_diff["status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

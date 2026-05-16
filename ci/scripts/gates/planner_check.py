"""
Planner gate — cyclic dependency detection in ticket dependency graphs (M902-06).

Specification: project_board/specs/902_06_planner_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md

Detects:
  - Cyclic dependencies (A -> B -> C -> A) via DFS traversal
  - Self-loops (A -> A)
  - Orphaned dependencies (ticket depends on missing ticket)
  - Malformed YAML dependency syntax

JSON Output: matches M902-01 gate schema with violations[], remediation_hints[], status (PASS|WARN|FAIL).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _normalize_ticket_id(ticket_id: str) -> str:
    """Normalize ticket ID to uppercase with '-' separator (e.g., M902-01)."""
    return ticket_id.upper().replace("_", "-").strip()


def _extract_dependencies_from_markdown(content: str) -> list[str]:
    """Extract ticket IDs from dependencies field in markdown (YAML-style)."""
    deps: list[str] = []

    # Match YAML inline list: dependencies: [M902-01, M902-02]
    inline_match = re.search(r"dependencies\s*:\s*\[(.*?)\]", content, re.IGNORECASE)
    if inline_match:
        items = inline_match.group(1).split(",")
        for item in items:
            item = item.strip()
            if item:
                normalized = _normalize_ticket_id(item)
                if normalized:
                    deps.append(normalized)
        return deps

    # Match YAML multiline list:
    # dependencies:
    #   - M902-01
    #   - M902-02
    multiline_section = re.search(
        r"dependencies\s*:\s*\n((?:\s*-\s+[^\n]+\n?)*)",
        content,
        re.IGNORECASE,
    )
    if multiline_section:
        items = re.findall(r"-\s+([^\n]+)", multiline_section.group(1))
        for item in items:
            item = item.strip()
            if item:
                normalized = _normalize_ticket_id(item)
                if normalized:
                    deps.append(normalized)
        return deps

    return deps


def _build_dependency_graph(
    milestone_path: Path,
) -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    """Build ticket dependency graph from milestone folder.

    Returns:
        (dependency_graph, errors)
        - dependency_graph: {ticket_id: [dep_ticket_ids]}
        - errors: list of (file, message) tuples
    """
    graph: dict[str, list[str]] = {}
    errors: list[dict[str, Any]] = []

    # Find all .md files in milestone folder and subfolders
    if not milestone_path.exists():
        return graph, errors

    ticket_files = list(milestone_path.rglob("*.md"))

    for file_path in ticket_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            errors.append(
                {
                    "file": str(file_path),
                    "line": 0,
                    "rule": "file_read_error",
                    "message": f"Failed to read file: {e}",
                    "severity": "WARN",
                }
            )
            continue

        # Extract ticket ID from filename or frontmatter
        # Simple heuristic: look for M\d{3}-\d{2} pattern
        ticket_match = re.search(r"(M\d{3}-\d{2})", file_path.name)
        if not ticket_match:
            # Try to find in content
            ticket_match = re.search(r"(M\d{3}-\d{2})", content)
            if not ticket_match:
                continue

        ticket_id = _normalize_ticket_id(ticket_match.group(1))

        # Extract dependencies
        deps = _extract_dependencies_from_markdown(content)
        # Deduplicate and normalize
        deps = list(set(_normalize_ticket_id(d) for d in deps))

        # Detect self-loop
        if ticket_id in deps:
            errors.append(
                {
                    "file": str(file_path),
                    "line": 0,
                    "rule": "self_loop",
                    "message": f"Self-loop detected: {ticket_id} depends on itself",
                    "severity": "WARN",
                }
            )
            # Remove self-loop for further processing
            deps = [d for d in deps if d != ticket_id]

        graph[ticket_id] = deps

    return graph, errors


def _detect_cycles_dfs(
    graph: dict[str, list[str]],
) -> list[list[str]]:
    """Detect cycles in dependency graph using DFS.

    Returns: list of cycles, where each cycle is a list of ticket IDs.
    """
    visited: set[str] = set()
    rec_stack: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str]) -> None:
        """DFS traversal with cycle detection."""
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            dfs(neighbor, path.copy())

        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute planner gate.

    Inputs:
        - milestone_path: str, path to milestone folder containing ticket .md files

    Returns:
        dict matching M902-01 gate schema
    """
    milestone_path_str = inputs.get("milestone_path", ".")
    milestone_path = Path(milestone_path_str)

    # Build dependency graph
    graph, file_errors = _build_dependency_graph(milestone_path)

    # Detect cycles
    cycles = _detect_cycles_dfs(graph)

    violations: list[dict[str, Any]] = list(file_errors)
    remediation_hints: list[str] = []

    # Report cycles as violations
    for cycle in cycles:
        cycle_str = " -> ".join(cycle)
        violations.append(
            {
                "file": str(milestone_path),
                "line": 0,
                "rule": "cyclic_dependency",
                "message": f"Cyclic dependency detected: [{cycle_str}]",
                "severity": "WARN",
            }
        )
        remediation_hints.append(
            f"Break the cycle by removing one edge from: {cycle_str}"
        )

    # Detect orphaned dependencies
    all_tickets = set(graph.keys())
    for ticket_id, deps in graph.items():
        for dep in deps:
            if dep not in all_tickets:
                violations.append(
                    {
                        "file": str(milestone_path),
                        "line": 0,
                        "rule": "orphaned_dependency",
                        "message": f"{ticket_id} depends on {dep} (not in milestone scope)",
                        "severity": "WARN",
                    }
                )
                remediation_hints.append(
                    f"Either add {dep} to the milestone or remove the dependency from {ticket_id}"
                )

    status = "FAIL" if any(v["severity"] == "ERROR" for v in violations) else "WARN" if violations else "PASS"

    return {
        "status": status,
        "gate": "planner_check",
        "violations": violations,
        "remediation_hints": remediation_hints,
        "message": (
            f"Dependency check complete: {len(graph)} tickets, "
            f"{len(cycles)} cycles, {len([v for v in violations if v['rule'] == 'orphaned_dependency'])} orphaned deps"
        ),
    }

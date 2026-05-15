# Title

Workflow visualization and runbook updates (Agent → Gate → Agent)

# Context

The MVP requires regenerating workflow diagrams to show validation gates, early exits, escalation paths, static analysis insertion points, governance hooks, and audit integration, using valid Mermaid. Operator documentation for humans/agents must reflect the new flow.

# Scope

- Update the Mermaid diagram(s) in the governing workflow doc(s) (likely `CLAUDE.md`, `.claude/skills/autopilot/SKILL.md`, `agent_context/agents/readme.md`, or milestone specs—pick the canonical locations already referenced by agents).
- Ensure diagrams match the implemented ordering: static analysis after implementation agents, before diff-cover and review stages, as per MVP.
- Add a short “how to run gates locally” section referencing the new commands (link-only if detailed elsewhere).

# Acceptance Criteria

- At least one checked-in Mermaid diagram renders in GitHub and matches the implemented pipeline at a high level.
- Autopilot / agent runbooks mention where gates occur and what artifacts are required to pass.
- No contradictions with `CLAUDE.md` command source-of-truth ordering; if changes are needed, update `CLAUDE.md` minimally and intentionally.

# Agent Execution Prompt

Update workflow visualization and agent runbooks for gated handoffs.

Goal: Align documentation diagrams and agent instructions with Milestone 902 implementations without rewriting unrelated process.

Constraints:
- Valid Mermaid syntax only.
- Do not add large new documentation files unless necessary; prefer updating existing canonical docs.

Expected output:
- Doc edits + diagram updates + links to gate commands.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (unknown canonical doc location)
- What assumption cannot be verified? (implemented pipeline differs from MVP diagram)
- What ambiguity prevents completion? (multiple competing workflow docs)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about which doc is authoritative for autopilot?
- What decision needs to be made about diagram granularity (one mega chart vs multiple)?
- What are the possible interpretations of “early exits” in the current toolchain?

# Dependencies

- Validation gate framework for multi-agent handoffs (orchestration, routing, remediation)
- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling
- Handoff metadata schema and risk-based escalation (PASS/WARN/FAIL/ESCALATE)

# Definition of Done

- Diagram(s) merged and reviewed for accuracy against the implemented runner order.
- Runbook updates merged with explicit gate checkpoints.

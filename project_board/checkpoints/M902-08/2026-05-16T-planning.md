# M902-08 Workflow Visualization and Agent Runbook Updates — PLANNING

**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md

**Stage:** PLANNING → SPECIFICATION

**Date:** 2026-05-16

---

## Ambiguities Resolved (Checkpoint Protocol)

### 1. Canonical Documentation Locations for Workflow Diagrams

**Would have asked:** Where is the authoritative location for workflow diagrams? (CLAUDE.md, agent_context/agents/readme.md, milestone README, new file?)

**Assumption made:** 
- Primary location for MVP workflow diagram: `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` (already exists, currently lists ticket summaries and tool config)
- Secondary location if needed: agent-facing runbook in CLAUDE.md "Common Workflows" section (but this is minimal, command-focused)
- No dedicated agent_context/agents/readme.md exists; search found no such file
- Proposal: Update milestone README with a Mermaid diagram showing Agent → Gate → Agent flow, then link from CLAUDE.md if needed for discoverability

**Confidence:** HIGH (milestone README is already the gathering point for M902 documentation per existing structure)

---

### 2. Diagram Scope: Single Mega Chart vs Multiple Focused Diagrams

**Would have asked:** Should we have one comprehensive workflow diagram or multiple per-stage diagrams?

**Assumption made:**
- Create ONE primary diagram in milestone README showing the full agent → gate → agent handoff cycle with all 7 completed and 1 active ticket stages
- Keep it high-level (planner/spec/test/implementation/review/learning/complete) with inset notes on gate insertion points
- Do NOT create separate per-stage diagrams unless they fit organically into existing docs
- Rationale: Single diagram is easier to maintain, less duplication; readers can click through to spec for details

**Confidence:** MEDIUM (could be challenged if readers prefer granular diagrams, but scope constraint says "do not add large new documentation files unless necessary")

---

### 3. What "Early Exits" and "Escalation Paths" Mean in This Context

**Would have asked:** Does "early exits" mean test failures that block implementation? Does "escalation paths" mean routing back to agent or human escalation?

**Assumption made:**
- "Early exits" = FAIL gates that cause work to route back to originating agent (e.g., spec fails completeness check → back to Spec Agent)
- "Escalation paths" = ESCALATE gates that emit advisory metadata (M902-04 handoff metadata with escalation_reasons) and may trigger human review in M903+
- In M902 diagram: show both as distinct box/node colors (FAIL = red, ESCALATE = yellow, PASS = green)
- Links to actual gate exit codes and remediation logic in specs (M902-01, M902-04)

**Confidence:** MEDIUM-HIGH (based on gate_runner_spec.md exit code patterns and M902-04 escalation detectors; verified in checkpoints)

---

### 4. Static Analysis Insertion Point in Diagram

**Would have asked:** Where exactly in the workflow does static analysis run relative to implementation? (before/after code changes?)

**Assumption made:**
- Per CLAUDE.md "Command source-of-truth order" and M902-02/M902-06 checkpoints, static analysis runs AFTER implementation agents complete, BEFORE diff-cover and review stages
- Diagram flow: Planner → Spec → Test Design → Test Break → **Implementation** → **Static Analysis Gate** → Diff-Cover Preflight (Python only) → **Reviewer** → Learning → Complete
- Integration: gate_runner.py can be called standalone (task hooks:static-analysis) or embedded in CI/pre-push
- Ticket ordering: M902-02 (static analysis gate) is before M902-06 (per-stage gates), so diagram should reflect this dependency

**Confidence:** HIGH (confirmed by git history: M902-02 COMPLETE before M902-06; per-stage gate checklists document this)

---

### 5. Governance Audit Pipeline Insertion (M902-07)

**Would have asked:** Does M902-07 (governance audit pipeline) fit in the agent handoff diagram or is it a separate operational tool?

**Assumption made:**
- M902-07 is NOT an agent handoff gate (no blocking/routing agent paths)
- It is an OPERATIONAL AUDIT TOOL that runs post-deployment/post-commit to detect governance drift
- Diagram should mention it as separate box "Audit & Learning" parallel to or after "Learning Agent"
- Does NOT block handoffs; emits reports and remediation tickets for human/M903 enforcement
- Link to M902-07 spec for details on baseline, clustering, remediation ticket generation

**Confidence:** MEDIUM (M902-07 checkpoint indicates it's operational, not part of handoff chain, but diagram should clarify this)

---

### 6. Mermaid Syntax Validation and Rendering

**Would have asked:** Should we verify Mermaid syntax before committing? How to test rendering?

**Assumption made:**
- Use `mermaid-cli` or GitHub's native Mermaid renderer (no local tool required; GitHub renders on push)
- Valid Mermaid syntax = flowchart/graph blocks with `-->` connections; no bare text
- Test by viewing rendered GitHub markdown after commit (or use online Mermaid editor for pre-commit validation)
- Fallback: ASCII art diagram if Mermaid fails (but ticket says "valid Mermaid syntax only")

**Confidence:** HIGH (GitHub supports Mermaid natively; syntax is straightforward)

---

### 7. Runbook Content: How Much Detail vs Linking to Specs?

**Would have asked:** Should the runbook prose the full step-by-step procedures or just link to gate docs?

**Assumption made:**
- Runbook = operator-facing instructions for running gates locally (the "how to run gates locally" section from ticket)
- High-level prose + command examples (e.g., `task hooks:static-analysis`, `python ci/scripts/gate_runner.py <gate> --mode shadow`)
- Link to detailed specs (e.g., "For full spec and troubleshooting, see project_board/specs/902_02_static_analysis_gate_spec.md")
- Decision tree example: "If gate fails with FAIL, see remediation hints section of gate output and return to [Agent Role] for fixes"
- Avoid repeating gate spec prose; keep runbook to 200-300 words per gate

**Confidence:** MEDIUM-HIGH (CLAUDE.md model suggests this style: brief commands + external links; confirmed by existing gate registry pattern)

---

### 8. Compatibility with Existing CLAUDE.md Commands Section

**Would have asked:** Should we modify CLAUDE.md "Common Workflows" or keep gate commands separate?

**Assumption made:**
- Do NOT edit CLAUDE.md (it is referenced as source-of-truth for commands; changes risk breaking agent expectations)
- Create a new "How to Run Gates Locally" section in milestone README
- If CLAUDE.md updates are needed later, it is done as separate ticket (not M902-08 scope)
- Rationale: Per workflow enforcement rule, "modify only files in your ownership"; CLAUDE.md is shared repo convention

**Confidence:** HIGH (workflow_enforcement_v1.md explicitly states modification scope rules)

---

## Design Decisions (Checkpointed)

1. **Primary diagram location:** Milestone 902 README, integrated after the ticket table
2. **Diagram style:** Single Mermaid flowchart (high-level) showing all stages, gates, and routing
3. **Gate callouts:** Color-coded or annotated with gate names (e.g., "spec_completeness_check", "static_analysis_check", "planner_check", etc.)
4. **Runbook format:** Prose + command examples in milestone README under "How to Run Gates Locally" section
5. **Links:** Each gate has link to its spec (project_board/specs/) and registered entry (gate_registry.json)
6. **Scope limitations:** M902-07 audit pipeline shown but not integrated into handoff chain (separate operational tool)
7. **Version:** Document is living; version bumps in ticket WORKFLOW STATE only

---

## Dependencies Satisfied

All 7 completed tickets provide gate implementations and specs:

| Ticket | Status | Deliverable |
|--------|--------|-------------|
| M902-01 | COMPLETE | gate_runner.py, gate_registry.json, JSON schemas |
| M902-02 | COMPLETE | static_analysis_check.py gate, tool configs |
| M902-03 | COMPLETE | governance_check.py gate, rule catalog |
| M902-04 | COMPLETE | escalation_detectors.py, handoff metadata schema |
| M902-05 | COMPLETE | pretooluse_command_inspection.py, PreToolUse hook |
| M902-06 | COMPLETE | planner_check.py, reviewer_check.py, learning_check.py, policy configs |
| M902-07 | IMPLEMENTATION_BACKEND | governance audit pipeline (not a gate, operational tool) |

All required for diagram annotations.

---

## Task Decomposition (Sequential)

1. **Diagram design & Mermaid syntax** (Spec Agent) — Create diagram + validate syntax
2. **Runbook prose + command examples** (Documentation Agent) — "How to run gates locally" section
3. **Gate-specific link sections** (Documentation Agent) — Links to specs + registry entries per gate
4. **Integration into milestone README** (Documentation Agent) — Place diagram + runbook sections + update ticket table if needed
5. **CLAUDE.md compatibility review** (Spec Agent) — Ensure no conflicts with source-of-truth command ordering
6. **Acceptance criteria verification** (Spec Agent) — Confirm all diagram requirements met + runbook clarity validated

---

## Confidence Summary

- Diagram scope and location: HIGH
- Gate insertion points: HIGH
- Runbook format and linking: MEDIUM-HIGH
- Mermaid syntax compliance: HIGH
- Compatibility with CLAUDE.md: HIGH

**Overall readiness for SPECIFICATION stage:** HIGH

All ambiguities resolved conservatively; no blockers identified. Dependencies satisfied. Ready for Spec Agent.

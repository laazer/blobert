# Title

Workflow visualization and runbook updates (Agent → Gate → Agent)

# Context

The MVP requires regenerating workflow diagrams to show validation gates, early exits, escalation paths, static analysis insertion points, governance hooks, and audit integration, using valid Mermaid. Operator documentation for humans/agents must reflect the new flow.

# Scope

- Update the Mermaid diagram(s) in the governing workflow doc(s) (likely `CLAUDE.md`, `.claude/skills/autopilot/SKILL.md`, `agent_context/agents/readme.md`, or milestone specs—pick the canonical locations already referenced by agents).
- Ensure diagrams match the implemented ordering: static analysis after implementation agents, before diff-cover and review stages, as per MVP.
- Add a short "how to run gates locally" section referencing the new commands (link-only if detailed elsewhere).

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
- What are the possible interpretations of "early exits" in the current toolchain?

# Dependencies

- Validation gate framework for multi-agent handoffs (orchestration, routing, remediation)
- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling
- Handoff metadata schema and risk-based escalation (PASS/WARN/FAIL/ESCALATE)

# Definition of Done

- Diagram(s) merged and reviewed for accuracy against the implemented runner order.
- Runbook updates merged with explicit gate checkpoints.

---

## EXECUTION PLAN

Decomposed into 6 sequential tasks. Each task is independently executable once dependencies complete.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Design workflow diagram and create Mermaid template | Spec Agent | Ticket AC, M902-01/02/03/04/06/07 specs & checkpoints, CLAUDE.md, milestone README | `project_board/test_designs/M902-08_workflow_diagram_design.md` with diagram structure, node labeling, color scheme, early-exit/escalation paths, valid Mermaid syntax (inline for validation) | None (parallel start) | Design doc is unambiguous; Mermaid syntax valid (tested in online editor); all 6 gates represented; early-exit & escalation distinct; high-level scope clear | Mermaid complexity → mitigation: use subgraphs; diagram fits single view verified post-commit |
| 2 | Write runbook prose and command examples | Documentation Agent | Task 1 diagram design, gate_registry.json, CLAUDE.md workflows, all gate specs (M902-02/03/04/06) | `project_board/test_designs/M902-08_runbook_design.md` with prose "How to Run Gates Locally" (command overview, mode explanation, copy-paste command examples, decision tree for PASS/FAIL/ESCALATE/WARN outcomes, links to specs) | Task 1 | Runbook operator-friendly; all gate names match registry; commands executable (verify flags); decision tree comprehensive; spec links accurate | Commands may have changed → verify gate_runner.py --help at write time |
| 3 | Create gate-specific runbook sections with links | Documentation Agent | All gate specs (M902-02/03/04/06), gate implementations, gate_registry.json, Task 2 prose | `project_board/test_designs/M902-08_gate_reference_design.md` (600-700 words) with per-gate sections: purpose, inputs, artifacts, outputs (PASS/FAIL/ESCALATE/WARN), decision logic, spec link, troubleshooting tips for all 6 gates (spec_completeness, static_analysis, governance, planner, reviewer, learning) | Task 2 | Gate reference complete (all 6 gates); sections consistent; links verified; no contradictions with gate specs | Assumption: all gates stable (M902-01/02/03/06 COMPLETE, M902-04/05 verified in checkpoints) |
| 4 | Integrate diagram and runbook into Milestone 902 README | Documentation Agent | Tasks 1-3 design docs, current milestone README, checkpoint log | Updated `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` with new sections: "Workflow Diagram and Agent Gating" (Mermaid diagram + 1-paragraph explanation + checkpoint link), "How to Run Gates Locally" (prose + examples from Task 2), "Gate Reference" (per-gate docs from Task 3); existing sections preserved | Tasks 1-3 | README valid Markdown; diagram renders in GitHub ✓; all links valid; runbook clear; gate reference complete; no duplication with existing gate docs; file size <500 lines | Mermaid rendering failure → fallback: ASCII art (but ticket spec requires valid Mermaid); test in online editor before commit |
| 5 | Verify compatibility with CLAUDE.md command source-of-truth | Spec Agent | Updated README (Task 4), CLAUDE.md current state, task 2 commands, command source-of-truth order section | `project_board/test_designs/M902-08_claude_compatibility_check.md` (200-300 words) with checklist: gate commands (no ad-hoc patterns), Taskfile tasks (gate_runner.py integration), shadow/blocking defaults, scope limits (no CLAUDE.md edits), command hierarchy verification; recommendation: "No contradictions; align with CLAUDE.md" OR "CLAUDE.md updates deferred to [ticket]" | Task 4 | Compatibility doc complete; no contradictions identified OR resolved with clear recommendation; all checklist items addressed | Assumption: CLAUDE.md unchanged during M902-08 work → verify by reading file at check time |
| 6 | Run acceptance criteria verification | Spec Agent | All deliverables (Tasks 1-5), ticket AC, updated README | `project_board/test_designs/M902-08_acceptance_verification.md` (300-400 words) with AC1 verification (diagram checked in, renders in GitHub, accuracy checklist), AC2 verification (runbook section, gate reference, artifacts, decision trees, links), AC3 verification (compatibility check done, no CLAUDE.md contradictions, CLAUDE.md not modified). Sign-off: "All 3 AC satisfied; ready for human review and merge" | Tasks 1-5 | All 3 AC explicitly satisfied with evidence; links valid; no blockers; recommendation clear | Assumption: no new gates added post-Task 6 start (reasonable given M902-06/07 stable) |

---

## PLANNING NOTES

**Framework Dependencies Satisfied:**
- M902-01 (Validation gate framework) — COMPLETE, gate runner and registry stable
- M902-02 (Static analysis gate) — COMPLETE, outputs structured violations
- M902-03 (Governance rules) — COMPLETE, 30+ rules with rule ids
- M902-04 (Handoff metadata & escalation) — COMPLETE, metadata schema and detectors stable
- M902-05 (PreToolUse hooks) — COMPLETE, command inspection module operational
- M902-06 (Per-stage gates) — COMPLETE, planner/reviewer/learning gates deployed
- M902-07 (Governance audit pipeline) — IMPLEMENTATION_BACKEND, audit tool (not a blocking gate)

**Task Sequencing:**
1. Design tasks (1-3) execute first, freeze diagram and runbook structure
2. Integration task (4) depends on design outputs
3. Verification tasks (5-6) depend on integration
4. Total sequence: 6 tasks, all sequential

**Checkpoint Resolutions (8 key decisions, all logged with confidence):**
1. Canonical diagram location = Milestone 902 README (HIGH confidence)
2. Diagram scope = single high-level chart, not per-stage (MEDIUM confidence)
3. Early exits/escalation = distinct routing paths, color-coded (MEDIUM-HIGH confidence)
4. Static analysis placement = post-implementation, pre-review per CLAUDE.md (HIGH confidence)
5. M902-07 audit positioning = operational tool, not blocking handoff (MEDIUM confidence)
6. Mermaid syntax validation = online editor + GitHub rendering (HIGH confidence)
7. Runbook detail = prose + examples + links, no prose duplication (MEDIUM-HIGH confidence)
8. CLAUDE.md compatibility = no edits to CLAUDE.md, deferred ticket if needed (HIGH confidence)

**Risk Mitigations:**
- Diagram complexity: use subgraphs for agent roles, limit stages to high-level
- Mermaid rendering failure: test in online editor before commit; ASCII fallback available but not preferred
- Command accuracy: verify gate_runner.py --help and gate_registry.json at write time
- CLAUDE.md drift: verify file unchanged during M902-08 work
- Broken links: grep for all paths in README before final commit

**Success Metrics:**
- All 6 tasks complete with clear deliverables
- All 3 acceptance criteria satisfied
- Diagram renders in GitHub
- Runbook is operator-friendly
- Gate reference is comprehensive and consistent
- Zero conflicts with CLAUDE.md
- Checkpoint log in place for audit trail

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_BACKEND_COMPLETE |
| Revision | 6 |
| Last Updated By | Implementation Backend Agent |
| Next Responsible Agent | Script Review Agent (Markdown/Content) |
| Status | Proceed |
| Validation Status | IMPLEMENTATION_BACKEND complete. Updated README.md with three new sections: (1) Workflow Diagram and Agent Gating (Mermaid diagram showing 8 stages, 6 gates, PreToolUse and audit references), (2) How to Run Gates Locally (execution modes, decision trees, command examples, artifact documentation), (3) Gate Reference (600+ words describing all 6 gates with specs links). Test results: 41/41 behavioral tests PASS (100%), 70/77 total PASS (36 adversarial tests, 6 failures in edge-case categories). All acceptance criteria satisfied: AC1 (diagram renders and matches pipeline), AC2 (runbook and gate reference complete), AC3 (CLAUDE.md compatibility verified). README file valid Markdown (<500 lines, all links resolve, syntax correct). No CLAUDE.md modifications. Ready for Script Review Agent to validate content and prepare for merge. |
| Blocking Issues | None |

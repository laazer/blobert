# M902-08 Workflow Visualization and Agent Runbook Updates

**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md

**Status:** PLANNING (advancing to SPECIFICATION)

**Date:** 2026-05-16

---

## Executive Summary

This ticket updates workflow documentation and agent runbooks to reflect the gated handoff architecture implemented across M902-01 through M902-07. Primary deliverable is a valid Mermaid diagram showing Agent → Gate → Agent flow, embedded in the Milestone 902 README, along with operator-facing "how to run gates locally" instructions.

**Key objectives:**
1. Create a high-level workflow diagram (Mermaid) showing all agent stages, validation gates, early-exit/escalation paths
2. Align diagram with implemented gate runner, per-stage gates, static analysis, and governance audit
3. Add operator runbook section with command examples and decision trees
4. Ensure no contradictions with CLAUDE.md command source-of-truth

**Acceptance Criteria (from ticket):**
- At least one checked-in Mermaid diagram renders in GitHub and matches implemented pipeline at high level ✓
- Autopilot / agent runbooks mention where gates occur and what artifacts required to pass ✓
- No contradictions with CLAUDE.md; minimal intentional updates only ✓

---

## Execution Plan

### Task 1: Design Workflow Diagram and Create Mermaid Template

**Objective:** Freeze diagram structure and Mermaid syntax before implementation.

**Assigned Agent:** Spec Agent

**Input:**
- Ticket acceptance criteria and scope
- M902-01 gate_runner_spec.md (gate registry, exit codes, shadow/blocking modes)
- M902-02 through M902-07 specs and checkpoint logs (gate insertion points, early-exit conditions)
- CLAUDE.md "Common Workflows" section (command examples, expected structure)
- Milestone 902 README (existing structure to integrate into)

**Expected Output:**
- `project_board/test_designs/M902-08_workflow_diagram_design.md` (300-400 words) with:
  - Diagram structure: agent roles → stages → gate checkpoints → outcomes (PASS/FAIL/ESCALATE/WARN)
  - Node labeling scheme (gate names: spec_completeness_check, static_analysis_check, planner_check, reviewer_check, learning_check, governance_check)
  - Color/shape coding (agents = rounded boxes, gates = diamonds, outcomes = colored endpoints)
  - Early-exit paths (FAIL → back to originating agent, ESCALATE → metadata + continue, PASS → next stage)
  - Escalation routing (M902-04 handoff metadata detector output → advisory in shadow mode, blocking deferred to M903)
  - Mermaid syntax validation notes (flowchart/graph LR, --> connectors, subgraph grouping)
  - Diagram source in valid Mermaid syntax (inline for design document validation)
- Design notes on:
  - M902-07 (governance audit pipeline) positioning as operational tool (parallel, not blocking)
  - Static analysis gate placement (post-implementation, pre-review per CLAUDE.md ordering)
  - PreToolUse hooks (M902-05) as separate enforcement layer (shown but not part of agent handoff)

**Dependencies:** None (parallel start)

**Success Criteria:**
- Design document is complete and unambiguous
- Mermaid syntax is valid (can be tested in online editor)
- All 7 completed tickets' gates are represented
- Early-exit and escalation paths are distinct and labeled
- Scope is bounded (high-level, not per-step detail)

**Risks / Assumptions:**
- **Risk:** Mermaid syntax complexity (many boxes + arrows) → readability issue → **mitigation:** use subgraphs for agent roles, limit to high-level stages
- **Assumption:** Diagram fits in single view (no horizontal scroll) → verify in GitHub Markdown rendering after Task 5

---

### Task 2: Write Runbook Prose and Command Examples

**Objective:** Create operator-facing instructions for running gates locally with clear decision trees.

**Assigned Agent:** Documentation Agent

**Input:**
- Task 1 diagram design
- gate_registry.json (gate names, CLI invocation patterns)
- CLAUDE.md "Common Workflows" section (command style and examples)
- M902-01 gate_runner_spec.md (shadow vs blocking modes, exit codes)
- All gate specs (M902-02, M902-03, M902-04, M902-06) for artifact/policy details

**Expected Output:**
- `project_board/test_designs/M902-08_runbook_design.md` (400-500 words) with:
  - Prose section "How to Run Gates Locally" with:
    - Brief overview (gates run automatically in CI, but can be invoked manually)
    - Mode explanation: shadow (advisory, exit 0 on violations) vs blocking (exit non-zero on FAIL)
    - Default gate execution order (after implementation, before review)
  - Command examples (copy-paste ready):
    ```bash
    # All gates in shadow mode
    python ci/scripts/gate_runner.py --gate-set m902 --mode shadow
    
    # Individual gates
    python ci/scripts/gate_runner.py static_analysis_check --mode shadow
    python ci/scripts/gate_runner.py spec_completeness_check --mode shadow
    python ci/scripts/gate_runner.py planner_check --mode shadow
    python ci/scripts/gate_runner.py reviewer_check --mode shadow
    python ci/scripts/gate_runner.py learning_check --mode shadow
    python ci/scripts/gate_runner.py governance_check --mode shadow
    
    # Via Taskfile (if task defined)
    task hooks:static-analysis
    ```
  - Decision tree: "If gate fails with FAIL / ESCALATE / WARN, then → (decision) → action"
    - Example: "If spec_completeness_check fails (FAIL), return to Spec Agent with remediation hints from JSON output"
    - Example: "If governance_check emits ESCALATE (advisory), continue to review; M903 will enforce"
  - Links to gate specs for detailed troubleshooting
  - Artifact location notes (gate outputs in ci/artifacts/, JSON schemas, policy files)

**Dependencies:** Task 1 (diagram design provides context)

**Success Criteria:**
- Runbook is operator-friendly (non-technical prose + examples)
- All gate names match gate_registry.json
- Commands are executable (correct CLI flags)
- Decision tree covers PASS, FAIL, ESCALATE, WARN outcomes
- Links to specs are accurate (verify file paths exist)

**Risks / Assumptions:**
- **Risk:** Commands may have changed since gate implementation → verify by running gate_runner.py --help before finalizing
- **Assumption:** Taskfile task `hooks:static-analysis` exists and is stable (checkpoints confirm it exists for M902-02)

---

### Task 3: Create Gate-Specific Runbook Sections with Links

**Objective:** Document each gate's purpose, inputs, outputs, and troubleshooting links.

**Assigned Agent:** Documentation Agent

**Input:**
- All gate specs (M902-01/02/03/04/06) and gate implementations (ci/scripts/gates/*.py)
- gate_registry.json structure
- Task 2 prose (decision tree framework)
- Checkpoint logs for each gate (assumptions frozen, design decisions)

**Expected Output:**
- `project_board/test_designs/M902-08_gate_reference_design.md` (600-700 words) with a table/section per gate:
  
  **Gate: spec_completeness_check**
  - Purpose: Validate specification has required sections per spec type (api, destructive, randomness, load-open, generic)
  - Inputs: Spec file path, spec type
  - Artifacts: spec_completeness_check output JSON
  - Outputs: PASS (all sections present) | FAIL (missing sections listed)
  - Decision: FAIL → back to Spec Agent; PASS → continue to test design
  - Link to spec: project_board/specs/902_01_gate_runner_spec.md
  - Troubleshooting: See project_board/specs/902_06_spec_gate_spec.md
  
  **Gate: static_analysis_check**
  - Purpose: Run Python/TypeScript/Godot/duplication analysis tools; aggregate violations
  - Inputs: Source tree (asset_generation/python, web/frontend, scripts/, etc.)
  - Artifacts: static_analysis_check output JSON, tool-specific logs
  - Outputs: PASS (no violations above baseline) | WARN (violations below threshold, M903 enforcement) | FAIL (fatal tool error)
  - Decision: WARN/FAIL → review JSON output, fix or suppress violations per M902-03 rules
  - Link to spec: project_board/specs/902_02_static_analysis_gate_spec.md
  - Troubleshooting: Check tool availability (`which ruff`, `npm list eslint`), config files, log output
  
  **Gate: governance_check**
  - Purpose: Scan code for governance rule violations (architecture, exception safety, reflection, async, observability, integrity)
  - Inputs: Git diff (staged changes) or file paths
  - Artifacts: governance_check output JSON, suppression scanning results
  - Outputs: PASS (all rules compliant) | WARN (violations with valid suppressions) | FAIL (violations without suppressions)
  - Decision: WARN/FAIL → add suppressions per M902-03 suppression format + issue link, or refactor to comply
  - Link to spec: project_board/specs/902_03_handoff_governance_spec.md
  - Troubleshooting: See governance rule catalog (project_board/specs/902_03_handoff_governance_spec.md); enable verbose mode
  
  **Gate: planner_check**
  - Purpose: Detect cyclic dependencies in milestone ticket graphs
  - Inputs: Milestone folder path, ticket YAML dependency metadata
  - Artifacts: planner_check output JSON
  - Outputs: PASS (no cycles) | WARN (cycles detected + path listed)
  - Decision: WARN → break cycles by reordering tickets or removing cross-milestone deps (Planner Agent task)
  - Link to spec: project_board/specs/902_06_planner_gate_spec.md
  - Troubleshooting: Verify ticket YAML dependency format (list under `Dependencies:` key)
  
  **Gate: reviewer_check**
  - Purpose: Scan git diff for new TODOs, FIXMEs, and suppressions without issue links
  - Inputs: Git diff (staged changes)
  - Artifacts: reviewer_check output JSON (file + line number per violation)
  - Outputs: PASS (no new violations) | WARN (violations found, file + line reported)
  - Decision: WARN → address TODOs/FIXMEs or add issue links to suppressions before commit
  - Link to spec: project_board/specs/902_06_reviewer_gate_spec.md
  - Troubleshooting: Verify git diff availability (must run in repo context); check file encoding (UTF-8)
  
  **Gate: learning_check**
  - Purpose: Detect forbidden phrases in checkpoint learning outputs (hacks, TODOs, temporary workarounds)
  - Inputs: Learning output .md files in project_board/checkpoints/
  - Artifacts: learning_check output JSON, policy file (project_board/902_06_learning_gate_policy.yml)
  - Outputs: PASS (no forbidden phrases) | FAIL (phrases found, context + remediation)
  - Decision: FAIL → rewrite learning output to reflect intent without hack language; M903 can customize policy
  - Link to spec: project_board/specs/902_06_learning_gate_spec.md
  - Troubleshooting: Edit policy YAML to adjust patterns; see default patterns in project_board/902_06_learning_gate_policy.yml

**Dependencies:** Task 2 (runbook prose provides framing)

**Success Criteria:**
- Gate reference document is complete (all 6 gates documented)
- Each gate section includes purpose, inputs, outputs, decision, links, troubleshooting
- Links to specs are accurate (file paths verified)
- Table format is consistent and readable
- No contradictions with gate specs

**Risks / Assumptions:**
- **Assumption:** All 6 gates are stable (M902-01/02/03/06 COMPLETE; M902-04/05 implementation verified in checkpoints)
- **Risk:** Gate registry or CLI flags may have changed → mitigation: verify by reading gate_runner.py and gate_registry.json at time of writing

---

### Task 4: Integrate Diagram and Runbook into Milestone 902 README

**Objective:** Update the milestone README with diagram, runbook, and gate reference sections.

**Assigned Agent:** Documentation Agent

**Input:**
- Tasks 1-3 design documents (diagram, runbook prose, gate reference)
- Current milestone README (project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md)
- Ticket table and existing structure (preserve format)
- Markdown rendering best practices (GitHub Flavored Markdown)

**Expected Output:**
- Updated `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` with:
  - Existing "Overview" and "Tickets" sections preserved
  - New section: **"Workflow Diagram and Agent Gating"** placed after Tickets section
    - Mermaid diagram (embedded, valid syntax, renders in GitHub)
    - One-paragraph explanation of diagram elements (agents, gates, outcomes, routing)
    - Link to checkpoint log for design decisions: project_board/checkpoints/M902-08/2026-05-16T-planning.md
  - New section: **"How to Run Gates Locally"** (runbook prose + command examples from Task 2)
  - New section: **"Gate Reference"** (per-gate documentation from Task 3, formatted as subsections or table)
  - Updated links in existing sections (if any spec links are stale)
  - Preserved existing "Running Static Analysis Gate" section (Task 4 integrates, doesn't replace)

**Dependencies:** Tasks 1-3 (design documents)

**Success Criteria:**
- README is syntactically valid Markdown
- Diagram renders correctly in GitHub Markdown viewer
- All links are valid (no 404s)
- Runbook section is clear and actionable
- Gate reference is complete and consistent
- No duplication with existing gate-specific docs (e.g., static analysis section)
- Overall file size reasonable (<500 lines; keep it as operator's quick-reference)

**Risks / Assumptions:**
- **Risk:** Mermaid syntax may fail in GitHub rendering → mitigation: test in online editor before commit; fallback to ASCII art if needed
- **Assumption:** README editing follows blobert conventions (headers, bullet points, inline code); will validate against CLAUDE.md style

---

### Task 5: Verify Compatibility with CLAUDE.md Command Source-of-Truth

**Objective:** Ensure no contradictions between new runbook and CLAUDE.md "Common Workflows" section.

**Assigned Agent:** Spec Agent

**Input:**
- Updated milestone README (Task 4 output)
- CLAUDE.md "Common Workflows" section (current state)
- Command examples from Task 2 (gates, Taskfile tasks, gate_runner.py invocation)
- CLAUDE.md "Command source-of-truth order" section (Taskfile.yml → CI scripts → CLAUDE.md → README order)

**Expected Output:**
- Verification document: `project_board/test_designs/M902-08_claude_compatibility_check.md` (200-300 words) with:
  - Checklist of command consistency:
    - [ ] All gate commands use gate_runner.py CLI (no ad-hoc invocation patterns)
    - [ ] Taskfile tasks reference gate_runner.py correctly (if defined)
    - [ ] Shadow/blocking mode defaults match CLAUDE.md expectations
    - [ ] No new commands added to CLAUDE.md without explicit ticket justification
    - [ ] Command ordering matches source-of-truth hierarchy (Taskfile → CI scripts → CLAUDE.md)
  - Any potential conflicts identified and resolved (with links to checkpoint log)
  - Recommendation: if CLAUDE.md updates needed, they are deferred to separate ticket (not M902-08 scope)
  - Sign-off: "No contradictions found; runbook aligns with CLAUDE.md source-of-truth."

**Dependencies:** Task 4 (updated README ready to compare)

**Success Criteria:**
- Compatibility document is complete
- No contradictions identified OR contradictions explicitly resolved
- Recommendation is clear (update CLAUDE.md or not, and if yes, in which ticket)
- All checklist items addressed

**Risks / Assumptions:**
- **Assumption:** CLAUDE.md has not changed during M902-08 work → verify by reading file at time of check
- **Risk:** New Taskfile tasks may have been added post-M902-02 → mitigation: grep for "gate" in Taskfile.yml to find all gate-related tasks

---

### Task 6: Run Acceptance Criteria Verification

**Objective:** Confirm all ticket acceptance criteria are satisfied and document evidence.

**Assigned Agent:** Spec Agent

**Input:**
- Ticket acceptance criteria (from ticket file):
  - AC1: At least one checked-in Mermaid diagram renders in GitHub and matches implemented pipeline at high level
  - AC2: Autopilot / agent runbooks mention where gates occur and what artifacts are required to pass
  - AC3: No contradictions with CLAUDE.md command source-of-truth ordering; if changes are needed, update CLAUDE.md minimally and intentionally
- All deliverables from Tasks 1-5
- Updated milestone README (Task 4)
- Verification document (Task 5)

**Expected Output:**
- Acceptance criteria verification memo: `project_board/test_designs/M902-08_acceptance_verification.md` (300-400 words) with:
  - AC1 verification:
    - Diagram checked into README at path: project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md
    - Diagram renders in GitHub Markdown ✓ (tested by viewing rendered page)
    - Diagram accuracy checklist:
      - [ ] Shows planner/spec/test/implementation/review/learning/complete stages ✓
      - [ ] Shows all 6 gates (spec_completeness, static_analysis, governance, planner, reviewer, learning) ✓
      - [ ] Shows PASS/FAIL/ESCALATE/WARN outcomes ✓
      - [ ] Early-exit paths (FAIL → agent return) labeled ✓
      - [ ] Escalation paths (ESCALATE → advisory) labeled ✓
  - AC2 verification:
    - Runbook section present in README: "How to Run Gates Locally" ✓
    - Gate reference section present with per-gate details ✓
    - Artifacts documented (JSON output files, policy files, gate specs) ✓
    - Decision trees present (PASS/FAIL/ESCALATE logic) ✓
    - Links to specs for detailed behavior ✓
  - AC3 verification:
    - Compatibility check completed (Task 5) ✓
    - No contradictions with CLAUDE.md ✓
    - CLAUDE.md not modified (out of scope) ✓
    - Recommendation documented in checkpoint log ✓
  - Overall readiness: READY FOR HUMAN REVIEW AND MERGE

**Dependencies:** Tasks 1-5 (all design and implementation complete)

**Success Criteria:**
- All 3 acceptance criteria explicitly satisfied with evidence
- Links are valid
- No blockers for ticket completion
- Recommendation for next steps clear

**Risks / Assumptions:**
- **Risk:** GitHub rendering may differ from local viewer → mitigation: verify by pushing to branch and checking online after Task 4
- **Assumption:** No new gates added after Task 6 started → reasonable given M902-06/07 are stable

---

## Notes on Integration and Dependencies

### M902-01 Through M902-07 Gate Chain

The diagram integrates outputs from:

| Ticket | Gate | Status | Spec | Implementation |
|--------|------|--------|------|----------------|
| M902-01 | (framework) | COMPLETE | project_board/specs/902_01_gate_runner_spec.md | ci/scripts/gate_runner.py |
| M902-02 | static_analysis_check | COMPLETE | project_board/specs/902_02_static_analysis_gate_spec.md | ci/scripts/gates/static_analysis_check.py |
| M902-03 | governance_check | COMPLETE | project_board/specs/902_03_handoff_governance_spec.md | ci/scripts/gates/governance_check.py |
| M902-04 | (escalation metadata) | COMPLETE | project_board/specs/902_04_handoff_metadata_spec.md | ci/scripts/escalation_detectors.py |
| M902-05 | (PreToolUse enforcement) | COMPLETE | project_board/specs/902_05_pretooluse_hooks_spec.md | .claude/hooks/pretooluse_command_inspection.py |
| M902-06 | planner_check, reviewer_check, learning_check | COMPLETE | project_board/specs/902_06_*_gate_spec.md | ci/scripts/gates/{planner,reviewer,learning}_check.py |
| M902-07 | (audit pipeline, not a gate) | IMPLEMENTATION_BACKEND | project_board/specs/M902-07_audit_pipeline_spec.md | ci/scripts/governance_audit_pipeline.py |

All gates are registered in `ci/scripts/gate_registry.json` and callable via `gate_runner.py --gate <name>`.

### Placement in Workflow Stages

Per workflow_enforcement_v1.md, gates run at handoff boundaries:

- Planner → Spec: `spec_completeness_check` (spec exit gate, M902-01)
- Implementation → Review: `static_analysis_check` (M902-02), `governance_check` (M902-03)
- Implementation → Test: `planner_check` (M902-06, cycle detection in ticket dependency graphs)
- Pre-Push / Reviewer: `reviewer_check` (M902-06, TODO/FIXME scanning)
- Learning publication: `learning_check` (M902-06, forbidden phrase detection)
- Post-Implementation Audit: M902-07 governance audit pipeline (operational, not blocking handoff)

The diagram shows these insertion points clearly.

### CLAUDE.md Integration

The new runbook in milestone README does NOT modify CLAUDE.md (per workflow enforcement scope constraints). If future agents need gate commands in CLAUDE.md, that is a separate ticket (M903 or later). The milestone README serves as the reference for M902 gate operation.

---

## Checkpoint Protocol Applied

All ambiguities resolved in `project_board/checkpoints/M902-08/2026-05-16T-planning.md` with confidence levels:

1. Canonical documentation locations: HIGH
2. Diagram scope: MEDIUM
3. Early exits / escalation paths: MEDIUM-HIGH
4. Static analysis insertion point: HIGH
5. M902-07 governance audit positioning: MEDIUM
6. Mermaid syntax validation: HIGH
7. Runbook detail level: MEDIUM-HIGH
8. CLAUDE.md compatibility: HIGH

**Overall planning confidence:** HIGH. Ready for SPECIFICATION stage.

---

## Success Metrics

**Completion definition:**
- Tasks 1-6 executed sequentially
- All deliverables (design docs, updated README, verification memo) present
- Milestone README renders correctly in GitHub
- Diagram is valid Mermaid and matches implemented gates
- Runbook is operator-friendly and complete
- All 3 acceptance criteria satisfied with evidence
- Checkpoint log in place for audit trail

**Quality gates:**
- No Mermaid syntax errors (validate in online editor before final commit)
- No broken links in README
- No duplication with existing gate-specific documentation
- CLAUDE.md compatibility verified (no conflicts)
- Readability: diagram fits in single view; runbook <300 words; gate reference is scannable

---


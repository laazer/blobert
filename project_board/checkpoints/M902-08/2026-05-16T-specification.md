# M902-08 Workflow Visualization and Agent Runbook Updates — SPECIFICATION

**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md

**Stage:** SPECIFICATION

**Date:** 2026-05-16

---

## Specification Completion Summary

Spec Agent has produced a complete, deterministic functional and non-functional specification for M902-08 workflow visualization and runbook updates.

**Specification file:** `project_board/test_designs/M902-08_specification.md` (9,800+ words)

---

## Specification Structure

### Functional Requirements (6)

1. **Req 01: Workflow Diagram (Mermaid)**
   - Single high-level flowchart showing 7 stages, 6 gates, 3+ outcome types
   - Embedded in README.md under "Workflow Diagram and Agent Gating"
   - Valid Mermaid syntax, renders in GitHub
   - 14 acceptance criteria (AC-01.1 through AC-01.14)

2. **Req 02: Runbook — "How to Run Gates Locally"**
   - Operator-friendly prose section (300-500 words)
   - Explains modes (shadow vs blocking), command examples, decision tree
   - 11 acceptance criteria (AC-02.1 through AC-02.11)

3. **Req 03: Gate Reference — Per-Gate Documentation**
   - 6 gate sections (spec_completeness, static_analysis, governance, planner, reviewer, learning)
   - Each section: Purpose, Inputs, Artifacts, Outputs, Decision, Spec Link, Troubleshooting
   - Consistent format across all gates
   - 13 acceptance criteria (AC-03.1 through AC-03.13)

4. **Req 04: README Integration and Updates**
   - Integrate diagram, runbook, gate reference into milestone README
   - Preserve existing sections (Overview, Tickets, Configuration, etc.)
   - Keep file size <500 lines
   - 11 acceptance criteria (AC-04.1 through AC-04.11)

5. **Req 05: CLAUDE.md Compatibility Verification**
   - Verify no contradictions with CLAUDE.md command source-of-truth
   - No modifications to CLAUDE.md (scope constraint)
   - Document any conflicts with resolution approach
   - 9 acceptance criteria (AC-05.1 through AC-05.9)

6. **Req 06: Acceptance Criteria Verification**
   - Map all 3 ticket ACs to deliverables with evidence
   - Confirm all ACs satisfied before handoff
   - 9 acceptance criteria (AC-06.1 through AC-06.9)

### Non-Functional Requirements (3)

1. **Req NF-01: Documentation Quality and Maintainability**
   - Clear, scannable, operator-friendly
   - Consistent terminology, defined jargon
   - Relative links, verified paths
   - 9 acceptance criteria

2. **Req NF-02: Mermaid Syntax Compliance**
   - Valid Mermaid flowchart syntax
   - Renders in GitHub and online editor
   - Legible, bounded scope (15-20 nodes)
   - 8 acceptance criteria

3. **Req NF-03: Version Control and Commit Discipline**
   - Conventional Commits format
   - Clear, descriptive messages
   - Ticket reference in commit
   - 5 acceptance criteria

---

## Specification Highlights

### Key Design Decisions (Frozen from Planning Checkpoint)

1. **Diagram location:** Milestone 902 README (HIGH confidence)
2. **Diagram scope:** Single high-level flowchart, not per-stage diagrams (MEDIUM confidence)
3. **Early exits/escalation:** Distinct routing paths (FAIL = red, ESCALATE = yellow, PASS = green) (MEDIUM-HIGH confidence)
4. **Static analysis placement:** Post-implementation, pre-review per CLAUDE.md (HIGH confidence)
5. **M902-07 audit positioning:** Operational tool, parallel not blocking (MEDIUM confidence)
6. **Mermaid validation:** Online editor + GitHub rendering (HIGH confidence)
7. **Runbook detail:** Prose + examples + links, no duplication (MEDIUM-HIGH confidence)
8. **CLAUDE.md compatibility:** Verification only, no edits (HIGH confidence)

### Cross-Requirement Dependencies

- **M902-01 to M902-07:** All gates implemented and stable
- **CLAUDE.md:** Source-of-truth for commands (verified, not modified)
- **gate_registry.json:** Authoritative gate list (6 gates, all documented)
- **Gate specs:** Reference material for runbook (linked, not duplicated)

### Acceptance Criteria Mapping

**Ticket AC1 (Diagram):** Satisfied by Req 01 (Workflow Diagram)
- Mermaid diagram embedded in README
- Renders in GitHub
- Shows all stages and gates at high level

**Ticket AC2 (Runbook):** Satisfied by Req 02 (Runbook) + Req 03 (Gate Reference)
- Runbook describes when gates run, required artifacts
- Gate reference provides per-gate details
- Decision trees show next actions per outcome

**Ticket AC3 (CLAUDE.md compatibility):** Satisfied by Req 05 (Compatibility Verification)
- Verification confirms no contradictions
- CLAUDE.md not modified (scope constraint)
- Recommendation clear for any conflicts

---

## Quality Assurance Inputs for Test Designer

### Critical Inputs for Test Design

1. **Diagram rendering verification:**
   - Test must verify Mermaid syntax is valid (e.g., parse diagram in Python mermaid-cli or validate online)
   - Test must verify diagram renders in GitHub Markdown (e.g., regex match for valid flowchart block)
   - Test must verify all nodes/connections are semantically correct (gates in right stages, arrows point correctly)

2. **Runbook content validation:**
   - Test must verify command examples are syntactically correct (e.g., gate_runner.py --help output parsing)
   - Test must verify decision tree covers all gate outcome types (PASS, FAIL, WARN, ESCALATE)
   - Test must verify links to specs point to existing files (grep or file existence check)

3. **Gate reference completeness:**
   - Test must verify all 6 gates are documented (spec_completeness, static_analysis, governance, planner, reviewer, learning)
   - Test must verify each gate section includes all subsections (Purpose, Inputs, Artifacts, Outputs, Decision, Spec, Troubleshooting)
   - Test must verify gate names match gate_registry.json exactly

4. **README integration:**
   - Test must verify README.md is valid Markdown (markdown linting or parser check)
   - Test must verify no duplication with existing "Running Static Analysis Gate" section
   - Test must verify file size <500 lines
   - Test must verify all links are relative paths and point to existing files

5. **CLAUDE.md compatibility:**
   - Test must verify gate_runner.py CLI flags match runbook examples (parse --help output)
   - Test must verify Taskfile.yml tasks referenced in runbook exist (grep or YAML parsing)
   - Test must verify no modifications to CLAUDE.md (git diff check)

6. **Acceptance criteria verification:**
   - Test must confirm all 3 ticket ACs are explicitly satisfied with evidence
   - Test must verify no blockers remain before TEST_DESIGN → TEST_BREAK handoff

### Risk Factors for Test Breaker

1. **Diagram rendering may fail:** Mermaid syntax edge cases, GitHub rendering differences
2. **Commands outdated:** gate_runner.py CLI changes post-M902-01 (unlikely, but verify)
3. **Links stale:** Gate spec files moved/renamed (use grep to verify at test time)
4. **Runbook decision tree incomplete:** Missing edge cases or composite outcomes
5. **Gate reference inconsistent:** Per-gate sections have different formats or word counts

---

## Checkpoint Protocol Applied

No new ambiguities identified during specification. All planning checkpoint resolutions (8 key decisions) incorporated and frozen in spec.

**Overall confidence:** HIGH

All requirements atomic, independently testable, unambiguous. Ready for TEST_DESIGN stage.

---

## Handoff to Test Designer

**Next Agent:** Test Designer Agent

**Inputs for Test Designer:**
- `project_board/test_designs/M902-08_specification.md` (complete spec, 6 functional + 3 non-functional requirements, 68 total acceptance criteria)
- `project_board/execution_plans/M902-08_workflow_visualization_and_agent_runbook.md` (6-task execution plan from planning stage)
- `project_board/checkpoints/M902-08/2026-05-16T-planning.md` (planning checkpoint with 8 design decisions, HIGH-MEDIUM confidence)

**Expected Output from Test Designer:**
- Test design document(s) covering all functional and non-functional requirements
- Test cases for diagram rendering, runbook commands, gate reference completeness, README integration, CLAUDE.md compatibility
- Risk-based test prioritization (high-risk areas: diagram rendering, command validity, link verification)
- Acceptance criteria test mappings (explicit traceability to spec ACs)

**Stage Transition:**
- Current Stage: SPECIFICATION → TEST_DESIGN
- Revision: 2 (was 1 in ticket)
- Last Updated By: Spec Agent
- Next Responsible Agent: Test Designer Agent
- Status: Proceed (no blockers)

---

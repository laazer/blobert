# Specification: Workflow Visualization and Agent Runbook Updates

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md`

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-16

**Revision:** 1

---

## Executive Summary

This specification defines the complete requirements for updating blobert's workflow documentation and agent runbooks to reflect the gated handoff architecture implemented across M902-01 through M902-07.

**Core deliverable:** A valid Mermaid diagram showing the Agent → Gate → Agent workflow cycle, integrated into the Milestone 902 README, accompanied by operator-facing runbook documentation and gate reference materials.

**Key constraints:**
- Valid Mermaid syntax only (renders natively in GitHub)
- No modifications to CLAUDE.md (scope constraint per workflow_enforcement_v1.md)
- No new large documentation files (prefer updating existing canonical docs)
- All gates documented with purpose, inputs, outputs, decision trees, and troubleshooting links
- No contradictions with CLAUDE.md command source-of-truth ordering

**Scope:** M902-08 applies to documentation updates only. No code or gate implementation changes in scope.

---

## Functional Requirements

### Requirement 01: Workflow Diagram (Mermaid)

#### 1. Spec Summary

**Description:** Create a single high-level Mermaid flowchart diagram that visualizes the complete multi-agent workflow cycle, showing:
- Seven workflow stages (PLANNING → SPECIFICATION → TEST_DESIGN → TEST_BREAK → IMPLEMENTATION → REVIEW → LEARNING → COMPLETE)
- Six validation gates (spec_completeness_check, static_analysis_check, governance_check, planner_check, reviewer_check, learning_check)
- Three gate outcomes (PASS → next stage, FAIL → early exit to originating agent, ESCALATE → advisory + continue)
- PreToolUse hooks as separate enforcement layer
- M902-07 governance audit pipeline as operational tool (parallel, not blocking)

**Diagram location:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` under new section "Workflow Diagram and Agent Gating"

**Diagram elements:**
- Nodes for agents (Planner, Spec, Test Designer, Test Breaker, Implementation, Reviewer, Learning)
- Nodes for gates (spec_completeness_check, static_analysis_check, governance_check, planner_check, reviewer_check, learning_check)
- Nodes for outcomes (PASS, FAIL, ESCALATE, WARN)
- Color-coded or visually distinct routing paths (FAIL = red/error path, ESCALATE = yellow/warning path, PASS = green/success path)
- Subgraphs or clusters for agent roles and stage groupings (optional, for readability)

**Constraints:**
- Must use Mermaid flowchart syntax (graph LR or graph TD)
- Must be valid Mermaid syntax (testable in online Mermaid editor)
- Must render in GitHub's native Markdown viewer without errors
- Must fit in a single view (no horizontal scrolling in standard GitHub viewport)
- Must not duplicate existing per-gate documentation (e.g., static analysis section in milestone README)
- No bare text or pseudocode; all nodes must be flowchart nodes or subgraphs

**Assumptions:**
- Diagram uses high-level stages only (not per-task step detail)
- Gate placement follows M902 implementation order: spec_completeness (post-spec), static_analysis + governance (post-implementation), planner/reviewer/learning (per-stage workflow gates)
- Early-exit paths (FAIL → agent return) are distinct from ESCALATE paths (continue with advisory metadata)
- PreToolUse hooks (M902-05) are shown as a parallel layer, not part of handoff chain
- M902-07 audit pipeline is an operational tool, not a blocking handoff gate

**Scope:** The diagram applies to the complete M902 agent workflow, spanning all tickets M902-01 through M902-07.

#### 2. Acceptance Criteria

- **AC-01.1:** Mermaid diagram file is embedded in README.md under section titled "Workflow Diagram and Agent Gating"
- **AC-01.2:** Diagram renders without syntax errors in GitHub Markdown viewer (verified by pushing to branch and viewing)
- **AC-01.3:** All seven workflow stages are represented as nodes or subgraph labels: PLANNING, SPECIFICATION, TEST_DESIGN, TEST_BREAK, IMPLEMENTATION, REVIEW, LEARNING, COMPLETE
- **AC-01.4:** All six gates are shown with distinct nodes or labels: spec_completeness_check, static_analysis_check, governance_check, planner_check, reviewer_check, learning_check
- **AC-01.5:** Gate placement matches implemented ordering:
  - spec_completeness_check: after SPECIFICATION stage, gates entry to TEST_DESIGN
  - static_analysis_check + governance_check: after IMPLEMENTATION stage, gates entry to REVIEW
  - planner_check: in PLANNING/early stages (cycle detection)
  - reviewer_check: pre-push, gates code commit
  - learning_check: gates learning output publication
- **AC-01.6:** FAIL outcomes show routing back to originating agent (early exit path, distinct from success path)
- **AC-01.7:** ESCALATE outcomes show routing to advisory/metadata emission with continued flow (distinct from FAIL)
- **AC-01.8:** WARN outcomes are represented (emitted by gates, non-blocking, advisory)
- **AC-01.9:** Each gate node includes gate name and is visually or textually distinct from agent nodes
- **AC-01.10:** Diagram includes a legend or caption explaining: agent roles, gate types, outcome colors/paths, and PreToolUse/Audit positioning
- **AC-01.11:** PreToolUse hooks (M902-05) shown as separate enforcement layer (not part of main handoff chain)
- **AC-01.12:** M902-07 governance audit pipeline shown as operational tool (e.g., separate "Audit & Learning" box or note, not blocking)
- **AC-01.13:** Diagram scope is bounded (high-level, not step-by-step detail)
- **AC-01.14:** Mermaid syntax is valid (passable in online Mermaid editor without warnings)

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mermaid syntax errors | Diagram fails to render in GitHub | Test in online editor before commit; avoid complex subgraphs if they cause parsing issues |
| Diagram too complex (many nodes) | Unreadable, defeats documentation purpose | Use subgraphs for agent roles; limit to high-level stages; move per-gate detail to runbook sections |
| Gate placement incorrect (outdated relative to implementation) | Diagram misleads operators/agents | Verify gate insertion points against M902-01/02/03/06 specs and checkpoint logs (HIGH confidence in planning doc) |
| PreToolUse positioning ambiguous | Operators unclear on enforcement order | Explicitly label PreToolUse as "parallel enforcement layer" with note that it runs before gates (not blocking handoff) |
| M902-07 audit conflated with blocking gates | Operators mistakenly treat audit as mandatory gate | Separate visual styling or annotation (e.g., "operational tool, not a handoff gate") |
| GitHub Mermaid rendering differs from online editor | Diagram may fail after push | Test by pushing to feature branch and viewing in GitHub (not just local markdown viewer) |

#### 4. Clarifying Questions

- **Q1:** Should the diagram show all 8 completion paths (Planner → Spec → ... → Complete) or focus on gate decision trees? **Assumption: Show full linear flow with gate decision trees at gate nodes (branch on PASS/FAIL/ESCALATE).**
- **Q2:** Should early-exit FAIL paths show explicit "back to Agent X" routing or just return arrows? **Assumption: Explicit routing (e.g., "FAIL → back to Spec Agent") for clarity.**
- **Q3:** Should WARN outcomes be distinct from FAIL/PASS/ESCALATE or merged into one outcome? **Assumption: WARN is distinct outcome (emitted by some gates, non-blocking, continues to next stage with advisory).**

---

### Requirement 02: Runbook — "How to Run Gates Locally"

#### 1. Spec Summary

**Description:** A prose section in the Milestone 902 README that provides operator-friendly instructions for running validation gates locally. The runbook must include:
- Brief overview of gate system (gates run automatically in CI, can be invoked manually)
- Mode explanation (shadow vs blocking)
- Copy-paste command examples
- Decision tree for interpreting gate outcomes (PASS/FAIL/WARN/ESCALATE)
- Links to gate specs for detailed troubleshooting

**Runbook location:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` under new section "How to Run Gates Locally"

**Runbook structure:**
```
## How to Run Gates Locally

### Overview
[Prose: Gates run automatically in CI, but can be invoked locally for testing/debugging]

### Modes
[Prose: Explain shadow (advisory, exit 0) vs blocking (enforcement, exit non-zero on FAIL)]

### Running All Gates (M902 Gate Set)
[Code block: python ci/scripts/gate_runner.py --gate-set m902 --mode shadow]

### Running Individual Gates
[Code blocks for each gate: spec_completeness_check, static_analysis_check, etc.]

### Gate Command Reference
[Table: Gate name, CLI invocation, mode, description]

### Decision Tree
[Prose + flowchart or bullet-point tree: If gate returns FAIL → action; If WARN → action; If ESCALATE → action]

### Troubleshooting
[Links to specs, artifact locations, common issues]
```

**Constraints:**
- Prose must be operator-friendly (non-technical language where possible)
- Commands must be copy-paste ready and executable from repo root
- All gate names must match gate_registry.json exactly
- CLI flags must match gate_runner.py CLI (verify --help output)
- No duplication of existing gate-specific docs (e.g., static analysis section already in README)
- Decision tree must cover PASS, FAIL, WARN, ESCALATE outcomes
- Links to specs must be accurate (file paths verified)

**Assumptions:**
- Operators have Python 3.11+, git, and repo access
- Gate runner lives at ci/scripts/gate_runner.py (per M902-01 spec)
- gate_registry.json is authoritative for gate names and CLI patterns
- Task hooks (e.g., task hooks:static-analysis) are optional (may not all be defined in Taskfile.yml)

**Scope:** Runbook applies to all six gates in M902 (spec_completeness, static_analysis, governance, planner, reviewer, learning).

#### 2. Acceptance Criteria

- **AC-02.1:** Runbook section titled "How to Run Gates Locally" exists in README.md
- **AC-02.2:** Runbook includes overview prose (1-2 paragraphs) explaining gate system and when to run gates manually
- **AC-02.3:** Runbook explains shadow vs blocking mode with concrete example (e.g., "shadow mode exits 0 regardless of violations; blocking mode exits non-zero on FAIL")
- **AC-02.4:** Runbook includes copy-paste command examples:
  - Run all gates in shadow mode
  - Run individual gates (at least spec_completeness, static_analysis, governance)
  - References to Task invocations if Taskfile tasks exist
- **AC-02.5:** All gate names in examples match gate_registry.json exactly
- **AC-02.6:** All CLI flags in examples are valid (match gate_runner.py --help output)
- **AC-02.7:** Runbook includes decision tree or flowchart showing:
  - PASS outcome → continue to next stage
  - FAIL outcome → return to originating agent with remediation hints
  - WARN outcome → review output, may trigger M903 enforcement
  - ESCALATE outcome → continue with advisory metadata, may trigger M903 escalation policy
- **AC-02.8:** Decision tree includes example actions (e.g., "If spec_completeness_check FAIL: fix missing spec sections and re-run")
- **AC-02.9:** Runbook links to gate spec documents (e.g., "For detailed spec, see project_board/specs/902_02_static_analysis_gate_spec.md")
- **AC-02.10:** Runbook mentions artifact output locations (e.g., gate results in ci/artifacts/ or project_board/checkpoints/)
- **AC-02.11:** Runbook word count is 300-500 words (keeps it as operator's quick-reference)

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Command examples outdated (gate_runner.py CLI changes) | Operators run incorrect commands | Verify gate_runner.py --help at time of writing; add note "commands as of [date]" |
| Taskfile tasks may not exist or differ by name | Copy-paste commands fail | Verify task names in Taskfile.yml before including; use fallback python ci/scripts/gate_runner.py commands |
| Decision tree too simplistic (doesn't cover edge cases) | Operators unsure how to interpret composite outcomes | Link to gate specs for detailed decision logic; runbook tree is simplified/high-level |
| Links to specs become stale | Broken references | Validate file paths exist before final commit; grep for spec file paths |

#### 4. Clarifying Questions

- **Q1:** Should the runbook show example gate outputs (JSON) or just command invocation? **Assumption: Command invocation only; spec details in gate spec documents.**
- **Q2:** Should task hooks be included if they may not exist in all environments? **Assumption: Include them with a note "if task defined in Taskfile.yml"; provide fallback python commands.**

---

### Requirement 03: Gate Reference — Per-Gate Documentation Sections

#### 1. Spec Summary

**Description:** Detailed documentation for each of the six gates, providing operator/implementer context without duplicating gate specs. Each gate reference section must include:
- **Purpose:** What the gate checks, when it runs
- **Inputs:** What data/files the gate needs
- **Artifacts:** Output files and their locations
- **Outputs:** Gate status (PASS/FAIL/WARN/ESCALATE) and what each means
- **Decision Logic:** How outcomes map to agent actions
- **Spec Link:** Reference to detailed gate spec (project_board/specs/)
- **Troubleshooting:** Common issues and remediation hints

**Gate reference location:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` under new section "Gate Reference"

**Per-gate sections (6 total):**

1. **spec_completeness_check**
   - Purpose: Validates specification .md file contains required sections for ticket type
   - Inputs: Spec file path, ticket type (api, destructive, randomness, load-open, generic)
   - Artifacts: spec_completeness_check output JSON, missing sections list
   - Outputs: PASS (all sections present) | FAIL (missing sections listed)
   - Decision: FAIL → back to Spec Agent; PASS → proceed
   - Spec: project_board/specs/902_06_spec_gate_spec.md
   - Troubleshooting: Check spec file path, verify ticket type matches spec type

2. **static_analysis_check**
   - Purpose: Run Python/TypeScript/Godot/duplication analysis tools; aggregate violations
   - Inputs: Source tree (asset_generation/python, web/frontend, scripts/, etc.)
   - Artifacts: static_analysis_check output JSON, per-tool logs (ruff, eslint, jscpd, etc.)
   - Outputs: PASS (no violations above baseline) | WARN (violations below threshold, M903 enforcement) | FAIL (fatal tool error)
   - Decision: WARN/FAIL → review JSON, fix violations or suppress per M902-03 rules
   - Spec: project_board/specs/902_02_static_analysis_gate_spec.md
   - Troubleshooting: Check tool availability (which ruff, npm list eslint), config files, tool logs

3. **governance_check**
   - Purpose: Scan code for governance rule violations (6 categories: architecture, exception safety, reflection, async, observability, integrity)
   - Inputs: Git diff (staged changes) or file paths
   - Artifacts: governance_check output JSON, suppression scanning results
   - Outputs: PASS (all rules compliant) | WARN (violations with valid suppressions) | FAIL (violations without suppressions)
   - Decision: WARN/FAIL → add suppressions per M902-03 suppression format + issue link, or refactor to comply
   - Spec: project_board/specs/902_03_handoff_governance_spec.md
   - Troubleshooting: See governance rule catalog (902_03 spec); enable verbose mode; check suppression format

4. **planner_check**
   - Purpose: Detect cyclic dependencies, self-loops, orphaned dependencies in ticket dependency graphs
   - Inputs: Milestone folder path, ticket YAML dependency metadata
   - Artifacts: planner_check output JSON, dependency graph, cycle paths
   - Outputs: PASS (no cycles) | WARN (cycles detected, path listed)
   - Decision: WARN → break cycles by reordering tickets or removing cross-milestone deps (Planner Agent task)
   - Spec: project_board/specs/902_06_planner_gate_spec.md
   - Troubleshooting: Verify ticket YAML format (Dependencies: list under ## WORKFLOW STATE), check milestone folder structure

5. **reviewer_check**
   - Purpose: Scan git diff (staged changes) for new TODO/FIXME comments and suppressions without issue links
   - Inputs: Git diff --cached (staged files)
   - Artifacts: reviewer_check output JSON (file + line number per violation)
   - Outputs: PASS (no new violations) | WARN (violations found, file + line reported)
   - Decision: WARN → address TODOs/FIXMEs or add issue links to suppressions before commit
   - Spec: project_board/specs/902_06_reviewer_gate_spec.md
   - Troubleshooting: Verify git diff availability (must run in repo context), check file encoding (UTF-8)

6. **learning_check**
   - Purpose: Detect forbidden phrases in checkpoint learning outputs (hacks, temporary workarounds, XXX, KLUDGE, etc.)
   - Inputs: Learning output .md files in project_board/checkpoints/
   - Artifacts: learning_check output JSON, policy file (project_board/902_06_learning_gate_policy.yml)
   - Outputs: PASS (no forbidden phrases) | FAIL (phrases found, context + remediation)
   - Decision: FAIL → rewrite learning output to reflect intent without hack language; M903 can customize policy
   - Spec: project_board/specs/902_06_learning_gate_spec.md
   - Troubleshooting: Edit policy YAML to adjust patterns; see default patterns in project_board/902_06_learning_gate_policy.yml

**Constraints:**
- Each gate section must be 150-250 words (concise, operator-friendly)
- Must not repeat prose from gate specs (link instead)
- Must cover all six gates (complete coverage)
- Links to specs must be accurate (file paths verified)
- Troubleshooting hints must be actionable (not vague)
- Format consistent across all six gates (same subsection order: Purpose, Inputs, Artifacts, Outputs, Decision, Spec, Troubleshooting)

**Assumptions:**
- All gates in gate_registry.json are functional (M902-01/02/03/06 COMPLETE)
- Gate specs are stable (all checkpoint assumptions frozen with HIGH-MEDIUM confidence)
- Operators familiar with JSON output format (references to "JSON output" without detailed schema)

**Scope:** Gate reference applies to all six gates in M902 (not M902-07 audit pipeline, which is operational tool).

#### 2. Acceptance Criteria

- **AC-03.1:** Gate reference section titled "Gate Reference" or "Gate-Specific Documentation" exists in README.md
- **AC-03.2:** All six gates are documented (spec_completeness, static_analysis, governance, planner, reviewer, learning)
- **AC-03.3:** Each gate section includes subsections: Purpose, Inputs, Artifacts, Outputs, Decision, Spec Link, Troubleshooting
- **AC-03.4:** Each gate section is 150-250 words (concise, not verbose)
- **AC-03.5:** Gate names in reference sections match gate_registry.json exactly
- **AC-03.6:** Outputs for each gate are documented (e.g., PASS, FAIL, WARN, ESCALATE, per gate)
- **AC-03.7:** Decision logic is clear (e.g., "FAIL → back to Agent X"; "WARN → continue with advisory")
- **AC-03.8:** Spec links point to correct files:
  - spec_completeness → 902_06_spec_gate_spec.md
  - static_analysis → 902_02_static_analysis_gate_spec.md
  - governance → 902_03_handoff_governance_spec.md
  - planner → 902_06_planner_gate_spec.md
  - reviewer → 902_06_reviewer_gate_spec.md
  - learning → 902_06_learning_gate_spec.md
- **AC-03.9:** All spec link paths verified to exist (grep before commit)
- **AC-03.10:** Troubleshooting hints are actionable (e.g., "check tool availability", "verify git diff context", "edit policy YAML")
- **AC-03.11:** No duplication with existing gate-specific docs (e.g., static analysis section already in milestone README)
- **AC-03.12:** Format consistent across all six gates (same subsection order, similar word count)
- **AC-03.13:** All gates are in M902 scope (exclude M902-07 audit pipeline)

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Spec link paths incorrect or files moved | Broken references | Verify paths exist by grepping before final commit; use relative paths (project_board/specs/...) |
| Gate outputs differ from documented (gate implementation changes) | Documentation misleads operators | Verify gate implementations (gate_registry.json + gate module code) match spec output list; mark as "as of [date]" |
| Per-gate detail too sparse (missing troubleshooting hints) | Operators unable to debug failures | Ensure troubleshooting section references concrete files/config locations (not generic advice) |
| Duplication with existing static analysis section | Reader confusion, maintenance burden | Review existing README sections; if static_analysis section exists, merge into gate reference or consolidate |

#### 4. Clarifying Questions

- **Q1:** Should troubleshooting include links to gate implementation code (ci/scripts/gates/*.py) or just spec links? **Assumption: Spec links only; implementation details deferred to developers; include tool CLI hints (which ruff, npm list).**

---

### Requirement 04: README Integration and Updates

#### 1. Spec Summary

**Description:** Update `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` to include the new diagram, runbook, and gate reference sections. Preserve existing content (Overview, Tickets, Running Static Analysis Gate, Configuration, Exclusions, Documentation References, Next Steps).

**Integration approach:**
- Insert new "Workflow Diagram and Agent Gating" section after Tickets section
- Insert new "How to Run Gates Locally" section after diagram
- Insert new "Gate Reference" section after runbook
- Consolidate existing "Running Static Analysis Gate" section with new gate reference (avoid duplication)
- Update existing links if stale

**Constraints:**
- Must preserve existing sections (Overview, Tickets, etc.)
- Must not break Markdown formatting
- Must keep overall file size <500 lines (operator's quick-reference)
- All links must be valid (no 404s)
- No duplication with existing gate-specific docs

**Assumptions:**
- Existing README structure is stable (no concurrent changes expected during M902-08)
- Diagram renders correctly in GitHub (tested in online editor)
- New sections fit without making README unwieldy

**Scope:** Updates to README.md only; no changes to other files.

#### 2. Acceptance Criteria

- **AC-04.1:** Updated README.md file is syntactically valid Markdown
- **AC-04.2:** Diagram section titled "Workflow Diagram and Agent Gating" appears after Tickets section
- **AC-04.3:** Diagram renders correctly in GitHub Markdown viewer (verified by pushing to branch)
- **AC-04.4:** Runbook section titled "How to Run Gates Locally" appears after diagram section
- **AC-04.5:** Gate reference section titled "Gate Reference" appears after runbook section
- **AC-04.6:** All existing sections preserved (Overview, Tickets, Configuration, Exclusions, Documentation References, Next Steps)
- **AC-04.7:** No duplication with existing "Running Static Analysis Gate" section (either consolidate or deconflict)
- **AC-04.8:** All links in README are valid (files exist, no 404s)
- **AC-04.9:** Updated README file size is <500 lines
- **AC-04.10:** Markdown formatting is correct (headers, code blocks, lists, links all render properly)
- **AC-04.11:** Diagram explanation paragraph (1-3 sentences) summarizes what diagram shows and links to checkpoint for design decisions

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Diagram syntax breaks GitHub Markdown rendering | File appears broken online (even if valid Mermaid) | Test by pushing to feature branch and viewing online (not just local markdown viewer) |
| Links become stale (files moved/renamed post-commit) | Operators encounter broken references | Use relative paths; verify paths exist at commit time; plan M903 link audits |
| File size grows too large | README becomes unwieldy, hard to scan | Keep gate reference sections concise (150-250 words each); defer detailed troubleshooting to specs |
| Existing "Running Static Analysis Gate" section conflicts with new gate reference | Duplication, maintenance burden | Review existing section; consolidate into gate reference or remove if subsumed |

#### 4. Clarifying Questions

- **Q1:** Should the diagram explanation link to checkpoint log (project_board/checkpoints/M902-08/2026-05-16T-planning.md) for design decisions? **Assumption: Yes, one-line link after diagram explanation.**

---

### Requirement 05: CLAUDE.md Compatibility Verification

#### 1. Spec Summary

**Description:** Verify that new runbook commands and gate descriptions do not contradict CLAUDE.md "Common Workflows" section or the "Command source-of-truth order" hierarchy (Taskfile.yml → CI scripts → CLAUDE.md → README).

**Verification approach:**
- Compare gate commands in runbook against gate_runner.py CLI (verify --help output)
- Verify Task invocations in runbook against Taskfile.yml (check task names exist)
- Check that no new commands are added to README that should be in CLAUDE.md
- Ensure command ordering follows source-of-truth hierarchy (Taskfile task → gate_runner.py fallback)
- Document any discrepancies and resolution approach

**Constraints:**
- Must NOT modify CLAUDE.md (out of scope per workflow_enforcement_v1.md)
- Must verify consistency, not enforce changes
- If conflicts discovered, document recommendation (defer to M903 or resolve now)

**Assumptions:**
- CLAUDE.md "Common Workflows" is authoritative for command style
- gate_runner.py CLI is stable (verified in M902-01 tests)
- Taskfile.yml task names are frozen (no concurrent edits expected)

**Scope:** Verification only; no implementation changes in scope for M902-08.

#### 2. Acceptance Criteria

- **AC-05.1:** Compatibility verification document created (project_board/test_designs/M902-08_claude_compatibility_check.md) or checkpointed
- **AC-05.2:** Document lists all gate commands from runbook
- **AC-05.3:** Document verifies each command against gate_runner.py --help output
- **AC-05.4:** Document checks Taskfile.yml for task definitions (if referenced in runbook)
- **AC-05.5:** Document confirms command ordering matches source-of-truth hierarchy (Taskfile → CI scripts → CLAUDE.md)
- **AC-05.6:** Document states either "No contradictions found" or lists conflicts with resolution approach
- **AC-05.7:** If conflicts found, document recommendation is clear (e.g., "Defer CLAUDE.md updates to M903 ticket X" or "Update CLAUDE.md in this ticket")
- **AC-05.8:** CLAUDE.md is NOT modified (scope constraint verified by git diff)
- **AC-05.9:** Verification document includes checklist:
  - [ ] All gate commands match gate_runner.py CLI flags
  - [ ] All Taskfile tasks reference gates correctly (if defined)
  - [ ] No ad-hoc invocation patterns (all via gate_runner.py)
  - [ ] No contradictions with CLAUDE.md command source-of-truth order
  - [ ] No new commands added to README that belong in CLAUDE.md

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| CLAUDE.md changes concurrently with M902-08 | Verification becomes outdated | Verify CLAUDE.md hasn't changed by reading file at verification time |
| Taskfile tasks renamed/removed post-M902-06 | Task references in runbook fail | Verify task names in Taskfile.yml at time of writing; use fallback python commands if task undefined |
| gate_runner.py CLI flags change post-M902-01 | Commands in runbook become invalid | Verify gate_runner.py --help at time of writing; gate runner is stable (M902-01 COMPLETE) |
| Conflict discovered, but M902-08 scope doesn't permit fix | Blocking issue, undefined resolution | Document conflict and defer to M903 with clear ticket recommendation |

#### 4. Clarifying Questions

- **Q1:** If conflicts found but M902-08 scope doesn't permit CLAUDE.md edit, should M902-08 be blocked or should recommendation be deferred to M903? **Assumption: Document conflict, recommend M903 ticket, do NOT block M902-08. Runbook in milestone README is valid reference; CLAUDE.md updates deferred.**

---

### Requirement 06: Acceptance Criteria Verification

#### 1. Spec Summary

**Description:** Verify that all three ticket acceptance criteria (from ticket file) are satisfied by the deliverables:

1. **AC (ticket):** At least one checked-in Mermaid diagram renders in GitHub and matches implemented pipeline at high level
2. **AC (ticket):** Autopilot / agent runbooks mention where gates occur and what artifacts are required to pass
3. **AC (ticket):** No contradictions with CLAUDE.md command source-of-truth ordering; if changes are needed, update CLAUDE.md minimally and intentionally

**Verification approach:**
- Create verification document mapping each ticket AC to deliverables
- Provide evidence for each AC (link to README sections, diagram checklist, runbook content)
- Confirm all ACs satisfied with no blockers

**Constraints:**
- Verification must be explicit and unambiguous (not assumed)
- Evidence must be concrete (file paths, checklist items)
- If any AC not fully satisfied, document gap and mitigation

**Assumptions:**
- All prior requirements (Req 01-05) completed successfully
- No new gates added post-Req 05
- Diagram and runbook are final and committed

**Scope:** Verification only; no additional work beyond confirming ACs.

#### 2. Acceptance Criteria

- **AC-06.1:** Acceptance criteria verification document created (project_board/test_designs/M902-08_acceptance_verification.md) or checkpointed
- **AC-06.2:** Document explicitly maps ticket AC1 to Req 01 diagram deliverable
- **AC-06.3:** Document verifies AC1 with checklist:
  - [ ] Diagram checked into README.md ✓
  - [ ] Diagram renders in GitHub ✓ (verified by branch push and visual inspection)
  - [ ] Diagram shows all 7 stages ✓
  - [ ] Diagram shows all 6 gates ✓
  - [ ] Diagram shows PASS/FAIL/ESCALATE outcomes ✓
  - [ ] Early-exit and escalation paths distinct ✓
- **AC-06.4:** Document explicitly maps ticket AC2 to Req 02 runbook + Req 03 gate reference deliverables
- **AC-06.5:** Document verifies AC2 with checklist:
  - [ ] Runbook section present ✓
  - [ ] Runbook describes gate placement (when gates run in workflow) ✓
  - [ ] Runbook describes artifacts (output files, JSON, logs) ✓
  - [ ] Gate reference documents all 6 gates ✓
  - [ ] Gate reference includes decision trees ✓
  - [ ] Gate reference includes spec links ✓
- **AC-06.6:** Document explicitly maps ticket AC3 to Req 05 CLAUDE.md compatibility verification
- **AC-06.7:** Document verifies AC3 with checklist:
  - [ ] Compatibility verification completed ✓
  - [ ] No contradictions found OR conflicts documented with resolution ✓
  - [ ] CLAUDE.md not modified (scope constraint) ✓
  - [ ] Recommendation clear (deferred to M903 or resolved) ✓
- **AC-06.8:** Document includes overall sign-off: "All 3 ticket ACs satisfied. Ready for human review and merge."
- **AC-06.9:** If any AC not fully satisfied, document explains gap and mitigation approach

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| AC1 verification superficial (assumes diagram renders without testing) | Diagram may fail on GitHub | Explicitly note "verified by pushing to branch and viewing rendered README" |
| AC2 verification incomplete (misses runbook or gate reference) | Ticket accepted but incomplete | Map both runbook (Req 02) AND gate reference (Req 03) to AC2 |
| AC3 contradiction discovered too late (after merge) | Blocking issue unresolved | Verify CLAUDE.md compatibility (Req 05) before acceptance sign-off |

#### 4. Clarifying Questions

- **Q1:** Should AC3 verification require pushing to GitHub and testing CLAUDE.md rendering, or is document review sufficient? **Assumption: Document review + file path verification (grep for CLAUDE.md) sufficient; GitHub rendering tested in AC1 verification.**

---

## Non-Functional Requirements

### Requirement NF-01: Documentation Quality and Maintainability

#### 1. Spec Summary

**Description:** Documentation must be clear, maintainable, and operationally useful.

**Constraints:**
- Diagram must be scannable in 2-3 minutes (high-level, not exhaustive)
- Runbook must be operator-friendly (non-technical prose where possible)
- Gate reference sections must be consistent in format (same subsection order, similar word count)
- Links must be relative paths (project_board/specs/...) and verified to exist
- No jargon without explanation (define terms like "escalation", "shadow mode", "artifacts")
- No external dependencies (all content self-contained in repo)

**Assumptions:**
- Target audience is operators, Implementation Agents, and Test Designers (not Planner/Spec Agents exclusively)
- Readers have access to gate specs (specs are reference material, not replicated in runbook)
- README will be viewed in GitHub (native Markdown rendering)

**Scope:** All requirements (Req 01-06) must meet documentation quality standards.

#### 2. Acceptance Criteria

- **AC-NF-01.1:** Diagram includes legend or caption explaining agent roles, gate types, outcome colors, and routing paths
- **AC-NF-01.2:** Runbook defines "shadow mode" and "blocking mode" before using terminology
- **AC-NF-01.3:** Gate reference explains "ESCALATE" outcome (distinct from FAIL) with example
- **AC-NF-01.4:** All internal links use relative paths (project_board/specs/..., not full URLs)
- **AC-NF-01.5:** All relative links verified to point to existing files (grep before commit)
- **AC-NF-01.6:** Runbook and gate reference use consistent terminology (e.g., all gates called "gates", not "validators" or "checks")
- **AC-NF-01.7:** No unexplained jargon (all terms defined in context or linked to spec)
- **AC-NF-01.8:** Diagram is scannable (fits in single view, not horizontally scrolled in GitHub)
- **AC-NF-01.9:** README sections are clearly titled and ordered logically (diagram → runbook → reference → troubleshooting)

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Jargon ("escalation", "shadow mode") unexplained | Readers confused | Define each term in runbook before use; link to gate specs for detailed semantics |
| Diagram too granular (shows implementation detail) | Operators overwhelmed | Limit to high-level stages; defer step-by-step detail to gate specs and runbook |
| Gate reference sections inconsistent in format | Reader must re-learn structure per section | Use template for all 6 gates: Purpose → Inputs → Artifacts → Outputs → Decision → Spec → Troubleshooting |

#### 4. Clarifying Questions

- **Q1:** Should runbook include error codes or only prose descriptions? **Assumption: Prose descriptions with links to JSON output examples (in gate specs, not duplicated in runbook).**

---

### Requirement NF-02: Mermaid Syntax Compliance

#### 1. Spec Summary

**Description:** Diagram must use valid Mermaid syntax and render in GitHub without errors.

**Constraints:**
- Must use Mermaid flowchart syntax (graph LR or graph TD)
- Must not use experimental Mermaid features
- Must avoid overly nested subgraphs (readability)
- Must pass validation in online Mermaid editor (https://mermaid.live)
- Must render in GitHub Markdown viewer (tested by branch push)

**Assumptions:**
- GitHub natively supports Mermaid diagrams (as of 2021+)
- Diagram will be embedded in Markdown code block with ```mermaid``` fence
- No custom CSS or styling required

**Scope:** Req 01 (Workflow Diagram) must meet Mermaid syntax compliance.

#### 2. Acceptance Criteria

- **AC-NF-02.1:** Diagram uses valid Mermaid flowchart syntax (flowchart or graph keyword)
- **AC-NF-02.2:** All nodes are valid Mermaid node types (rectangle, diamond, rounded, etc.)
- **AC-NF-02.3:** All connections use valid Mermaid arrow syntax (-->, --, -|label|->)
- **AC-NF-02.4:** Diagram validates in online Mermaid editor without errors or warnings
- **AC-NF-02.5:** Diagram renders in GitHub Markdown viewer (verified by pushing to branch and viewing)
- **AC-NF-02.6:** No experimental Mermaid features used (only stable syntax)
- **AC-NF-02.7:** Subgraph nesting (if used) is at most 1-2 levels deep
- **AC-NF-02.8:** Diagram is legible (no overlapping nodes, clear connections)

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mermaid syntax changes between versions | Diagram may fail in newer GitHub/Mermaid | Use stable syntax only (no experimental features); test in online editor before commit |
| GitHub Mermaid renderer differs from online editor | Diagram works locally but fails online | Test by pushing to branch and viewing in GitHub (not just online editor) |
| Diagram too complex (many nodes) | Mermaid rendering engine struggles | Limit to ~15-20 nodes; use subgraphs for clustering; simplify if needed |

#### 4. Clarifying Questions

- **Q1:** Should the diagram use subgraphs to group agents by role (Planner, Spec, Implementation, Review, Learning) or keep flat? **Assumption: Use subgraphs for clarity, but limit to 1-2 levels (not nested subgraphs within subgraphs).**

---

### Requirement NF-03: Version Control and Commit Discipline

#### 1. Spec Summary

**Description:** All changes must be committed with clear, descriptive messages per Conventional Commits.

**Constraints:**
- One commit per logical change (not one giant commit for all deliverables)
- Commit message format: `feat(902-08): <description>`
- Commit message must reference ticket (M902-08) and what was updated
- No working tree left dirty (all changes committed before handoff)

**Assumptions:**
- Commits will be pushed to origin (part of integration workflow)
- Conventional Commits are enforced by lefthook or CI (already in project)

**Scope:** All requirements (Req 01-06) must be committed with appropriate messages.

#### 2. Acceptance Criteria

- **AC-NF-03.1:** README.md updates committed with message like `feat(902-08): add workflow diagram and runbook sections to milestone README`
- **AC-NF-03.2:** Test design documents committed with message like `docs(902-08): add specification and design docs for workflow visualization`
- **AC-NF-03.3:** All commits follow Conventional Commits format (feat/docs/refactor, scope in parens)
- **AC-NF-03.4:** Commit messages reference ticket ID (902-08) or linked concept
- **AC-NF-03.5:** No commits with "WIP", "temp", "fix typo" without context

#### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Commits bundled together (hard to bisect) | History becomes harder to navigate | Split commits by concern: README diagram → README runbook → README gate ref → verification docs |
| Commit messages vague or missing context | Next agent unsure what changed | Include ticket ID and summary (e.g., "feat(902-08): add gate reference to milestone README") |

#### 4. Clarifying Questions

- **Q1:** Should diagram and runbook be one commit or separate? **Assumption: One commit (both are README updates); verification docs separate commit.**

---

## Cross-Requirement Dependencies and Integration Points

### Integration with M902-01 (Gate Runner Framework)

- Diagram references gate_runner.py CLI (Req 01, 02)
- Runbook includes gate_runner.py command examples (Req 02)
- Gate reference links to gate_registry.json (Req 03)
- Compatibility verification checks gate_runner.py --help (Req 05)

**Dependency status:** M902-01 COMPLETE; no blocking issues.

### Integration with M902-02 (Static Analysis Gate)

- Diagram shows static_analysis_check gate placement (Req 01)
- Runbook includes static_analysis_check command example (Req 02)
- Gate reference documents static_analysis_check in detail (Req 03)
- Existing README section "Running Static Analysis Gate" may duplicate new gate reference (Req 04 integration point)

**Dependency status:** M902-02 IMPLEMENTATION_BACKEND (not COMPLETE); checkpoint confirms gate is stable.

### Integration with M902-03 (Governance Rules)

- Diagram shows governance_check gate placement (Req 01)
- Runbook includes governance_check command example (Req 02)
- Gate reference documents governance_check (Req 03)

**Dependency status:** M902-03 COMPLETE; no blocking issues.

### Integration with M902-04 (Handoff Metadata & Escalation)

- Diagram shows ESCALATE outcome routing (Req 01)
- Runbook explains escalation vs FAIL outcomes (Req 02)
- Gate reference describes ESCALATE for all applicable gates (Req 03)

**Dependency status:** M902-04 COMPLETE; no blocking issues.

### Integration with M902-05 (PreToolUse Hooks)

- Diagram shows PreToolUse as separate enforcement layer (Req 01)
- Runbook may reference PreToolUse hooks in "Enforcement Layers" section (Req 02, optional)

**Dependency status:** M902-05 COMPLETE; no blocking issues.

### Integration with M902-06 (Per-Stage Gates)

- Diagram shows planner_check, reviewer_check, learning_check gates (Req 01)
- Runbook includes examples for all three per-stage gates (Req 02)
- Gate reference documents all three gates (Req 03)

**Dependency status:** M902-06 COMPLETE; no blocking issues.

### Integration with M902-07 (Governance Audit Pipeline)

- Diagram shows governance audit as operational tool (not blocking gate) (Req 01)
- Runbook may reference audit tool (Req 02, optional)
- Gate reference excludes audit from gating gates (Req 03 - only 6 gates, not 7)

**Dependency status:** M902-07 IMPLEMENTATION_BACKEND; spec complete.

### Integration with CLAUDE.md

- Req 05 verifies no contradictions with CLAUDE.md command source-of-truth
- Req 02 runbook may reference task hooks from Taskfile.yml (not modifying CLAUDE.md)
- Scope constraint: no CLAUDE.md modifications (out of scope per workflow_enforcement_v1.md)

**Integration status:** No modifications to CLAUDE.md; compatibility verified only.

---

## Checkpoint Protocol Resolutions

All ambiguities from the planning checkpoint are addressed by this specification:

1. **Canonical documentation locations:** PRIMARY = Milestone 902 README; SECONDARY = gate specs; NO modifications to CLAUDE.md (Req 04 integration, Req 05 compatibility)

2. **Diagram scope:** Single high-level Mermaid flowchart (Req 01); not per-stage diagrams; all 7 stages shown

3. **Early exits and escalation:** Distinct routing paths in diagram (FAIL = red/error, ESCALATE = yellow/advisory, PASS = green/success) (Req 01)

4. **Static analysis insertion:** Placement post-implementation, pre-review per CLAUDE.md ordering (Req 01, verified in Req 05)

5. **M902-07 audit positioning:** Operational tool, separate from handoff chain (Req 01 diagram shows as parallel/operational, not blocking)

6. **Mermaid validation:** Online editor + GitHub rendering (Req NF-02); test by branch push before final commit

7. **Runbook detail:** Prose + command examples + links to specs (Req 02); no duplication of gate spec prose

8. **CLAUDE.md compatibility:** Verified only, no edits (Req 05); defer any needed updates to M903

---

## Quality Assurance Gates

### Pre-Merge Checklist

Before final handoff to TEST_DESIGN:

- [ ] Diagram renders in GitHub Markdown viewer (test by pushing to feature branch)
- [ ] Diagram is valid Mermaid syntax (validate in online editor)
- [ ] All links in README verified (grep for project_board/specs/...)
- [ ] Runbook commands verified against gate_runner.py --help
- [ ] Gate reference sections consistent in format (all 6 gates)
- [ ] No duplication with existing README sections (consolidate if needed)
- [ ] CLAUDE.md compatibility verified (Req 05); no contradictions or CLAUDE.md edits
- [ ] All acceptance criteria (AC-01 through AC-06) explicitly satisfied
- [ ] Commits follow Conventional Commits format
- [ ] Working tree clean (all changes committed)

---

## Success Metrics

**Completion is achieved when:**

1. **Req 01 (Diagram):** Valid Mermaid diagram embedded in README.md, renders in GitHub, shows all 7 stages, 6 gates, and 3 outcome types with clear routing paths.

2. **Req 02 (Runbook):** Operator-friendly "How to Run Gates Locally" section with prose overview, mode explanation, command examples, decision tree, and spec links (300-500 words).

3. **Req 03 (Gate Reference):** Complete per-gate documentation for all 6 gates (spec_completeness, static_analysis, governance, planner, reviewer, learning) with Purpose, Inputs, Artifacts, Outputs, Decision, Spec Link, Troubleshooting.

4. **Req 04 (README Integration):** Updated README.md with new sections integrated logically, no duplication, all links valid, file size <500 lines.

5. **Req 05 (CLAUDE.md Compatibility):** Verification document confirms no contradictions with CLAUDE.md, all commands valid, no CLAUDE.md modifications.

6. **Req 06 (Acceptance Verification):** All 3 ticket ACs explicitly satisfied with evidence; ready for human review and merge.

7. **Req NF-01 (Documentation Quality):** Clear, scannable, operator-friendly; consistent terminology; no unexplained jargon.

8. **Req NF-02 (Mermaid Compliance):** Valid Mermaid syntax; renders in GitHub and online editor; legible, bounded scope.

9. **Req NF-03 (Commit Discipline):** All changes committed with clear, descriptive Conventional Commits messages.

---

## Risks and Mitigation Summary

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Mermaid syntax fails in GitHub rendering | HIGH | Test by pushing to feature branch; validate in online editor first |
| Gate placement incorrect (outdated relative to implementation) | MEDIUM | Verify against M902-01/02/03/06 specs; planning checkpoint HIGH confidence |
| Commands outdated (gate_runner.py CLI changes) | MEDIUM | Verify gate_runner.py --help at time of writing; mark date/version |
| Links become stale (files moved/renamed) | MEDIUM | Use relative paths; verify at commit time; plan M903 link audits |
| Diagram too complex (many nodes, unreadable) | MEDIUM | Use subgraphs for clarity; limit to 15-20 nodes; simplify if needed |
| Per-gate documentation incomplete (missing troubleshooting) | LOW | Use gate specs as reference; link instead of duplicate; ensure hints are actionable |
| CLAUDE.md contradiction discovered late | LOW | Verify early (Req 05); document recommendation; don't block on M903 deferral |

---

## Summary for Test Designer

This specification defines **6 functional requirements** (Req 01-06) and **3 non-functional requirements** (Req NF-01 to NF-03) for Milestone 902 documentation updates.

**Core deliverables:**
1. Valid Mermaid diagram showing Agent → Gate → Agent workflow (7 stages, 6 gates, 3 outcomes)
2. Operator runbook "How to Run Gates Locally" (300-500 words, decision tree, command examples)
3. Per-gate reference documentation for all 6 gates (Purpose, Inputs, Outputs, Decision, Spec Link, Troubleshooting)
4. README.md integration (diagram + runbook + reference sections, <500 lines total)
5. CLAUDE.md compatibility verification (no contradictions, no edits)
6. Acceptance criteria verification (all 3 ticket ACs satisfied)

**Success metrics:** Diagram renders in GitHub, runbook is actionable, gate reference complete and consistent, README integrated logically, no CLAUDE.md contradictions, all ACs satisfied.

**Key assumptions:**
- All gates (M902-01/02/03/06) stable and functional
- Diagram scope is high-level (not step-by-step detail)
- Early-exit/escalation paths distinct in diagram
- CLAUDE.md not modified (verification only)
- All links relative paths, verified to exist

**Critical dependencies:** M902-01, M902-02, M902-03, M902-04, M902-05, M902-06, M902-07 (all complete or stable)

---

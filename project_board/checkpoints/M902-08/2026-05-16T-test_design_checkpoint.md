# M902-08 Test Design Checkpoint

**Date:** 2026-05-16  
**Agent:** Test Designer Agent  
**Stage:** TEST_DESIGN  
**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md

---

## Scope Analysis

M902-08 is a **documentation-only ticket** (updates to README, diagram, runbook). Specification frozen with 6 functional requirements (Req 01-06) and 3 non-functional requirements (Req NF-01 to NF-03).

Per workflow_enforcement_v1.md: "Tests must verify executable behavior, not documentation prose. Treat tests that assert markdown/ticket/spec wording under `project_board/**` as invalid unless the ticket explicitly targets documentation tooling/parsing behavior."

---

## Critical Ambiguity

**Would have asked:** Should TEST_DESIGN write tests that assert README markdown structure/content (e.g., "README section titled 'Workflow Diagram and Agent Gating' exists"), or should it focus on behavioral tests of the gates themselves (unit tests of gate CLI, mermaid syntax validation, etc.)?

**Assumption made:** 
1. **README schema validation** is acceptable: parse README as structured data, validate sections, check links are resolvable files. This is integration-style testing of documentation artifacts (not asserting prose wording).
2. **Mermaid syntax validation** is acceptable: verify the diagram is valid Mermaid (parseable, renders without errors). This tests the diagram as a structured artifact.
3. **Gate CLI behavior tests** are out of scope for M902-08: gates (static_analysis_check, governance_check, etc.) are already tested in M902-01/02/03/06 tests. Those tests stay in their respective modules. M902-08 tests focus on documentation integration only.
4. **Command validation** is acceptable: verify commands in the runbook (e.g., `python ci/scripts/gate_runner.py static_analysis_check`) are valid against gate_runner.py CLI schema.

**Confidence:** MEDIUM-HIGH. The spec explicitly defines README integration (Req 04) and acceptance criteria that are testable as structured data (section headers, link targets, command flags). These are observable behavioral assertions about documentation artifacts, not prose-content assertions.

---

## Test Strategy

Write tests under `tests/ci/test_m902_08_documentation_integration.py` that:
1. Parse `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md`
2. Validate section structure (headers, code blocks)
3. Validate Mermaid diagram syntax (embedded in README)
4. Validate link targets exist (relative paths to gate specs, etc.)
5. Validate gate commands in runbook examples match gate_runner.py schema
6. Validate gate names in gate reference match gate_registry.json

**Note:** Test file name follows convention (subsystem + behavior, no ticket ID): `test_m902_08_documentation_integration.py`. Traceability to M902-08 goes in module docstring.

---

## Acceptance Criteria Mapping to Tests

**Ticket AC1:** "At least one checked-in Mermaid diagram renders in GitHub and matches the implemented pipeline at a high level."
- **Test:** Extract Mermaid diagram from README, validate syntax against Mermaid spec.
- **Observable:** Diagram parses without errors and contains required nodes (all 7 stages, all 6 gates).

**Ticket AC2:** "Autopilot / agent runbooks mention where gates occur and what artifacts are required to pass."
- **Test:** Parse runbook sections for gate names, validate gates exist in gate_registry.json, validate artifact descriptions exist.
- **Observable:** All 6 gates documented with Purpose, Inputs, Artifacts sections.

**Ticket AC3:** "No contradictions with CLAUDE.md command source-of-truth ordering."
- **Test:** Parse runbook commands, validate against gate_runner.py CLI schema, check no forbidden patterns.
- **Observable:** Commands use standard gate_runner.py CLI format, no ad-hoc invocations, flags match schema.

---

## Test Design Notes

- **No prose assertions:** Tests do NOT assert exact wording like "Section must say exactly 'X'". Instead, assert structured data: section exists, code blocks contain gate names, links resolve.
- **Schema-based:** Use YAML/JSON parsing (gate_registry.json) and regex/AST parsing (README sections) as observable contracts.
- **Mermaid validation:** Use mermaid.cli or parse the diagram grammar to ensure nodes and connections are valid (not just "diagram is a string").
- **Link validation:** Verify relative paths like `project_board/specs/902_02_static_analysis_gate_spec.md` actually exist in the repo.

---

## Proceed to implementation.

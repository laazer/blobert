# M902-08 Test Break Stage Checkpoint

**Date:** 2026-05-16  
**Agent:** Test Breaker Agent  
**Stage:** TEST_BREAK  
**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md

---

## Scope

M902-08 is a documentation-only ticket requiring README updates with Mermaid diagram, runbook, and gate reference sections. TEST_BREAK stage: extend test suite with adversarial tests that expose edge cases, vulnerabilities, and hidden assumptions in the existing test contracts.

---

## Adversarial Test Suite

Created: `/tests/ci/test_m902_08_documentation_adversarial.py` (36 tests)

**Adversarial coverage matrix:**

| Dimension | Test Categories | Count | Example Tests |
|-----------|-----------------|-------|---------------|
| **Null/Empty** | Empty sections, sparse content | 3 | `test_gate_reference_sections_too_sparse`, `test_diagram_with_empty_node_labels` |
| **Boundary** | Min/max sizes, thresholds | 4 | `test_readme_max_section_size`, `test_mermaid_diagram_not_overly_complex` |
| **Type/Structure** | Malformed syntax, wrong structure | 5 | `test_diagram_with_malformed_mermaid_keywords`, `test_gate_reference_subsection_formatting_inconsistent` |
| **Invalid/Corrupt** | Typos, unregistered gates, bad refs | 6 | `test_diagram_stage_names_match_enforcement_enum`, `test_runbook_command_with_unregistered_gate_name`, `test_gate_reference_links_to_nonexistent_specs` |
| **Concurrency/Order** | Duplicates, ordering sensitivity | 4 | `test_readme_duplicate_sections`, `test_readme_section_ordering_backward`, `test_readme_gate_reference_before_runbook` |
| **Combinatorial** | Multiple edge factors | 3 | `test_diagram_with_unreachable_nodes` + empty labels, gate ref missing all gates |
| **Stress/Load** | Large data, complexity | 3 | `test_readme_max_section_size`, `test_gate_reference_section_not_excessive`, `test_mermaid_diagram_not_overly_complex` |
| **Mutation Testing** | Flip outcomes, change names | 3 | `test_diagram_outcome_labels_match_spec`, `test_diagram_all_gates_reachable_from_start`, `test_diagram_escape_paths_from_fail_outcome` |
| **Error Handling** | Graceful degradation, missing deps | 2 | `test_runbook_command_missing_required_arguments` |
| **Assumption Checks** | Implicit ordering, defaults | 3 | `test_diagram_arrow_syntax_consistency`, `test_mermaid_diagram_node_ids_not_matching_gate_names` |
| **Determinism** | Consistency, idempotency | 2 | `test_mermaid_diagram_parse_idempotency`, `test_gate_names_extracted_consistently` |
| **CLAUDE.md Compat** | Source-of-truth conflicts | 2 | `test_runbook_commands_use_wrong_task_invocation_style`, `test_runbook_references_undefined_task_names` |

---

## Critical Vulnerabilities Found

### 1. Mermaid Diagram Connectivity (HIGH)
**Risk:** Test `test_diagram_has_all_gates` checks gate presence but NOT connectivity.
- Vulnerability: Gates could be orphaned nodes (not connected to flow).
- Mitigation Test: `test_diagram_with_unreachable_nodes` ensures all nodes connected.
- Mutation: Add `G1[Orphaned Gate]` without arrow connections.

### 2. Stage Name Typos (HIGH)
**Risk:** Test accepts any text; no enforcement against typo stages (PLANNIN, IMPLEMENTION).
- Vulnerability: Diagram stage names might not match `workflow_enforcement_v1.md` enum.
- Mitigation Test: `test_diagram_stage_names_match_enforcement_enum` validates against strict enum.
- Mutation: Replace "PLANNING" with "PLANNIN"; diagram still renders but spec violated.

### 3. Gate CLI Flag Injection (MEDIUM)
**Risk:** Runbook command examples could use invalid flags not in `gate_runner.py --help`.
- Vulnerability: Copy-paste commands that don't actually work (e.g., `--force`, `--no-verify`).
- Mitigation Test: `test_runbook_command_with_invalid_cli_flags` extracts and validates all flags.
- Mutation: Add `python ci/scripts/gate_runner.py static_analysis_check --verbose --force`.

### 4. Missing Decision Logic (MEDIUM)
**Risk:** Gate reference sections document gates without outcome branches (PASS/FAIL paths).
- Vulnerability: Operators don't know what to do when gate FAILS.
- Mitigation Test: `test_gate_reference_missing_decision_logic` requires PASS and FAIL terms.
- Mutation: Remove "If FAIL, escalate to..." subsection.

### 5. Gate Reference Completeness (MEDIUM)
**Risk:** Only 4 of 6 gates documented; sparse sections (<30 words).
- Vulnerability: Learning_check and planner_check have minimal documentation.
- Mitigation Test: `test_gate_reference_sections_too_sparse` enforces min 30 words/gate.
- Mutation: Remove subsections from learning_check; leave only header.

### 6. Link Validation Bypass (MEDIUM)
**Risk:** Relative links in gate reference might point to non-existent specs.
- Vulnerability: `project_board/specs/902_02_tool_audit.md` exists, but typo links like `902_02_tool_audit.md`` (with backtick) not caught.
- Mitigation Test: `test_gate_reference_links_to_nonexistent_specs` validates target existence.
- Mutation: Change link to `project_board/specs/learning_check_spec.md` (doesn't exist).

### 7. Section Ordering (MEDIUM)
**Risk:** Gate reference could appear before runbook; confuses operator flow.
- Vulnerability: Reading order matters for understanding: execute first, then understand details.
- Mitigation Test: `test_readme_gate_reference_before_runbook` enforces: How-To before Reference.
- Mutation: Swap sections; gate reference appears at line 100, runbook at line 200.

### 8. Command Mode Validation (MEDIUM)
**Risk:** Examples could use invalid modes (e.g., `--mode enforce`, `--mode production`).
- Vulnerability: Only 'shadow' and 'blocking' valid in M902; typo modes silently fail.
- Mitigation Test: `test_runbook_command_mode_values_invalid` enforces valid modes.
- Mutation: `python ci/scripts/gate_runner.py static_analysis_check --mode blocking-dry-run`.

### 9. Diagram Connectivity (Mutation) (MEDIUM)
**Risk:** FAIL outcome could be dead-end (no escalation path).
- Vulnerability: Diagram shows FAIL but no ESCALATE or remediation; operator stuck.
- Mitigation Test: `test_diagram_escape_paths_from_fail_outcome` requires escape paths.
- Mutation: `FAIL --> END` without ESCALATE branch.

### 10. Unregistered Gate Names (HIGH)
**Risk:** Examples reference non-existent gates (typos in gate_registry.json names).
- Vulnerability: `static_analysis_chec` instead of `static_analysis_check`.
- Mitigation Test: `test_runbook_command_with_unregistered_gate_name` cross-checks registry.
- Mutation: Change one gate name in example to `spec_completeness_chck`.

---

## Coverage Gaps (Not in Original Test Suite)

1. **Mermaid Syntax Strictness** — Original suite checks for `graph` or `flowchart` keyword but not for malformed arrows (e.g., `-->>` instead of `-->`).
   - New Test: `test_diagram_arrow_syntax_consistency` (HIGH)

2. **Node Label Validation** — No check for empty labels (`A[]`, `B{}`).
   - New Test: `test_diagram_with_empty_node_labels` (MEDIUM)

3. **Multiple Diagrams in README** — Original suite finds first diagram but doesn't check for accidental duplicates.
   - Assumption: Single authoritative diagram per README.
   - New Test: Implicit in parsing strategy.

4. **Command Required Arguments** — spec_completeness_check needs spec_file and ticket_type; not validated.
   - New Test: `test_runbook_command_missing_required_arguments` (HIGH)

5. **Determinism** — No test that parsing diagram twice gives identical results.
   - New Test: `test_mermaid_diagram_parse_idempotency` (MEDIUM)

6. **Gate Cross-Reference Consistency** — Gates mentioned in diagram, runbook, and gate reference should be same set.
   - New Test: `test_gate_names_extracted_consistently` (MEDIUM)

7. **CLAUDE.md Source-of-Truth Adherence** — Runbook commands should use gate_runner.py, not direct gate module invocation.
   - New Test: `test_runbook_commands_use_wrong_task_invocation_style` (MEDIUM)

8. **README Preservation** — Existing sections (Overview, Tickets) should not be removed.
   - New Test: `test_readme_preserves_existing_overview_section`, `test_readme_existing_tickets_section_preserved` (LOW)

---

## Test Execution Summary

**Original Suite:** `test_m902_08_documentation_integration.py`
- 41 tests total
- 31 FAILED (expected; README not yet updated)
- 10 PASSED
- 0 SKIPPED

**Adversarial Suite:** `test_m902_08_documentation_adversarial.py`
- 36 tests total
- 0 FAILED
- 6 PASSED (tests of existing README that don't require new sections)
- 30 SKIPPED (tests of sections not yet added)

**Combined Result:** 77 tests, 31 failures, 36 skips, 10 passes (expected state for TEST_BREAK).

---

## Checkpoint Decisions

### Would have asked: What if README sections exist but with wrong heading levels?
**Assumption made:** Heading level consistency is secondary; existence and content matter most. Test `test_gate_reference_subsection_formatting_inconsistent` checks consistency but allows some variation (##, ###).  
**Confidence:** MEDIUM — could be stricter but operator-friendly approach allows flexibility.

### Would have asked: Should gate names in diagram be exact matches to gate_registry.json or allow aliases?
**Assumption made:** Exact matches required (no aliases). If gate is "static_analysis_check" in registry, diagram must use exact same string.  
**Confidence:** HIGH — prevents subtle naming bugs and silent failures.

### Would have asked: How strictly should we validate Mermaid syntax (full parser vs heuristic)?
**Assumption made:** Heuristic validation (regex) acceptable for TEST_BREAK; full parser (mermaid-cli) could be added in IMPLEMENTATION. Current tests validate nodes, arrows, keywords, and syntax patterns.  
**Confidence:** MEDIUM-HIGH — catches common mistakes without tool overhead.

### Would have asked: Should README have max line limit enforced by test?
**Assumption made:** Yes, <500 lines enforced (per spec: "operator's quick reference"). Applied in `test_readme_max_section_size`.  
**Confidence:** HIGH — spec explicitly states <500 lines.

---

## Severity Classification (Test Failure Mapping)

| Test | Severity | If Fails, Implementation Must | Blocker |
|------|----------|-------------------------------|---------|
| test_diagram_with_unreachable_nodes | HIGH | Remove orphaned nodes; ensure all connected | YES |
| test_diagram_stage_names_match_enforcement_enum | HIGH | Fix stage name typos; use enum values | YES |
| test_runbook_command_with_unregistered_gate_name | HIGH | Fix gate name typos in examples | YES |
| test_diagram_escape_paths_from_fail_outcome | MEDIUM | Add escalation paths for FAIL outcomes | YES |
| test_gate_reference_missing_decision_logic | MEDIUM | Document PASS and FAIL branches per gate | YES |
| test_runbook_command_mode_values_invalid | MEDIUM | Use only 'shadow' or 'blocking' | YES |
| test_gate_reference_sections_too_sparse | MEDIUM | Add min 30 words/gate section | NO (warning) |
| test_readme_max_section_size | MEDIUM | Keep README <500 lines | YES |
| test_gate_reference_links_to_nonexistent_specs | MEDIUM | Update links to correct spec files | YES |
| test_readme_duplicate_sections | LOW | Remove duplicate sections | NO (validation only) |
| test_readme_preserves_existing_overview_section | LOW | Keep existing sections | NO (guard) |

---

## Determinism and Reproducibility

All adversarial tests are **deterministic** and **reproducible**:
- No random inputs or non-deterministic APIs (regex, file reads, JSON parsing all deterministic).
- All tests skip gracefully if README sections not yet present.
- No environmental dependencies (no network, no shell state).
- Test isolation: each test self-contained, no setup/teardown side effects.

---

## Proceed to Implementation

Implementation agent should:
1. Run full test suite: `pytest tests/ci/test_m902_08_documentation_integration.py tests/ci/test_m902_08_documentation_adversarial.py -v`
2. Update README to satisfy all failing tests.
3. Mermaid diagram must pass all connectivity and syntax checks.
4. Runbook commands must use valid gate names, modes, and flags.
5. Gate reference must document all 6 gates with outcomes and links.
6. Final check: all 77 tests PASS.

---

## Test Files

- Original: `/tests/ci/test_m902_08_documentation_integration.py` (41 tests)
- Adversarial: `/tests/ci/test_m902_08_documentation_adversarial.py` (36 tests)
- Combined: 77 executable behavior tests, zero prose assertions.

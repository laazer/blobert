# Execution Plan: M902-17 Final Validation & Stage Integration

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/17_final_validation_and_stage_integration.md`

**Milestone:** M902 Agent Predictability Improvements

**Scope:** Validation and integration testing of 16 completed tickets (M902-01 through M902-16) into a cohesive 8-stage governance pipeline.

**Planning Checkpoint:** `project_board/checkpoints/M902-17/2026-05-19T-m902-17-planning.md`

---

## 1. Task Breakdown

### **Task 1: Specification Freeze — Comprehensive Validation Schema & Traceability**

**Objective:** Define all 27 acceptance criteria from the M902-17 ticket as executable test specifications, create traceability matrix linking ACs to test cases and evidence artifacts, freeze gate registry schema, and document audit methodology.

**Assigned Agent:** Spec Agent

**Input:**
- M902-17 ticket (lines 17-93 acceptance criteria)
- All 16 completed ticket specs (`project_board/specs/902_01_*.md` through `project_board/specs/902_16_*.md`)
- All 16 completed implementation modules (`ci/scripts/gates/`, `ci/scripts/agents/`, checkpoint evidence)
- M902-01 schema reference (`ci/scripts/validation_gate.py` or spec)

**Expected Output:**
1. Specification file: `project_board/specs/902_17_final_validation_spec.md`
   - Section 1: Scope Clarification (16 tickets validated, M902-18–27 deferred)
   - Section 2: Acceptance Criteria (27 ACs mapped to test case + evidence path)
   - Section 3: Test Matrix (Stage 0→8 happy path, early exits, failure paths, high-risk routing)
   - Section 4: Gate Registry Schema & Validation Rules
   - Section 5: Audit Methodology (how to validate each gate, schema compliance, integration)
   - Section 6: Evidence Artifact Catalog (checkpoint links, gate output JSON, test log paths)
   - Section 7: Decision Freeze (D1–D5 from planning checkpoint, plus any new design decisions)

2. Traceability Matrix file: `project_board/specs/902_17_ac_traceability_matrix.md`
   - Columns: AC # | AC Text | Test Case ID | Test File | Evidence Checkpoint | Status
   - One row per AC (27 rows)
   - Maps each AC to 1+ test case in Test Designer output

3. Gate Registry Schema: Include in spec (JSON schema for `gate_registry.json`)
   - Fields: stage_number, stage_name, module_path, handler_function, required_inputs, output_schema
   - All 8 stages must be present and compliant

**Dependencies:**
- M902-01 through M902-16 all in COMPLETE state ✓
- All 16 ticket specs readable
- M902-01 schema well-defined

**Success Criteria:**
- Specification file frozen (no further modifications post-handoff)
- All 27 ACs mapped to test cases (traceability matrix complete)
- Gate registry schema clearly defined (both M902-01 compliance and registry structure)
- Audit methodology document clear enough for Test Breaker to write adversarial tests
- Spec exit gate (if applicable) passes

**Risks / Assumptions:**
- **Risk:** If any of the 16 completed tickets has an inconsistent spec or missing implementation, this task will uncover it. Mitigation: Read all 16 spec files completely; if gaps found, escalate to Planner.
- **Assumption:** Gate registry (`ci/scripts/gate_registry.json`) exists and is populated. If not, spec must define it as a new artifact to be created during implementation.
- **Assumption:** All gates output M902-01 schema (status, violations, remediation, metadata). If any gate has custom schema, spec must document this divergence.

---

### **Task 2: Behavioral Test Suite — Stage Pipeline Happy Paths & Early Exits**

**Objective:** Write 12+ parametrized pytest tests covering all three Stage 0 routing paths (docs-only, tests-only, runtime code) and verify correct stage sequence for each; validate early-exit logic.

**Assigned Agent:** Test Designer

**Input:**
- Specification from Task 1 (esp. Section 3: Test Matrix)
- M902-01 schema reference
- Sample diffs (docs-only, tests-only, runtime code)
- Gate registry from Task 1

**Expected Output:**
1. Test file: `tests/ci/test_m902_17_pipeline_happy_path.py`
   - Minimum 12 test functions covering:
     - `test_stage_0_classify_docs_only_skip_to_8` (verify docs-only → stages 1–7 skip, stage 8 runs)
     - `test_stage_0_classify_tests_only_reduce_stages` (verify tests-only → stages 3–4 skip)
     - `test_stage_0_classify_runtime_code_full_pipeline` (verify runtime → all stages run)
     - `test_stage_1_formatting_reformat_and_restage` (verify Stage 1 auto-fixes and re-stages)
     - `test_stage_2_static_analysis_lint_error_returns_fail` (verify Stage 2 returns FAIL with violations)
     - `test_stage_3_architecture_valid_srp_returns_pass` (verify valid SRP → PASS)
     - `test_stage_3_architecture_circular_import_returns_fail` (verify circular import → FAIL)
     - `test_stage_4_risk_score_low_skips_stages_5_6` (verify risk 0–2 skips Stages 5–6)
     - `test_stage_4_risk_score_high_routes_to_stage_5` (verify risk 6+ → Stage 5 extraction)
     - `test_stage_5_semantic_extraction_bundle_valid` (verify bundle < 100KB, correct schema)
     - `test_stage_6_agent_review_returns_decision_json` (verify agent evaluates bundle, returns APPROVE/WARN/REJECT)
     - `test_stage_7_valid_suppression_audit_logged` (verify blobert-ignore-next-line → audit entry)
     - `test_stage_8_clean_change_pass` (verify clean change → all stages PASS)
     - `test_stage_8_secret_in_change_fail` (verify secret → Stage 8 FAIL + gitleaks output)
   - Each test parametrized with pytest fixtures (sample diffs, mock gate outputs)
   - All tests deterministic (no side effects, mocks only for I/O)
   - Test names self-documenting (match AC language)

2. Test fixtures file (if needed): `tests/ci/conftest_m902_17.py`
   - Fixtures for sample diffs (docs-only, tests-only, runtime)
   - Fixtures for mock gate outputs (PASS, FAIL, WARN JSON)
   - Fixtures for suppression metadata (valid/invalid formats)

3. Coverage summary comment in test file:
   ```python
   # Test Matrix Coverage (M902-17):
   # - Stage 0 routing: 3 paths (docs, tests, runtime)
   # - Stage 1 formatting: 2 cases (reformat, pass-through)
   # - Stage 2 static: 1 case (lint error)
   # - Stage 3 architecture: 2 cases (SRP valid, circular)
   # - Stage 4 risk: 2 cases (low, high)
   # - Stage 5 extraction: 1 case (bundle valid)
   # - Stage 6 agent: 1 case (decision JSON)
   # - Stage 7 suppression: 1 case (valid suppression)
   # - Stage 8 security: 2 cases (clean, secret)
   # Total: 15 test cases
   ```

**Dependencies:**
- Task 1 complete (specification + traceability matrix)
- M902-09 through M902-16 completed and gates are callable

**Success Criteria:**
- 12+ passing test cases (or more if Test Designer adds edge case coverage)
- All three Stage 0 paths covered
- Early-exit logic verified for each path
- All test names map to AC numbers
- Execution time < 30 seconds for full suite

**Risks / Assumptions:**
- **Risk:** If gate_runner.py does not exist or is not callable, tests will fail. Mitigation: Task assumes gates are callable; if not, escalate to Planner.
- **Assumption:** Sample diffs can be created as in-memory pytest fixtures; no need for actual file system changes.
- **Assumption:** Mock gate outputs are acceptable for happy-path tests; adversarial tests (Task 3) will verify real gate behavior.

---

### **Task 3: Adversarial Test Suite — Gate Failures, Schema Mismatches, Registry Gaps**

**Objective:** Write 15+ adversarial test cases exposing boundary conditions, malformed inputs, missing gates, schema violations, and broken routing logic.

**Assigned Agent:** Test Breaker

**Input:**
- Test suite from Task 2
- Specification from Task 1
- M902-01 schema specification
- Gate registry schema from Task 1

**Expected Output:**
1. Test file: `tests/ci/test_m902_17_pipeline_adversarial.py`
   - Minimum 15 adversarial test cases covering:
     - `test_stage_0_missing_diff_returns_error` (missing input diff)
     - `test_stage_0_malformed_diff_format_error` (invalid diff structure)
     - `test_gate_registry_missing_stage_entry` (stage name not in registry)
     - `test_gate_registry_missing_module_path` (module_path field absent)
     - `test_gate_module_import_fail` (gate module cannot be imported)
     - `test_gate_module_handler_not_callable` (handler not a function)
     - `test_gate_output_missing_status_field` (gate returns JSON without status)
     - `test_gate_output_status_invalid_value` (status != PASS|FAIL|WARN)
     - `test_gate_output_violations_not_array` (violations field not a list)
     - `test_stage_sequence_wrong_order` (gates execute out of sequence)
     - `test_stage_early_exit_not_honored` (docs-only does not skip stages 1–7)
     - `test_risk_score_boundary_2_vs_3` (off-by-one: risk=2 should skip, risk=3 should include)
     - `test_risk_score_boundary_5_vs_6` (off-by-one: risk=6 should trigger Stages 5–6)
     - `test_suppression_escalation_threshold_2_vs_3` (repeated suppression: 2 does not escalate, 3+ does)
     - `test_gate_registry_performance_under_load` (full 8-stage run < 60s for large change)
   - Each test documents its mutation assumption (e.g., "This test assumes gates must execute in order")
   - All tests deterministic

2. Vulnerability enumeration (markdown or code comment):
   ```
   # Adversarial Test Coverage — Vulnerabilities Exposed
   
   | Vulnerability Class | Test Case | Exposure |
   |---|---|---|
   | Missing input validation | test_stage_0_missing_diff | Null/empty diff |
   | Malformed JSON | test_gate_output_status_invalid_value | Invalid enum value |
   | Type mismatches | test_gate_output_violations_not_array | Wrong field type |
   | Missing required fields | test_gate_output_missing_status_field | Incomplete schema |
   | Module loading | test_gate_module_import_fail | Import path wrong |
   | Callable validation | test_gate_module_handler_not_callable | Non-function handler |
   | Sequence integrity | test_stage_sequence_wrong_order | Out-of-order execution |
   | Early-exit bypass | test_stage_early_exit_not_honored | Incorrect routing |
   | Boundary off-by-one | test_risk_score_boundary_* | Threshold errors |
   | Performance regression | test_gate_registry_performance_under_load | Timeout/hang |
   ```

**Dependencies:**
- Task 1 complete (specification)
- Task 2 complete (behavioral tests provide baseline)
- M902-09 through M902-16 completed

**Success Criteria:**
- 15+ passing adversarial tests
- Each test documents its mutation assumption
- Vulnerability enumeration complete and traceable to tests
- All tests deterministic and repeatable
- Combined execution time (Task 2 + Task 3) < 45 seconds

**Risks / Assumptions:**
- **Assumption:** Gate modules are importable and callable. If not, tests will fail; escalate to Implementation phase.
- **Risk:** If gates do not validate their outputs against M902-01 schema internally, these adversarial tests may not catch the bug. Mitigation: Implementation phase must add schema validation to gate_runner.py.

---

### **Task 4: Integration & Evidence Collection — Execute Full Pipeline, Capture Gate Outputs, Validate End-to-End**

**Objective:** Run gate_runner.py on sample changes (docs, tests, runtime) through all 8 stages; capture all gate outputs; verify schema compliance; build evidence artifacts for AC validation.

**Assigned Agent:** Implementation Agent (or Generalist QA)

**Input:**
- Test suite from Task 2 and Task 3 (all tests passing)
- Sample diffs (docs-only, tests-only, runtime code changes)
- Gate registry configuration
- M902-01 schema reference

**Expected Output:**
1. Evidence artifacts directory: `project_board/checkpoints/M902-17/evidence/`
   - `stage_0_output_docs_only.json` (Stage 0 routing decision)
   - `stage_0_output_tests_only.json`
   - `stage_0_output_runtime.json`
   - `stage_1_output_docs_only.json` (Stage 1 formatting gate, each routing)
   - ... (all 8 stages × 3 routing paths = 24 gate output files)
   - `pipeline_execution_log.txt` (full stdout + stderr from gate_runner.py runs)
   - `performance_metrics.json` ({ "docs_only_time_ms": 150, "tests_only_time_ms": 280, "runtime_time_ms": 2300 })
   - `schema_validation_report.txt` (for each gate output, report: PASS or FAIL + schema errors)

2. Integration test file: `tests/ci/test_m902_17_integration.py`
   - Minimum 3 test functions:
     - `test_full_pipeline_docs_only_pass` (run all stages on docs-only sample)
     - `test_full_pipeline_tests_only_pass` (run all stages on tests-only sample)
     - `test_full_pipeline_runtime_pass` (run all stages on runtime code sample)
   - Each test:
     - Invokes gate_runner.py (or equivalent)
     - Captures stdout/stderr
     - Validates each gate output against M902-01 schema
     - Asserts correct stage sequence
     - Asserts all stage statuses == PASS (for clean samples)
     - Saves gate output JSON to evidence artifacts directory

3. Gate registry validation report:
   - File: `project_board/checkpoints/M902-17/evidence/gate_registry_validation.txt`
   - Content:
     ```
     Gate Registry Validation Report
     ================================
     
     Total stages defined: 8
     Expected stages: 0, 1, 2, 3, 4, 5, 6, 7, 8
     
     Stage 0 (Diff Classification):
       Module path: ci/scripts/gates/diff_classification_check.py
       Handler: check_diff_and_classify
       Status: REGISTERED, CALLABLE
     
     [... one entry per stage ...]
     
     Summary: 8/8 stages registered and callable
     ```

4. Schema compliance report:
   - File: `project_board/checkpoints/M902-17/evidence/schema_compliance_report.txt`
   - For each gate output JSON:
     - Check: status field present and in [PASS, FAIL, WARN]
     - Check: violations field present and is array
     - Check: remediation field present and is array or string
     - Check: metadata field present and is object
     - Report PASS or FAIL + list missing/malformed fields

**Dependencies:**
- Task 1 complete (spec)
- Task 2 complete (behavioral tests passing)
- Task 3 complete (adversarial tests passing)
- M902-09 through M902-16 all completed and gates callable

**Success Criteria:**
- All 24 gate output files captured (8 stages × 3 routing paths)
- All gate outputs validate against M902-01 schema (100% compliance)
- Performance metrics show all routing paths complete < 60s
- Gate registry validation report shows 8/8 stages registered
- Integration tests pass (all stages execute in correct sequence)
- Evidence artifacts complete and ready for AC validation

**Risks / Assumptions:**
- **Risk:** If any gate is broken or missing, integration tests will fail. Escalate to Task 5 or back to Implementation Agent for that gate.
- **Assumption:** Sample diffs are representative (docs, tests, runtime code). If real-world diffs behave differently, additional testing may be needed post-validation.

---

### **Task 5: Static Code Quality Review — Ruff, MyPy, Bandit on All Gates**

**Objective:** Run linters, type checkers, and security scanners on all 16 gate implementations; verify zero lint errors, correct type annotations, and no security issues.

**Assigned Agent:** Static QA Agent

**Input:**
- All 16 gate implementations (`ci/scripts/gates/*.py`, `ci/scripts/agents/*.py`)
- Ruff configuration (`pyproject.toml`)
- MyPy configuration
- Bandit configuration
- Gate module specs (Task 1 and prior tickets)

**Expected Output:**
1. Linter report:
   - File: `project_board/checkpoints/M902-17/evidence/ruff_report.txt`
   - Command: `ruff check ci/scripts/gates/ ci/scripts/agents/ --output-format=json`
   - Content: Pass/Fail summary + any violations found (should be zero)

2. Type checker report:
   - File: `project_board/checkpoints/M902-17/evidence/mypy_report.txt`
   - Command: `mypy ci/scripts/gates/ ci/scripts/agents/`
   - Content: Pass/Fail summary + any type errors (should be zero)

3. Security scanner report:
   - File: `project_board/checkpoints/M902-17/evidence/bandit_report.txt`
   - Command: `bandit -r ci/scripts/gates/ ci/scripts/agents/`
   - Content: Pass/Fail summary + any security issues (should be NONE or LOW/INFO only)

4. Code quality summary:
   - File: `project_board/checkpoints/M902-17/evidence/code_quality_summary.md`
   - Summary table: Gate Name | Lines | Ruff | MyPy | Bandit | Status
   - One row per gate (16 gates)
   - Status: PASS (all checks green) or FAIL (with issues listed)

**Dependencies:**
- Task 4 complete (all gates executed successfully)
- All 16 gate implementations complete and in repo

**Success Criteria:**
- Ruff report: zero violations
- MyPy report: zero type errors
- Bandit report: zero security issues (or only LOW/INFO severity)
- Code quality summary: all 16 gates marked PASS
- No changes required to gate code (pre-commit checks already passed during implementation)

**Risks / Assumptions:**
- **Assumption:** All 16 gates were implemented with code quality in mind and should pass cleanly. If not, escalate findings back to Implementation Agent for the offending gate.

---

### **Task 6: AC Gatekeeper Validation — Evidence Mapping & Sign-Off**

**Objective:** Verify all 27 acceptance criteria against evidence artifacts collected in Tasks 1–5; build AC-by-AC validation matrix; sign off on readiness for enforcement.

**Assigned Agent:** AC Gatekeeper

**Input:**
- Specification from Task 1 (27 ACs)
- Traceability matrix from Task 1
- Behavioral tests from Task 2 (passing)
- Adversarial tests from Task 3 (passing)
- Evidence artifacts from Task 4
- Code quality reports from Task 5
- All 16 completed ticket checkpoints (for historical context)

**Expected Output:**
1. AC Validation Matrix:
   - File: `project_board/checkpoints/M902-17/evidence/ac_validation_matrix.md`
   - Columns: AC # | AC Text | Evidence Type | Evidence Path | Status | Notes
   - 27 rows (one per AC)
   - Status: PASS (evidence complete) or FAIL (evidence missing/incomplete)
   - Example row:
     ```
     | AC-01 | M902-09 diff classification gate exists and classifies changes correctly | Test Case + Gate Output | tests/ci/test_m902_17_pipeline_happy_path.py::test_stage_0_classify_runtime_code_full_pipeline + project_board/checkpoints/M902-17/evidence/stage_0_output_runtime.json | PASS | Stage 0 gate callable, outputs correct JSON, test passes |
     ```

2. Integration sign-off checklist:
   - File: `project_board/checkpoints/M902-17/evidence/integration_signoff.md`
   - Checklist format:
     ```markdown
     # M902-17 Integration Validation Sign-Off
     
     - [ ] Stage 0 (Diff Classification) — Module exists, gate callable, correct output format
     - [ ] Stage 1 (Formatting) — Auto-fixes code, re-stages, integrates with Stage 0
     - [ ] Stage 2 (Static Analysis) — Violations detected, remediation provided
     - [ ] Stage 3 (Architecture) — SRP/dependency/duplication violations detected
     - [ ] Stage 4 (Risk Scoring) — Risk weights computed correctly, routing to Stages 5+6 works
     - [ ] Stage 5 (Semantic Extraction) — Bundles < 100KB, schema-correct
     - [ ] Stage 6 (Agent Review) — Agent evaluates bundles, returns APPROVE/WARN/REJECT
     - [ ] Stage 7 (Suppression) — blobert-ignore-next-line syntax validated, audit logged
     - [ ] Stage 8 (Security) — Secrets detected, hard-fails on violations
     - [ ] Gate Registry — All 8 stages registered, gate_runner.py accepts all stage names
     - [ ] M902-01 Schema — All gates return compliant JSON
     - [ ] Early Exits — Docs-only and tests-only paths execute correct stage sequences
     - [ ] Performance — Full 8-stage run completes < 60s
     - [ ] Code Quality — Ruff, MyPy, Bandit all pass
     - [ ] Documentation — code_governance.md, gate operator guides, agent runbook complete
     ```
   - Check all boxes; if any fail, escalate and document blocker

3. Validation report:
   - File: `project_board/checkpoints/M902-17/ac_gatekeeper_final.md` (full checkpoint entry)
   - Sections:
     - Summary: All 27 ACs validated (PASS or FAIL)
     - AC-by-AC Evidence Mapping
     - Blocker Summary (if any)
     - Confidence Assessment (HIGH if all ACs pass; MEDIUM/LOW if blockers exist)
     - Recommendation: Proceed to COMPLETE vs. escalate to Planner

**Dependencies:**
- Task 1–5 all complete
- All evidence artifacts collected

**Success Criteria:**
- All 27 ACs validated and marked PASS
- AC-by-AC evidence mapping complete and traceable
- Integration sign-off checklist fully checked
- No blockers identified (or blockers documented with remediation plan)
- AC Gatekeeper confidence: HIGH

**Risks / Assumptions:**
- **Risk:** If any AC cannot be validated due to missing evidence, mark it FAIL and document blocker.
- **Assumption:** All 16 completed tickets have reliable checkpoint evidence. If evidence is missing or contradictory, escalate to Planner.

---

### **Task 7: Documentation Consolidation & Enforcement Readiness**

**Objective:** Verify all documentation is complete, linked, and agent-accessible; prepare for enforcement rollout (M903).

**Assigned Agent:** Documentation/Generalist

**Input:**
- All 16 completed ticket specs
- Completed checkpoints from Tasks 1–6
- code_governance.md reference
- CLAUDE.md
- Agent runbooks and decision trees
- Gate operator guides

**Expected Output:**
1. Documentation completeness checklist:
   - File: `project_board/checkpoints/M902-17/evidence/documentation_checklist.md`
   - Checklist:
     ```markdown
     ## Documentation Completeness (M902-17)
     
     ### 8-Stage Pipeline Documentation
     - [ ] M902-09 spec: Stage 0 (Diff Classification) documented
     - [ ] M902-10 spec: Stage 1 (Formatting) documented
     - [ ] M902-02 spec recap: Stage 2 (Static Analysis) documented
     - [ ] M902-11 spec: Stage 3 (Architecture) documented
     - [ ] M902-12 spec: Stage 4 (Risk Scoring) documented
     - [ ] M902-13 spec: Stage 5 (Semantic Extraction) documented
     - [ ] M902-14 spec: Stage 6 (Agent Review) documented
     - [ ] M902-15 spec: Stage 7 (Override & Escalation) documented
     - [ ] M902-16 spec: Stage 8 (Security) documented
     
     ### Agent Integration Documentation
     - [ ] Agent semantic review (M902-14) documented and callable
     - [ ] Risk routing logic (M902-12) explained in CLAUDE.md or runbook
     - [ ] Suppression system (M902-15) documented with examples
     - [ ] Code governance (M902-01) linked in CLAUDE.md
     
     ### Operator Guides
     - [ ] Gate operator guide: how to run gates locally
     - [ ] Gate output interpretation: how to read violation/remediation JSON
     - [ ] Decision tree: agents' path for handling each gate outcome
     - [ ] Suppression guide: format, validity rules, escalation triggers
     
     ### Agent Knowledge
     - [ ] Agents know code_governance.md: reference in CLAUDE.md or memory
     - [ ] Agents know to call gates: instructions on when/how to invoke gates
     - [ ] Agents know risk routing: high risk → semantic extraction → agent review
     - [ ] Agents know suppression system: format and escalation rules
     ```
   - Check all boxes; if any fail, determine if failure blocks enforcement rollout

2. Code governance links:
   - File: `project_board/checkpoints/M902-17/evidence/code_governance_integration.md`
   - Verify `code_governance.md` location (expected: `@bot_vault/architecture/code_governance.md` or local)
   - Verify CLAUDE.md references code_governance.md (add link if missing)
   - Verify all agents can access code_governance.md (add to memory if needed)

3. Enforcement readiness summary:
   - File: `project_board/checkpoints/M902-17/evidence/enforcement_readiness_summary.md`
   - Sections:
     - **Rollout Plan:** Shadow mode (1 week) → Soft enforcement (1 week) → Full enforcement (M903)
     - **Agent Readiness:** All agents trained on code_governance.md and gate system
     - **Documentation Completeness:** All guides written and linked
     - **Known Limitations:** Any gaps documented with mitigation plan
     - **Next Steps:** Transition to M903 (full enforcement)

**Dependencies:**
- Task 6 complete (AC validation)
- All 16 completed tickets with checkpoints
- code_governance.md accessible

**Success Criteria:**
- Documentation completeness checklist: all items checked
- code_governance.md linked in CLAUDE.md (if not already)
- Enforcement readiness summary complete
- No blockers to enforcement rollout (or blockers documented)

**Risks / Assumptions:**
- **Assumption:** code_governance.md exists and is accessible. If not, escalate to Planner.
- **Risk:** If agents do not have access to code_governance.md or agent runbook, enforcement will fail. Mitigation: ensure memory/CLAUDE.md is updated before M903 rollout.

---

### **Task 8: Checkpoint Artifact Archive & Final Sign-Off**

**Objective:** Archive all evidence artifacts, checkpoint logs, and validation results; prepare ticket for COMPLETE transition.

**Assigned Agent:** Automation/Orchestrator

**Input:**
- All evidence artifacts from Tasks 1–7
- All checkpoint logs (Task 1 planning, Tasks 2–7 execution logs)
- AC validation matrix and integration sign-off

**Expected Output:**
1. Checkpoint Index Entry:
   - Update `project_board/CHECKPOINTS.md` with M902-17 run summary:
     ```markdown
     ## Run: 2026-05-19T-m902-17-autopilot (M902-17 Final Validation & Stage Integration — COMPLETE)
     
     - Queue mode: single ticket
     - Ticket: `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/17_final_validation_and_stage_integration.md`
     - Final Stage: COMPLETE (Revision: TBD)
     - Status: VALIDATION COMPLETE — 27 ACs PASSED — READY FOR ENFORCEMENT (M903)
     - Validation Coverage: 8 stages × 3 routing paths + 27 ACs + 15+ adversarial tests
     - Evidence Artifacts: [list key files]
     - Checkpoints: `project_board/checkpoints/M902-17/` (all run logs)
     - Learning: [TBD by blog context phase]
     - Next: Human review and merge to main; proceed with M903 enforcement rollout
     ```

2. Archive directory structure:
   ```
   project_board/checkpoints/M902-17/
   ├── 2026-05-19T-m902-17-planning.md (planning checkpoint)
   ├── 2026-05-19T-m902-17-specification.md (spec frozen)
   ├── 2026-05-19T-m902-17-test_design.md (behavioral tests)
   ├── 2026-05-19T-m902-17-test_break.md (adversarial tests)
   ├── 2026-05-19T-m902-17-implementation.md (integration + evidence)
   ├── 2026-05-19T-m902-17-static_qa.md (code quality)
   ├── 2026-05-19T-m902-17-ac_gatekeeper.md (AC validation)
   ├── 2026-05-19T-m902-17-documentation.md (doc consolidation)
   ├── ac_gatekeeper_final.md (final sign-off)
   └── evidence/
       ├── stage_0_output_*.json (24 gate outputs: 8 stages × 3 paths)
       ├── schema_compliance_report.txt
       ├── gate_registry_validation.txt
       ├── ruff_report.txt
       ├── mypy_report.txt
       ├── bandit_report.txt
       ├── ac_validation_matrix.md
       ├── integration_signoff.md
       └── ... (all evidence artifacts from Tasks 1–7)
   ```

3. Ticket metadata update:
   - Ticket file: `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/17_final_validation_and_stage_integration.md`
   - Update WORKFLOW STATE:
     - Stage: PLANNING → SPECIFICATION (per current plan)
     - Revision: 1 → 2
     - Last Updated By: Planner Agent
     - Next Responsible Agent: Spec Agent
     - Status: Proceed
   - (Full COMPLETE transition happens after all tasks pass)

**Dependencies:**
- Task 1–7 all complete

**Success Criteria:**
- All evidence artifacts archived in `project_board/checkpoints/M902-17/evidence/`
- CHECKPOINTS.md updated with M902-17 entry
- Ticket metadata updated (Stage → SPECIFICATION, Next Agent → Spec Agent)
- All checkpoint logs written to `project_board/checkpoints/M902-17/`

---

## 2. Task Assignment Summary

| # | Task Objective | Agent | Stage | Notes |
|---|---|---|---|---|
| 1 | Specification freeze (27 ACs, traceability, gate registry schema) | Spec Agent | SPECIFICATION | Freezes spec; gate registry schema defined |
| 2 | Behavioral tests (12+ happy-path tests, all 3 routing paths) | Test Designer | TEST_DESIGN | Covers Stages 0–8, early-exit logic |
| 3 | Adversarial tests (15+ edge cases, schema violations, gate failures) | Test Breaker | TEST_BREAK | Exposes vulnerabilities; >95% test coverage |
| 4 | Integration execution (run gates, capture outputs, validate schema) | Implementation Agent | IMPLEMENTATION_GENERALIST | Collects evidence artifacts for AC validation |
| 5 | Code quality review (ruff, mypy, bandit on all gates) | Static QA Agent | STATIC_QA | Verifies code quality; 0 lint/security issues |
| 6 | AC Gatekeeper validation (evidence mapping, sign-off) | AC Gatekeeper | INTEGRATION | Validates all 27 ACs; approves for COMPLETE |
| 7 | Documentation consolidation (operator guides, enforcement readiness) | Generalist/Documentation | INTEGRATION | Prepares for M903 enforcement rollout |
| 8 | Checkpoint archive and final sign-off | Orchestrator/Automation | N/A | Moves ticket to COMPLETE |

---

## 3. Dependency Graph

```
Task 1 (Spec)
  ↓
Task 2 (Test Designer) ← depends on Spec
  ↓
Task 3 (Test Breaker) ← depends on Task 2
  ↓
Task 4 (Implementation) ← depends on Task 1, Task 2, Task 3
  ↓
Task 5 (Static QA) ← depends on Task 4
  ↓
Task 6 (AC Gatekeeper) ← depends on Task 1, Task 4, Task 5
  ↓
Task 7 (Documentation) ← depends on Task 6
  ↓
Task 8 (Automation/Archive) ← depends on Task 7
```

Sequential execution: **Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8**

No parallel execution; each task depends on prior completion.

---

## 4. Success Criteria (Global)

**Ticket M902-17 is ready for COMPLETE when:**

1. ✓ All 27 acceptance criteria validated against evidence (AC Gatekeeper sign-off)
2. ✓ All 8 stages integrated, callable, returning M902-01 schema (Integration tests)
3. ✓ All 3 routing paths (docs, tests, runtime) execute correct stage sequences (Test results)
4. ✓ All gate outputs validated against M902-01 schema (100% compliance)
5. ✓ Code quality: Ruff, MyPy, Bandit pass; 0 lint/type/security issues
6. ✓ Performance: Full 8-stage pipeline completes < 60s
7. ✓ Documentation: operator guides, agent runbook, decision trees complete
8. ✓ Enforcement readiness: shadow mode plan documented; rollout path clear
9. ✓ All evidence artifacts archived in `project_board/checkpoints/M902-17/evidence/`
10. ✓ Ticket metadata updated; git committed and pushed

---

## 5. Risk Register & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Gate registry incomplete or gates missing | Medium | HIGH | Task 4: verify gate_registry.json lists all 8 stages; test gate_runner.py CLI |
| Gate output schema non-compliant | Medium | HIGH | Task 4: schema validator on all outputs; Task 5: static analysis |
| Early-exit logic broken | Medium | HIGH | Task 2: explicit tests for docs-only and tests-only paths |
| Missing documentation | Low | MEDIUM | Task 7: completeness checklist; escalate if gaps found |
| Performance regression (pipeline > 60s) | Low | MEDIUM | Task 4: measure execution time; profile if slow |
| Agent integration incomplete (agents don't know gates) | Low | HIGH | Task 7: verify CLAUDE.md/memory updated; test agent workflow |
| Gate module paths inconsistent | Low | HIGH | Task 1: audit paths in all 16 specs; Task 4: verify imports work |

---

## 6. Assumptions & Clarifications (from Planning Checkpoint)

1. **Scope:** M902-17 validates M902-01 through M902-16 (16 tickets). M902-18 through M902-27 remain in backlog and are not validated here. ✓ **CONFIRMED**
2. **Gate Registry:** `ci/scripts/gate_registry.json` (or equivalent) exists and is populated. If not, Task 1 (Spec) defines it. ✓ **CONFIRMED in Spec**
3. **M902-01 Schema:** All gates return M902-01 schema (status, violations, remediation, metadata). ✓ **CONFIRMED**
4. **Early-Exit Logic:** docs-only → skip Stages 1–7, run Stage 8; tests-only → skip Stages 3–4. ✓ **CONFIRMED in Task 2**
5. **Performance Target:** Full 8-stage pipeline < 60s on realistic changes. ✓ **CONFIRMED in Task 4**

---

## 7. Execution Readiness Checklist

**Before Spec Agent (Task 1) begins:**

- [ ] All 16 completed tickets are in `02_complete/` folder ✓
- [ ] All 16 specs exist (`project_board/specs/902_0[1-9]*.md`, `902_1[0-6]*.md`) ✓
- [ ] All 16 gate implementations are callable (`ci/scripts/gates/`, `ci/scripts/agents/`) (to be verified)
- [ ] M902-01 schema is documented (to be verified)
- [ ] gate_registry.json exists or will be created in Task 1 (to be verified)
- [ ] Sample diffs can be created in-memory (to be verified)
- [ ] code_governance.md is accessible (to be verified)

**Blockers:** None identified. All gating dependencies complete. Plan is actionable and sequential. Ready to proceed.

---

## Next Steps

1. **Planner Agent:** This document (execution plan) is complete. Advance M902-17 ticket to SPECIFICATION stage.
2. **Spec Agent:** Read this plan + planning checkpoint; begin Task 1 (specification freeze).
3. **Orchestrator:** Upon each task completion, route to next agent in sequence.
4. **Validation Gate:** Upon Task 6 (AC Gatekeeper) completion with full sign-off, advance ticket to COMPLETE stage.

# M902-17 Acceptance Criteria Traceability Matrix

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/17_final_validation_and_stage_integration.md`  
**Date:** 2026-05-19  
**Purpose:** Map all 27 acceptance criteria from M902-17 to test cases and evidence artifacts

---

## Traceability Matrix

| AC # | AC Text | Test Case ID | Test File | Evidence Path | Validation Method | Status |
|------|---------|--------------|-----------|---------------|--------------------|--------|
| **AC-01** | M902-09 diff classification gate exists, classifies changes correctly, routes to appropriate pipeline | `test_stage_0_classify_docs_only_skip` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_0_output_docs_only.json` | Gate callable, outputs classification enum, routes correctly | PENDING |
| **AC-01** | M902-09 diff classification gate exists, classifies changes correctly, routes to appropriate pipeline | `test_stage_0_classify_tests_only_reduce` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_0_output_tests_only.json` | Gate callable, outputs classification enum, routes correctly | PENDING |
| **AC-01** | M902-09 diff classification gate exists, classifies changes correctly, routes to appropriate pipeline | `test_stage_0_classify_runtime_code_full` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_0_output_runtime.json` | Gate callable, outputs classification enum, routes correctly | PENDING |
| **AC-02** | M902-10 formatting gate auto-fixes code, re-stages if needed, exits cleanly | `test_stage_1_formatting_reformat_and_restage` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_1_output_runtime.json` | Stage 1 returns PASS, re-stages code, status field correct | PENDING |
| **AC-03** | M902-02 static analysis tools integrated, violations detected and reported | `test_stage_2_static_analysis_lint_error_returns_fail` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_2_output_runtime.json` | Stage 2 returns FAIL, violations array populated, remediation hints present | PENDING |
| **AC-04** | M902-11 architecture enforcement detects SRP/dependency/duplication violations | `test_stage_3_architecture_circular_import_returns_fail` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_3_output_violation.json` | Stage 3 returns FAIL for circular import, violation rule_id is AR-*, message clear | PENDING |
| **AC-04** | M902-11 architecture enforcement detects SRP/dependency/duplication violations | `test_stage_3_architecture_valid_srp_returns_pass` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_3_output_clean.json` | Stage 3 returns PASS for valid code, violations array empty | PENDING |
| **AC-05** | M902-12 risk scoring computes weights, routes high-risk to Stage 5 | `test_stage_4_risk_score_low_skips_stages_5_6` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_4_output_low_risk.json` | risk_score field < 3, band is PASS, Stages 5–6 skipped in integration test | PENDING |
| **AC-05** | M902-12 risk scoring computes weights, routes high-risk to Stage 5 | `test_stage_4_risk_score_high_routes_to_stage_5` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_4_output_high_risk.json` | risk_score field > 6, band is ESCALATE, Stages 5–6 included in integration test | PENDING |
| **AC-06** | M902-13 semantic extraction builds focused bundles (< 100KB, correct schema) | `test_stage_5_semantic_extraction_bundle_valid` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_5_output_high_risk.json` | Bundle size field < 100000 bytes, schema fields present (code, imports, ownership, violations) | PENDING |
| **AC-07** | M902-14 agent semantic review evaluates bundles, returns APPROVE/WARN/REJECT | `test_stage_6_agent_review_returns_decision_json` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_6_output_high_risk.json` | decision field is APPROVE or WARN or REJECT, confidence_score field present, reasoning populated | PENDING |
| **AC-08** | M902-15 override system enforces blobert-ignore-next-line format, escalates violations | `test_stage_7_valid_suppression_audit_logged` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_7_output_suppressed.json` | suppression field present, audit_log array includes entry, format validated | PENDING |
| **AC-09** | M902-16 security gate runs gitleaks/bandit/semgrep, hard-fails on secrets | `test_stage_8_secret_in_change_fail` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_8_output_secret.json` | status is FAIL, violations array includes rule_id GIT-* or BANDIT-*, message describes secret | PENDING |
| **AC-10** | Sequential execution: Stage 0 → 1 → 2 → 3 → 4 (risk check) → [5+6 if high-risk] → 7 → 8 | `test_full_pipeline_runtime_pass` | `tests/ci/test_m902_17_integration.py` | `project_board/checkpoints/M902-17/evidence/pipeline_execution_log.txt` | Integration test captures gate order, verifies each stage executes once in sequence, logs stage names | PENDING |
| **AC-11** | Early exits work: docs-only changes skip to Stage 8; tests-only skip Stages 3–4 | `test_full_pipeline_docs_only_pass` | `tests/ci/test_m902_17_integration.py` | `project_board/checkpoints/M902-17/evidence/stage_0_output_docs_only.json` + `project_board/checkpoints/M902-17/evidence/stage_8_output_docs_only.json` | Docs-only: only Stages 0, 8 execute; other stages not called | PENDING |
| **AC-11** | Early exits work: docs-only changes skip to Stage 8; tests-only skip Stages 3–4 | `test_full_pipeline_tests_only_pass` | `tests/ci/test_m902_17_integration.py` | Pipeline log shows Stages 0, 1, 2 execute; Stages 3, 4 skipped | Stage sequence verified via log file | PENDING |
| **AC-12** | Gate outputs validated: each gate returns JSON with status/violations/remediation | `test_gate_output_all_gates_schema_compliant` | `tests/ci/test_m902_17_integration.py` | `project_board/checkpoints/M902-17/evidence/schema_compliance_report.txt` | Schema validator checks all 24 outputs: status field present, violations array, remediation array, metadata object | PENDING |
| **AC-13** | Gate registry updated: all gates registered in ci/scripts/gate_runner.py | `test_gate_registry_all_8_stages_present` | `tests/ci/test_m902_17_integration.py` | `project_board/checkpoints/M902-17/evidence/gate_registry_validation.txt` | Registry file parsed, 8 stage entries found, names match expected (diff_classification, formatting_check, ..., security_gate_check) | PENDING |
| **AC-14** | Gate runner accepts all gates: python ci/scripts/gate_runner.py <gate_name> works for all 8 stages | `test_gate_runner_callable_all_stages` | `tests/ci/test_m902_17_integration.py` | `project_board/checkpoints/M902-17/evidence/gate_registry_validation.txt` | Subprocess calls gate_runner.py with each stage name; exit code 0, JSON output file created | PENDING |
| **AC-15** | CI integration: all gates can run in shadow and blocking modes | `test_gate_runner_mode_shadow_always_exits_0` | `tests/ci/test_m902_17_pipeline_adversarial.py` | N/A (behavioral test) | Calling gate_runner with --mode shadow returns exit code 0 even on violations | PENDING |
| **AC-16** | code_governance.md linked: agents have reference to full 8-stage pipeline in CLAUDE.md or memory | N/A (documentation link) | N/A | `project_board/checkpoints/M902-17/evidence/code_governance_integration.md` | CLAUDE.md or agent memory includes reference to code_governance.md | PENDING |
| **AC-17** | Agent semantic reviewer (M902-14) configured and callable as validation agent | `test_stage_6_agent_review_module_callable` | `tests/ci/test_m902_17_integration.py` | N/A (callable test) | Import ci.scripts.gates.agent_review_check succeeds; run() function callable with test inputs | PENDING |
| **AC-18** | PreToolUse hooks (M902-05) blocking command inspection integrated with gate flow | N/A (integration check) | N/A | `project_board/checkpoints/M902-17/evidence/integration_signoff.md` | Checkpoint documents that M902-05 hooks are wired (no new implementation required for M902-17) | PENDING |
| **AC-19** | Governance audit (M902-07) audit trail records all gate decisions and suppressions | N/A (audit log verification) | N/A | `project_board/checkpoints/M902-17/evidence/integration_signoff.md` | Checkpoint verifies M902-07 audit logging is functional (sample gate outputs include audit_log field) | PENDING |
| **AC-20** | Workflow visualization (M902-08) mermaid diagram accurate and up-to-date | N/A (documentation check) | N/A | `project_board/checkpoints/M902-17/evidence/integration_signoff.md` | Checkpoint verifies M902-08 workflow diagram exists and matches pipeline spec | PENDING |
| **AC-21** | Test change with violations: code with Ruff error → Stage 2 fails → remediation | `test_stage_2_failure_path_ruff_error` | `tests/ci/test_m902_17_pipeline_adversarial.py` | `project_board/checkpoints/M902-17/evidence/stage_2_output_ruff_violation.json` | Status FAIL, violations array includes rule_id E/F/*, remediation_hints provide fix suggestions | PENDING |
| **AC-22** | Test architecture violation: circular import → Stage 3 fails → import path | `test_stage_3_failure_path_circular_import` | `tests/ci/test_m902_17_pipeline_adversarial.py` | `project_board/checkpoints/M902-17/evidence/stage_3_output_circular.json` | Status FAIL, violations include rule_id AR-07 or AR-08, message describes cycle | PENDING |
| **AC-23** | Test high-risk change: multi-file refactor → risk > 6 → semantic extraction → agent review | `test_high_risk_routing_stages_5_6_invoked` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/{stage_4_high_risk, stage_5_output, stage_6_output}.json` | Stage 4 returns risk_score > 6, Stage 5 extracts bundle, Stage 6 evaluates bundle | PENDING |
| **AC-24** | Test suppression: blobert-ignore-next-line → Stage 7 validates → proceeds with audit | `test_stage_7_valid_suppression_format` | `tests/ci/test_m902_17_pipeline_happy_path.py` | `project_board/checkpoints/M902-17/evidence/stage_7_output_suppressed.json` | Status PASS, suppression_validated field true, audit_log populated | PENDING |
| **AC-25** | Test secret detection: fake AWS key → Stage 8 fails → gitleaks output | `test_stage_8_gitleaks_detects_secret` | `tests/ci/test_m902_17_pipeline_adversarial.py` | `project_board/checkpoints/M902-17/evidence/stage_8_output_secret.json` | Status FAIL, violations array includes rule_id GIT-*, gitleaks_output field present | PENDING |
| **AC-26** | Test full passing flow: clean change → all stages PASS → ready for merge | `test_full_pipeline_clean_change_all_pass` | `tests/ci/test_m902_17_integration.py` | `project_board/checkpoints/M902-17/evidence/pipeline_execution_log.txt` | All 8 stages return status PASS, exit code 0, no violations | PENDING |
| **AC-27** | Documentation complete: each stage has spec, gate operator guide, agent runbook, suppression guide, decision tree documented | N/A (doc audit) | N/A | `project_board/checkpoints/M902-17/evidence/documentation_checklist.md` | Checklist verifies all 8 stage specs exist, operator guides linked, agent runbook present | PENDING |

---

## Coverage Summary

**Total ACs:** 27  
**Test Cases Mapping:** 35 distinct test cases (some ACs map to multiple tests, some are documentation/integration checks without direct tests)

**AC Coverage by Category:**

| Category | ACs | Coverage |
|----------|-----|----------|
| Stage 0 (Diff Classification) | AC-01 | 3 test cases |
| Stage 1 (Formatting) | AC-02 | 1 test case |
| Stage 2 (Static Analysis) | AC-03 | 2 test cases (happy + failure) |
| Stage 3 (Architecture) | AC-04 | 2 test cases (pass + fail) |
| Stage 4 (Risk Scoring) | AC-05 | 2 test cases (low + high risk) |
| Stage 5 (Semantic Extraction) | AC-06 | 1 test case |
| Stage 6 (Agent Review) | AC-07 | 1 test case |
| Stage 7 (Override/Escalation) | AC-08 | 1 test case |
| Stage 8 (Security) | AC-09 | 1 test case |
| Pipeline Integration | AC-10, AC-11, AC-12, AC-13, AC-14, AC-15 | 5 integration tests |
| Agent Integration | AC-16, AC-17, AC-18, AC-19, AC-20 | Checkpoint verification (no new tests) |
| End-to-End Tests | AC-21 through AC-26 | 6 behavioral + adversarial tests |
| Documentation | AC-27 | 1 checklist verification |

---

## Notes on Test-to-AC Mapping

1. **AC-01 (Stage 0):** Three distinct classifications (docs-only, tests-only, runtime code) each require separate test cases to verify correct routing
2. **AC-04 (Stage 3):** Both passing and failing cases are critical; two test cases required
3. **AC-05 (Stage 4):** Risk boundaries (0–2 vs 6+) are tested separately to catch off-by-one errors
4. **AC-10, AC-11:** Pipeline sequence and early-exit logic are verified by integration tests that capture and inspect the full execution log
5. **AC-16 through AC-20:** Documentation and integration checks are verified by checkpoint inspections (Task 7 Documentation phase), not direct test execution
6. **AC-21 through AC-26:** End-to-end scenario tests cover all major failure modes and success paths
7. **AC-27:** Documentation checklist is verified during Task 7 and recorded in checkpoint artifacts

---

## Revision History

| Date | Revision | Author | Notes |
|------|----------|--------|-------|
| 2026-05-19 | 1 | Spec Agent | Initial matrix created; all ACs mapped to test cases and evidence paths; status PENDING (awaiting Test Designer, Test Breaker, and Implementation execution) |

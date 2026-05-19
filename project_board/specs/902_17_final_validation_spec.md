# M902-17: Final Validation & Stage Integration — Specification

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/17_final_validation_and_stage_integration.md`  
**Milestone:** M902 — Agent Predictability Improvements  
**Agent:** Spec Agent  
**Date:** 2026-05-19  
**Status:** SPECIFICATION  
**Revision:** 1

---

## Overview

This specification defines the **final validation phase** for Milestone 902. It formalizes the acceptance criteria of M902-17 into executable test specifications, traceability matrices, gate registry schemas, and audit methodologies.

**Scope:**
- Validates all 16 completed tickets (M902-01 through M902-16)
- Confirms correct implementation of the 8-stage governance pipeline (Stages 0–8)
- Verifies all 27 acceptance criteria via test cases and evidence artifacts
- Does NOT validate M902-18 through M902-27 (future context optimization and API contract features remain in backlog)

**Outcome:** Full validation matrix proving the pipeline is architecturally sound, properly integrated, and ready for enforcement rollout (M903).

---

## Requirement 01: Scope Clarification and Validation Target

### 1. Spec Summary

**Description:** M902-17 is an **umbrella validation ticket** that coordinates testing and evidence collection across 16 completed child tickets (M902-01 through M902-16). It is NOT a feature implementation ticket; it produces no new runtime code. Instead, it formalizes acceptance criteria into executable specifications, test matrices, and artifact catalogs.

**Validation targets:**
1. **M902-01 through M902-08:** Core infrastructure (gate runner framework, governance rules, metadata, handoff system, audit pipeline, workflow visualization)
2. **M902-09 through M902-16:** 8-stage pipeline implementation (Stages 0–8: diff classification, formatting, static analysis, architecture enforcement, risk scoring, semantic extraction, agent review, override/escalation, security)

**Out of scope (M902-18 through M902-27):**
- Tool categorization layer (M902-18)
- Forgiving tool parsing middleware (M902-19)
- TODO validation gates (M902-20)
- Context budget tracking (M902-21)
- Early-stop detection (M902-22)
- Atomic handoff checkpoint (M902-23)
- OpenAPI → TypeScript generation (M902-24)
- Pydantic + Zod dual validation (M902-25)
- API contract testing (M902-26)
- Pre-commit hook (M902-27)

These remain in `00_backlog/` and are NOT validated by M902-17.

**Constraints:**
- All 16 child tickets must be in COMPLETE state (`02_complete/` folder) before validation begins
- Validation uses only executable test cases, gate output artifacts, and checkpoint evidence — not markdown prose assertions
- Gate registry schema is read from `ci/scripts/gate_registry.json`
- M902-01 gate success/failure schemas are the source of truth for all gate outputs

**Assumptions:**
- All 16 gate implementations are complete, callable, and produce M902-01 schema-compliant JSON
- Gate registry includes all 8 stages with correct module paths and handler functions
- Sample test changes (docs-only, tests-only, runtime code) can be created via pytest fixtures (no filesystem mutations required)
- Code governance.md is the reference document for pipeline semantics and stage routing logic

**Scope rationale:** Ticket AC list (lines 17-93 in M902-17 ticket file) explicitly references M902-01 through M902-16 and contains 0 references to M902-18 through M902-27. The ticket states "validates the entire system, not implements new features" — this is a **validation gate**, not a feature gate.

### 2. Acceptance Criteria

- **AC-01.1:** All 16 child tickets (M902-01 through M902-16) are in COMPLETE state (folder `02_complete/`); no gating dependencies are blocked
- **AC-01.2:** Validation scope explicitly excludes M902-18 through M902-27 (documented in spec)
- **AC-01.3:** Validation targets are enumerated: core infrastructure (8 tickets) + 8-stage pipeline (8 tickets)
- **AC-01.4:** All test cases are executable (not prose-only assertions on documentation)
- **AC-01.5:** Gate registry source of truth is `ci/scripts/gate_registry.json`
- **AC-01.6:** All gate outputs conform to M902-01 schema (success/failure records with status, violations, remediation, metadata fields)

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Child ticket incompleteness | Validation cannot begin | Verify all 16 tickets in 02_complete/ before Task 1 starts |
| Missing gate registry entries | Stages cannot be discovered | Audit gate_registry.json against all 8 stage specs (M902-09 through M902-16) |
| Schema drift in gate outputs | Tests fail spuriously | Define schema validation as first test suite task; document expected fields |
| Scope creep to M902-18+ | Work expands beyond plan | Enforce scope boundary via test case naming (only test M902-01 through M902-16) |

### 4. Clarifying Questions

- **Q1:** Does M902-17 validate against deployed enforcement, or just implementation correctness? **Answer:** Implementation correctness only. Enforcement (shadow mode → blocking mode transition) is M903's responsibility.
- **Q2:** If a child ticket has a spec but no implementation, does M902-17 fail? **Answer:** Yes, AC-01.1 requires all 16 to be COMPLETE. Escalate to Planner.

---

## Requirement 02: Acceptance Criteria Traceability Matrix

### 1. Spec Summary

**Description:** A comprehensive traceability matrix that maps all 27 acceptance criteria from the M902-17 ticket (lines 17-93 in the ticket file) to concrete test cases, evidence artifacts, and audit paths. Each AC is uniquely identified (AC-01 through AC-27) and mapped to:
- **Test Case ID:** Name of the test function (e.g., `test_stage_0_classify_docs_only`)
- **Test File:** Path to the test module (e.g., `tests/ci/test_m902_17_pipeline_happy_path.py`)
- **Evidence Checkpoint:** Path to the artifact that proves the AC (e.g., `project_board/checkpoints/M902-17/evidence/stage_0_output_docs_only.json`)
- **Validation Method:** How the AC is verified (test execution, schema compliance, gate output inspection)
- **Status:** PENDING (during spec phase) → PASS (after test execution) → FAIL (if test fails)

**Constraints:**
- Matrix is a markdown table with 27 rows (one per AC)
- All test case IDs must exist and be executable
- All evidence checkpoint paths must be creatable during Task 4 (Implementation & Evidence Collection)
- Matrix is the authoritative source for AC coverage; every AC has ≥1 test case

**Assumptions:**
- Test cases are deterministic and repeatable
- Evidence artifacts (JSON gate outputs, test logs, checkpoint reports) are machine-parseable
- No test case is shared between ACs (1:N mapping: AC → tests, but each test covers specific ACs)

**Scope:** Traceability matrix only; actual test implementation is Requirements 03–04.

### 2. Acceptance Criteria

- **AC-02.1:** Traceability matrix file exists at `project_board/specs/902_17_ac_traceability_matrix.md`
- **AC-02.2:** Matrix has 27 rows (one per AC from M902-17 ticket lines 19-88)
- **AC-02.3:** Each row maps AC → test case ID + test file + evidence path
- **AC-02.4:** All test case IDs are unique and follow naming convention `test_<stage>_<scenario>_<outcome>`
- **AC-02.5:** All test files are paths under `tests/ci/` directory
- **AC-02.6:** All evidence paths point to `project_board/checkpoints/M902-17/evidence/` directory
- **AC-02.7:** No AC is unmapped (all 27 have ≥1 test case)
- **AC-02.8:** Matrix includes a Status column; all entries are PENDING (to be updated post-execution)

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Test case IDs don't match actual test names | Matrix becomes stale | Test file is written by Test Designer; matrix is created before; verify names match during AC Gatekeeper phase |
| AC grouping ambiguity (one AC maps to multiple tests) | Coverage unclear | Spec defines clear 1:N mapping rules; each test covers one "atomic AC scenario" |
| Evidence paths don't exist | Matrix validation fails | Task 4 (Implementation) creates all evidence artifacts; Task 6 (AC Gatekeeper) validates existence |

### 4. Clarifying Questions

None. Traceability is a straightforward data structure; matrix format is documented in execution plan Task 6.

---

## Requirement 03: Test Matrix and Test Case Specifications

### 1. Spec Summary

**Description:** A detailed specification of all test cases required to validate the 8-stage pipeline and 27 acceptance criteria. The test matrix is organized by stage (0–8) and covers:
- **Happy path tests:** Normal execution, all stages pass
- **Early-exit tests:** Docs-only and tests-only routing with correct stage skips
- **Failure path tests:** Gate failures, violations, remediation output
- **High-risk routing tests:** Risk scoring boundary conditions, semantic extraction, agent review routing
- **Adversarial tests:** Schema violations, missing gates, registry gaps, performance regressions

**Minimum test cases:** 30+ total (12+ behavioral, 15+ adversarial)

**Test categories:**

| Stage | Happy Path | Early Exit | Failure | Adversarial | Total |
|-------|-----------|-----------|---------|------------|-------|
| 0 (Diff Classification) | 1 | 2 | 1 | 2 | 6 |
| 1 (Formatting) | 1 | 0 | 1 | 1 | 3 |
| 2 (Static Analysis) | 1 | 0 | 1 | 2 | 4 |
| 3 (Architecture) | 1 | 0 | 2 | 2 | 5 |
| 4 (Risk Scoring) | 2 | 0 | 0 | 3 | 5 |
| 5 (Semantic Extraction) | 1 | 0 | 0 | 1 | 2 |
| 6 (Agent Review) | 1 | 0 | 0 | 1 | 2 |
| 7 (Suppression) | 1 | 0 | 0 | 1 | 2 |
| 8 (Security) | 2 | 0 | 1 | 2 | 5 |
| Integration | 1 | 0 | 0 | 0 | 1 |
| **TOTAL** | **12** | **2** | **6** | **15** | **35** |

**Constraints:**
- Each test is deterministic (same inputs → same outputs)
- Each test name documents the scenario (e.g., `test_stage_0_classify_docs_only_skip`)
- Test fixtures are reusable (sample diffs, mock gate outputs, suppression metadata)
- Tests use pytest (or unittest for Godot); no manual test execution required
- Execution time: full suite < 45 seconds

**Assumptions:**
- Gate modules are callable via `python ci/scripts/gate_runner.py <gate_name>`
- Sample diffs can be created in-memory (no filesystem writes)
- Mock gate outputs conform to M902-01 schema
- Tests can mock subprocess calls where needed

**Scope:** Test specification only; actual test code is written by Test Designer (Task 2) and Test Breaker (Task 3).

### 2. Acceptance Criteria (Test Matrix)

- **AC-03.1:** Behavioral test suite (happy + early-exit + failure) covers ≥12 distinct scenarios across all 8 stages
- **AC-03.2:** Adversarial test suite covers ≥15 vulnerability classes (schema violations, missing gates, boundary conditions, performance)
- **AC-03.3:** All three Stage 0 routing paths are tested (docs-only, tests-only, runtime code)
- **AC-03.4:** Early-exit logic is verified for each path (docs-only skips Stages 1–7; tests-only skips Stages 3–4)
- **AC-03.5:** Risk scoring boundary conditions are tested (risk 0–2 skips Stages 5–6; risk 6+ includes Stages 5–6)
- **AC-03.6:** All test names follow pattern `test_<stage>_<scenario>_<outcome>` or `test_<component>_<case>`
- **AC-03.7:** Each test is isolated and deterministic (no shared state, no side effects)
- **AC-03.8:** Test execution time is < 45 seconds for full suite (Task 2 + Task 3)

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Test fixtures don't represent real changes | Tests pass but real pipelines fail | Test Designer creates fixtures from real git diffs (Godot, Python, web changes) |
| Mock gate outputs are incomplete or inconsistent | Tests don't catch real failures | Schema validator runs on all mocks during test setup |
| Boundary condition off-by-one errors | Risk routing logic broken in production | Adversarial tests explicitly test boundaries (risk=2 vs 3, risk=5 vs 6, suppression=2 vs 3) |
| Performance regression undetected | Pipeline hangs in production | Integration tests measure execution time; Task 4 produces performance_metrics.json |

### 4. Clarifying Questions

- **Q1:** Should tests mock the gate implementations or call real gates? **Answer:** Behavioral tests mock; integration tests call real gates. Adversarial tests mock to simulate edge cases (missing modules, schema violations).
- **Q2:** Should tests validate the gate registry JSON structure? **Answer:** Yes; AC-04 (Gate Registry Schema) includes schema validation tests.

---

## Requirement 04: Gate Registry Schema and Validation Rules

### 1. Spec Summary

**Description:** Formal specification of the gate registry JSON schema (`ci/scripts/gate_registry.json`) and validation rules. The registry is the single source of truth for all 8 stages and their handlers.

**Registry structure:**
- Top-level: JSON array of gate entries
- Each entry: JSON object with mandatory fields (`name`, `module`, `required_inputs`, `default_mode`, `description`, `category`) and optional fields (`run_function`, `optional_inputs`)
- All fields are strings, arrays, or objects; no nested objects beyond 1 level

**Validation rules:**
1. **File existence:** `ci/scripts/gate_registry.json` exists and is valid JSON
2. **Array structure:** Top level is a JSON array; each element is an object
3. **Mandatory fields per entry:**
   - `name` (string, non-empty, unique across all entries)
   - `module` (string, valid Python module path or filesystem path)
   - `required_inputs` (array of strings, may be empty)
   - `default_mode` (string, must be "shadow" or "blocking")
   - `description` (string, non-empty, < 500 chars)
   - `category` (string, one of: `workflow`, `analysis`, `governance`, `review`, `learning`, `security`)
4. **Optional fields per entry:**
   - `optional_inputs` (array of strings)
   - `run_function` (string, default value is "run" if omitted)
5. **Cross-file validation:**
   - Each `module` value must correspond to a Python file under `ci/scripts/gates/` (or be a valid importable path)
   - Each `module` must export the `run()` function (or the function named in `run_function` field)
   - No duplicate `name` values across entries
6. **Stage coverage:**
   - Registry must include exactly 8 entries with the following names (in any order):
     - `diff_classification` (Stage 0)
     - `formatting_check` (Stage 1)
     - `static_analysis_check` (Stage 2)
     - `architecture_enforcement_check` (Stage 3)
     - `risk_scoring_check` (Stage 4)
     - `semantic_extraction_check` (Stage 5)
     - `agent_review_check` (Stage 6)
     - `override_and_escalation_check` (Stage 7)
     - `security_gate_check` (Stage 8)

**Current state (as of 2026-05-19):** `ci/scripts/gate_registry.json` exists with 13 entries (including 8 pipeline stages + 5 supporting gates). All 8 stages are present and have correct module paths.

**Constraints:**
- Registry is read-only at runtime (gate_runner.py does not modify it)
- Module paths must be importable by Python's import system from the repo root
- All entries must conform to the schema; no custom fields are allowed (for forward compatibility)
- Categories are fixed; new categories require schema versioning (M903+)

**Assumptions:**
- Python import paths can use dot notation (e.g., `ci.scripts.gates.risk_scoring_check`) or filesystem paths (e.g., `risk_scoring_check`)
- Default `run_function` is "run" (the standard gate entry point per M902-01)
- Registry is not versioned (no `version` field); versioning is deferred to M903

**Scope:** Schema specification and validation rules only; registry management (adding/removing entries) is operational (M903+).

### 2. Acceptance Criteria

- **AC-04.1:** File `ci/scripts/gate_registry.json` exists and contains valid JSON
- **AC-04.2:** Top-level structure is a JSON array
- **AC-04.3:** Each array element is an object with all mandatory fields: `name`, `module`, `required_inputs`, `default_mode`, `description`, `category`
- **AC-04.4:** All `name` values are unique within the array
- **AC-04.5:** All `name` values are strings, non-empty, and follow pattern `<descriptive_name>` (lowercase, underscores)
- **AC-04.6:** All `module` values are valid Python importable paths or filesystem paths under `ci/scripts/gates/`
- **AC-04.7:** All `default_mode` values are "shadow" or "blocking" (case-sensitive)
- **AC-04.8:** All `category` values are one of: `workflow`, `analysis`, `governance`, `review`, `learning`, `security`
- **AC-04.9:** Registry includes all 8 pipeline stages (diff_classification, formatting_check, static_analysis_check, architecture_enforcement_check, risk_scoring_check, semantic_extraction_check, agent_review_check, override_and_escalation_check, security_gate_check)
- **AC-04.10:** A test exists that validates the registry file against this schema (file existence, JSON validity, required fields, unique names, valid categories, module file existence)
- **AC-04.11:** The registry passes validation with 0 errors

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Module path changes without registry update | Gates become uncallable | Test (AC-04.10) validates module file existence on every CI run |
| Registry entries deleted or corrupted | Pipeline stages are skipped | Version control (git) tracks changes; test validates completeness |
| Import path conflicts (two modules with same name) | Runtime ImportError | Restrict modules to flat `ci/scripts/gates/` directory (no subdirectories) |
| Schema drift (new fields, removed fields) | Registry breaks forward/backward compatibility | Schema is frozen for M902; versioning deferred to M903 |

### 4. Clarifying Questions

- **Q1:** Should the registry include supporting gates (spec_completeness_check, governance_check, etc.) or only the 8 pipeline stages? **Answer:** Both. The 8 stages are mandatory for pipeline execution; supporting gates are optional. Validation focuses on the 8 stages but accepts additional entries.
- **Q2:** Can module paths use relative imports or only absolute imports? **Answer:** Absolute imports only (e.g., `ci.scripts.gates.risk_scoring_check`); relative imports are fragile and not supported.

---

## Requirement 05: Audit Methodology and Evidence Artifact Catalog

### 1. Spec Summary

**Description:** Formal specification of how validation is performed (audit methodology) and what artifacts are collected as proof (evidence catalog). This enables the AC Gatekeeper (Task 6) to verify each AC independently and reproducibly.

**Audit phases:**
1. **Structural audit (Task 1):** Read all 16 completed specs; verify module paths, gate registry entries, and schema contracts are documented and consistent
2. **Behavioral audit (Task 2):** Run happy-path and early-exit tests; verify all stage sequences are correct for each routing path
3. **Adversarial audit (Task 3):** Run edge-case and failure tests; expose boundary condition bugs and schema violations
4. **Integration audit (Task 4):** Execute full 8-stage pipeline on real sample changes; capture all gate outputs; validate schema compliance
5. **Code quality audit (Task 5):** Run ruff, mypy, bandit on all gate modules; verify 0 lint/type/security issues
6. **AC evidence audit (Task 6):** Map each AC to evidence artifacts (test logs, gate outputs, reports); validate completeness; sign off

**Evidence artifacts:**
- **Test execution logs:** `tests/ci/test_m902_17_pipeline_happy_path.py`, `tests/ci/test_m902_17_pipeline_adversarial.py`, `tests/ci/test_m902_17_integration.py` (pytest output, coverage)
- **Gate output files:** 24 JSON files (8 stages × 3 routing paths) under `project_board/checkpoints/M902-17/evidence/stage_*.json`
- **Schema compliance reports:** `project_board/checkpoints/M902-17/evidence/schema_compliance_report.txt`
- **Gate registry validation:** `project_board/checkpoints/M902-17/evidence/gate_registry_validation.txt`
- **Code quality reports:** `project_board/checkpoints/M902-17/evidence/{ruff,mypy,bandit}_report.txt`
- **Performance metrics:** `project_board/checkpoints/M902-17/evidence/performance_metrics.json`
- **AC validation matrix:** `project_board/checkpoints/M902-17/evidence/ac_validation_matrix.md`
- **Integration sign-off:** `project_board/checkpoints/M902-17/evidence/integration_signoff.md`
- **Checkpoint logs:** All task run logs under `project_board/checkpoints/M902-17/` (planning, spec, test_design, test_break, implementation, static_qa, ac_gatekeeper, documentation)

**Constraints:**
- All artifacts are machine-parseable (JSON, CSV, markdown tables with structured data)
- All artifacts include timestamps (ISO 8601 format) and source references (test name, gate name, etc.)
- No prose-only assertions on documentation (all evidence is behavioral: code paths, test results, gate outputs)
- Artifacts are immutable post-collection (no edits after initial generation)

**Assumptions:**
- Artifacts can be generated deterministically (same inputs → same outputs)
- Gate outputs are JSON-serializable and conform to M902-01 schema
- Test logs are captured via pytest `-v` and `--tb=short` options

**Scope:** Audit methodology and evidence requirements only; actual audit execution is Tasks 4–6.

### 2. Acceptance Criteria

- **AC-05.1:** Audit methodology is documented with five phases: structural, behavioral, adversarial, integration, code quality, AC evidence
- **AC-05.2:** Evidence artifact catalog is enumerated: 24 gate outputs, 3+ reports, performance metrics, AC validation matrix, sign-off checklist
- **AC-05.3:** All artifacts are stored under `project_board/checkpoints/M902-17/evidence/` directory
- **AC-05.4:** Each artifact has a creation timestamp and source reference
- **AC-05.5:** Artifacts are machine-parseable (no prose-only assertions; all evidence is behavioral)
- **AC-05.6:** Artifact file names follow pattern `<stage>_<scenario>.json` (e.g., `stage_0_output_docs_only.json`) or `<report_type>_report.txt`
- **AC-05.7:** All 24 gate output files (8 stages × 3 paths) are collected and validated for schema compliance
- **AC-05.8:** Performance metrics are captured in `performance_metrics.json` with fields: docs_only_time_ms, tests_only_time_ms, runtime_time_ms
- **AC-05.9:** AC validation matrix maps all 27 ACs to evidence paths and status (PASS/FAIL)

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Artifacts are incomplete or missing | AC Gatekeeper cannot validate ACs | Task 4 creates all artifacts; Task 6 validates completeness before sign-off |
| Artifacts become stale (out of sync with tests) | Evidence is misleading | Artifacts are created during Task 4 execution; no manual edits post-creation |
| Gate outputs are non-compliant with schema | Schema validator fails spuriously | Task 4 includes schema validation as first step; non-compliant outputs block Task 5 |
| Performance metrics are too high (pipeline > 60s) | Regression undetected | Task 4 measures execution time; if > 60s, escalate to Implementation for profile/optimization |

### 4. Clarifying Questions

- **Q1:** Should artifacts include raw subprocess output (stdout/stderr) or only structured results? **Answer:** Structured results (JSON, CSV); raw output is for debugging only (stored in checkpoint logs, not artifact directory).
- **Q2:** Should artifacts be committed to git or kept as ephemeral test outputs? **Answer:** Committed to git under `project_board/checkpoints/M902-17/evidence/` for traceability and historical record.

---

## Requirement 06: Pipeline Stage Sequence and Routing Logic

### 1. Spec Summary

**Description:** Formal specification of the 8-stage pipeline execution sequence, stage routing decisions, and early-exit logic. This is the operational definition of how changes flow through the validation gates.

**Pipeline stages (in order):**

| Stage | Name | Gate | Input | Output | Skip Condition |
|-------|------|------|-------|--------|----------------|
| 0 | Diff Classification | `diff_classification` | staged git diff | classification enum + recommended route | Never (always runs) |
| 1 | Formatting | `formatting_check` | staged files | re-staged code + PASS | None (runs if Stage 0 PASS) |
| 2 | Static Analysis | `static_analysis_check` | staged files | violations + remediation | None (runs if Stage 1 PASS) |
| 3 | Architecture Enforcement | `architecture_enforcement_check` | staged files + violations from Stage 2 | architecture violations | Tests-only classification (tests don't require architecture checks) |
| 4 | Risk Scoring | `risk_scoring_check` | violations from Stages 2–3 | risk_score [0–100] + band (PASS/WARN/ESCALATE) | Tests-only classification |
| 5 | Semantic Extraction | `semantic_extraction_check` | violations + risk_score | JSON bundle < 100KB | Low risk (score 0–2) or tests-only |
| 6 | Agent Review | `agent_review_check` | semantic bundle | decision JSON (APPROVE/WARN/REJECT) | Low risk or tests-only |
| 7 | Override & Escalation | `override_and_escalation_check` | staged files + violations | suppression validation + audit log | Tests-only classification |
| 8 | Security Gate | `security_gate_check` | staged files | security violations | Docs-only classification (docs don't require security checks) |

**Routing logic (based on Stage 0 classification):**

| Classification | Pipeline Routing | Rationale |
|---|---|---|
| `docs-only` | Stage 0 PASS → Stage 8 PASS → Done | Documentation changes don't require code/architecture/risk analysis |
| `formatting-only` | Stage 0 → Stage 1 → Stage 8 → Done | Formatting-only changes skip Stages 2–7 (no logic/architecture/security impact) |
| `lockfile-only` | Stage 0 → Stages 1–7 → Stage 8 → Done | Dependency updates require full pipeline (dependency security is critical) |
| `tests-only` | Stage 0 → Stages 1–2 → Skip 3–4 → Stage 7–8 → Done | Tests don't impact production architecture or risk (skip Stages 3–4) |
| `migration-only` | Stage 0 → Stages 1–8 → Done | Migrations must pass all stages (schema changes are high-risk) |
| `runtime-code` | Stage 0 → Stages 1–8 → Done | Production code requires full pipeline |

**Risk-based routing (within pipeline):**

After Stage 4 risk scoring:
- If `risk_score` ∈ [0, 2]: Skip Stages 5–6 (low risk, no semantic extraction needed)
- If `risk_score` ∈ [3, 5]: Run Stages 5–6 with advisory mode (medium risk, extract bundle but don't block)
- If `risk_score` ∈ [6, 100]: Run Stages 5–6 in escalation mode (high risk, agent review required)

**Early-exit logic:**

| Condition | Action |
|---|---|
| Any stage returns FAIL in blocking mode | Stop pipeline; report violations + remediation; exit non-zero |
| Stage outputs are non-compliant with M902-01 schema | Stop pipeline; report schema error; exit non-zero |
| docs-only classification | Execute Stage 0 PASS → Stage 8 PASS; skip Stages 1–7 |
| tests-only classification | Execute Stages 0, 1–2, 7–8; skip Stages 3–4 |
| formatting-only classification | Execute Stages 0, 1, 8; skip Stages 2–7 |

**Constraints:**
- Stage sequence is **strictly ordered** (no parallel execution, no out-of-order skips)
- All stages run in shadow mode during M902 (exit 0 regardless of violations); blocking mode is M903
- Each stage's input is the previous stage's output (pipelined data flow)
- No stage modifies the registry or gate runner behavior
- Early exits must be logged with stage name and reason

**Assumptions:**
- Stage 0 classification is always accurate (diff analysis is deterministic)
- Stage 4 risk score is computed correctly (signal extraction + weighted average formula from M902-12)
- Stages 5–6 are optional (low-risk changes skip them); Stages 1–4, 7–8 are mandatory for non-docs changes
- All stages emit M902-01 schema-compliant results (validated by schema validator in gate_runner.py)

**Scope:** Pipeline logic and routing rules only; orchestration (decision-making code in gate_runner.py) is implementation (Tasks 4–5).

### 2. Acceptance Criteria

- **AC-06.1:** 8-stage pipeline sequence is documented with stage names, gates, inputs, outputs
- **AC-06.2:** Routing logic for all 6 classifications is specified (docs-only, formatting-only, lockfile-only, tests-only, migration-only, runtime-code)
- **AC-06.3:** Early-exit conditions are enumerated (docs-only → Stages 0, 8; tests-only → Stages 0, 1–2, 7–8; etc.)
- **AC-06.4:** Risk-based routing is specified (risk 0–2 skips Stages 5–6; risk 6+ includes Stages 5–6)
- **AC-06.5:** Stage sequence is strictly ordered (no parallel execution, no out-of-order execution)
- **AC-06.6:** All stages run in shadow mode (exit 0) during M902; blocking mode is deferred to M903
- **AC-06.7:** Data flow between stages is documented (Stage N output → Stage N+1 input)
- **AC-06.8:** Test cases cover all three routing paths (docs-only, tests-only, runtime-code) with correct stage counts

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Early-exit logic not honored | Wrong stages execute for a classification | Test cases explicitly verify stage counts for each routing path (AC-06.8) |
| Risk score boundaries off-by-one | Stages 5–6 skipped when should run (or vice versa) | Adversarial tests check risk=2 vs 3, risk=5 vs 6 boundaries explicitly |
| Stage sequence parallelized (by orchestration code) | Deadlocks, race conditions | Spec mandates strict ordering; implementation tests verify sequential execution |
| Missing early-exit logic | Docs-only changes take 60s (full pipeline) instead of < 5s | Integration tests measure execution time per routing path |

### 4. Clarifying Questions

- **Q1:** If Stage 2 (Static Analysis) finds violations but Stage 4 (Risk Scoring) scores risk 0–2, are Stages 5–6 still skipped? **Answer:** Yes. Risk score is the decision point; if risk < 3, Stages 5–6 are skipped regardless of violation count. Low-risk violations are logged but don't escalate to semantic extraction.
- **Q2:** Can a stage skip its check if it receives empty input (e.g., no violations from Stage 2)? **Answer:** No. Each stage runs its full logic on all inputs. Empty input is a valid input state; stage returns status PASS with empty violations array.

---

## Non-Functional Requirements

### NFR-01: Performance
- Full 8-stage pipeline (runtime-code classification) completes in < 60 seconds on realistic changes
- Docs-only changes complete in < 5 seconds (Stages 0, 8 only)
- Tests-only changes complete in < 15 seconds (Stages 0, 1–2, 7–8)
- Gate startup overhead is < 1 second per gate

### NFR-02: Reliability
- All 8 stages produce M902-01 schema-compliant JSON 100% of the time
- Gate registry is validated on every CI run (test AC-04.10)
- No gate modifies working tree or staging area (read-only execution)
- All gate outputs are deterministic (same inputs → same outputs)

### NFR-03: Observability
- All gate outputs include `timestamp` (ISO 8601 UTC format) and `duration_ms` (milliseconds)
- All gate outputs include `violations[]` array with file, line, rule, message, severity fields
- All gate outputs include `remediation_hints[]` array with actionable strings
- Gate runner logs stage name, classification, risk score to stderr for debugging

### NFR-04: Maintainability
- All gate modules are ≤ 300 lines each (fits in one screen)
- Gate registry is ≤ 20 entries (future entries require M903 review)
- No gate imports undeclared dependencies (all imports are stdlib or repo-local)
- Code follows project CLAUDE.md conventions (no bare except, proper error logging)

### NFR-05: Security
- Gate outputs do not include secrets (API keys, passwords, tokens)
- Gate modules do not execute arbitrary code (only import known gates from registry)
- Result files are created with permissions 0644 (readable by all, writable by owner)
- No gate makes outbound network calls (all I/O is local filesystem + git)

---

## Risk Register

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|-----------|
| R1 | Gate registry incomplete (missing stage entry) | MEDIUM | Task 1 spec: audit all 8 stages in registry; Task 4: verify gate_runner.py accepts all names |
| R2 | Gate outputs non-compliant with M902-01 schema | MEDIUM | Task 4: schema validator on all outputs; non-compliance blocks Task 5 |
| R3 | Early-exit logic broken (wrong stages execute for classification) | MEDIUM | Task 2–3: explicit tests for all 3 routing paths; measure stage count per path |
| R4 | Performance regression (full pipeline > 60s) | LOW | Task 4: measure execution time; profile if slow; escalate to Implementation |
| R5 | Module import paths inconsistent | MEDIUM | Task 1: audit paths in all 16 specs; Task 4: verify imports work |
| R6 | Test coverage gaps (some ACs untested) | MEDIUM | Task 6 AC Gatekeeper: verify all 27 ACs have test coverage; escalate if gaps found |
| R7 | Code quality issues (lint/type/security failures) | LOW | Task 5: run ruff, mypy, bandit; 0 errors required before Task 6 |

---

## File Tree (Post-Specification)

```
project_board/
├── specs/
│   ├── 902_17_final_validation_spec.md          (this file)
│   └── 902_17_ac_traceability_matrix.md         (AC → test mapping)
│
├── checkpoints/M902-17/
│   ├── 2026-05-19T-m902-17-planning.md          (planning checkpoint)
│   ├── 2026-05-19T-m902-17-specification.md     (spec frozen, this run)
│   ├── evidence/                                 (artifacts collected during Tasks 4–6)
│   │   ├── stage_0_output_docs_only.json
│   │   ├── stage_0_output_tests_only.json
│   │   ├── stage_0_output_runtime.json
│   │   ├── stage_1_output_docs_only.json
│   │   ├── ... (24 total: 8 stages × 3 paths)
│   │   ├── schema_compliance_report.txt
│   │   ├── gate_registry_validation.txt
│   │   ├── ruff_report.txt
│   │   ├── mypy_report.txt
│   │   ├── bandit_report.txt
│   │   ├── performance_metrics.json
│   │   ├── ac_validation_matrix.md
│   │   ├── integration_signoff.md
│   │   └── documentation_checklist.md
│   │
│   ├── 2026-05-19T-m902-17-test_design.md
│   ├── 2026-05-19T-m902-17-test_break.md
│   ├── 2026-05-19T-m902-17-implementation.md
│   ├── 2026-05-19T-m902-17-static_qa.md
│   ├── 2026-05-19T-m902-17-ac_gatekeeper.md
│   └── 2026-05-19T-m902-17-documentation.md
│
└── 902_milestone_902_agent_predictabilitiy_improvements/
    └── 01_in_progress/
        └── 17_final_validation_and_stage_integration.md (ticket file, updated)

tests/ci/
├── test_m902_17_pipeline_happy_path.py          (behavioral tests)
├── test_m902_17_pipeline_adversarial.py         (adversarial tests)
├── test_m902_17_integration.py                  (end-to-end tests)
└── conftest_m902_17.py                          (fixtures)

ci/scripts/
├── gate_registry.json                           (existing, validated)
└── gates/                                        (existing, all 8 stages)
    ├── diff_classification.py
    ├── formatting_check.py
    ├── static_analysis_check.py
    ├── architecture_enforcement_check.py
    ├── risk_scoring_check.py
    ├── semantic_extraction_check.py
    ├── agent_review_check.py
    ├── override_and_escalation_check.py
    └── security_gate_check.py
```

---

## Decision Freeze

**D1: Validation Scope**
- M902-17 validates M902-01 through M902-16 only
- M902-18 through M902-27 are explicitly out of scope (remain in backlog)
- Scope rationale: Ticket AC structure and "validates the entire system" language confirm this is a validation gate for the 16-ticket cycle, not a launch point for 27 tickets

**D2: Traceability Model**
- Each AC maps 1:N to test cases (one test per atomic AC scenario)
- Evidence artifacts are behavioral (test results, gate outputs) not prose
- Audit trail is deterministic: same inputs → same outputs, repeatable on every CI run

**D3: Test Matrix Coverage**
- Happy path: all 8 stages + 3 routing paths = 12+ tests
- Failure path: each stage has ≥1 failure case = 6+ tests
- Adversarial: schema violations, missing gates, boundary conditions, performance = 15+ tests
- Total: 30+ executable test cases

**D4: Pipeline Sequence**
- Stages execute in strict order (0 → 1 → 2 → ... → 8)
- No parallel execution, no out-of-order skips
- Early exits are based on Stage 0 classification (docs-only, tests-only) and Stage 4 risk score
- All stages run in shadow mode (M902); blocking mode is M903

**D5: Evidence Artifacts**
- All artifacts stored under `project_board/checkpoints/M902-17/evidence/`
- 24 gate outputs (8 stages × 3 paths) + 5+ reports (schema, registry, code quality, performance, AC validation)
- Artifacts are machine-parseable and immutable post-collection
- AC Gatekeeper validates completeness and sign-off readiness

**D6: Gate Registry Source of Truth**
- `ci/scripts/gate_registry.json` is the authoritative registry
- All 8 stages are present and validated on every CI run
- No runtime modifications to registry (read-only at execution)
- Future registry changes (M903+) require manual edits + validation

---

## Spec Exit Gate Checklist

This spec is ready for the spec exit gate (before TEST_DESIGN) when:

- [x] All 27 ACs from M902-17 ticket are mapped to test cases
- [x] Acceptance Criteria are measurable, unambiguous, and independently verifiable
- [x] All assumptions are documented with checkpoint resolutions
- [x] Risks and edge cases are identified with mitigations
- [x] Clarifying questions are resolved
- [x] Non-functional requirements are defined (performance, reliability, maintainability, observability, security)
- [x] File tree is specified (post-implementation state)
- [x] Decision freeze is documented (D1–D6)
- [x] No gameplay changes are included (workflow validation only)
- [x] No new third-party dependencies introduced
- [x] All gate module references point to existing implementations (M902-01 through M902-16 complete)
- [x] Traceability matrix file path is specified (`project_board/specs/902_17_ac_traceability_matrix.md`)
- [x] Evidence artifact catalog is enumerable (checkpoint paths, file patterns, JSON schemas)
- [x] Gate registry schema is formally specified (JSON structure, validation rules, coverage)
- [x] Pipeline sequence and routing logic are documented (stage order, early exits, risk-based routing)
- [x] Audit methodology is specified (five phases: structural, behavioral, adversarial, integration, code quality, AC evidence)

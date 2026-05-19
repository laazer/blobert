# Execution Plan: M902-09 Stage 0 — Diff Classification Gate

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/09_stage_0_diff_classification_gate.md`  
**Milestone:** 902 — Agent Predictability Improvements  
**Created:** 2026-05-18  
**Prepared by:** Planner Agent  
**Status:** FROZEN — Ready for Specification Phase

---

## Project Description

**M902-09** implements **Stage 0 of the governance pipeline**: a diff classification gate that analyzes staged git changes and categorizes them to determine whether to exit early (trivial changes) or route to the full governance pipeline (runtime code changes).

The gate is the **first filter** in an 8-stage governance system, reducing pipeline load by skipping unnecessary checks for docs-only, formatting-only, or lockfile-only changes while routing substantive changes (runtime code, migrations, tests) to appropriate reduced or full validation pipelines.

---

## Execution Context

### Gating Dependencies

| Dependency | Ticket | Status | Blocks M902-09? |
|-----------|--------|--------|-----------------|
| M902-01 (Validation Gate Framework) | `01_validation_gate_framework.md` | COMPLETE | No — framework is ready; M902-09 is a consumer |

**Verdict:** No blocking dependencies. M902-01 (gate runner, schemas, registry, shadow mode) is complete and stable.

### Design Assumptions (Logged per Checkpoint Protocol)

| # | Assumption | Confidence | Notes |
|---|-----------|-----------|-------|
| A1 | Gate module at `ci/scripts/gates/diff_classification.py`, registry entry in `ci/scripts/gate_registry.json` | High | Consistent with M902-01 framework; confirmed by ticket AC |
| A2 | Gate follows M902-01 pattern: implements `run(inputs: dict) -> dict`, returns gate result conforming to success/failure schemas | High | M902-01 spec defines the interface; all gates use it |
| A3 | Classification is file-path-based with priority hierarchy (e.g., runtime-code > migration > test > lockfile > formatting > docs) | Medium-High | Governance plan suggests this; spec will formalize |
| A4 | Output includes classification category and recommended route, both advisory (not machine-callable directives) | Medium | Gate framework defines success/failure JSON; spec will detail routing fields |
| A5 | Early exit logic (actually skipping pipeline stages) deferred to M903 orchestrator or downstream wiring | Medium | This gate only classifies; orchestration logic is post-M902 work |
| A6 | Test vectors cover all 6 categories + mixed scenarios (20+ cases) | High | AC explicitly requests "20+ change vectors" |

### Schedule & Scope

- **Target completion:** 2026-06-15
- **Scope:** Gate module, tests, registry integration, documentation
- **Out of scope:** Orchestration/routing logic (M903), pre-commit hook wiring (Phase 1 governance plan), actual enforcement (M903)

---

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author specification for diff classification gate, defining classification categories, file patterns, output contract, and acceptance criteria | Spec Agent | Ticket (M902-09), Planning Checkpoint (`project_board/checkpoints/M902-09/2026-05-18T-planning.md`), M902-01 spec (`project_board/specs/902_01_gate_runner_spec.md`), Governance plan (`project_board/plans/governance-adoption-phase1-precommit.md`) | Spec document: `project_board/specs/902_09_diff_classification_gate_spec.md` with: (a) 6 categories + file patterns (docs, formatting, lockfile, test, migration, runtime-code), (b) priority hierarchy logic, (c) output schema (classification + recommended_route fields), (d) 20+ test vectors (all categories + edge cases), (e) AC coverage matrix (each AC mapped to spec section), (f) non-functional requirements (performance, reliability) | None — can start immediately | Spec exists and is complete; covers all 7 AC from ticket; no ambiguous or prose-only AC; test vectors are specific (not "test with various files"); output contract aligns with M902-01 schemas | **Risk:** Spec scope creep (orchestration logic). Mitigate: Spec focuses on classification logic only; orchestration deferred to M903. **Assumption A3:** File patterns and hierarchy are formalized by Spec Agent (not assumed from governance plan); spec is authoritative. Confidence: High. **Assumption A4:** Output contract clarity is critical for Test Designer. Spec must include example JSON output showing classification field. Confidence: Medium — spec must be precise. |
| 2 | Design comprehensive test suite covering all classification categories, edge cases, and gate framework integration | Test Designer Agent | Spec document (`project_board/specs/902_09_diff_classification_gate_spec.md`), M902-01 test patterns (`tests/ci/test_gate_runner.py` for reference), Sample gate test (`tests/ci/gates/test_spec_completeness_gate.py` for reference) | Test design document: `project_board/checkpoints/M902-09/<run_id>-test-design.md` with: (a) behavioral test matrix (8-10 tests per category, plus edge cases = 20+ total), (b) mock git diff setup (staged file fixtures), (c) assertion mapping to AC, (d) adversarial scenarios (malformed input, no changes, binary files), (e) integration test (gate runs via gate_runner.py CLI). Test files: `tests/ci/test_diff_classification_gate.py` (primary tests), `tests/ci/gates/test_diff_classification.py` (if gate is in gates/ subdirectory). All tests deterministic (mock git, fixed file sets). | Spec Agent completes Task 1 | Tests exist for all 20+ vectors; each test maps to one AC; tests run deterministically (no random file generation); gate result schema validation (success/failure); CLI integration test passes; all tests pass (100% pass rate) | **Risk:** Test scope explosion. Mitigate: Focus on classification logic, not orchestration. Behavioral tests only (no prose assertions). **Assumption A6:** 20+ vectors = 3-4 tests per category + 8 edge cases. Deterministic file mocks are critical (no temp file cleanup issues). Confidence: High. |
| 3 | Break/strengthen test suite with adversarial, mutation, and stress tests; validate test quality and gate robustness | Test Breaker Agent | Test design from Task 2 (`tests/ci/test_diff_classification_gate.py`, design doc), Spec document | Test break document: `project_board/checkpoints/M902-09/<run_id>-test-break.md` with: (a) adversarial tests (5-8): malformed git output, binary files, symlinks, permission errors, huge file lists, empty staged changes; (b) mutation tests (3-5): inverted category logic, wrong priority, off-by-one in patterns; (c) stress tests (2-3): 1000+ staged files, deeply nested paths, special chars in filenames. All tests deterministic. Test files: `tests/ci/gates/test_diff_classification_adversarial.py`, `tests/ci/gates/test_diff_classification_mutation.py`, `tests/ci/gates/test_diff_classification_stress.py` | Test Designer completes Task 2 and submits tests for breaker review | Adversarial suite catches regressions (inverted logic, off-by-one); mutation tests fail on intentional bugs (seeded into gate logic); stress tests pass under load (no timeouts, no crashes); total test count 20+ primary + 15+ adversarial + 10+ mutation + 5+ stress = 50+ tests; all deterministic; all pass at 100% | **Risk:** Over-testing (too many variants). Mitigate: Focus on classification-layer regressions only (not orchestration). **Assumption:** Test count is proportional to AC count and category complexity. Confidence: Medium. |
| 4 | Implement the diff classification gate module, registry entry, and CLI integration; validate against test suite | Implementation Agent (Backend) | Spec document, test suite (all tests from Tasks 2-3), M902-01 gate framework reference (`ci/scripts/gate_runner.py`, `ci/scripts/gates/spec_completeness.py` for pattern), Governance plan (file pattern rules) | Implementation: (a) `ci/scripts/gates/diff_classification.py` (module with `run(inputs: dict) -> dict` function, <200 lines), (b) Updated `ci/scripts/gate_registry.json` (add entry for `diff_classification_check` gate: name, module, required_inputs=[], default_mode="shadow", description, category), (c) No new dependencies (stdlib only). Artifacts: implementation file, registry update. All 50+ tests pass (100% pass rate). Test execution time <5 seconds (per M902-01 NFR-01). | Test Breaker completes Task 3 | Gate module exists and is importable; registry entry is valid JSON and references gate; gate runs via gate_runner.py CLI (`python ci/scripts/gate_runner.py diff_classification_check ...`); all 50+ tests pass; gate output conforms to M902-01 success/failure schemas; classification logic matches spec exactly; performance <5 sec for 1000+ staged files | **Risk:** Git diff parsing fragility. Mitigate: Mock git in tests; use `git diff --cached --name-status` for robust parsing; document failure modes. **Assumption:** Gate takes no required inputs (reads staged files from git directly). Confidence: High. **Assumption:** Registry entry uses `"module": "diff_classification"` (not `"diff_classification_check"`) — gate runner appends `.py`. Confidence: High. |
| 5 | Static QA: run linters, type checkers, and security scans; validate code style and absence of blockers | Static QA Agent | Implementation from Task 4 (`ci/scripts/gates/diff_classification.py`, updated `gate_registry.json`), Existing Ruff config (`asset_generation/python/pyproject.toml` + `ci/scripts/` conventions), CLAUDE.md guidelines | Static QA report: (a) `project_board/checkpoints/M902-09/<run_id>-static-qa.md` (tool outputs: ruff, mypy, bandit, pylint excerpts); (b) All lint/type/security violations addressed (fixed or explicitly waived with justification); (c) Code style conforms to blobert conventions (no unexplained tuning literals, proper docstrings, type hints). Gate module is <200 lines (NFR-03). Registry is <50 entries (NFR-03). All checks pass. | Implementation Agent completes Task 4 | All linters pass (Ruff E/F/I rules, mypy strict mode, bandit security); no type violations; no security findings; code is well-documented; gate module is readable and maintainable; registry remains valid JSON | **Risk:** Registry bloat (too many gates). Mitigate: Registry is cumulative (all M902 gates); M902-09 adds 1 entry, within limits. Confidence: High. **Assumption:** `ci/scripts/` code follows same Ruff/mypy rules as main Python project. Confidence: High. |
| 6 | Integration: wire gate into framework, update documentation, ensure end-to-end pipeline readiness | Integration Agent | Static QA report, Implementation from Task 4, M902-01 documentation (`project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` if exists), Checkpoint log | Integration deliverables: (a) Gate is registered and callable via gate_runner.py; (b) Milestone README (or new section) documents the diff classification gate: what it does, how to run it, example output; (c) Example gate result JSON file (success + failure cases) in `project_board/checkpoints/M902-09/` for documentation; (d) All 50+ tests pass in CI context (via `ci/scripts/run_tests.sh` or equivalent); (e) No blocking issues; readiness for M902-10 (Stage 1 gate) confirmed | Static QA Agent completes Task 5 | Gate registry is valid and gate is discoverable; documentation is complete and accurate; example output matches actual gate behavior; CI tests pass; no manual post-integration fixes needed; next gate (M902-10) can assume diff_classification_check is stable | **Risk:** Documentation drift. Mitigate: Example output is fixture-based (generated by test, then verified manually). Confidence: High. **Assumption:** README section is brief (<30 lines) and links to spec for details. Confidence: Medium. |
| 7 | Learning & escalation: document design decisions, capture lessons, identify deferred work and cross-milestone dependencies | Learning Agent | All prior deliverables, Checkpoint logs, Spec + Test + Implementation documents | Learning deliverables: (a) `project_board/checkpoints/M902-09/<final_run_id>-learning.md` documenting key decisions (file pattern rules, category priority hierarchy, schema design); (b) Entries appended to `project_board/LEARNINGS.md` (3-5 key insights: e.g., "classification hierarchy simplifies routing logic", "file-path-based approach avoids false positives on imports", "advisory-only mode is critical for early-stage rollout"); (c) Cross-milestone notes: "M903 wiring will implement actual early-exit logic; M902-09 is classification layer only"; (d) Escalation analysis: none (no blockers, no design crises) | Integration Agent completes Task 6 | Learning log exists and is readable; insights are actionable and non-obvious; cross-milestone dependencies are documented; LEARNINGS.md is updated; ticket is ready for Stage COMPLETE | **Assumption:** Learning is lightweight (not heavy documentation). Confidence: High. **Assumption:** No major blockers exist (ticket was well-scoped). Confidence: High. |

---

## Acceptance Criteria Traceability

All 7 acceptance criteria from the ticket are addressed by the execution plan:

| AC # | Acceptance Criterion | Task(s) | Verification |
|------|----------------------|---------|--------------|
| AC-1 | Gate classifies staged changes into 6 categories | Task 1 (spec), Task 2-3 (tests), Task 4 (impl) | Spec defines categories + patterns; tests cover all 6; implementation categorizes correctly |
| AC-2 | Early exit routes defined (docs-only → SKIP, etc.) | Task 1 (spec) | Spec documents routing recommendations (advisory, not enforced) |
| AC-3 | Reduced pipeline routes (tests-only, migration-only) | Task 1 (spec) | Spec documents routes; tests validate classification precision |
| AC-4 | Full pipeline route for runtime-code | Task 1 (spec), Task 2-4 (tests + impl) | Spec + tests ensure runtime-code always returns full-pipeline recommendation |
| AC-5 | Implemented as `ci/scripts/gates/diff_classification.py` | Task 4 (impl) | File exists at exact path; is valid Python module |
| AC-6 | Tested with 20+ change vectors | Task 2-3 (test design + break) | Tests cover all 6 categories + edge cases; 50+ total tests |
| AC-7 | Integrated into gate registry | Task 4 (impl), Task 6 (integration) | Registry entry added; gate is discoverable and callable via gate_runner.py |

---

## Risk & Assumptions Summary

### Critical Risks

| Risk ID | Description | Severity | Mitigation | Contingency |
|---------|-------------|----------|-----------|------------|
| R1 | Git diff parsing is fragile (Windows line endings, symlinks, binary files) | Medium | Mock git in all tests; use `git diff --cached --name-status` for robustness; document assumptions | Implementation Agent adds explicit error handling in gate module |
| R2 | File pattern rules become overly complex (too many special cases) | Low | Spec Agent enforces simplicity (max 10 patterns per category); prioritize common cases | If patterns bloat, defer edge cases to M903 |
| R3 | Category boundaries are ambiguous (e.g., is a README in src/ a docs or runtime change?) | Low | Spec Agent defines clear hierarchy (path > extension > heuristic); examples in test vectors | Test Designer adds edge case tests to clarify boundaries |
| R4 | Early exit logic (actual skipping) is out of scope, causing confusion | Medium | Spec Agent explicitly states "Gate only classifies; routing/skipping is M903 work" in documentation | Next ticket (M902-10) confirms M903 orchestration plan |

### Design Assumptions (see Checkpoint Protocol Log)

All assumptions logged in `project_board/checkpoints/M902-09/2026-05-18T-planning.md` are **Medium to High confidence**. No blocking ambiguities.

---

## File Tree (Post-Implementation)

```
ci/scripts/
├── gate_registry.json                                 # Updated: add diff_classification_check entry
├── gates/
│   └── diff_classification.py                        # New: gate module (~100-150 lines)

tests/ci/
├── gates/
│   ├── test_diff_classification.py                   # Primary tests (20+ cases)
│   ├── test_diff_classification_adversarial.py       # Adversarial tests
│   ├── test_diff_classification_mutation.py          # Mutation tests
│   └── test_diff_classification_stress.py            # Stress tests

project_board/
├── specs/
│   └── 902_09_diff_classification_gate_spec.md      # Spec (new, authored by Spec Agent)
├── checkpoints/
│   └── M902-09/
│       ├── 2026-05-18T-planning.md                  # Planning checkpoint (this run)
│       ├── <run_id>-test-design.md                  # Test design checkpoint (Task 2)
│       ├── <run_id>-test-break.md                   # Test break checkpoint (Task 3)
│       ├── <run_id>-static-qa.md                    # Static QA report (Task 5)
│       ├── <run_id>-learning.md                     # Learning log (Task 7)
│       └── gate-result-example-success.json         # Example gate output (success case)
│       └── gate-result-example-failure.json         # Example gate output (failure case - for docs)
├── execution_plans/
│   └── M902-09_stage_0_diff_classification_gate.md  # This execution plan

project_board/902_milestone_902_agent_predictabilitiy_improvements/
├── 01_in_progress/
│   └── 09_stage_0_diff_classification_gate.md       # Updated ticket (workflow state advanced)
└── README.md                                          # Updated with diff classification gate section (Task 6)
```

---

## Success Criteria (Per Task)

### Task 1 — Specification
- [ ] Spec document exists at `project_board/specs/902_09_diff_classification_gate_spec.md`
- [ ] Spec covers all 7 AC with measurable, testable requirements
- [ ] 6 categories defined with file patterns and examples
- [ ] Priority hierarchy clearly stated
- [ ] Output contract (JSON schema) matches M902-01 success/failure schemas
- [ ] 20+ test vectors specified (all categories + edge cases)
- [ ] No ambiguous prose; all requirements are testable

### Task 2 — Test Design
- [ ] Test design document exists
- [ ] 20+ behavioral tests designed (AC coverage matrix)
- [ ] Deterministic fixtures (no random file generation)
- [ ] Mock git diff strategy documented
- [ ] Tests runnable and expected to pass (100% pass rate target)

### Task 3 — Test Break
- [ ] Adversarial tests added (5-8 scenarios)
- [ ] Mutation tests added (3-5 logic variants)
- [ ] Stress tests added (2-3 scale tests)
- [ ] Total test count 50+
- [ ] All tests deterministic and pass at 100%

### Task 4 — Implementation
- [ ] Gate module exists at `ci/scripts/gates/diff_classification.py`
- [ ] Module is <200 lines
- [ ] Registry entry added to `ci/scripts/gate_registry.json`
- [ ] Gate runs via `python ci/scripts/gate_runner.py diff_classification_check ...`
- [ ] All 50+ tests pass
- [ ] Gate output conforms to M902-01 schemas

### Task 5 — Static QA
- [ ] All linters pass (Ruff, mypy, bandit)
- [ ] No type violations
- [ ] No security findings
- [ ] Code is well-documented

### Task 6 — Integration
- [ ] Gate is registered and callable
- [ ] Milestone README section added (or updated)
- [ ] Example outputs provided
- [ ] CI tests pass
- [ ] No manual fixes needed

### Task 7 — Learning
- [ ] Learning log created
- [ ] 3-5 insights appended to LEARNINGS.md
- [ ] Cross-milestone dependencies documented
- [ ] No escalations

---

## Notes

1. **Test Determinism:** All tests use mocked git (no actual git repo interaction). File patterns are fixtures (test_vectors.json or hardcoded). No temp files or cleanup issues.

2. **Gate Framework Alignment:** This plan assumes M902-01 (gate runner, schemas, registry) is complete and stable. M902-09 is a "consumer" gate, not framework work.

3. **Scope Boundary:** Classification logic only. Orchestration logic (actually skipping pipeline stages, routing to different validation pipelines) is M903 work.

4. **Documentation:** Spec-driven; all AC are testable. No prose-only acceptance criteria.

5. **Performance:** Per M902-01 NFR-01, gate must complete in <5 seconds. Diff classification should be <100ms even with 1000+ staged files.

6. **Handoff Clarity:** Each task produces specific deliverables and hands off to the next agent. No overlapping ownership.

---

## Glossary

- **Classification:** The act of categorizing a set of staged files into one of 6 categories (docs, formatting, lockfile, test, migration, runtime-code).
- **Priority Hierarchy:** The rule determining which category is selected when staged files span multiple categories (e.g., if a change touches both tests/ and scripts/, it's classified as runtime-code due to priority).
- **Recommended Route:** An advisory string suggesting which pipeline(s) should validate the change (e.g., "full_pipeline", "reduced_checks", "skip").
- **Advisory:** Non-blocking; the gate result is informational, not a hard block.
- **Shadow Mode:** Default execution mode for gates in M902; always exits 0, even on FAIL. Blocking mode is M903+ work.

---

## Sign-Off

**Plan Status:** FROZEN — Ready for Specification Phase  
**Prepared by:** Planner Agent  
**Date:** 2026-05-18  
**Next Agent:** Spec Agent  
**Confidence Level:** High (no blocking ambiguities; M902-01 is stable)

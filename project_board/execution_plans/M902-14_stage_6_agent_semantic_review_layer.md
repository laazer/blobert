# M902-14 Execution Plan: Stage 6 — Agent Semantic Review Layer

**Planner Agent Run:** 2026-05-19T-m902-14-planning  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/14_stage_6_agent_semantic_review_layer.md`  
**Status:** SPECIFICATION (Revision 2)  
**Confidence:** HIGH

---

## Project Overview

**M902-14** implements Stage 6 of the 8-stage governance pipeline: the **Agent Semantic Review Layer**. This stage receives focused semantic bundles extracted by M902-13 and evaluates them using rule-based agent logic to render APPROVE/WARN/REJECT decisions. The agent evaluates 8 key signals (SRP, abstraction, hierarchy, ownership, observability, async safety, exception handling, suppression justification) and outputs structured JSON with decision, confidence score, reasoning, and violations. The gate integrates into the M902-01 validation framework and routes decisions back to the pipeline (Stage 7: Override System).

**Key Constraints:**
- Agent receives only JSON bundle (no repo/git context)
- Decision logic is deterministic (same bundle → same output)
- Integration with M902-01 gate framework (registry, schema, runner)
- Evaluation against code_governance.md Stage 6 rules
- Non-blocking by default (advisory; enforcement deferred to M903)

---

## Task Breakdown

### Task 1: Freeze M902-14 Specification (Spec Agent)

**Objective:** Produce specification document with 6 frozen requirements, all 7 ACs mapped, design decisions logged in checkpoint protocol.

**Input:**
- Ticket M902-14 (acceptance criteria, dependencies)
- code_governance.md Stage 6 rules (8 evaluation signals, exit rules, decision priority)
- M902-13 bundle schema v1.0 (bundle structure, 20+ fields)
- M902-01 gate framework examples (registry entry, gate success schema)
- M902-02 spec examples (requirements structure, test vector format)

**Expected Output:**
- Specification file at `project_board/specs/902_14_agent_review_layer_spec.md` (v1.0 FROZEN)
- 6 Requirements documented with acceptance criteria:
  1. **Agent Module & Registry Entry:** Agent callable function `evaluate_bundle(bundle: dict) -> dict` at `ci/scripts/agents/semantic_reviewer.py`; gate wrapper at `ci/scripts/gates/agent_review_check.py`; registered in `gate_registry.json`
  2. **Bundle Evaluation Scope:** 8 signals (SRP, abstraction, hierarchy, ownership, observability, async, exception, suppression) with evaluation rules; input validation; confidence scoring logic
  3. **Agent Output Contract:** JSON schema with `decision` (approve/warn/reject), `confidence` (0.0–1.0), `reasoning` (str), `violations` (array with rule_id/severity/message), `evaluated_signals` (array)
  4. **Gate Integration:** Gate reads bundle from `.semantic_reviews/<issue_id>.json`, validates input, calls agent, returns result in M902-01 gate schema + agent fields
  5. **Test Vector Coverage:** 35+ test vectors covering: (a) all 8 signals, (b) decision outcomes (approve/warn/reject), (c) confidence edge cases, (d) bundle variations (clean/violations/edge cases), (e) determinism validation
  6. **Edge Cases & Error Handling:** Malformed bundles, missing fields, type mismatches, determinism requirements, performance constraints, graceful degradation
- All 7 ticket ACs mapped to requirements
- Checkpoint decisions logged: (1) determinism strategy (same bundle → same JSON), (2) decision priority (reject if critical signal, else warn if ambiguous, else approve), (3) confidence bounds [0.0, 1.0], (4) bundle-only input contract, (5) rule-based logic (not LLM), (6) suppression validation approach, (7) performance target <2s per bundle
- No ambiguities remain; all clarifying questions resolved

**Dependencies:** None (M902-01, M902-13 already COMPLETE; code_governance.md available)

**Success Criteria:**
- Spec v1.0 file created at `project_board/specs/902_14_agent_review_layer_spec.md`
- All 6 requirements ≥150 words each with clear acceptance criteria
- All 7 ticket ACs mapped to requirement(s) with traceability
- Checkpoint log at `project_board/checkpoints/M902-14/2026-05-19T-m902-14-specification.md` with decisions + confidence
- No missing sections (deferred scope listed explicitly: M903+ orchestration, agent scheduling, feedback loops)
- File tree specified (input: `.semantic_reviews/<issue_id>.json`; output: decision JSON; agent module path; test paths)
- Spec marked "FROZEN v1.0" and ready for spec exit gate

**Risks / Assumptions:**
- **Risk:** Agent reasoning domain too large (8 signals hard to weigh jointly) → **Mitigation:** Spec freezes decision priority (reject if any critical signal, else warn if ambiguous, else approve); signal evaluation is independent
- **Risk:** Bundle schema mismatch with M902-13 → **Mitigation:** Spec references M902-13 bundle v1.0 schema explicitly; input contract frozen in Requirement 02
- **Risk:** Non-deterministic agent (LLM-based sampling) conflicts with determinism mandate → **Mitigation:** Spec requires rule-based logic, not LLM sampling; tests validate idempotence
- **Assumption:** M902-13 bundle schema v1.0 is stable (no changes) → Evidence: M902-13 COMPLETE, bundle schema frozen in spec
- **Assumption:** code_governance.md Stage 6 rules are authoritative (no later changes) → Evidence: code_governance.md is architectural spec, treated as read-only after publication
- **Assumption:** Agent SDK supports instruction-based agents (not full dialogue agents) → Evidence: (TBD during implementation) if SDK doesn't support, escalate to Human for re-scoping

---

### Task 2: Design Behavioral Test Suite (Test Designer)

**Objective:** Create 50+ behavioral tests covering all 8 evaluation signals and decision outcomes.

**Input:**
- Spec v1.0 from Task 1
- M902-13 bundle examples (from project_board/checkpoints/M902-13 or mocked)
- code_governance.md Stage 6 rules
- M902-02 test design examples (parametrized tests, fixtures, assertions)

**Expected Output:**
- Test file `tests/ci/test_semantic_reviewer_agent.py` with 50+ behavioral tests
- Test organization by signal type:
  - **SRP (5+ tests):** single-responsibility vs multi-role classes, composition vs inheritance, proper layering
  - **Abstraction (5+ tests):** unnecessary abstraction, leaky abstraction, proper abstraction, composition patterns
  - **Hierarchy (5+ tests):** deep inheritance chains, proper layering, cross-layer imports, cycle detection
  - **Ownership (5+ tests):** conflicting owners, ambiguous ownership, clear assignment, ownership matrix validation
  - **Observability (5+ tests):** missing logging, missing audit events, structured logging, correlation IDs
  - **Async (5+ tests):** blocking calls in async context, proper cancellation handling, sync/async boundary correctness
  - **Exception (5+ tests):** silent failures, proper re-raise, recovery logic, exception context preservation
  - **Suppression (5+ tests):** justified suppression, unjustified suppression, expiration validation, ticket references
  - **Cross-functional (5+ tests):** bundles with multiple violations, decision priority, confidence scoring
  - **Edge cases (3+ tests):** empty bundle, minimal bundle, malformed suppression
- Each test uses pytest parametrize; fixtures provide M902-13 bundle mocks
- Each test validates: (1) decision (approve/warn/reject), (2) confidence [0.0, 1.0], (3) reasoning non-empty, (4) violations array structure
- All tests deterministic (no randomness, no mocking of agent internals, only bundle fixtures)
- Test names describe scenario clearly (e.g., `test_srp_single_responsibility_approved`, `test_abstraction_unnecessary_rejected`)

**Dependencies:** Task 1 (Spec v1.0 COMPLETE)

**Success Criteria:**
- Test file `tests/ci/test_semantic_reviewer_agent.py` exists with 50+ passing tests (before implementation, expected failures OK)
- All 8 signal types covered with ≥5 tests each
- Each test validates decision + confidence + reasoning + violations structure
- Test names self-documenting (describe signal + scenario)
- Docstrings reference AC numbers and rule IDs from code_governance.md
- Edge case coverage: empty bundles, malformed input (handled gracefully)
- All tests deterministic (can run twice, produce same results)
- Coverage aligns with Requirement 05 test vectors from spec (35 vectors → ~5–7 tests per signal type)

**Risks / Assumptions:**
- **Risk:** Test vectors conflict with code_governance.md rules → **Mitigation:** Spec freezes rule priorities in Requirement 02; tests validate against those
- **Risk:** Agent logic not yet implemented (tests fail before Task 4) → **Mitigation:** Behavioral tests define expected behavior; implementation must satisfy all tests
- **Assumption:** Bundle schema from M902-13 matches input contract → Evidence: spec references M902-13 v1.0 schema
- **Assumption:** code_governance.md rules are source of truth → Evidence: rules are architectural spec, frozen

---

### Task 3: Develop Adversarial Test Suite (Test Breaker)

**Objective:** Create 40+ adversarial tests for edge cases, stress conditions, and determinism validation.

**Input:**
- Spec v1.0 from Task 1
- Behavioral tests from Task 2
- code_governance.md Stage 6 rules
- Checkpoint protocol (for decision logging)

**Expected Output:**
- Test file `tests/ci/test_semantic_reviewer_agent_adversarial.py` with 40+ parametrized tests
- Test categories:
  - **Boundary conditions (8 tests):** confidence thresholds (0.0, 0.5, 1.0), empty violations, null optional fields, rule_id edge lengths
  - **Malformed input (6 tests):** missing required bundle fields (code_hunks, violations_summary), extra unexpected fields, type mismatches
  - **Decision consistency (4 tests):** same bundle twice → identical output, violations in different order → same decision
  - **Confidence scoring (4 tests):** high-confidence approvals, low-confidence warns, reject with uncertainty
  - **Rule conflict resolution (4 tests):** multiple violations (SRP + async) → decision priority (reject async > warn SRP > approve)
  - **Suppression edge cases (4 tests):** suppression without justification, expiration date (past/future), invalid ticket reference
  - **Performance & stress (3 tests):** large bundle (100+ violations), deep import graph (50+ modules), code hunks >1000 lines
  - **Schema compliance (4 tests):** output JSON valid, all required fields, types correct, enum values only
  - **Determinism emphasis (4 tests):** idempotence, order independence, no timestamps in logic
- Checkpoint decisions logged for:
  1. Determinism priority (same bundle → identical JSON, not just semantically equal)
  2. Decision priority cascade (reject > warn > approve when multiple signals)
  3. Confidence bounds strict [0.0, 1.0] (no negative, no >1.0)
  4. Suppression without justification → violation added to output
  5. Empty bundle (0 violations) → approve with confidence 0.7–0.8
- All tests initially expected to fail (before Task 4 implementation)

**Dependencies:** Tasks 1–2 (Spec v1.0, behavioral tests COMPLETE)

**Success Criteria:**
- Test file `tests/ci/test_semantic_reviewer_agent_adversarial.py` exists with 40+ tests
- All tests parametrized and documented with checkpoint decisions
- Assertions are strict (not "approximately equal"; exact bounds/enum values)
- Edge case coverage: confidence boundaries, empty/minimal bundles, malformed input, determinism, rule conflict, performance
- Checkpoint log at `project_board/checkpoints/M902-14/2026-05-19T-m902-14-test_break.md` documenting decisions
- Performance assertions target <2s per bundle
- Determinism tests call agent twice and compare JSON byte-for-byte

**Risks / Assumptions:**
- **Risk:** Adversarial tests too strict (implementation can't satisfy) → **Mitigation:** Checkpoint decisions are conservative (match code_governance.md Stage 6 rules)
- **Risk:** Determinism conflicts with LLM-based agent → **Mitigation:** Spec mandates rule-based logic, not LLM sampling
- **Assumption:** code_governance.md decision priority (reject async > reject SRP > warn observability) is correct → Evidence: architectural spec

---

### Task 4: Implement Agent Module & Gate Integration (Implementation Agent)

**Objective:** Implement agent module and gate wrapper; ensure all 90+ tests pass.

**Input:**
- Spec v1.0 from Task 1
- Behavioral + adversarial tests (Tasks 2–3)
- code_governance.md Stage 6 rules
- M902-13 bundle examples
- M902-01 gate framework (for schema reference)

**Expected Output:**

**(a) Agent module** at `ci/scripts/agents/semantic_reviewer.py` (~200 LOC):
- Function `evaluate_bundle(bundle: dict) -> dict` that:
  1. Validates bundle schema (required fields: code_hunks, import_graph, ownership, related_tests, violations_summary, change_summary, metadata)
  2. Evaluates 8 signals (SRP, abstraction, hierarchy, ownership, observability, async, exception, suppression)
  3. Scores confidence per signal (0.0–1.0)
  4. Determines decision (reject if critical, warn if ambiguous, approve if clean)
  5. Generates reasoning (1–3 sentences per signal, max 500 chars total)
  6. Compiles violations array (for warn/reject decisions)
  7. Returns JSON dict: `{decision, confidence, reasoning, violations, evaluated_signals}`
- Signal evaluation functions (one per signal, modular SRP design)
- Exception handling per code_governance.md (no bare except, all logged with context)
- Determinism enforced (same bundle → identical JSON; sorted output)

**(b) Gate wrapper** at `ci/scripts/gates/agent_review_check.py` (~100 LOC):
- Function `run(inputs: dict) -> dict` that:
  1. Reads bundle path from inputs (or from `.semantic_reviews/<issue_id>.json`)
  2. Loads bundle JSON
  3. Calls `evaluate_bundle()`
  4. Transforms output to gate success schema (M902-01: status, gate, timestamp, ticket_id, message, violations, artifacts, duration_ms)
  5. Adds agent-specific fields: `decision`, `confidence`, `agent_decision_reasoning`
  6. Registers gate in `ci/scripts/gate_registry.json`
- Entry in gate_registry.json: `{name: agent_review_check, module: ci.scripts.gates.agent_review_check, run_function: run, ...}`

**(c) Code quality:**
- No bare except; all exceptions logged with context, re-raised or transformed
- Bundle validation errors → log WARNING, skip validation, continue with best-effort evaluation
- Determinism: same bundle input → identical JSON (no timestamps in decision, sorted JSON output)

**Dependencies:** Tasks 1–3 (Spec v1.0, tests all written COMPLETE)

**Success Criteria:**
- Agent module `ci/scripts/agents/semantic_reviewer.py` exists, importable, passes all 50+ behavioral tests (100% pass rate)
- Gate module `ci/scripts/gates/agent_review_check.py` exists, importable, registered in gate_registry.json
- All 40+ adversarial tests pass (100% pass rate)
- Code review: (1) no bare except, (2) modular signal functions, (3) clear confidence thresholds documented, (4) decision priority documented, (5) determinism validated
- Determinism proven: running gate twice with same input produces identical JSON (byte-for-byte)
- Performance: agent <2s per bundle; gate overhead <500ms
- Git commit with message: `feat(M902-14): implement agent semantic review layer (Stage 6) with gate integration`
- Changes pushed to origin

**Risks / Assumptions:**
- **Risk:** Agent logic too complex (8 signals hard to weight jointly) → **Mitigation:** Decision priority cascades (reject if critical, else warn if ambiguous, else approve); signal evaluation is independent, no ML weighting
- **Risk:** Determinism requires frozen logic (not LLM) → **Mitigation:** Implementation uses rule-based logic, not sampling
- **Risk:** Bundle validation too strict (rejects valid bundles) → **Mitigation:** Error handling degrades gracefully (skip validation, continue with evaluation, log WARNING)
- **Assumption:** code_governance.md Stage 6 rules define decision tree (not ambiguous) → Evidence: rules from architectural spec
- **Assumption:** Confidence scoring uses heuristic weights (SRP violation → -0.2, clear abstraction → +0.1, etc.) → Evidence: spec Requirement 03 defines confidence logic

---

### Task 5: Static QA & Code Review (Static QA Agent)

**Objective:** Verify code quality, security, test coverage, and design choices.

**Input:**
- Implementation from Task 4: agent module + gate module + gate_registry.json + test files
- code_governance.md Stage 6
- Confidence thresholds & decision priority from Task 4 checkpoint

**Expected Output:**

**(a) Linting & imports** (`task hooks:py-review`):
- Ruff E9/F/I checks: 0 errors, 0 warnings
- Import organization: correct, no undefined names

**(b) Type checking** (mypy if configured):
- 0 type errors on agent module

**(c) Code organization** (`task hooks:py-organization`):
- SRP verified at module level (8 signals separated or clearly demarcated)
- No cross-domain logic bleed
- Naming consistent with codebase

**(d) Test coverage** (diff-cover if configured):
- Agent module coverage ≥90%
- Gate wrapper coverage ≥80%

**(e) Security checks** (bandit):
- 0 hardcoded secrets
- 0 unsafe deserialization in bundle loading

**(f) Code review findings** (manual spot-check):
- Confidence threshold documentation (why 0.8 approve, why 0.3 warn?)
- Signal evaluation order (why reject async first?)
- Exception handling patterns (no bare except, all logged)
- Bundle validation edge cases (what if code_hunks empty?)
- Determinism proof (no timestamps, sorted JSON)

**Dependencies:** Task 4 (Implementation COMPLETE)

**Success Criteria:**
- Linting report: 0 errors, 0 warnings
- Type checking: 0 errors (if mypy used)
- Code organization: SRP boundary clear, modular signal functions
- Test coverage: ≥90% agent, ≥80% gate
- Security findings: 0 issues
- Code review: 5–10 findings documented with resolutions (code fixes or design notes)
- No blocking issues; all findings addressed before handoff
- Confidence: HIGH

**Risks / Assumptions:**
- **Risk:** Coverage thresholds too strict → **Mitigation:** Agent module logically complete (all 8 signals evaluated), gate wrapper simple
- **Risk:** Code review disputes design choices → **Mitigation:** Spec and checkpoint log document decisions
- **Assumption:** diff-cover and mypy configured for project (check if available)

---

### Task 6: Integration Testing (Integration Agent)

**Objective:** Validate agent + gate in pipeline context; end-to-end workflow testing.

**Input:**
- Implementation from Task 4 + Static QA findings resolved (Task 5)
- M902-13 bundle examples
- M902-01 gate framework
- M902-12 risk_scoring output examples

**Expected Output:**

**(a) Integration test file** `tests/ci/test_agent_review_integration.py` with 3–5 E2E tests:
1. Simple bundle (clean code) → approve decision
2. High-risk bundle with violations → warn/reject decision
3. Determinism test (run twice) → identical outputs
4. Schema compliance (gate output has all required fields)
5. Performance baseline (agent <2s, gate overhead <500ms)

**(b) Compatibility matrix:**
- Bundle schema v1.0 input matches spec contract
- Gate output extends M902-01 schema (all fields present)
- Agent decision enum (approve/warn/reject) matches orchestrator expectations
- Confidence score [0.0–1.0] usable for decision weighting by M903

**(c) Determinism validation:**
- Run pipeline twice with same inputs
- Compare agent outputs byte-for-byte (determinism across full pipeline)

**(d) Documentation:**
- Integration notes in Task 6 checkpoint (how M902-14 fits into M902-01 framework, M903 orchestration contract)

**Dependencies:** Tasks 4–5 (Implementation + Static QA COMPLETE)

**Success Criteria:**
- Integration test file exists with 3–5 tests, all passing
- No schema mismatches (bundle input, gate output, orchestrator compatibility)
- Determinism validated (same input → identical output)
- Performance acceptable (<2.5s per bundle)
- Integration test coverage ≥80% of critical paths (clean → warn/reject paths)
- No blockers for Stage 7 (M903 orchestration)

**Risks / Assumptions:**
- **Risk:** M903 orchestrator not yet implemented → **Mitigation:** Integration test mocks orchestrator logic; actual M903 integration deferred
- **Risk:** Bundle schema v1.0 incompatible → **Mitigation:** Test validates against M902-13 schema explicitly
- **Assumption:** M902-13 bundle examples available (in checkpoints or can be mocked)

---

### Task 7: AC Gatekeeper Final Validation (AC Gatekeeper)

**Objective:** Verify all 7 acceptance criteria satisfied; evidence matrix complete; ready for COMPLETE.

**Input:**
- Implementation from Task 4 + tests from Tasks 2–3 + integration tests from Task 6
- Spec v1.0 from Task 1
- All 7 acceptance criteria

**Expected Output:**

**(a) AC evidence matrix** (one-page summary):
- AC # → Requirement(s) → Test(s) → Implementation code section
- All 7 ACs → corresponding requirements + test evidence + implementation

**(b) Final validation report:**
- All 7 ACs marked SATISFIED with evidence references
- Blockers: None (or escalate if any)
- Confidence assessment per AC (HIGH/MEDIUM/LOW)
- Overall recommendation: READY FOR COMPLETE if all ACs satisfied + no blockers

**(c) Checkpoint log:**
- `project_board/checkpoints/M902-14/2026-05-19T-m902-14-ac_gatekeeper_final.md`
- Validation matrix + confidence assessment

**(d) Git state:**
- All changes committed
- Working tree clean
- Commits pushed to origin

**AC Verification:**

| AC # | Description | Evidence | Status |
|------|-------------|----------|--------|
| AC-1 | Agent evaluates 8 signals (SRP, abstraction, hierarchy, ownership, observability, async, exception, suppression) | Implementation of all 8 signal evaluation functions in semantic_reviewer.py; 8 separate test groups (8×5+ tests = 40+ tests) | EVIDENCED |
| AC-2 | Agent output JSON: decision (approve/warn/reject), confidence (0.0–1.0), reasoning, violations | Output validation in 50+ behavioral tests + schema compliance tests (4 tests); determinism tests verify JSON structure | EVIDENCED |
| AC-3 | Integrated into validation gate system as callable agent | Gate wrapper agent_review_check.py + gate_registry.json entry; integration tests validate gate_runner compatibility | EVIDENCED |
| AC-4 | Gate routes: APPROVE → Stage 7, WARN → log + proceed, REJECT → FAIL back to implementation | Routing logic documented in gate wrapper; integration test mocks M903 orchestrator; actual M903 routing deferred | EVIDENCED (for Stage 6 scope) |
| AC-5 | Implemented as agent instruction set in `agent_context/agents/` | Agent module path: ci/scripts/agents/semantic_reviewer.py (not agent_context/agents/); location TBD based on actual agent_context structure; importable + tested | NEEDS CLARIFICATION |
| AC-6 | Tested with known architectural patterns and edge cases | 90+ tests (50 behavioral + 40 adversarial) covering all 8 signals, edge cases, determinism, performance | EVIDENCED |
| AC-7 | Agent receives only extracted bundle (not full repo context) | Input contract spec: bundle JSON only; agent has no file/git/repo access; integration test validates bundle-only input | EVIDENCED |

**AC-5 Note:** Ticket specifies `agent_context/agents/` but this directory may not exist yet. Clarification needed:
- If `agent_context/agents/` exists: move semantic_reviewer.py there and update imports
- If `agent_context/agents/` doesn't exist: create it as part of Task 4 (Implementation Agent)
- Alternative: Keep agent module in `ci/scripts/agents/` if that's the project convention

**Dependencies:** All tasks 1–6 COMPLETE

**Success Criteria:**
- All 7 ACs evidenced and satisfied
- Evidence is executable (test results, not prose)
- No blockers
- Git state clean (all changes committed + pushed)
- Confidence ≥HIGH for advancing to COMPLETE
- Checkpoint log complete with validation matrix

**Risks / Assumptions:**
- **Risk:** AC-4 routing not fully testable (M903 not implemented) → **Mitigation:** Integration test mocks routing per spec; actual M903 validation deferred
- **Risk:** AC-5 location ambiguous (agent_context/agents/ vs ci/scripts/agents/) → **Mitigation:** Clarify with project structure; move if needed during implementation

---

## Dependencies & Blockers

### Hard Dependencies
| Dependency | Ticket | Status | Impact |
|---|---|---|---|
| M902-01 (Validation Gate Framework) | COMPLETE | Gate registry, schema, runner framework available and stable |
| M902-13 (Semantic Extraction) | COMPLETE | Bundle schema v1.0 frozen; bundle examples in checkpoints |
| code_governance.md Stage 6 | Reference | 8 evaluation signals, exit rules, decision priority defined |

**No blocking dependencies.** All hard dependencies COMPLETE.

### Child Tickets
None. M902-14 is not an umbrella ticket.

---

## Assumptions & Risk Register

### Critical Assumptions

1. **M902-01 gate framework stable:** Registry, schema, runner available without changes
2. **M902-13 bundle schema frozen:** Bundle v1.0 is final; no changes during M902-14 implementation
3. **code_governance.md Stage 6 authoritative:** 8 evaluation signals, exit rules, decision priority are source of truth
4. **Agent SDK supports instruction-based agents:** Implementation uses deterministic rule-based logic, not LLM sampling/dialogue
5. **Bundle input contract read-only:** Agent never receives git, file system, or full repo context; only JSON bundle
6. **Determinism mandatory:** Same bundle → same JSON output (no randomness, no timestamps in decision logic)
7. **Decision routing deferred to M903:** Agent outputs decision + confidence; actual routing (APPROVE → Stage 7) handled by orchestrator
8. **AC-5 location:** `agent_context/agents/` location either exists or will be created during implementation; clarification TBD

### Risk Register

| Risk ID | Description | Probability | Impact | Mitigation |
|---------|---|---|---|---|
| R1 | Agent logic too complex (8 signals hard to weigh jointly) | MEDIUM | HIGH | Spec freezes decision priority cascade (reject if critical, else warn if ambiguous, else approve); signal evaluation independent |
| R2 | Bundle schema mismatch with M902-13 | LOW | MEDIUM | Spec references M902-13 bundle v1.0 schema explicitly; input contract frozen in Requirement 02; test validates against contract |
| R3 | Non-deterministic agent output (LLM-based sampling) conflicts with determinism mandate | MEDIUM | MEDIUM | Spec requires rule-based logic, not LLM sampling; tests validate idempotence (run twice, same result) |
| R4 | Agent sees full repo context (violates AC-7) | LOW | CRITICAL | Input contract spec: bundle JSON only; agent has no file/git/repo access; integration test validates |
| R5 | M903 orchestrator not ready; routing logic incomplete | LOW | LOW | Integration test mocks orchestrator logic per spec; actual M903 integration deferred; no blocker for Stage 6 |
| R6 | Code review disputes design choices (confidence bounds, decision priority) | MEDIUM | LOW | Spec and checkpoint decisions document design choices; code comments reference rules from code_governance.md |
| R7 | Performance degradation (agent >2s per bundle) | LOW | MEDIUM | Target <2s agent, <500ms gate overhead; stress test bundle (100+ violations) in adversarial suite; establish baseline |
| R8 | AC-5 location ambiguity (agent_context/agents/ vs ci/scripts/agents/) | MEDIUM | LOW | Clarify with project structure; move if needed during Task 4 (Implementation Agent) |

---

## Schedule & Sequencing

**All tasks sequential (no parallelization).** Each task depends on prior tasks completing.

| Task | Agent | Estimated Duration | Sequence |
|------|-------|-------------------|----------|
| 1 | Spec Agent | 2–3 hours | After Planner (this run); before Test Designer |
| 2 | Test Designer | 2–3 hours | After Spec v1.0 COMPLETE |
| 3 | Test Breaker | 1.5–2 hours | After behavioral tests; before Implementation |
| 4 | Implementation | 2–3 hours | After all tests frozen; may run tests concurrently |
| 5 | Static QA | 1–1.5 hours | After Implementation |
| 6 | Integration | 1–1.5 hours | After Static QA findings resolved |
| 7 | AC Gatekeeper | 1 hour | Final validation before COMPLETE |

**Total: ~11–15 hours across 7 sequential tasks**

---

## File Tree & Paths (Post-Implementation)

```
project_board/
├── specs/
│   └── 902_14_agent_review_layer_spec.md             # Spec v1.0 (Task 1)
├── execution_plans/
│   └── M902-14_stage_6_agent_semantic_review_layer.md # This file
├── checkpoints/
│   └── M902-14/
│       ├── 2026-05-19T-m902-14-planning.md            # Planner (this run)
│       ├── 2026-05-19T-m902-14-specification.md       # Spec Agent (Task 1)
│       ├── 2026-05-19T-m902-14-test_design.md         # Test Designer (Task 2)
│       ├── 2026-05-19T-m902-14-test_break.md          # Test Breaker (Task 3)
│       ├── 2026-05-19T-m902-14-implementation.md      # Implementation (Task 4)
│       ├── 2026-05-19T-m902-14-static_qa.md           # Static QA (Task 5)
│       ├── 2026-05-19T-m902-14-integration.md         # Integration (Task 6)
│       └── 2026-05-19T-m902-14-ac_gatekeeper_final.md # AC Gatekeeper (Task 7)
└── (01_active|02_complete)/
    └── 14_stage_6_agent_semantic_review_layer.md      # Ticket (moved to 02_complete at Stage COMPLETE)

ci/scripts/
├── agents/
│   └── semantic_reviewer.py                            # Agent module (NEW, Task 4)
├── gates/
│   ├── __init__.py
│   └── agent_review_check.py                           # Gate wrapper (NEW, Task 4)
└── gate_registry.json                                  # Updated entry (Task 4)

tests/ci/
├── test_semantic_reviewer_agent.py                    # Behavioral tests (NEW, Task 2)
├── test_semantic_reviewer_agent_adversarial.py        # Adversarial tests (NEW, Task 3)
└── test_agent_review_integration.py                   # Integration tests (NEW, Task 6)

.semantic_reviews/                                      # Input bundle directory (OUTPUT ARTIFACTS, NOT COMMITTED)
└── <issue_id>.json                                     # Example: PR-42.json, M902-14.json
```

---

## Success Criteria Summary

**All 7 tasks must complete with:**
1. Spec v1.0 FROZEN (all ambiguities resolved, all design decisions logged)
2. 50+ behavioral tests PASSING
3. 40+ adversarial tests PASSING
4. Implementation 100% PASSING all 90+ tests
5. Static QA 0 issues (or all resolved)
6. Integration tests PASSING (determinism validated, schema compatible)
7. AC Gatekeeper validates all 7 ACs satisfied; no blockers
8. Git state clean (all changes committed + pushed)
9. Ticket moved to `02_complete/` with Stage COMPLETE

---

## Deferred Scope (M903+)

- **Orchestration & routing:** Which changes trigger bundling, per-PR vs per-commit routing, bundle archival (M903 responsibility)
- **Agent scheduling:** When/how agent review runs, feedback loops, re-evaluation after fixes (M903+)
- **Bundle versioning & trends:** Long-term storage, statistical analysis, historical comparison (M903+)
- **Multi-language support:** Python-centric in M902-14; JavaScript, GDScript extension (M904+)
- **Semantic code analysis:** AST-level feature extraction, complexity scoring beyond imports (M904+)
- **Machine learning refinement:** ML-based signal weighting, neural feature extraction (M905+)
- **Interactive agent feedback:** Bundle clarifications, agent follow-up questions (M906+)
- **Full dialogue agents:** LLM-based conversational review (M906+)

**M902-14 scope:** Stage 6 agent semantic review layer (evaluation, decision, JSON output) only. Orchestration deferred.

---

**Status:** PLANNING COMPLETE. Ready for Spec Agent (Task 1).

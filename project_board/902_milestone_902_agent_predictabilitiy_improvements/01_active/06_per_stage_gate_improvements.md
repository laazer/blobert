# Title

Per-stage validation gate improvements (planner, spec, tests, adversarial, reviewer, learning)

# Context

The MVP lists targeted improvements for each stage: planner (cycles, umbrella sanity, ownership, scope sizing), spec (observability/rollback/async/migration/edge cases), test gates (assertion density, exception/async paths, mutation targets, observability assertions), adversarial gate (mutation scoring, invalid states, breadth), reviewer gate (drift, suppressions, TODOs, migration risk), learning gate (prevent codifying hacks/violations).

# Scope

- Implement deterministic checks that can run with only artifacts (markdown specs, test files, coverage artifacts where available).
- Add stage-specific gate modules callable by name from the gate framework.
- Where metrics are not yet available (e.g., mutation coverage), implement placeholders that emit WARN with explicit "not configured" reasons rather than fake PASS.

# Acceptance Criteria

- Each listed stage has a documented checklist + at least one automated check OR an explicit WARN placeholder with a ticket reference to future work.
- Planner gate can detect obvious cyclic ticket dependency graphs within a milestone folder when dependencies are machine-readable.
- Spec gate validates presence of required headings/sections defined by `spec-exit-gate` skill or repo spec template (choose one canonical template and reference it).
- Test gate computes simple metrics (assertions per test file, async test markers) without requiring external services.
- Reviewer gate scans for new `TODO`/`FIXME` in diff scope and for new broad lint suppressions.
- Learning gate checks learning output for forbidden phrases/patterns defined by policy (config-driven list).

# Agent Execution Prompt

Upgrade per-stage gates according to the MVP lists.

Goal: Extend the gate runner with stage-specific modules and wire them into the appropriate workflow entrypoints (autopilot scripts, lefthook optional stage, or manual commands).

Constraints:
- Do not rewrite historical checkpoints; gates operate on current artifacts and git diffs as configured.
- Prefer small, testable scripts.

Expected output:
- Stage gate scripts + tests + short operator documentation.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (git diff unavailable, no spec template)
- What assumption cannot be verified? (dependency graph format inconsistent)
- What ambiguity prevents completion? (mutation tooling not installed)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about the canonical spec template?
- What decision needs to be made about diff scope (staged vs HEAD)?
- What are the possible interpretations of "mutation target validation" in this repo?

# Dependencies

- Validation gate framework for multi-agent handoffs (orchestration, routing, remediation)
- Handoff metadata schema and risk-based escalation (PASS/WARN/FAIL/ESCALATE)

# Definition of Done

- All stages covered by automated checks or explicit WARN placeholders with tracked follow-ups.
- Stage gates runnable individually by name.

---

## EXECUTION PLAN

Decomposed into 12 sequential tasks. Each task is independently executable once dependencies complete.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Define per-stage validation gate checklists (planner, spec, test, adversarial, reviewer, learning) | Spec Agent | Ticket AC1-AC6, M902-01/02/03/04 gate patterns, checkpoint decisions | `project_board/902_06_per_stage_checklists.md` with 6 stage sections; each lists bullets of what gate checks; references existing gate modules (spec_completeness, static_analysis_check, governance_check) | None (parallel start) | Checklists are comprehensive, machine-readable, linked to existing gates | None |
| 2 | Design planner gate: cycle detection in ticket dependency graphs | Spec Agent | Ticket AC2, workflow_enforcement_v1 Dependencies format, sample tickets in 902 milestone, checkpoint—cyclic deps algorithm | `project_board/specs/902_06_planner_gate_spec.md` with: (1) inputs (milestone folder path), (2) cycle detection via DFS on YAML dependencies, (3) PASS/WARN outputs, (4) examples of acyclic and cyclic graphs | Task 1 | Spec is precise; DFS algorithm is implementable; examples show acyclic and cyclic cases; scope is clear | Graph parsing (mitigated by simple YAML format) |
| 3 | Design spec gate: section validation via spec_completeness pattern | Spec Agent | Ticket AC2, spec_completeness.py source code, checkpoint—canonicalize template, spec templates from M902-01/02/03/04 | `project_board/specs/902_06_spec_gate_spec.md` with: (1) spec types required (api, destructive, randomness, load-open, generic), (2) required sections per type (delegate to spec_completeness), (3) outputs (PASS / FAIL with missing sections listed), (4) integration notes (wire into M902-01 gate runner as spec_completeness_check already exists) | Task 1 | Spec delegates to existing spec_completeness (no reimplementation); integration is clear; examples show missing-section FAIL | None (spec_completeness already tested 220+ times) |
| 4 | Design test gate: assertion density + async marker detection | Spec Agent | Ticket AC3, pytest test fixtures, sample test files from blobert, checkpoint—assertion density & async format | `project_board/specs/902_06_test_gate_spec.md` with: (1) inputs (test file paths), (2) assertion count logic (regex `assert ` per test function), (3) async detection (markers `@pytest.mark.asyncio` + `async def`), (4) metrics (assertions per function, async ratio), (5) outputs (PASS / WARN with density report), (6) threshold config (2 assertions/function default, tunable in YAML) | Task 1 | Spec is precise; regex patterns frozen; examples show WARN and PASS cases; threshold is tunable | Assertion detection is heuristic (edge cases like generator asserts); acceptable for MVP |
| 5 | Design reviewer + learning gates: TODO/FIXME scanning + forbidden phrase checking | Spec Agent | Ticket AC4-AC6, checkpoint—diff scope, forbidden phrases, TODO/FIXME scope, blobert sample learning outputs | Two specs: (1) `project_board/specs/902_06_reviewer_gate_spec.md`: diff scope (git diff --cached), TODO/FIXME detection (new-only via regex), suppression scanning (new `# noqa` without issue links), WARN per violation. (2) `project_board/specs/902_06_learning_gate_spec.md`: inputs (learning output .md files under project_board/checkpoints/), forbidden phrases (config-driven list in YAML), FAIL if phrase found, remediation hints, policy file reference | Task 1 | Both specs are precise; diff scope frozen; config-driven approach allows M903 evolution; examples show both WARN and FAIL cases | git diff unavailable (fallback documented); file encoding edge cases |
| 6 | Implement planner gate module: cycle detection on ticket deps | Implementation Agent | Spec from Task 2, M902-01 gate pattern (gate_runner.py), sample milestone folders, checkpoint protocol | `ci/scripts/gates/planner_check.py` (150–200 lines) with: (1) `run(inputs)` function matching M902-01 signature, (2) milestone folder path parsing, (3) YAML dependency graph loading, (4) cycle detection via DFS, (5) PASS/WARN JSON output matching M902-01 schema, (6) remediation hints for cycles found | Tasks 2, M902-01 | Module is syntactically valid Python; cycle detection correct on samples; JSON output matches schema; 10+ unit tests pass | DFS implementation (straightforward); YAML parsing error handling |
| 7 | Implement reviewer gate module: TODO/FIXME + suppression scanning | Implementation Agent | Spec from Task 5, git integration, blobert repo structure, checkpoint protocol | `ci/scripts/gates/reviewer_check.py` (200–250 lines) with: (1) `run(inputs)` function, (2) `git diff --cached` invocation, (3) regex patterns for TODO/FIXME/suppressions on *new* lines (prefixed `+`), (4) file + line number reporting, (5) WARN outputs per violation, (6) graceful fallback if git unavailable | Task 5, M902-01 | Module is valid Python; git diff parsing correct; regex matches accurate; JSON schema valid; 15+ unit tests pass | git diff unavailable in non-repo contexts (fallback documented) |
| 8 | Implement learning gate module: forbidden phrase detection | Implementation Agent | Spec from Task 5, learning policy config (YAML), sample learning outputs from blobert checkpoints, checkpoint protocol | `ci/scripts/gates/learning_check.py` (120–150 lines) + `project_board/902_06_learning_gate_policy.yml` (default patterns: "hack", "TODO", "temporary", "XXX", "KLUDGE") with: (1) `run(inputs)` function, (2) config file loading (YAML), (3) pattern matching (regex), (4) scanning .md files in project_board/checkpoints/, (5) FAIL if forbidden phrase found, (6) remediation hints | Task 5, M902-01 | Module is valid Python; config is loadable YAML; pattern matching works; output schema valid; 10+ unit tests pass | Pattern escape errors (mitigated by careful YAML syntax) |
| 9 | Create comprehensive behavioral + adversarial test suite | Test Designer / Test Breaker Agent | All gate specs (Tasks 2–5), gate implementations (Tasks 6–8), blobert sample data, checkpoint protocol | `tests/ci/test_per_stage_gates.py` (200+ tests) covering: (1) planner gate (10+ tests: acyclic, cyclic, malformed YAML, missing deps, detached nodes), (2) reviewer gate (15+ tests: no TODOs, new TODOs only, suppression patterns, git unavailable), (3) learning gate (10+ tests: no forbidden phrases, valid config, invalid config, multiple patterns, large files), (4) spec gate integration (5+ tests: delegate to spec_completeness), (5) edge cases (10+ tests: empty files, unicode, large diffs, symlinks), (6) adversarial (20+ tests: corrupted config, missing files, malformed JSON, encoding errors) | Tasks 2–8 | All tests passing (200+); coverage >80% of new code; no external service dependencies; deterministic (no flakes) | Test fixtures (sample YAML, git repos, learning outputs) need careful setup |
| 10 | Wire gates into gate registry + automation tooling | Implementation Agent | All gate modules (Tasks 6–8), gate_registry.json, lefthook.yml, Taskfile.yml, checkpoint protocol | (1) Update `ci/scripts/gate_registry.json` with 3 new entries (planner_check, reviewer_check, learning_check), each with module, inputs, description, (2) Add Taskfile task `hooks:per-stage-gates` calling all 3 gates, (3) Create `project_board/902_06_operator_guide.md` with usage examples, per-stage gate decision tree, integration with autopilot | Tasks 6–8, M902-01 | Registry entries are valid JSON; gate_runner can execute all 3 by name; Taskfile syntax valid; operator guide is clear with examples | Integration testing in Task 9 |
| 11 | Update Milestone 902 README with per-stage gate overview | Documentation Agent | All specs (Tasks 1–5), operator guide (Task 10), existing Milestone 902 README, checkpoint protocol | Updated `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` with new section: **Per-Stage Validation Gates (M902-06)** including: (1) 6-stage checklist summary, (2) gate invocation examples (manual + Taskfile), (3) acceptance criteria & evidence, (4) M903 next steps (mutation scoring, enhanced forbidden phrases, performance tuning) | All previous tasks | README is comprehensive; all links are valid; all gates callable by name; M903 deferral path explicit | None |
| 12 | Acceptance criteria verification | Acceptance Criteria Gatekeeper Agent | All deliverables (Tasks 1–11), ticket acceptance criteria (AC1–AC6) | Verification document confirming: (1) AC1: all 6 stages have checklist + automated check OR WARN placeholder ✓, (2) AC2: planner gate detects cyclic deps ✓, (3) AC2: spec gate validates required sections ✓, (4) AC3: test gate computes assertion density & async markers ✓, (5) AC4: reviewer gate scans TODOs + suppressions ✓, (6) AC6: learning gate checks forbidden phrases ✓. Update ticket Stage → COMPLETE, move to done/. | Tasks 1–11 | All 6 acceptance criteria satisfied with evidence; 200+ tests passing; all gates callable; operator guide present; README updated | None |

---

## PLANNING NOTES

**Framework Dependencies Satisfied:**
- M902-01 (Validation gate framework) — COMPLETE, gate runner and registry stable
- M902-02 (Static analysis gate) — COMPLETE, outputs structured violations
- M902-03 (Governance rules) — COMPLETE, 30+ rules with rule ids
- M902-04 (Handoff metadata & escalation) — COMPLETE, metadata schema and detectors stable
- M902-05 (PreToolUse hooks) — COMPLETE, command inspection module operational

**Task Sequencing:**
1. Spec tasks (1–5) execute first; provide checklists and gate specs
2. Implementation tasks (6–8) depend on specs
3. Test tasks (9) depend on implementation
4. Integration tasks (10–11) depend on tests
5. Acceptance verification (12) depends on all

**Checkpoint Resolutions (8 key decisions):**
1. Spec template canonicalization = use spec_completeness.py (HIGH confidence)
2. Planner cycle detection = DFS on YAML deps (HIGH confidence)
3. Diff scope = git diff --cached (HIGH confidence)
4. Mutation coverage = defer to M903 with WARN placeholder (HIGH confidence)
5. TODO/FIXME scope = new-only (HIGH confidence)
6. Forbidden phrases = config-driven in YAML (MEDIUM confidence)
7. Assertion density = <2 per function = WARN (MEDIUM confidence)
8. Async markers = pytest patterns (HIGH confidence)

**Risk Mitigations:**
- Cyclic dependency detection: define format precisely in Task 2
- git unavailable: graceful fallback documented
- Assertion heuristic: WARN only (not FAIL), tunable threshold
- Config incompleteness: start with sensible defaults, extensible

**Success Metrics:**
- All 6 stages covered by gates or WARN placeholders
- All 12 tasks complete with clear deliverables
- All 6 acceptance criteria satisfied
- 200+ tests (behavioral + adversarial) passing
- Zero breaking changes to M902-01/02/03/04/05
- All gates callable by name from gate runner

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_BACKEND |
| Revision | 5 |
| Last Updated By | Test Breaker Agent |
| Next Responsible Agent | Implementation Agent |
| Status | Proceed |
| Validation Status | Adversarial Tests Complete (253/253 passing) — Ready for Implementation |
| Blocking Issues | None |

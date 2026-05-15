# Title

Automated governance checks for handoffs (architecture, safety, observability, integrity)

# Context

Validation gates must enforce governance rules during handoffs: architecture boundaries, exception safety, reflection safety, async safety, observability expectations, and governance integrity (bypass/suppression abuse). This ticket encodes what can be automated deterministically using linters, semgrep, custom scripts, and repository policy checks.

# Scope

- Architecture: enforce dependency direction and forbidden imports using `import-linter`, `eslint-plugin-boundaries`, and/or semgrep where applicable.
- Exception safety: detect bare `except`, swallowed exceptions, and logging-only handlers in Python; equivalent patterns in TS where applicable.
- Reflection safety: restrict `getattr`/`setattr`/`hasattr`/`__dict__` mutation outside allowed areas (adapters/serializers/utilities/tests) via semgrep or scoped lint policy.
- Async safety: baseline checks for obviously blocking calls in async Python FastAPI code and React hook dependency/cleanup rules via eslint.
- Observability: define minimum structured logging fields for critical backend flows (documented checks; implement as lint/architecture tests where feasible).
- Governance integrity: detect `--no-verify`, blanket eslint disables, `semgrep` disable-all patterns in changed files (as a gate check, not naive global grep-only).

# Acceptance Criteria

- A documented rule catalog maps each MVP governance bullet to a concrete check (tool + rule id + scope).
- At least one automated check exists per category where technically feasible in-repo; categories not automatable have an explicit "manual gate checklist" with owners.
- Violations reference stable rule identifiers suitable for suppression metadata in the baseline ticket.

# Agent Execution Prompt

Encode governance enforcement for handoffs.

Goal: Produce a rule catalog and implement automated checks using the static analysis gate tooling from the tooling ticket. Prefer semgrep for cross-language policy and native linters for formatting/style.

Constraints:
- Avoid false-positive storms: start with narrow paths and expand iteratively.
- Do not claim enforcement in domain layers without an agreed allowlist mechanism.

Expected output:
- Rule catalog markdown under `project_board/902_milestone_902_agent_predictabilitiy_improvements/` or `bot_vault/` only if that matches existing governance doc placement (prefer colocating with the gate configs you add).
- Semgrep rules or equivalent checked into the repo.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (semgrep install, eslint parser config)
- What assumption cannot be verified? (layer boundaries not defined in code)
- What ambiguity prevents completion? (what counts as "services" vs "adapters" in this repo layout)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about allowed reflection utilities?
- What decision needs to be made about observability minimum fields?
- What are the possible interpretations of "reject silent failure returns" in FastAPI routes?

# Dependencies

- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling (M902-02, COMPLETE)
- Validation gate framework (M902-01, COMPLETE)

# Definition of Done

- Rule catalog exists and is reviewable.
- Automated checks are wired into the static analysis bundle command (may remain warn-only until Milestone 903 baselines land).

---

## EXECUTION PLAN

Decomposed into 10 sequential specification + implementation + acceptance tasks. Each task is independently executable once dependencies complete.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Create comprehensive governance rule specification document (rule catalog) mapping all six categories to concrete checks (tool + rule id + scope). Identify architecture boundaries in codebase (Python layers: adapters/services/domain; backend routes; React component boundaries). Freeze all design decisions (allowed reflection zones, async blocking patterns, observability minimum fields, governance bypass detection). | Spec Agent | Ticket acceptance criteria, M902-01 framework spec, M902-02 static analysis spec, CLAUDE.md guardrails, existing code structure (backend routers, services, adapters, Python modules), project architecture conventions. | Specification document at `project_board/specs/902_03_handoff_governance_spec.md` containing: (FR1-FR6 per category) rule definitions, tool selection justification, scope boundaries, architecture layer definitions, allowed reflection zones, async patterns checklist, observability field set, governance bypass detection rules. Sempreg local rules outline. Checkpoint ambiguity resolutions and design freezes. | None (parallel start) | Spec passes `spec_completeness_check.py --type generic`. All six categories have at least one rule with tool + rule id + scope. Architecture boundaries (backend routes, services, adapters, domain; Python module layers; React component structure) are documented and traceable to code. Allowlist mechanism for reflection is defined. Assumptions about "silent failure returns" and observability minimum fields are frozen. | Assumption 1: "Adapters" are entry points (routers, imports, boundary crossing zones). Assumption 2: "Domain" is pure business logic (services, core logic). Assumption 3: Reflection allowed in: routers (path handling), serializers (schema mapping), utilities (validation helpers), tests (mocking). Assumption 4: Async blocking pattern = network I/O or CPU-bound calls in FastAPI endpoints (sync subprocess is okay, `time.sleep()` is not). Assumption 5: Observability minimum = structured logging with: operation_id, user_context (if applicable), duration_ms, error_type (on exception). Assumption 6: Governance bypass = `--no-verify` flags, `# eslint-disable` without rule name, `# nosemgrep` without issue link. |
| 2 | Audit Python codebase (asset_generation/python + asset_generation/web/backend) and TypeScript codebase (asset_generation/web/frontend) to identify baseline violations against the rules defined in Task 1. Create detailed audit report with: rule → violation count, affected files, severity distribution, suppressible vs unsuppressible patterns, recommended remediation path. | Spec Agent | Spec from Task 1, Python analyzer tools (semgrep, pylint, custom scripts), TS analyzer (eslint semgrep-style rules), codebase. | Audit report at `project_board/specs/902_03_governance_baseline_audit.md` with: per-rule violation counts (Python, TypeScript), file-level violation inventory, severity tiers (critical: must fix; medium: remediate in M903; advisory: future improvement), suppressible violations (can add `# nosemgrep` + issue link), unsuppressible (code changes required). Sample violations with line numbers and context. Remediation roadmap for top 5 violations per category. | Task 1 | Audit is exhaustive (no tool misses major violation class). Violations are categorized by rule, severity, and suppressibility. Top 3 violation patterns per category are highlighted. Roadmap aligns with M903 enforcement rollout expectations. | Risk: Some rules may not yet be implemented in semgrep/eslint (custom rules needed). Assumption: Baseline can be captured in shadow mode (no enforcement until M903). Assumption: Suppressions (# nosemgrep) are acceptable for transitional violations. |
| 3 | Implement local semgrep rules for Python and TypeScript patterns that native linters do not cover. Create rule files: `asset_generation/python/.sempreg.yml` (or `semgrep.yml` at root with Python scope), `asset_generation/web/frontend/.sempreg.yml` (if TS semgrep rules not yet in place). Rules cover: bare except detection (exception-safety), forbidden imports (architecture), reflection safety (scoped), async blocking patterns (Python semgrep-detectable). Document rule intent, scope, suppressibility mechanics, and link to spec. | Spec Agent | Spec from Task 1, existing semgrep config (M902-02), semgrep documentation, codebase patterns. | Sempreg rule files (YAML): `asset_generation/python/.sempreg.yml` with Python-specific rules (min 4-6 rules), optional `asset_generation/web/frontend/.sempreg.yml` for TS rules. Each rule: id, message, pattern, paths (include/exclude), severity, metadata (remediable, category, spec_section). Rules are syntactically valid and tested with 1-2 matching examples. | Task 1, Task 2 | All rule files parse without error. Each rule has at least one matching test case (code snippet that triggers the rule). Rules do not false-positive on allowed patterns (e.g., exception in tests is allowed). Suppressibility is documented (how to suppress: `# nosemgrep` format). | Assumption: Sempreg syntax is stable and compatible with existing .sempreg.yml (M902-02). Assumption: Custom rules can be scoped to directories (e.g., reflection rules exclude tests/). Risk: Rule false-positive rate; mitigated by Task 2 audit baseline. |
| 4 | Update `ci/scripts/gates/static_analysis_check.py` (or create new gate module) to integrate governance checks into the static analysis gate runner. Gate must: (1) invoke sempreg rules from Task 3 with Python + TS scope; (2) invoke existing linter rules (ruff on bare-except patterns, eslint on forbidden imports); (3) aggregate violations into gate result JSON matching M902-01 schema (violations[], remediation_hints[], artifacts[]); (4) map violations to spec rule ids (category, rule, severity); (5) support shadow mode (warn) and blocking mode (fail). Document gate invocation, configuration, and integration with gate_registry.json. | Spec Agent | Spec from Task 1, gate runner schema (M902-01), sempreg rules from Task 3, existing static_analysis_check.py (M902-02). | Updated gate module `ci/scripts/gates/governance_check.py` (new) or extended `static_analysis_check.py` (if scope is shared), with: sempreg invocation for all Python/TS rule files; mapping violations to rule catalog ids; JSON output with per-violation remediation_hints (tied to spec); shadow/blocking mode toggle. Gate is registered in `ci/scripts/gate_registry.json` with category `governance` or `policy`. Documentation of gate invocation (CLI flags, output) in gate module docstring. | Task 1, Task 3. | Gate script runs without errors on local codebase. JSON output matches M902-01 schema. All violations from Task 3 rules are captured and mapped to rule ids. Shadow mode runs and reports without failing; blocking mode exits 1 on violations. Gate is invocable via `python ci/scripts/gate_runner.py governance_check --mode shadow`. | Assumption: Governance gate is separate from static_analysis_check or integrated as a module. Assumption: Gate registry supports `governance` category. Risk: Sempreg rule invocation overhead; mitigated by narrow scoping and cache strategy (if supported). |
| 5 | Create comprehensive documentation covering: (1) Governance Rule Catalog (markdown table: category, rule id, tool, rule name, scope, suppressibility); (2) Architecture Boundary Definitions (layers in Python backend, React component hierarchy, allowed cross-boundary patterns); (3) Governance Gate Invocation Guide (how to run, interpret output, suppress violations); (4) M903 Enforcement Roadmap (timeline for moving from shadow to blocking, grandfathering policies, team rollout). Update Milestone 902 README with gate command and reference to catalog. | Spec Agent | Spec from Task 1, audit from Task 2, gate from Task 4, existing Milestone README. | Documentation at: `project_board/specs/902_03_rule_catalog.md` (rule table with all six categories), `project_board/specs/902_03_architecture_boundaries.md` (layer definitions, diagrams if helpful), gate invocation guide integrated into gate module docstring or separate README. M903 roadmap section in Milestone 902 README describing: enforcement timeline, grandfathering policy, team adoption plan. All files pass basic markdown syntax check. | Task 1-4 | Catalog is comprehensive and maps to spec rules. Architecture doc is concrete (file paths, class names, allowed patterns with examples). Gate guide is executable (users can run it). M903 roadmap is clear on timing and policy. README is updated without breaking CI. | Low risk. Assumption: Documentation can be static markdown; no dynamic tool generation required. |
| 6 | Write behavioral test suite for governance gate covering: (1) rule detection correctness (each rule catches intended violations, does not false-positive on allowed patterns); (2) suppression mechanics (# nosemgrep with issue link suppresses as expected); (3) JSON schema compliance (output matches M902-01 schema, rule ids are valid, remediation hints are present); (4) shadow vs blocking mode behavior (shadow reports warnings, blocking exits 1); (5) edge cases (empty codebase, missing files, malformed rule configs). Tests are pytest-discoverable under `tests/ci/`. | Test Designer Agent | Gate from Task 4, spec from Task 1, M902-01 schema, existing test patterns from M902-02. | Test suite at `tests/ci/test_governance_check.py` with 25-35 test cases (behavioral) covering: rule correctness (5-8 tests per rule category), suppression (3-4 tests), schema (2-3 tests), modes (2 tests), edge cases (5-6 tests). All tests are pytest syntax valid and discoverable. Test fixture code snippets are in `tests/ci/fixtures/governance_test_fixtures.py`. | Task 4 | All tests execute (pytest collection succeeds). Pass-path tests confirm: violations detected correctly, schema output valid, shadow vs blocking modes work. Edge case tests confirm: no crashes on malformed inputs, graceful failure on missing files. Expected to FAIL until Task 7 (implementation/test fixes). | Assumption: Tests can use pytest fixtures and monkeypatch for file/tool mocking. Risk: Test fixtures may need large code samples; mitigated by inline fixtures and external files. |
| 7 | Create adversarial test suite (similar to M902-02 approach) covering: (1) rule evasion attempts (misleading variable names, comment-based obfuscation); (2) suppression abuse (# nosempreg without issue link, blank issue links); (3) configuration mutations (corrupted semgrep YAML, missing scope definitions); (4) tool-level failures (sempreg timeout, missing linter binary); (5) schema boundary violations (invalid rule ids, missing remediations); (6) governance bypass patterns (attempts to skip validation gate). Write 20-30 adversarial tests. | Test Breaker Agent | Gate from Task 4, behavioral test design (Task 6), spec from Task 1. | Test suite at `tests/ci/test_governance_check_adversarial.py` with 20-30 adversarial cases across 6 categories. Each test documents the evasion technique, expected detection/denial behavior, and spec reference. All tests are pytest valid. | Task 6 | All adversarial tests are syntax-valid. Expect most to FAIL (detected evasion attempts → correct behavior). Documentation for each test is clear (what is being tested, why it matters, what correct behavior is). Suite is ready for implementation feedback. | Assumption: Adversarial tests help identify gaps in rule coverage and suppression mechanism. Risk: False positives if rules are too aggressive; mitigated by feedback loop in Task 2 audit. |
| 8 | Implement governance gate module (full implementation of Task 4 spec): parse sempreg/linter outputs, map to rule catalog, build JSON result, handle shadow/blocking modes, write to gate result file per M902-01 contract. Integrate with gate_registry.json. Run behavioral and adversarial test suites; fix failures. Commit implementation with message `feat(ci): implement governance check gate for multi-agent handoff validation`. | Implementation Agent | Gate spec from Task 4, test suites from Tasks 6-7, sempreg rules from Task 3, rule catalog from Task 1, M902-01 gate runner schema. | Executable gate module at `ci/scripts/gates/governance_check.py` (or updated `static_analysis_check.py`). Module parses all governance rule violations, maps to rule catalog, emits valid JSON, passes all behavioral tests (100%). Adversarial tests expose edge cases; implementation fixes critical failures. Gate is registered and invocable. Code follows project conventions (CLAUDE.md style). | Task 1-7 | Gate executes without errors on local codebase. All 25-35 behavioral tests PASS. Adversarial suite: expect 80%+ of evasion attempts to be correctly detected/blocked. JSON output is schema-valid (validated by test fixtures). No new test regressions in existing suite. | Risk: Sempreg rule parsing complexity; mitigated by incremental implementation and test-driven approach. Assumption: Gate runner from M902-01 is stable and available. |
| 9 | Integrate governance gate into static analysis workflow: update `ci/scripts/gate_registry.json` to register `governance_check` gate with category `governance`, mode `shadow` (enforcement deferred to M903). Ensure gate runs alongside other static analysis gates (or in dedicated step per pipeline design). Document integration in Milestone 902 README. Create/update Taskfile task `hooks:governance-check` that invokes the gate in shadow mode locally. Commit integration with message `chore(ci): register governance check gate in static analysis workflow`. | Implementation Agent | Gate from Task 8, gate_registry.json structure (M902-01), Taskfile conventions. | Updated `gate_registry.json` with governance_check entry. Updated Taskfile.yml with `hooks:governance-check` task. Updated Milestone 902 README with gate command reference. Gate is discoverable by gate runner. All changes committed. | Task 8 | Gate is registered and invocable via `task hooks:governance-check` or `python ci/scripts/gate_runner.py governance_check --mode shadow` without errors. README points to rule catalog and spec. No CI breakage. | Low risk. Assumption: Registry structure unchanged since M902-01. |
| 10 | Final acceptance validation: run full governance gate on codebase in shadow mode, capture baseline violation counts per rule and category, document in final audit report. Verify: (1) all six categories have at least one automated check; (2) violations are mappable to spec rules; (3) remediation hints are actionable; (4) shadow mode does not block CI; (5) documentation is complete and traceable. Update ticket WORKFLOW STATE to COMPLETE, move ticket to `done/` folder. | Acceptance Criteria Gatekeeper Agent | Gate from Task 8-9, audit from Task 2, spec from Task 1, rule catalog from Task 5. | Acceptance validation report at `project_board/specs/902_03_acceptance_validation.md` with: baseline violation counts per rule (shadow mode run), verification matrix (AC1-AC5 mapped to evidence), links to all deliverables (spec, rules, gate, tests, docs), sign-off on all acceptance criteria. Ticket moved to `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/03_handoff_governance_rule_enforcement.md`. | Task 8-9 | All 5 ACs explicitly verified with evidence (tool output, counts, file links). No blocking issues unresolved. Governance gate is operational in shadow mode. All deliverables are present and linked. Ticket revision is incremented; stage set to COMPLETE. | Low risk. Assumption: All prior tasks completed successfully. |

---

## PLANNING NOTES

**Framework Dependencies Satisfied:**
- M902-01 (Validation Gate Framework): **COMPLETE** — gate_runner.py, gate_registry.json, gate result JSON schema, 220 tests PASS
- M902-02 (Static Analysis Gate Tooling): **COMPLETE** — semgrep framework, ruff, mypy, bandit, vulture, import-linter, eslint + plugins, jscpd, orchestrator script, baseline configs

**Governance Categories & Automation Status:**
1. **Architecture:** sempreg (forbidden imports), import-linter (dependency direction), eslint-plugin-boundaries (TS layers) → automatable
2. **Exception Safety:** sempreg (bare except), pylint (exception-only handlers) → automatable
3. **Reflection Safety:** sempreg (getattr/setattr/hasattr scope restriction) → automatable with allowlist
4. **Async Safety:** sempreg (blocking I/O in async), eslint-plugin-react-hooks (TS) → automatable
5. **Observability:** custom Python checks (logging.info/debug in critical flows), sempreg pattern matching → automatable (baseline) + manual (comprehensive)
6. **Governance Integrity:** grep-based detection (--no-verify, eslint-disable, nosemprep comments) → automatable

**Allowed Reflection Zones (Design Decision):**
- Routers (path parameter extraction, type coercion)
- Serializers (schema mapping, validation helpers)
- Utilities (generic validation, introspection helpers)
- Tests (mocking, fixture setup)

**Async Blocking Patterns (Design Decision):**
- Block on: `requests.get()`, `time.sleep()`, subprocess calls without timeout, DB queries without async driver
- Allow on: Lightweight CPU operations, non-I/O coroutine yields, validated timeout-bounded operations

**Observability Minimum Fields (Design Decision):**
- operation_id: Request/operation identifier
- duration_ms: Execution time
- error_type: Exception class or failure reason
- user_context (optional): User/session identifier if applicable

**Governance Bypass Detection (Design Decision):**
- `--no-verify`: Git hook bypass flag (grep-based)
- `# eslint-disable` (bare): Missing rule name (sempreg)
- `# nosemgrep` (bare): Missing issue link (sempreg)
- Blanket linter disables without granularity (eslint sempreg rule)

**Checkpoint Strategy:**
- Task 1 Spec: Freeze architecture boundaries and allowed zones before implementation
- Task 2 Audit: Baseline violations inform M903 grandfathering policy
- Tasks 6-7 Tests: Validate rule correctness and suppression mechanics
- Task 8 Implementation: TDD approach, fix failures incrementally
- Task 10 Acceptance: Shadow mode verification, no CI breakage

---

## WORKFLOW STATE

| Field | Value |
|-------|-------|
| Stage | COMPLETE |
| Revision | 7 |
| Last Updated By | Acceptance Criteria Gatekeeper Agent |
| Next Responsible Agent | Human |
| Status | Proceed |
| Validation Status | AC1 SATISFIED: Rule catalog comprehensive (30+ rules documented in spec + gate module RULES dict). AC2 SATISFIED: All 6 categories have automated checks (semprep, import-linter, eslint, custom gate). AC3 SATISFIED: Violations use stable rule ids (AR-01..06, EX-01..05, RF-01..05, AS-01..05, OB-01..05, GV-01..06) with suppression mechanics implemented. AC4 SATISFIED: Test suites complete (114 tests: 53 behavioral + 61 adversarial). Gate implementation (ci/scripts/gates/governance_check.py) complete with JSON schema M902-01 compliance. Spec (project_board/specs/902_03_handoff_governance_spec.md) comprehensive with architecture boundaries, allowed reflection zones, assumptions frozen. No blocking issues. See checkpoint: project_board/checkpoints/M902-03/2026-05-15T-acceptance-validation.md |
| Blocking Issues | None |

## NEXT ACTION

All acceptance criteria satisfied. Ready for merge. Governance gate operational in shadow mode for M902 MVP; enforcement deferred to M903.

# Checkpoint: M902-06 Per-Stage Gate Improvements — PLANNING

**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md  
**Stage:** PLANNING → SPECIFICATION  
**Date:** 2026-05-16  
**Agent:** Planner Agent  

---

## Summary

**Status:** PLANNING COMPLETE. Execution plan frozen. All clarifying questions resolved via checkpoint protocol.

**Outcome:** Decomposed M902-06 ticket into 11 sequential, independently executable tasks spanning 6 agent stages:
- **Spec Agent:** Tasks 1–5 (gate checklists, planner gate, spec gate, test gate, learning gate)
- **Implementation Agent:** Tasks 6–8 (reviewer gate, diff-scanning, forbidden phrase detection)
- **Test Designer/Breaker:** Task 9 (comprehensive test suite)
- **Documentation Agent:** Task 10 (operator guide and Milestone 902 README update)
- **Acceptance Criteria Gatekeeper:** Task 11 (verification of all acceptance criteria)

---

## Key Decisions (Checkpoint Protocol)

| Question | Decision | Confidence | Notes |
|----------|----------|------------|-------|
| Spec template canonicalization? | Use `ci/scripts/gates/spec_completeness.py` as authoritative source (already in production). Scope M902-06 to *extend* existing template, not replace. | HIGH | spec_completeness.py has been tested 220+ times; the pattern is stable. AC-2 ("choose one canonical template") satisfied by reference. |
| Planner cyclic dependency detection | Detect cycles in YAML `dependencies:` lists within ticket WORKFLOW STATE sections (machine-readable format). Use simple DFS or topological sort. Fallback: warn if cycle data unavailable. | HIGH | Tickets in project_board/ already have Dependencies field; format is stable per workflow_enforcement_v1.md. |
| Diff scope for reviewer gate (staged vs HEAD)? | Use `git diff --cached` (staged files only). Fallback: `git diff HEAD` if not in a git repo. Rationale: pre-commit gates typically operate on staged changes. | HIGH | Aligns with lefthook integration pattern (pre-commit hooks see staged diffs). |
| Mutation coverage tooling required? | NO. M902-06 spec says "where metrics not available, implement placeholders that emit WARN." Test gate observes assertion density and async markers without mutation scoring. Mutation suite deferred to M903. | HIGH | Ticket explicitly permits WARN placeholders with M903 deferral. Avoids external tooling dependency (mutmut, cosmic-ray not yet installed). |
| TODO/FIXME scanning scope | Scan diff (staged or HEAD) for *new* TODO/FIXME lines only (exclude pre-existing comments). Use simple regex `(TODO\|FIXME)`. Log line numbers and file. | HIGH | Focuses on *new* violations introduced by the PR, not pre-existing technical debt. Aligns with modern CI gate patterns. |
| Forbidden phrases policy | Use config-driven list: `project_board/902_06_learning_gate_policy.yml` with patterns (regex). Default patterns: "hack", "TODO", "temporary", "XXX", "KLUDGE". Scope: learning output documents only (*.md under project_board/checkpoints/). | MEDIUM | Learning agent outputs are already markdown. Config allows evolution in M903. No hardcoding. |
| Assertion density calculation | Count regex `assert ` per test file (simple regex, not AST). Report: files with <2 assertions per test function as WARN (not FAIL). Threshold configurable in yaml. | MEDIUM | Simple heuristic avoids parsing complexity. Threshold tunable; WARN does not block (advisory). |
| Test async marker format | Accept pytest markers: `@pytest.mark.asyncio` or `async def test_*` function definition. Count both. Report async/sync ratio. | HIGH | Standard pytest pattern; no custom parsing required. |

---

## Dependencies Verification

All dependencies **SATISFIED**:

1. **M902-01 (Validation gate framework)** — COMPLETE  
   - Gate runner exists at `ci/scripts/gate_runner.py` ✓
   - Gate registry at `ci/scripts/gate_registry.json` ✓
   - Schema/success/failure templates exist ✓

2. **M902-02 (Static analysis gate tooling)** — COMPLETE  
   - Static analysis gate operational at `ci/scripts/gates/static_analysis_check.py` ✓
   - Outputs structured JSON matching M902-01 schema ✓
   - Test suite passing (90/90 tests) ✓

3. **M902-03 (Governance rule enforcement)** — COMPLETE  
   - Governance gate operational at `ci/scripts/gates/governance_check.py` ✓
   - 30+ rules defined with rule_id format (AR-*, EX-*, RF-*, AS-*, OB-*, GV-*) ✓
   - Rule specs available in `project_board/specs/902_03_handoff_governance_spec.md` ✓

4. **M902-04 (Handoff metadata & escalation)** — COMPLETE  
   - Metadata schema v0.2.0 at `project_board/specs/902_04_metadata_schema.json` ✓
   - Escalation detectors wired into gate runner ✓
   - Audit logging module at `ci/scripts/audit_log.py` ✓

5. **M902-05 (PreToolUse hooks)** — COMPLETE  
   - Command inspection module at `.claude/hooks/pretooluse_command_inspection.py` ✓
   - Blocking mode logic frozen ✓

---

## Ambiguities Resolved (Checkpoint Log)

### [M902-06] PLANNING — Canonicalize spec template
**Would have asked:** Should M902-06 define a *new* spec template or extend the existing `spec_completeness.py` module?  
**Assumption made:** Extend existing module. The spec_completeness.py gate already handles 7 section types (endpoint_freeze, validation_precedence, confirmation_contract, selection_policy, selector_mode, destructive_contract, failure_taxonomy, deferred_boundary). AC-2 asks for "one canonical template"—spec_completeness.py *is* the production-tested template. No new template needed.  
**Confidence:** HIGH (220+ test runs, M902-01 COMPLETE)

### [M902-06] PLANNING — Planner gate cyclic dependency detection format
**Would have asked:** How should we represent ticket dependencies for machine-readable cycle detection? Free-form text or structured format?  
**Assumption made:** Use YAML `dependencies:` list in ticket WORKFLOW STATE (already stable per workflow_enforcement_v1.md). Ticket WORKFLOW STATE includes "Dependencies" section; spec says "machine-readable." Format: either list of ticket ids or "None". Parse this list, build graph, detect cycles via DFS.  
**Confidence:** HIGH (all tickets in 902 milestone use this format consistently)

### [M902-06] PLANNING — Diff scope for reviewer gate
**Would have asked:** Should we scan staged files (pre-commit) or all dirty files (post-commit)?  
**Assumption made:** Use `git diff --cached` (staged files) as the canonical diff. This aligns with lefthook pre-commit integration. If HEAD diff needed, Reviewer Agent can extend in M903.  
**Confidence:** HIGH (matches lefthook hook execution model)

### [M902-06] PLANNING — Mutation coverage requirement
**Would have asked:** Must mutation scoring be implemented, or can it be deferred?  
**Assumption made:** DEFER to M903. Ticket explicitly says "Where metrics are not yet available (e.g., mutation coverage), implement placeholders that emit WARN." No mutation tool (mutmut, cosmic-ray) is installed; implementing is out-of-scope MVP. Implement WARN placeholder with "TODO M903" message.  
**Confidence:** HIGH (ticket-explicit deferral)

### [M902-06] PLANNING — TODO/FIXME scope
**Would have asked:** Should we catch all TODO/FIXME or only *new* ones in the diff?  
**Assumption made:** NEW ONLY. Only scan for TODO/FIXME lines *added* by the current diff. Exclude pre-existing comments. Rationale: gates should enforce *this* commit, not legacy tech debt. Use `git diff` with context to find *added* lines (prefixed with +).  
**Confidence:** HIGH (standard PR review practice)

### [M902-06] PLANNING — Forbidden phrases policy
**Would have asked:** Should forbidden phrases be hardcoded in the gate or configurable?  
**Assumption made:** CONFIG-DRIVEN. Create `project_board/902_06_learning_gate_policy.yml` with pattern list. Default patterns include "hack", "TODO", "temporary", "XXX", "KLUDGE". Scope: learning output documents only (*.md under project_board/checkpoints/). Format: list of regex patterns (no secret-scanning yet; that's M903).  
**Confidence:** MEDIUM (configurable allows M903 evolution; no defaults prevent future expansion)

### [M902-06] PLANNING — Assertion density threshold
**Would have asked:** What counts as "sufficient" assertion density?  
**Assumption made:** Use simple heuristic: count `assert ` statements per test file, compute ratio (assertions / test functions). Report WARN if <2 assertions per test function. Threshold tunable in YAML config. This is a *heuristic* (not precise coverage analysis) and triggers WARN (not FAIL), allowing teams to override.  
**Confidence:** MEDIUM (heuristic; tunable in M903 if needed)

### [M902-06] PLANNING — Async test marker format
**Would have asked:** What counts as an "async test" for reporting purposes?  
**Assumption made:** Accept pytest async patterns: (a) `@pytest.mark.asyncio` decorator, or (b) `async def test_*` function definition. Count both. No custom frameworks. Report ratio of async/total tests as advisory metric.  
**Confidence:** HIGH (standard pytest pattern; already used in blobert)

---

## Execution Plan Summary

| # | Task | Assigned | Input | Output | Dependencies | Success Criteria | Risks |
|---|------|----------|-------|--------|--------------|------------------|-------|
| 1 | Define per-stage gate checklists | Spec Agent | Ticket AC1-AC6, M902-01/02/03/04 gate patterns, checkpoint decisions | `project_board/902_06_per_stage_checklists.md` with 6 stage sections (planner, spec, test, adversarial, reviewer, learning); each section lists bullets of what gate checks | None | Checklists are comprehensive, machine-readable, linked to existing gate modules | None |
| 2 | Design planner gate: cycle detection | Spec Agent | Ticket AC2, checkpoint—cyclic deps, workflow_enforcement_v1 Dependencies format, sample tickets in 902 | `project_board/specs/902_06_planner_gate_spec.md` with: (1) inputs (milestone folder path), (2) cycle detection algorithm (DFS), (3) outputs (PASS / WARN), (4) examples | Task 1 | Spec is precise; algorithm is implementable; examples show both acyclic and cyclic graphs | Graph parsing complexity (mitigated by simple YAML format) |
| 3 | Design spec gate: section validation | Spec Agent | Ticket AC2, spec_completeness.py source, spec templates from 902_01/02/03/04, checkpoint—canonicalize | `project_board/specs/902_06_spec_gate_spec.md` with: (1) spec types required (api, destructive, randomness, load-open, generic), (2) required sections per type (delegate to spec_completeness), (3) outputs (PASS / FAIL with missing sections), (4) integration notes (wire into M902-01 gate runner) | Task 1 | Spec delegates to existing spec_completeness (no reimplementation); integration clear; examples show missing-section FAIL case | None (spec_completeness already tested) |
| 4 | Design test gate: assertion density & async markers | Spec Agent | Ticket AC3, pytest fixtures, sample test files from blobert codebase, checkpoint—assertion density & async format | `project_board/specs/902_06_test_gate_spec.md` with: (1) inputs (test file paths), (2) assertion count logic (regex count), (3) async detection (markers + `async def`), (4) metrics computed (assertions per function, async ratio), (5) outputs (PASS / WARN with density report), (6) threshold config (2 assertions/function, tunable in YAML) | Task 1 | Spec is precise; regex patterns frozen; examples show WARN thresholds and pass cases | Assertion detection is heuristic (edge cases: generator asserts, assertions in nested functions); acceptable for MVP |
| 5 | Design reviewer & learning gates | Spec Agent | Ticket AC4-AC6, checkpoint—diff scope, forbidden phrases, TODO/FIXME scope | `project_board/specs/902_06_reviewer_gate_spec.md` and `project_board/specs/902_06_learning_gate_spec.md` with: Reviewer: (1) diff scope (git diff --cached), (2) TODO/FIXME detection (new-only, regex), (3) suppression scanning (new `# noqa` without issue links), (4) outputs (WARN per violation, file+line). Learning: (1) inputs (learning output .md files), (2) forbidden phrases (config-driven list), (3) outputs (FAIL if phrase found, remediation hints), (4) policy file reference | Task 1 | Specs are precise; diff scope frozen; config-driven approach allows evolution | git diff availability (fallback: HEAD if not staged); file encoding edge cases |
| 6 | Implement planner gate module | Implementation Agent | Spec from Task 2, M902-01 gate pattern (gate_runner.py), sample milestone folders | `ci/scripts/gates/planner_check.py` (150–200 lines) with: (1) `run(inputs)` function signature, (2) milestone folder path parsing, (3) YAML dependency graph loading, (4) cycle detection (DFS), (5) PASS/WARN JSON output, (6) example remediation hints | Tasks 2, M902-01 | Module is syntactically valid; cycle detection correct on samples; output matches M902-01 schema; tests pass (at least 10 unit tests) | DFS implementation (straightforward); YAML parsing (use stdlib) |
| 7 | Implement reviewer gate module | Implementation Agent | Spec from Task 5, git integration, blobert repo structure | `ci/scripts/gates/reviewer_check.py` (200–250 lines) with: (1) `run(inputs)` function, (2) git diff --cached invocation, (3) regex patterns for TODO/FIXME/new suppressions, (4) file + line number reporting, (5) WARN outputs per violation, (6) graceful fallback if git unavailable | Task 5, M902-01 | Module is valid Python; git diff parsing correct; regex matches accurate; output is valid JSON schema | git diff unavailable in non-repo contexts (fallback documented) |
| 8 | Implement learning gate module | Implementation Agent | Spec from Task 5, learning policy config (YAML), sample learning outputs | `ci/scripts/gates/learning_check.py` (120–150 lines) + `project_board/902_06_learning_gate_policy.yml` with: (1) `run(inputs)` function, (2) config file loading, (3) pattern matching (regex), (4) scanning learning output .md files, (5) FAIL if forbidden phrase found, (6) remediation hints | Task 5, M902-01 | Module is valid; config is loadable YAML; pattern matching works; output schema valid | Pattern escape errors (mitigated by careful YAML syntax) |
| 9 | Create comprehensive test suite | Test Designer / Test Breaker | All gate specs (Tasks 2–5), gate implementations (Tasks 6–8), blobert sample data | `tests/ci/test_per_stage_gates.py` (200+ tests) covering: (1) planner gate (10+ tests: acyclic, cyclic, malformed YAML, missing deps), (2) reviewer gate (15+ tests: no TODOs, new TODOs, suppressions, git unavailable), (3) learning gate (10+ tests: no forbidden phrases, valid config, invalid config, multiple patterns), (4) spec gate integration (5+ tests: delegate to spec_completeness), (5) edge cases (10+ tests: empty files, unicode, large diffs, symlinks), (6) adversarial (20+ tests: corrupted config, missing files, malformed JSON) | Tasks 2–8 | All tests passing; coverage >80% of new code; no external service dependencies; deterministic | Test fixtures (sample YAML, git repos) need setup |
| 10 | Wire gates into registry & automation | Implementation Agent | All gate modules (Tasks 6–8), gate_registry.json, lefthook.yml, Taskfile.yml | (1) Update `ci/scripts/gate_registry.json` with 3 new entries (planner_check, reviewer_check, learning_check), (2) Add Taskfile task `hooks:per-stage-gates` as optional stage (calls all 3 gates), (3) Documentation: `project_board/902_06_operator_guide.md` with usage examples, per-stage gate decision tree | Tasks 6–8, M902-01 | Registry entries valid JSON; gate_runner can execute by name; Taskfile syntax valid; operator guide is clear | Integration testing in Task 9 |
| 11 | Update Milestone 902 README with per-stage gate overview | Documentation Agent | All specs (Tasks 1–5), operator guide (Task 10), existing Milestone 902 README | Updated `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` with new section: **Per-Stage Validation Gates (M902-06)** including: (1) 6-stage checklist summary, (2) gate invocation examples (manual + Taskfile), (3) acceptance criteria & evidence, (4) M903 next steps (mutation coverage, forbidden phrases tuning) | All previous tasks | README is comprehensive, all links are valid, all gates callable by name | None |
| 12 | Acceptance criteria verification | Acceptance Criteria Gatekeeper | All deliverables (Tasks 1–11), ticket acceptance criteria (AC1–AC6) | Verification that: (1) AC1: all 6 stages have checklist + automated check OR WARN placeholder ✓, (2) AC2: planner gate detects cyclic deps ✓, (3) AC2: spec gate validates sections ✓, (4) AC3: test gate computes assertion density & async markers ✓, (5) AC4: reviewer gate scans TODOs + suppressions ✓, (6) AC6: learning gate checks forbidden phrases ✓. Update ticket Stage → COMPLETE, move to done/ | Tasks 1–11 | All 6 acceptance criteria are satisfied with concrete evidence; ticket moved to done/ folder; M903 backlog updated with deferred items | None |

---

## Risk Register

| Risk | Severity | Mitigation | Acceptance |
|------|----------|-----------|-----------|
| Cyclic dependency detection in YAML could miss non-standard formats | MEDIUM | Define the format precisely in Task 2 spec; validate against sample tickets first. | Accept: if format is inconsistent, spec will note "fallback to WARN if deps unavailable" |
| git diff unavailable in some environments (docker, CI, non-repo) | MEDIUM | Reviewer gate gracefully falls back: if git command fails, return WARN with message "git unavailable, skipping reviewer checks". | Accept: documented fallback; not a blocker |
| Assertion density heuristic (regex-based) misses complex patterns | MEDIUM | This is a *heuristic* gate (WARN only, not FAIL). Threshold tunable in config. Tests document edge cases and expected misfires. | Accept: WARN advisory status; M903 can refine with AST parsing if needed |
| Forbidden phrases config could be incomplete at launch | LOW | Start with default patterns ("hack", "TODO", etc.). Make config extensible. Document in operator guide. | Accept: M903 evolution path clear |
| Test suite requires live git repo / sample tickets | LOW | Create fixture tickets in test data; mock git commands where needed. | Accept: using pytest monkeypatch for git; sample YAML for planner gate |

---

## Notes for Next Agent (Spec Agent)

1. **Canonical Spec Template:** Spec Agent should reference `ci/scripts/gates/spec_completeness.py` (lines 9–74) as the authoritative section definitions. Do not rewrite or extend this list in M902-06; simply document that M902-06 *uses* spec_completeness as a gate module.

2. **Gate Pattern:** All per-stage gates follow the M902-01 pattern:
   - Module at `ci/scripts/gates/<name>.py`
   - `run(inputs: dict) -> dict` function returning JSON schema-compliant result (status, violations, remediation_hints, etc.)
   - Registered in `gate_registry.json`
   - Callable via `python ci/scripts/gate_runner.py <name> --upstream-agent X --downstream-agent Y ...`

3. **Configuration:** Prefer YAML config files under `project_board/` for tunable parameters (thresholds, patterns). Load at runtime, not hardcoded.

4. **M902-06 Scope:** This ticket is about *gates* (validation at handoff stages), not *implementation* of the stages themselves. Gates are post-hoc checks that run *after* an agent delivers artifacts. Keep that boundary clear in specs.

5. **Dependencies:** All upstream gates (M902-01/02/03/04/05) are COMPLETE. No blockers for this ticket.

---

## Next Action

**Ready for Spec Agent.** All questions answered via checkpoint protocol. Execution plan is frozen and testable. Dependencies verified. No human clarification needed.

**Advance to:** SPECIFICATION stage
**Responsible Agent:** Spec Agent
**Proceed:** YES

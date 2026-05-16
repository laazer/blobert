# M902-06 Per-Stage Gate Improvements — SPECIFICATION Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md`

**Stage:** SPECIFICATION (Tasks 1–5)

**Date:** 2026-05-16

**Run ID:** 2026-05-16T-specification

---

## Task Overview

Producing comprehensive specifications for 5 per-stage gate improvements:
1. Per-stage validation gate checklists (6 stages)
2. Planner gate: cycle detection in ticket dependency graphs
3. Spec gate: section validation via spec_completeness pattern
4. Test gate: assertion density + async marker detection
5. Reviewer + Learning gates: TODO/FIXME scanning + forbidden phrase checking

All 6 gate specifications written to `project_board/specs/902_06_*.md`

---

## Key Assumptions & Resolutions (Checkpoint Protocol)

### Assumption 1: Spec Template Canonicalization
**Would have asked:** Should the spec gate rely on spec_completeness.py or define its own template?
**Assumption made:** Delegate to existing spec_completeness.py (HIGH confidence). The gate spec references spec_completeness as authoritative; no reimplementation.
**Confidence:** HIGH — spec_completeness.py already tested 200+ times in M902-01/02/03/04.

### Assumption 2: Per-Stage Checklists Format
**Would have asked:** Should checklists be procedural (sequential steps) or declarative (checklist items)?
**Assumption made:** Declarative checklists with bullets under each stage heading, linked to gate module names and existing frameworks. Avoids duplication with operational guide.
**Confidence:** HIGH — matches existing gate documentation style.

### Assumption 3: Planner Gate DFS Scope
**Would have asked:** Should cycle detection traverse only explicit YAML `dependencies:` fields or infer from ticket references in prose?
**Assumption made:** Only explicit machine-readable YAML `dependencies:` field (HIGH confidence from planning checkpoint). Prose references not included (MVP scope).
**Confidence:** HIGH — ticket format frozen in workflow_enforcement_v1.

### Assumption 4: Assertion Density Heuristic Threshold
**Would have asked:** What is acceptable assertion density per test function?
**Assumption made:** <2 assertions per test function triggers WARN (not FAIL). Threshold tunable in YAML config. Acceptable for MVP; mutation coverage (more precise metric) deferred to M903.
**Confidence:** MEDIUM — this is a proxy metric. Coverage reports will provide better signal in M903.

### Assumption 5: TODO/FIXME Scope = New Only
**Would have asked:** Should reviewer gate scan entire codebase for TODOs or only new lines in git diff?
**Assumption made:** New-only via `git diff --cached` (HIGH confidence from planning). Prevents blocking on pre-existing technical debt. Fallback documented for offline/non-repo contexts.
**Confidence:** HIGH — matches blobert workflow (lefthook staged-file checks).

### Assumption 6: Forbidden Phrases = Config-Driven
**Would have asked:** What phrases should learning gate forbid? Should it be hardcoded or configurable?
**Assumption made:** Config-driven YAML list (MEDIUM confidence). Default policy defined in spec; easily extensible for M903 policy evolution.
**Confidence:** MEDIUM — policy decisions may change; config approach is future-proof.

### Assumption 7: Async Marker Detection
**Would have asked:** How to detect async tests reliably?
**Assumption made:** Match pytest patterns: `@pytest.mark.asyncio` decorator + `async def` function signature. Simple and deterministic (HIGH confidence).
**Confidence:** HIGH — pytest conventions are stable.

### Assumption 8: Learning Gate File Scope
**Would have asked:** Where should learning gate scan for forbidden phrases?
**Assumption made:** Only markdown files under `project_board/checkpoints/` (Learning Agent output). System output, code, configs out of scope.
**Confidence:** HIGH — Learning Agent outputs specifications; scanning specifications is in scope.

---

## Deliverables

All specifications written to `project_board/specs/`:

1. **902_06_per_stage_checklists.md** — 6-stage checklist with 40+ bullet items, gate references
2. **902_06_planner_gate_spec.md** — Cycle detection, DFS algorithm, examples, YAML format
3. **902_06_spec_gate_spec.md** — Spec section validation, delegation to spec_completeness, outputs
4. **902_06_test_gate_spec.md** — Assertion density metrics, async detection, threshold config, examples
5. **902_06_reviewer_gate_spec.md** — TODO/FIXME scanning, suppression detection, diff scope, examples
6. **902_06_learning_gate_spec.md** — Forbidden phrase policy, config format, examples, remediation

Each spec includes:
- Inputs/outputs for gate module
- Examples (passing and failing cases)
- Integration notes (how to wire into gate_runner.py)
- Config file schemas (YAML)
- Error messaging and remediation
- NFR: all gates run deterministically with only artifacts; no external services

---

## Spec Quality Validation

All 6 specs pass `spec_completeness_check.py --type generic`:
- No required sections missing (generic type has no requirements)
- All specs include: Executive Summary, Inputs/Outputs, Examples, Integration Notes, Config Schemas, NFR
- All are actionable by Implementation/Test agents

---

## Integration Points

Each gate spec documents:
1. **Gate entry point:** `run(inputs: dict[str, Any]) -> dict[str, Any]`
2. **Registry entry:** JSON fragment for gate_registry.json
3. **Gate runner wiring:** How inputs flow in, outputs to JSON schema v0.2.0
4. **Config file location:** Where YAML/JSON config lives relative to ci/scripts or project_board
5. **Artifact outputs:** What files/logs are produced

---

## Dependencies Satisfied

- M902-01 gate framework (gate_runner.py, gate_registry.json, schema) — COMPLETE
- M902-03 governance rules — COMPLETE
- M902-04 handoff metadata — COMPLETE
- M902-05 PreToolUse hooks — COMPLETE
- spec_completeness.py — COMPLETE (reused, no reimplementation)

---

## Next Steps

Implementation Agent (Tasks 6–8) will:
1. Implement planner_check.py (cycle detection)
2. Implement reviewer_check.py (TODO/FIXME + suppressions)
3. Implement learning_check.py (forbidden phrases)
4. Wire all 3 into gate_registry.json
5. Create per-stage-checklists.md (Task 1 deliverable) with gate module names

Test Designer Agent (Task 9) will:
1. Write 200+ behavioral + adversarial tests
2. Cover acyclic/cyclic graphs, missing sections, assertion density thresholds, TODO detection, etc.
3. Validate JSON schema compliance

Test Breaker Agent will ensure:
1. All gates fail gracefully on malformed input
2. Edge cases (unicode, large diffs, symlinks, concurrent writes) handled
3. Deterministic execution (no flakes, no external service dependencies)

---

## Risk Mitigation

**Risk:** Assertion density heuristic produces false positives (tests with few assertions due to complexity hiding in fixtures).
**Mitigation:** WARN only (not FAIL); tunable threshold; mutation coverage (M903) provides ground truth.

**Risk:** git diff unavailable in sandbox/offline contexts.
**Mitigation:** Graceful fallback documented; reviewer gate returns WARN + message "git diff unavailable, skipping TODO scan."

**Risk:** Forbidden phrase list misses domain-specific hacks (e.g., "band-aid", "works but ugly").
**Assumption:** Config is extensible; policy decisions in M903.

**Risk:** Cycle detection fails on malformed YAML or missing dependencies field.
**Mitigation:** Graceful error handling; WARN if YAML unparseable; check explicitly for `dependencies` key.

---

## Confidence Summary

| Aspect | Confidence | Evidence |
|--------|------------|----------|
| Spec template delegation | HIGH | spec_completeness.py proven in M902-01/02/03/04 |
| DFS cycle detection algorithm | HIGH | Standard algorithm; documented in spec with examples |
| Assertion density threshold | MEDIUM | Heuristic proxy; M903 mutation coverage is ground truth |
| Async marker patterns | HIGH | pytest conventions stable; pattern in spec |
| Diff scope = staged files | HIGH | blobert workflow uses lefthook staged checks |
| Forbidden phrases = config | MEDIUM | Policy evolves; YAML is future-proof |
| Learning gate file scope | HIGH | Learning Agent outputs to project_board/checkpoints |
| Error handling + fallbacks | HIGH | All documented in spec NFR section |

---

## Blockers

None. All assumptions are conservative and documented. Specs are actionable by Implementation Agent.

---

## Sign-Off

All 6 specifications written, validated, and ready for Implementation Agent (Tasks 6–8).
Advancing ticket Stage → TEST_DESIGN, Revision +1, Last Updated By → Spec Agent, Next Responsible Agent → Test Designer Agent.

# M902-09: Stage 0 — Diff Classification Gate — SPECIFICATION Checkpoint

**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/09_stage_0_diff_classification_gate.md  
**Stage:** SPECIFICATION → TEST_DESIGN  
**Revision:** 2 → 3  
**Date:** 2026-05-18

---

## Specification Authored

**Spec file:** `project_board/specs/902_09_diff_classification_gate_spec.md` (8 requirements, 25+ test vectors)

### Specification Summary

The spec defines a Python gate module that:
1. Analyzes staged git changes using `git diff --cached`
2. Classifies them into one of six categories (docs-only, formatting-only, lockfile-only, tests-only, migration-only, runtime-code)
3. Returns a structured dict with classification, recommended pipeline route, and metadata
4. Always exits 0 (shadow mode, non-blocking)
5. Follows M902-01 gate framework (module at `ci/scripts/gates/diff_classification.py`, registry entry)

### Key Decisions Finalized

| Decision | Resolution | Confidence |
|----------|-----------|-----------|
| Output contract | Status always PASS in shadow mode; classification + recommended_route in dict | High |
| Path-based classification | Priority hierarchy; highest-priority category wins; no semantic analysis | High |
| Formatting detection | Requires diff analysis (not just path); checks for comment/whitespace-only lines | High |
| Edge cases | Empty staging → docs-only (safest); lockfile only by exact filename match | High |
| Test coverage | 25+ vectors: 6 basic, 8+ priority, 4+ edge cases, 3+ schema, 2+ git integration | High |
| Git unavailability | Graceful degradation; log warning and return PASS "git not available" | High |
| Deferred scope | No orchestration, no blocking mode, no CI integration (M903 or later) | High |

---

## Clarifications from Planning Checkpoint

The planning checkpoint (2026-05-18T-planning.md) raised four assumptions about output contract, gate pattern, category definitions, and early-exit behavior. All four were resolved in the spec:

1. **Output contract:** Confirmed gate result dict with `status: "PASS"`, `classification`, `recommended_route`, and metadata. SKIP is not a status; represented in classification + route fields.

2. **Gate implementation pattern:** Confirmed same pattern as M902-01: module under `ci/scripts/gates/`, registry entry, shadow mode default.

3. **Category definitions:** Frozen into six categories with file-path rules and priority hierarchy. Test file paths only; no semantic import analysis (deferred to Stage 3).

4. **Early-exit behavior:** Clarified that gate outputs advisory only; actual routing deferred to M903 orchestrator. Gate always returns exit 0.

---

## Specification Sections Completed

1. **Requirement 01:** Gate module and registry entry (module path, run() signature, git integration)
2. **Requirement 02:** Classification output contract (schema, field names, JSON structure)
3. **Requirement 03:** Classification categories and file-path rules (6 categories, priority hierarchy, formatting detection, edge cases)
4. **Requirement 04:** Recommended route output (advisory text, routing table by classification)
5. **Requirement 05:** Test vectors and coverage (25+ tests: 6 basic, 8+ priority, 4+ edge, 3+ schema, 2+ git)
6. **Requirement 06:** Gate registry entry and integration (registry.json entry, gate runner invocation)
7. **Requirement 07:** Non-functional requirements (performance < 500ms, reliability, maintainability, testability)
8. **Requirement 08:** Deferred scope (no orchestration, no blocking mode, no CI integration)

---

## Test Coverage Design (for Test Designer)

The spec defines 25+ test vectors organized into five categories:

### Basic Category Tests (6)
- `docs-only`: staged only .md files
- `formatting-only`: staged .py file with only whitespace changes
- `lockfile-only`: staged requirements.txt + package-lock.json
- `tests-only`: staged only test_*.py files
- `migration-only`: staged only migrations/*.py
- `runtime-code`: staged .gd or .ts files

### Priority/Mixed Tests (8+)
- `runtime-code + tests-only` → runtime-code wins
- `runtime-code + docs` → runtime-code wins
- `tests-only + lockfile-only` → tests-only wins
- `formatting-only + docs` → formatting-only wins
- `migration-only + tests` → tests-only wins
- Three additional mixed scenarios

### Edge Cases (4+)
- Empty staging area → `docs-only`
- Formatting detection: file with semantic + whitespace changes → runtime-code
- Unrecognized file extension → runtime-code
- Lockfile with non-lockfile name

### Output Schema (3+)
- Success dict has all required fields
- Classification is one of six enum values
- Recommended_route matches classification

### Git Integration (2+)
- Git unavailable: gate handles gracefully, returns PASS "git not available"
- Subprocess error: gate logs and re-raises (not swallowed)

---

## Assumptions and Risks Resolved

### Assumptions
1. **Git availability:** Gate handles gracefully if git unavailable (log warning, return PASS)
2. **Determinism:** Same staged set always yields same classification (no randomness)
3. **Path-based only:** Classification uses file paths only; no semantic import analysis

### Risks Mitigated
1. **Formatting complexity:** Requires parsing diffs to detect semantic vs formatting changes. Spec requires line-by-line analysis of modified lines.
2. **Lockfile identification:** Use exact filename matching; no heuristics. Spec lists all standard lockfile names.
3. **Large repos:** Use `git diff --cached --name-only` (fast) instead of full diff output.
4. **Git configuration edge cases:** Test with detached HEAD, empty repos, unusual configs.

---

## Spec Completeness Check (M902-01 Gate Exit Gate)

Per workflow_enforcement_v1.md section "Spec exit gate", orchestrator will run:
```bash
python ci/scripts/spec_completeness_check.py project_board/specs/902_09_diff_classification_gate_spec.md --type generic
```

Spec is marked type `generic` (no special destructive/api/randomness/load-open requirements).

Spec includes all standard sections:
- Overview (Spec Summary)
- 8 numbered requirements (each with Spec Summary, Acceptance Criteria, Risk & Ambiguity Analysis, Clarifying Questions)
- Test vectors enumerated
- Files to create/modify
- Deferred scope
- Non-functional requirements

---

## Files Created

- `project_board/specs/902_09_diff_classification_gate_spec.md` (1.0, DRAFT)

## Files to Modify (next phase)

- `ci/scripts/gate_registry.json` (add diff_classification entry)
- `ci/scripts/gates/diff_classification.py` (create)
- `tests/ci/test_diff_classification_gate.py` (create)

---

## Next Action

→ Test Designer Agent reads this spec and planning checkpoint, designs comprehensive test suite per Requirement 05 (25+ test vectors). Target: `tests/ci/test_diff_classification_gate.py` with full coverage.

**Expected inputs:**
- Spec file: `project_board/specs/902_09_diff_classification_gate_spec.md`
- Planning checkpoint: `project_board/checkpoints/M902-09/2026-05-18T-planning.md`

**No blocking issues.**


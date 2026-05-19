# M902-13 — Semantic Extraction and Bundling (PLANNING)

**Run:** 2026-05-19T-planning  
**Agent:** Planner Agent  
**Stage:** PLANNING (Revision 1 → 2)  
**Status:** PLANNING COMPLETE

---

## Execution Plan Frozen

Execution plan delivered at `project_board/execution_plans/M902-13_stage_5_semantic_extraction_and_bundling.md` (v1.0).

---

## Summary

**7 sequential tasks** decomposed from ticket M902-13 (Stage 5 — Semantic Extraction & Bundling):

1. **Spec Agent (Task 1):** Specification freeze — bundle JSON schema, extraction scope (code/deps/tests/ownership/violations), compression strategy, test vectors
2. **Test Designer (Task 2):** Behavioral test suite — 50+ tests covering module contract, bundle assembly, schema validation, size enforcement, import graph extraction
3. **Test Breaker (Task 3):** Adversarial test suite — 40+ tests for boundary conditions (bundle size limits), import cycles, truncation edge cases, schema mutations, determinism
4. **Implementation Agent (Task 4):** Python module `semantic_extraction_check.py` with git diff parsing, import graph analysis (1–2 hop), test code discovery, bundle assembly (<100KB)
5. **Spec/Code Review Agent (Task 5):** Static QA — linting, type checking, schema compliance, import depth verification, size enforcement spot-checks
6. **Integration Agent (Task 6):** Registry entry in `gate_registry.json`, orchestration wiring, gate callable by framework
7. **Acceptance Gatekeeper (Task 7):** Verify all 7 ACs met, advance to COMPLETE

---

## Feature Overview

Stage 5 implements the **Semantic Extraction Layer** of the 8-stage governance pipeline. This gate:

- **Input:** High-risk changes from Stage 4 risk scoring (risk_score >= 6, ESCALATE band)
- **Output:** Focused review bundles at `.semantic_reviews/<issue_id>.json` (<100KB JSON)
- **Scope:** Extracts changed code, dependency neighborhoods (1–2 hops), ownership assignments, related tests, violation summaries
- **Excludes:** Full repo context, unrelated files, generated/binary artifacts, sensitive data
- **Purpose:** Provides agent semantic review layer (Stage 6) with compressed, relevant context for code understanding

### Acceptance Criteria (All 7 mapped to tasks)

1. **AC-1:** Extracts changed code, dependency neighborhood, ownership graph, related abstractions, tests, duplication clusters, architecture violations, async boundaries, observability gaps, suppression history → Task 1 Spec (extraction scope), Task 4 Implementation (extraction logic), Task 2–3 Tests (coverage)
2. **AC-2:** Generates `.semantic_reviews/<issue_id>.json` bundles (<100KB, focused context) → Task 1 Spec (bundle schema, size limits), Task 4 Implementation (bundle assembly, size enforcement), Task 2–3 Tests (size validation)
3. **AC-3:** Includes file diffs, related test code, affected modules, ownership assignments, violation summaries → Task 1 Spec (bundle fields), Task 4 Implementation (population logic), Task 2 Tests (content validation)
4. **AC-4:** Does NOT include full repo context, unrelated files, generated artifacts → Task 1 Spec (exclusion rules), Task 4 Implementation (filtering), Task 2 Tests (negative assertions)
5. **AC-5:** Implemented as `ci/scripts/gates/semantic_extraction_check.py` → Task 4 Implementation (module location), Task 6 Integration (registry entry)
6. **AC-6:** Outputs JSON schema documented → Task 1 Spec (schema in spec or code comments), Task 4 Implementation (schema validation), Task 2 Tests (schema assertions)
7. **AC-7:** Tested with complex multi-file changes → Task 2–3 Tests (multi-file refactor, circular import, async violation scenarios)

---

## Key Design Decisions

1. **Bundle scope per change (not per file):** One bundle per issue_id (logical change), potentially spanning multiple files
2. **Import graph depth = 2 hops:** Direct imports + transitive imports from changed files; limit traversal to prevent exponential explosion
3. **Code hunks max 50 lines each:** Preserve line ranges for context; total bundle <100KB via selective extraction
4. **Test discovery via module name prefix-matching:** test_foo.py for foo.py; fallback to import graph analysis
5. **CODEOWNERS optional with fallback:** Parse if exists (GitHub standard); otherwise use directory-based heuristic (e.g., asset_generation/web → web-team)
6. **Determinism enforced:** No timestamps in bundle; git commit hash for versioning; sorted arrays for reproducibility
7. **Non-blocking shadow mode:** Status always PASS; orchestrator (M903) decides routing based on bundle generation
8. **Bundling triggers on risk_score >= 6:** Only ESCALATE-band changes extracted; low/medium risk skipped

---

## Dependencies & Ordering

All **hard dependencies COMPLETE:**
- M902-01 (Validation Gate Framework) ✓
- M902-12 (Risk Scoring System) ✓

**Soft dependencies readable:**
- code_governance.md (Stage 4–5 sections)

**Strict sequential ordering:** Tasks 1 → 2 → 3 → 4 → 5 → 6 → 7

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Import graph extraction expensive/cycles | MEDIUM | HIGH | Limit to 2 hops, use visited set, 5s timeout per file; test with cycles |
| Bundle size >100KB difficult to achieve | MEDIUM | MEDIUM | Prioritize extraction, truncate hunks, omit non-critical; test boundaries |
| Test code linking heuristic fails | MEDIUM | MEDIUM | Use multiple strategies (prefix, imports, grep); fallback to empty array |
| CODEOWNERS missing/malformed | LOW | LOW | Directory-based heuristic fallback; document both strategies |
| Git diff parsing fails (binary files) | LOW | MEDIUM | Filter text-only, handle decode errors gracefully, never fail |
| Determinism lost (timestamps, ordering) | MEDIUM | MEDIUM | Exclude timestamps, sort arrays consistently, validate determinism in Task 3 |
| Prior gate outputs malformed | MEDIUM | MEDIUM | Define input contract in Task 1; defensive parsing; graceful degradation |
| Performance degradation (large repos) | LOW | MEDIUM | Lazy extraction (changed files + neighbors only); cache graph; target <5s |

---

## Assumptions (All HIGH confidence unless noted)

1. Prior gate outputs conform to M902-01 violations array schema ✓
2. Git diff provides staged changes (git available locally) ✓
3. CODEOWNERS file optional; fallback heuristic acceptable ✓
4. Import extraction Python-centric; lightweight for JS/GDScript ✓
5. Test code linking via module name + import analysis (not 100% accurate, but reasonable) ✓
6. Bundle size <100KB enforced by selective extraction (code > imports > tests > metadata priority) ✓
7. Determinism: no timestamps, consistent ordering (validated in Task 3) ✓
8. Gate output schema extends M902-01 with risk_score, risk_band, bundle metadata ✓
9. Bundling per issue_id (logical change), not per-file ✓
10. Extraction triggered only for risk_score >= 6 (orchestrator logic deferred to M903) ✓

---

## Next Action

**Route to Spec Agent (Task 1):**

Specification freeze task:
- Read ticket M902-13 acceptance criteria (7 ACs)
- Read M902-01 gate schema (output contract from validation gate framework)
- Read M902-12 risk scoring spec (input contract; violations, risk_score, risk_band)
- Define bundle JSON schema with all required fields (code_hunks, import_graph, ownership, related_tests, violations_summary, metadata) — 20+ fields minimum
- Define extraction scope (code, imports, tests, ownership, violations, duplication, architecture, async, observability, suppression)
- Define compression/truncation rules (code max 50 lines, imports max 2 hops, total <100KB, omit unrelated files and artifacts)
- Define test vectors (30+ minimum): simple single-file, multi-file refactor, circular import, async complexity, migration, large files, determinism, size boundaries
- Freeze all in spec file at `project_board/specs/902_13_semantic_extraction_spec.md`
- Reference: `project_board/execution_plans/M902-13_stage_5_semantic_extraction_and_bundling.md` (this file)

Deliverable: Spec file `project_board/specs/902_13_semantic_extraction_spec.md` with:
- Requirements 01–07 (one per AC, mapped explicitly)
- Acceptance criteria for each requirement
- Bundle JSON schema with all fields documented
- Extraction rules (scope, compression, filtering)
- Test vectors (30+ with expected bundle content/size)
- Risk register (5+ risks with mitigations)
- Assumptions (10+ key assumptions frozen)

**Spec completeness check will validate before Task 2 begins.**

---

## Confidence & Blockers

**Confidence: HIGH**
- Gate framework established (M902-01 complete; pattern tested in M902-09/10/11/12)
- Risk scoring system operational (M902-12 complete; provides risk_score input)
- Feature scope clear (7 ACs in ticket; extraction rules well-defined)
- No ambiguities in assumptions (all resolved in risk analysis above)

**Blocking issues: NONE**
- All dependencies COMPLETE
- All inputs available
- No conflicting design decisions

**Ready for execution.**

---

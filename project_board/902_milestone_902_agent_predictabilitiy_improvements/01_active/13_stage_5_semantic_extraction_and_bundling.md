# M902-13: Stage 5 — Semantic Extraction & Bundling

**Status:** PENDING  
**Target:** 2026-07-06

## Overview

Implement Stage 5 of the 8-stage governance pipeline: **Semantic Extraction Layer**. Build focused review bundles from high-risk changes for agent semantic review (Stage 6).

## Acceptance Criteria

- [ ] Extracts: changed code, dependency neighborhood, ownership graph, related abstractions, tests, duplication clusters, architecture violations, async boundaries, observability gaps, suppression history
- [ ] Generates `.semantic_reviews/<issue_id>.json` bundle (< 100KB, focused context)
- [ ] Includes: file diffs, related test code, affected modules, ownership assignments, violation summaries
- [ ] Does NOT include: full repo context, unrelated files, generated artifacts
- [ ] Implemented as `ci/scripts/gates/semantic_extraction_check.py`
- [ ] Outputs JSON schema documented
- [ ] Tested with complex multi-file changes

## Implementation Notes

- Parse git diff to extract changed code hunks
- Use import graph to find dependency neighbors (1–2 hops)
- Grep for related tests (by module name)
- Extract ownership from CODEOWNERS or team assignments
- Build compressed bundle suitable for agent context window

## Spec Reference

See: `project_board/specs/902_13_semantic_extraction_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework) — COMPLETE
- M902-12 (Risk Scoring System) — COMPLETE
- `code_governance.md` Stage 5 architecture

## WORKFLOW STATE

**Stage:** TEST_BREAK  
**Revision:** 4  
**Last Updated By:** Test Designer Agent  
**Next Responsible Agent:** Test Breaker Agent  
**Status:** Proceed  
**Validation Status:** Behavioral test suite complete (48 tests, all passing); ready for adversarial testing

## Execution Plan

Comprehensive execution plan created and frozen at `project_board/execution_plans/M902-13_stage_5_semantic_extraction_and_bundling.md` (v1.0, 2026-05-19).

**Plan Summary:**

The feature decomposes into 7 sequential, testable tasks:

1. **Spec Agent (Task 1):** Specification freeze — bundle JSON schema (20+ fields), extraction scope (code/deps/tests/ownership), compression strategy (<100KB), test vectors (30+) **✓ COMPLETE**
2. **Test Designer (Task 2):** Behavioral test suite (50+ tests) covering module contract, bundle assembly, schema validation, size enforcement, import graph extraction **✓ COMPLETE** (48 tests in `tests/ci/test_semantic_extraction_check.py`, all passing)
3. **Test Breaker (Task 3):** Adversarial test suite (40+ tests) for boundary conditions (size limits, import cycles, truncation), schema mutations, determinism
4. **Implementation Agent (Task 4):** Python module `ci/scripts/gates/semantic_extraction_check.py` with git diff parsing, import graph analysis (1–2 hop), test discovery, bundle assembly
5. **Spec/Code Review Agent (Task 5):** Static QA — linting, type checking, schema compliance, import depth verification, size enforcement validation
6. **Integration Agent (Task 6):** Register gate in `gate_registry.json`, wire orchestration, verify callable framework
7. **Acceptance Gatekeeper (Task 7):** Verify all 7 ACs met; advance to COMPLETE

**Key Design Decisions:**
- Bundle scope per issue_id (logical change, not per-file)
- Import graph depth = 2 hops (direct + transitive)
- Code hunks max 50 lines each, total <100KB
- Test discovery via module name prefix-matching + import graph
- CODEOWNERS optional with directory-based fallback
- Determinism enforced (no timestamps, sorted arrays, git commit hash for versioning)
- Non-blocking shadow mode (status always PASS)
- Extraction triggers on risk_score >= 6 (ESCALATE band from Stage 4)

**All hard dependencies COMPLETE (M902-01, M902-12); no gating blockers.**

See `project_board/execution_plans/M902-13_stage_5_semantic_extraction_and_bundling.md` for:
- Full task breakdown with input/output/success criteria
- Signal extraction scope (code/imports/tests/ownership/violations/duplication/architecture/async/observability/suppression)
- Bundle JSON schema (version, issue_id, risk_score, risk_band, change_summary, code_hunks, import_graph, ownership, related_tests, violations_summary, metadata)
- Risk register (8 risks with mitigations)
- Assumptions (10 key assumptions, all HIGH confidence)
- File paths (absolute)

**Checkpoint:** `project_board/checkpoints/M902-13/2026-05-19T-specification.md`

## Specification

Complete specification at `project_board/specs/902_13_semantic_extraction_spec.md` (v1.0, frozen).

**Specification includes:**
- **6 Requirements:** Gate module and registry (Req 01), semantic extraction scope and JSON schema (Req 02), compression and truncation strategy (Req 03), determinism and stability (Req 04), test vector coverage — 35 vectors (Req 05), edge cases and error handling (Req 06)
- **7 AC mappings:** Each ticket AC explicitly mapped to specification requirements and test vectors
- **Bundle JSON schema:** 20+ fields fully documented with type, required flag, and description
- **Extraction scope:** 11 mandatory sections (code hunks, import graph, ownership, tests, violations, modules, duplication, architecture, async, observability, suppression)
- **Compression strategy:** Priority-based extraction (code > imports > tests > metadata), size-enforced truncation, fallback rules
- **Determinism rules:** No timestamps as decision factors, sorted arrays, json.dumps(sort_keys=True) serialization, validation rules
- **Test vectors:** 35 vectors covering simple scenarios, multi-file refactors, circular imports, edge cases, determinism, NFR (performance, schema, language detection)
- **Edge case catalog:** 20+ edge cases with expected behavior and graceful degradation
- **Non-functional requirements:** Performance (<5s), reliability (determinism), maintainability (module size <300 lines), observability (logging), security (no secrets), correctness (schema compliance)
- **Risk register:** 10 identified risks with probability, impact, and mitigation strategies
- **Assumptions:** 10 key assumptions (prior gates conform, git available, CODEOWNERS optional, Python-centric import extraction, test linking heuristic, size <100KB enforced, determinism via serialization, bundling per issue_id, Stage 5 after Stage 4)
- **Deferred scope:** M903+ (orchestration, agent invocation, archival, multi-language, ML)

## NEXT ACTION

Route to Test Breaker Agent (Task 3 of execution plan):

**Test Break Phase:**

Build adversarial test suite `tests/ci/test_semantic_extraction_check_adversarial.py` with 40+ tests covering:
- Boundary conditions (size limits: 99KB pass, 101KB truncate)
- Import graph edge cases (circular A→B→A, deep chains A→B→C→D→E truncated at depth 2)
- CODEOWNERS missing/malformed (fallback heuristic activation)
- Empty code hunks (no code, only config/docs)
- Very large files (>10K lines, extract only relevant hunks via git diff)
- Binary files in diff (skip gracefully, no error)
- Test code not found (empty related_tests, no failure)
- Special characters and unicode (non-UTF8 files)
- Determinism validation (same input → same output byte-for-byte)
- Malformed git diff, syntax errors in Python files
- Schema mutation tests (null fields, missing required, type violations)
- Performance stress (100+ files, 1000+ import edges, 100+ violations, <5s)
- Assumption validation (prior gate output format variations)

**Deliverable:** Adversarial test suite at `tests/ci/test_semantic_extraction_check_adversarial.py` (40+ tests, ready for Task 4 Implementation)

**Input:** Behavioral test suite `tests/ci/test_semantic_extraction_check.py` (Task 2 complete)

---

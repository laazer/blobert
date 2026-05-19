# M902-13 — Semantic Extraction and Bundling (SPECIFICATION)

**Run:** 2026-05-19T-specification  
**Agent:** Spec Agent (Autonomous)  
**Stage:** SPECIFICATION (Revision 2 → 3)  
**Status:** SPECIFICATION COMPLETE

---

## Checkpoint Decisions

### [M902-13] SPECIFICATION — Bundle Schema & Extraction Scope

**Would have asked:** How to structure import graph extraction (AST-based vs regex-based vs hybrid)? Should import graph include cycle detection? How deeply should we track transitive imports (1 hop, 2 hops, adaptive)?

**Assumption made:** 
- Import extraction uses `ast.parse()` for Python files (deterministic, AST-based); fallback to regex for non-Python (JS: `import/require` statements; GDScript: simple regex for `import` keyword).
- Import graph includes direct imports (1 hop) and direct imports of those (2 hops total); depth limit enforced to prevent exponential explosion.
- Cycle detection is built in (visited set during traversal); cycles are not errors — they are documented in the bundle and skipped on loop detection to prevent infinite traversal.

**Confidence:** High

---

### [M902-13] SPECIFICATION — Test Code Linking Heuristic

**Would have asked:** How precise must test code linking be? Should we require exact file matches or allow fuzzy matching? What happens when test code is not found?

**Assumption made:**
- Multiple strategies (priority order): (1) prefix-match (test_foo.py for foo.py in same directory), (2) import graph (test files importing the module), (3) fallback to empty array (no error if test not found — defensive).
- Test code linking is heuristic; 100% accuracy not required. Focus on commonly-named tests and import-based matches.
- When test code is found, include function signatures and key test names (not full code blocks).

**Confidence:** High

---

### [M902-13] SPECIFICATION — CODEOWNERS vs Directory-Based Fallback

**Would have asked:** What's the priority if CODEOWNERS file exists but is malformed? Should we use both strategies simultaneously or fall back to one?

**Assumption made:**
- Try to parse CODEOWNERS first (GitHub standard format: `owner_name path_pattern` per line).
- If CODEOWNERS doesn't exist or parsing fails, use directory-based heuristic (e.g., `asset_generation/python/*` → `python-team`, `asset_generation/web/*` → `web-team`, `ci/scripts/*` → `ci-team`).
- Only one strategy used per bundle run; no blending (pick CODEOWNERS if available, else fallback).
- Document in bundle metadata which strategy was used (`codeowners_available: bool`, `ownership_source: string`).

**Confidence:** High

---

### [M902-13] SPECIFICATION — Code Hunk Truncation Strategy

**Would have asked:** When code hunks exceed 50 lines, how should truncation work? Should we preserve line numbers or truncate the actual code? How to prioritize hunks if total <100KB?

**Assumption made:**
- Code hunks are extracted by line range from git diff; max 50 lines per hunk (if original hunk >50, include first 50 + ellipsis).
- Line range is always preserved for readability (start_line, end_line, actual_code).
- If bundle exceeds 100KB, prioritize in order: (1) code hunks (full), (2) import graph (full), (3) related tests (truncated), (4) metadata (required).
- Warn in metadata if truncation occurred (`truncated: bool`, `truncation_reason: string`).

**Confidence:** High

---

### [M902-13] SPECIFICATION — Bundle Size Enforcement

**Would have asked:** Should >100KB bundles fail the gate or just warn? What happens if even after truncation we can't get below 100KB?

**Assumption made:**
- Gate never fails due to size (status always PASS in shadow mode).
- If bundle <100KB: no issues.
- If bundle 100–150KB: warn in metadata, include `truncated: true`, continue (do not fail).
- If bundle >150KB after truncation attempts: emit WARNING-level message in bundle metadata, continue (defensive approach; bundling succeeds, downstream may reject if needed).
- This aligns with shadow-mode, non-blocking semantics.

**Confidence:** High

---

### [M902-13] SPECIFICATION — Determinism & Timestamps

**Would have asked:** What timestamp information should the bundle include? Should timestamps affect bundle comparison or just be metadata?

**Assumption made:**
- Bundle includes **no decision-making timestamps** (no creation_time, generated_at, etc. as bundle keys).
- Optional metadata fields: `extraction_time_ms` (for monitoring), `git_commit_hash` (for versioning).
- Determinism enforced: same git state + same violations → identical bundle JSON (when serialized with sorted keys).
- Tests validate determinism by running gate twice with same inputs and comparing JSON byte-for-byte (after parsing and re-serializing to normalize).

**Confidence:** High

---

### [M902-13] SPECIFICATION — Bundle Format Stability (M902-01 Alignment)

**Would have asked:** Should bundle extend the gate success schema from M902-01 or be a completely separate contract?

**Assumption made:**
- Bundle output extends M902-01 gate success schema (status: PASS, timestamp, ticket_id, etc.).
- Additional fields specific to semantic extraction: `risk_score`, `risk_band`, `change_summary`, `code_hunks`, `import_graph`, `ownership`, `related_tests`, `violations_summary`, `metadata`.
- Gate return type is M902-01-compliant success record with embedded bundle data structure in a `bundle` or root-level field (to be resolved in spec based on payload size).

**Confidence:** Medium-High (will clarify in spec based on M902-01 field structure)

---

### [M902-13] SPECIFICATION — Violation Input Format

**Would have asked:** What does the violation array look like coming from M902-12? What fields are required vs optional?

**Assumption made:**
- Violations input matches M902-01/M902-12 schema: `{rule_id: string, severity: string, file: string, line: int | null, message: string}`.
- All fields are expected; if any are missing, skip with WARN.
- Violations from prior gates (M902-11 architecture, M902-12 risk scoring) are parsed and included in bundle `violations_summary`.

**Confidence:** High (M902-12 spec freezes this contract)

---

### [M902-13] SPECIFICATION — Multi-File Refactor Test Coverage

**Would have asked:** What counts as a "complex multi-file change"? Should test vectors include cross-module refactors with circular imports?

**Assumption made:**
- Complex multi-file scenarios for testing: (1) refactor moving functionality across 5+ files, (2) circular imports (A→B→A), (3) async/sync boundary changes, (4) migration + runtime code changes, (5) large files (>1000 lines) with small hunks extracted.
- Test vectors must exercise import graph traversal, test code discovery across multiple test files, and bundle size boundaries with realistic multi-file scenarios.

**Confidence:** High

---

## Specification Output

Specification file created at: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_13_semantic_extraction_spec.md`

**Contents:**
- 7 Requirements (one per ticket AC)
- Acceptance criteria for each requirement
- Bundle JSON schema (20+ fields)
- Extraction scope rules
- Compression & truncation strategy
- Test vectors (35 total)
- Edge case catalog
- Risk register (8 identified risks)
- Assumptions (10 resolved)
- Deferred scope

**Status:** READY FOR SPEC COMPLETENESS CHECK (gate_type: generic)

---

## Next Action

Route to orchestrator for spec completeness check validation:
```bash
python ci/scripts/spec_completeness_check.py \
  project_board/specs/902_13_semantic_extraction_spec.md \
  --type generic
```

If check passes: advance Stage to TEST_DESIGN, route to Test Designer Agent (Task 2).  
If check fails: route back to Spec Agent with error list.

---

# M902-13 Specification: Stage 5 — Semantic Extraction & Bundling

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/13_stage_5_semantic_extraction_and_bundling.md`  
**Version:** 1.0  
**Status:** SPECIFICATION  
**Date:** 2026-05-19  
**Spec Agent:** Autonomous (Checkpoint Protocol)

---

## Overview

This specification defines Stage 5 of the 8-stage governance pipeline: **Semantic Extraction Layer**. The gate ingests high-risk changes from Stage 4 risk scoring (risk_score >= 6, ESCALATE band) and generates focused, compressed review bundles for agent semantic review (Stage 6). The gate extracts relevant context (changed code, dependency neighborhoods, ownership assignments, related tests, violation summaries) into JSON bundles under `.semantic_reviews/<issue_id>.json`, each <100KB. The gate is **non-blocking shadow mode**; status is always "PASS" and bundling succeeds regardless of complexity. The bundle JSON schema is fully documented, deterministic, and suitable for agent context windows.

This gate follows the validation gate framework established in M902-01: it is a Python module under `ci/scripts/gates/`, registered in `gate_registry.json`, and emits structured JSON results conforming to the gate success schema.

---

## Requirement 01: Gate Module and Registry Entry

### 1. Spec Summary

**Description:** Implement `ci/scripts/gates/semantic_extraction_check.py` as a Python module that:
- Accepts an `inputs` dict with optional risk_score, violations array, and change metadata
- Ingests high-risk change context from Stage 4 risk scoring and prior gates
- Parses git diff to extract changed code hunks (staged changes or specified commit range)
- Builds a dependency graph by analyzing imports (1–2 hops from changed files)
- Discovers related test code via module name matching and import analysis
- Extracts ownership assignments from CODEOWNERS file (or directory-based fallback)
- Summarizes violations from prior gates and maps to bundle context
- Assembles a compressed JSON bundle with all required fields
- Writes bundle to `.semantic_reviews/<issue_id>.json`
- Returns a dict matching the gate success schema from M902-01, with added fields for risk_score, risk_band, and bundle metadata
- Exports a `run(inputs: dict) -> dict` function callable by `gate_runner.py`

**Constraints:**
- Must be importable as `ci.scripts.gates.semantic_extraction_check` and callable by gate_runner
- Must validate output conforms to M902-01 gate success schema extended with semantic extraction fields
- Must not swallow exceptions; all failures logged and transformed per code_governance.md
- Module must be registered in `ci/scripts/gate_registry.json` with entry mapping gate to module path
- Bundle size must be <100KB; truncate non-critical sections if needed
- Determinism enforced: same git state + violations → identical bundle (byte-for-byte after normalization)
- Gate operates in **shadow mode only** (status always "PASS", exit 0 regardless of bundle size or complexity)
- No external API calls; pure local analysis (git, file I/O, AST parsing)

**Assumptions:**
- Violations conform to M902-01 gate schema (violations array with rule_id, severity, file, line, message fields)
- Git diff is available locally (git commands executable in repo context)
- CODEOWNERS file (GitHub standard) is optional; fallback to directory-based heuristic if not found
- Import extraction is Python-centric (ast.parse); lightweight for non-Python (regex-based)
- Test code linking via module name prefix-matching + import graph (heuristic, not guaranteed)
- Bundle triggers on risk_score >= 6 (ESCALATE band); risk_score < 6 skips bundling (optional optimization)
- Extraction targets staged changes (git diff --cached); alternative: specified commit range (deferred to M903)

**Scope:**
- Semantic extraction module implementation, bundling logic, and output contract only
- Downstream orchestration (routing based on bundle generation, agent invocation) deferred to M903
- Machine learning-based signal refinement deferred to M904+

### 2. Acceptance Criteria

1. **Module exists at correct path:** `ci/scripts/gates/semantic_extraction_check.py` is present, syntactically valid Python, importable without errors
2. **run() function signature:** Exports `run(inputs: dict) -> dict` where:
   - `inputs` may contain: `risk_score` (number), `risk_band` (string), `violations` (array), `issue_id` (string), `ticket_id`, `upstream_agent`, `downstream_agent`, `mode`
   - Returns a dict with fields: `status` ("PASS"), `gate` ("semantic_extraction_check"), `timestamp`, `ticket_id`, `message`, `violations` (array), `artifacts` (array), `duration_ms`, `risk_score`, `risk_band`, `bundle_path`, `change_summary`, `violations_summary`, `metadata` (see Requirement 02)
   - Function matches M902-01 gate framework contract (JSON-serializable, deterministic output)
3. **Registry entry:** Gate is registered in `ci/scripts/gate_registry.json`:
   ```json
   {
     "name": "semantic_extraction_check",
     "module": "ci.scripts.gates.semantic_extraction_check",
     "run_function": "run",
     "required_inputs": [],
     "optional_inputs": ["risk_score", "risk_band", "violations", "issue_id", "ticket_id", "upstream_agent", "downstream_agent", "mode"],
     "default_mode": "shadow",
     "description": "Extracts focused review bundles (code, imports, ownership, tests, violations) from high-risk changes for agent semantic review (Stage 6)"
   }
   ```
4. **Exit codes:** Shadow mode always exits 0 (non-blocking); status always "PASS"
5. **Exception handling:** No bare `except:` or silent swallowing; all exceptions logged with context and either re-raised or transformed to violations
6. **Determinism:** Same risk_score, violations, git state always yields same bundle JSON (when serialized with sorted keys)
7. **Bundle generation:** `.semantic_reviews/<issue_id>.json` is created and path returned in `bundle_path` field

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Import graph extraction too expensive:** Traversing imports for large codebases could timeout. Mitigation: Limit depth to 2 hops (direct + transitive). Use visited set to detect cycles. Timeout import extraction at 5s per file. Fallback: skip import graph if timeout (include code hunks only, not error).
- **Bundling fails on binary files or git errors:** Git diff may encounter binary files or merge conflicts. Mitigation: Filter for text files only (skip .png, .glb, .pyc, .class). Handle decode errors gracefully (log WARNING, skip file, continue). Never fail extraction due to git error; degrade gracefully.
- **CODEOWNERS file missing or malformed:** File may not exist or have syntax errors. Mitigation: Fallback to directory-based heuristic (e.g., `asset_generation/python/*` → `python-team`). Document both strategies in bundle metadata.
- **Test code linking heuristic fails:** Test files may use non-standard naming (not `test_foo.py` for `foo.py`). Mitigation: Use multiple strategies (1) prefix-match, (2) import graph, (3) grep. Log all strategies used. Fallback: empty array (no error).
- **Bundle size enforcement hard to achieve:** Complex changes may exceed 100KB even with truncation. Mitigation: Prioritize extraction (code > imports > tests > metadata). Truncate code hunks to 50 lines. Omit non-critical sections. Warn if truncation occurs, but do not fail.
- **Determinism lost (timestamps, dict ordering, sorted lists):** Floating-point arithmetic or randomness could affect output. Mitigation: Exclude timestamps from bundle. Use json.dumps with sort_keys=True. Validate determinism in tests (same input → same output byte-for-byte).
- **Prior gate outputs missing or malformed:** M902-11/M902-12 may not provide expected fields. Mitigation: Spec Task 1 defines input contract (what violations look like). Treat malformed violations as skip-with-WARN, not error. Defensive parsing throughout.
- **Performance degradation with large repos:** Processing many files and import edges could exceed time budget. Mitigation: Lazy extraction (process only changed files + 2-hop neighbors). Cache import graph. Target <5s per extraction. Stress test with 100+ file changes.

**Ambiguities resolved (per checkpoint protocol):**
- **Q1: Import extraction strategy?** → AST-based for Python (ast.parse), regex-based fallback for JS/GDScript. Cycle detection with visited set.
- **Q2: Import depth?** → 2 hops (direct + transitive) to prevent exponential explosion. Hard limit enforced.
- **Q3: Test code linking precision?** → Heuristic; 100% accuracy not required. Use multiple strategies (prefix, imports, grep). Fallback to empty array (no error).
- **Q4: CODEOWNERS vs fallback?** → Try CODEOWNERS first; if not found or malformed, use directory-based heuristic. One strategy per bundle (no blending).
- **Q5: Code hunk truncation?** → Max 50 lines per hunk; preserve line ranges. If total >100KB, truncate lowest-priority sections (metadata, tests, non-critical violations).
- **Q6: Bundle size enforcement?** → Never fail (shadow mode). Warn if >100KB, truncate, continue.
- **Q7: Determinism (timestamps)?** → No decision-making timestamps. Include optional metadata fields (extraction_time_ms, git_commit_hash). Validate determinism by byte-for-byte comparison after normalization.
- **Q8: Violation input format?** → Matches M902-01/M902-12 schema: rule_id, severity, file, line, message.

**Confidence: HIGH.** Gate framework established (M902-01 complete). Risk scoring input available (M902-12 complete). Extraction rules well-defined in execution plan. Assumptions all resolved.

### 4. Clarifying Questions

None. Scope and constraints frozen per execution plan and checkpoint protocol.

---

## Requirement 02: Semantic Extraction Scope and Bundle JSON Schema

### 1. Spec Summary

**Description:** The gate extracts and bundles focused context from high-risk changes. The bundle includes all relevant information for agent semantic review without bloating to full-repo context.

**Extraction Scope (Mandatory Sections):**

1. **Changed Code:** Git diff hunks from staged changes (or commit range if specified). Preserve line ranges (start_line, end_line). Max 50 lines per hunk; truncate with ellipsis if needed. Total code <40KB (to leave room for imports, tests, metadata).
2. **Dependency Neighborhood (Import Graph):** 1–2 hops from changed files. Direct imports (1 hop) and imports of those (2 hops). Include module names, import types (internal vs external), and affected module signatures. Cycle detection and loop prevention (visited set). Max 30KB total.
3. **Ownership Assignments:** From CODEOWNERS file (if exists) or directory-based heuristic. Map changed files to owners (team names, individual names, or roles). Include source metadata (CODEOWNERS vs heuristic).
4. **Related Test Code:** Test files matching changed modules by name (test_foo.py for foo.py) or via import graph. Include test function signatures, setup/teardown methods, and key test names. Max 10KB.
5. **Violation Summaries:** From prior gates (M902-11 architecture, M902-12 risk scoring). Structured as violations array with rule_id, severity, message. Include risk_score and risk_band from M902-12.
6. **Affected Modules:** List of modules touched by change. Include module-level docstrings and exported functions/classes (signatures only, not full code).
7. **Duplication Clusters:** If detected by prior gates, high-level summary (files involved, lines duplicated), not full code.
8. **Architecture Violations:** Cross-layer imports, circular dependencies (brief summary with affected modules).
9. **Async Boundaries:** Async/sync context mismatches (if detected by prior gates).
10. **Observability Gaps:** Missing logging or audit events (if detected by prior gates).
11. **Suppression History:** `blobert-ignore` comments in changed code (document intent and issue references).

**Excluded (per Requirement 03):**
- Full repo context (no commit history, no blame, no large traversals)
- Unrelated files (only files touched by change or imports from touched files)
- Generated artifacts (compiled .pyc, .class, images, .glb, dist/, build/, cache files)
- Dependencies not in import graph (e.g., random npm packages)
- Sensitive data (secrets, credentials, large test data blobs)

**Bundle JSON Schema (20+ fields, frozen):**

```json
{
  "version": "1.0",
  "issue_id": "PR-42",
  "risk_score": 8.5,
  "risk_band": "ESCALATE",
  "change_summary": {
    "files_changed": 5,
    "lines_added": 120,
    "lines_deleted": 45,
    "categories": ["runtime-code", "tests"],
    "change_type": "refactor"
  },
  "code_hunks": [
    {
      "file": "asset_generation/python/src/model_registry/service.py",
      "lines": [45, 80],
      "hunk": "def get_model(model_id: str) -> Model:\n  ...",
      "language": "python",
      "violation_rule_ids": ["AS-01", "OB-01"],
      "truncated": false
    }
  ],
  "import_graph": {
    "changed_files": ["model_registry/service.py"],
    "direct_imports": [
      {
        "from": "model_registry.service",
        "to": "fastapi",
        "type": "external",
        "line_number": 5
      },
      {
        "from": "model_registry.service",
        "to": "core.config",
        "type": "internal",
        "line_number": 3
      }
    ],
    "affected_modules": [
      {
        "module": "model_registry.service",
        "exports": ["get_model", "list_models"],
        "docstring": "Registry service layer...",
        "language": "python"
      }
    ],
    "cycles_detected": false,
    "depth_limit_2_hops": true,
    "extraction_time_ms": 45
  },
  "ownership": {
    "assignments": [
      {
        "file": "model_registry/service.py",
        "owner": "team:backend",
        "source": "CODEOWNERS"
      }
    ],
    "codeowners_available": true,
    "fallback_used": false
  },
  "related_tests": [
    {
      "file": "tests/model_registry/test_service.py",
      "relevant_tests": ["test_get_model", "test_list_models"],
      "code_snippet": "def test_get_model():\n  assert get_model('123').id == '123'",
      "import_match": true
    }
  ],
  "violations_summary": {
    "from_prior_gates": [
      {
        "gate": "architecture_enforcement",
        "rule_id": "AS-01",
        "severity": "HIGH",
        "message": "Blocking I/O in async context",
        "file": "model_registry/service.py",
        "line": 50
      },
      {
        "gate": "risk_scoring",
        "rule_id": "OB-01",
        "severity": "MEDIUM",
        "message": "Missing audit logging"
      }
    ],
    "violation_count": 2,
    "risk_signals": ["async_complexity", "observability_gaps"]
  },
  "metadata": {
    "git_commit_hash": "abc123def456",
    "staged_changes": true,
    "bundle_size_bytes": 45230,
    "extraction_time_ms": 150,
    "compressed": false,
    "schema_version": "1.0",
    "truncated": false,
    "truncation_reason": null,
    "codeowners_source": "CODEOWNERS",
    "git_diff_command": "git diff --cached"
  }
}
```

**Schema Field Definitions (AUTHORITATIVE):**

| Field | Type | Required | Description |
|---|---|---|---|
| `version` | string | YES | Bundle schema version (frozen: "1.0") |
| `issue_id` | string | YES | GitHub issue/PR number or internal ticket id (e.g., "PR-42", "M902-13") |
| `risk_score` | number | YES | From M902-12 (0–100 scale) |
| `risk_band` | string | YES | From M902-12 ("EXIT", "WARN", "ESCALATE") |
| `change_summary` | object | YES | Meta-summary of change (see sub-fields below) |
| `change_summary.files_changed` | integer | YES | Count of files touched |
| `change_summary.lines_added` | integer | YES | Total lines added |
| `change_summary.lines_deleted` | integer | YES | Total lines deleted |
| `change_summary.categories` | array[string] | YES | Change categories ("runtime-code", "tests", "docs", "migrations", etc.) |
| `change_summary.change_type` | string | YES | Type of change ("bugfix", "feature", "refactor", "chore", "migration") |
| `code_hunks` | array | YES | Git diff hunks with context (see sub-fields below) |
| `code_hunks[].file` | string | YES | File path relative to repo root |
| `code_hunks[].lines` | array[int] | YES | [start_line, end_line] preserving original line numbers |
| `code_hunks[].hunk` | string | YES | Code snippet (max 50 lines; truncate with "..." if needed) |
| `code_hunks[].language` | string | YES | Language (python, javascript, gdscript, etc.) |
| `code_hunks[].violation_rule_ids` | array[string] | NO | Rule IDs of violations affecting this hunk (empty array if none) |
| `code_hunks[].truncated` | boolean | YES | Was hunk truncated from original? |
| `import_graph` | object | YES | Dependency graph (1–2 hops) |
| `import_graph.changed_files` | array[string] | YES | Files modified in this change |
| `import_graph.direct_imports` | array[object] | YES | Direct imports from changed files (see sub-fields) |
| `import_graph.direct_imports[].from` | string | YES | Importing module name |
| `import_graph.direct_imports[].to` | string | YES | Imported module name |
| `import_graph.direct_imports[].type` | string | YES | Import type ("internal" or "external") |
| `import_graph.direct_imports[].line_number` | integer | NO | Line number of import statement (if available) |
| `import_graph.affected_modules` | array[object] | YES | Module summaries for changed files (see sub-fields) |
| `import_graph.affected_modules[].module` | string | YES | Module name |
| `import_graph.affected_modules[].exports` | array[string] | YES | Exported symbols (functions, classes) |
| `import_graph.affected_modules[].docstring` | string | NO | Module-level docstring |
| `import_graph.affected_modules[].language` | string | YES | Language (python, javascript, gdscript) |
| `import_graph.cycles_detected` | boolean | YES | Were circular imports detected? |
| `import_graph.depth_limit_2_hops` | boolean | YES | Extraction limited to 2 hops? |
| `import_graph.extraction_time_ms` | integer | YES | Time spent extracting import graph |
| `ownership` | object | YES | Ownership assignments |
| `ownership.assignments` | array[object] | YES | File-to-owner mappings (see sub-fields) |
| `ownership.assignments[].file` | string | YES | File path |
| `ownership.assignments[].owner` | string | YES | Owner name (team:name, individual name, or role) |
| `ownership.assignments[].source` | string | YES | Source ("CODEOWNERS" or "heuristic") |
| `ownership.codeowners_available` | boolean | YES | Was CODEOWNERS file found? |
| `ownership.fallback_used` | boolean | YES | Was fallback heuristic used? |
| `related_tests` | array[object] | YES | Related test code |
| `related_tests[].file` | string | YES | Test file path |
| `related_tests[].relevant_tests` | array[string] | YES | Test function names (signatures only) |
| `related_tests[].code_snippet` | string | YES | Key test code (max 500 chars) |
| `related_tests[].import_match` | boolean | YES | Was test found via import analysis? |
| `violations_summary` | object | YES | Summary of violations from prior gates |
| `violations_summary.from_prior_gates` | array[object] | YES | Violation records from M902-11, M902-12 (see sub-fields) |
| `violations_summary.from_prior_gates[].gate` | string | YES | Gate name that detected violation |
| `violations_summary.from_prior_gates[].rule_id` | string | YES | Rule ID (e.g., "AS-01", "OB-01") |
| `violations_summary.from_prior_gates[].severity` | string | YES | Severity ("CRITICAL", "ERROR", "WARN", "INFO") |
| `violations_summary.from_prior_gates[].message` | string | YES | Human-readable violation message |
| `violations_summary.from_prior_gates[].file` | string | NO | File path (if applicable) |
| `violations_summary.from_prior_gates[].line` | integer | NO | Line number (if applicable) |
| `violations_summary.violation_count` | integer | YES | Total violation count from all prior gates |
| `violations_summary.risk_signals` | array[string] | YES | Risk signal types detected ("SRP", "architecture_drift", "async_complexity", etc.) |
| `metadata` | object | YES | Bundle metadata |
| `metadata.git_commit_hash` | string | YES | Git commit SHA (for versioning bundles) |
| `metadata.staged_changes` | boolean | YES | Bundle from staged changes (vs committed range)? |
| `metadata.bundle_size_bytes` | integer | YES | Total JSON bundle size in bytes |
| `metadata.extraction_time_ms` | integer | YES | Total extraction time (including all sub-operations) |
| `metadata.compressed` | boolean | YES | Is bundle gzip-compressed? (false for JSON, true if stored as .gz) |
| `metadata.schema_version` | string | YES | Schema version (same as top-level version field) |
| `metadata.truncated` | boolean | YES | Was any content truncated? |
| `metadata.truncation_reason` | string | NO | Reason for truncation (if truncated=true) |
| `metadata.codeowners_source` | string | YES | "CODEOWNERS" or "heuristic" |
| `metadata.git_diff_command` | string | YES | Git command used to extract diff (e.g., "git diff --cached") |

**Constraints:**
- All fields are JSON-serializable (strings, numbers, arrays, objects; no NaN, Infinity, custom types)
- Bundle must be valid JSON (tested via json.dumps() + json.loads())
- code_hunks array must not be empty (if change has no code, use minimal stub)
- Violation rule_ids must match M902-01 schema (case-sensitive)
- All timestamps are ISO 8601 UTC format (if any included in metadata)
- Bundle is deterministic: same inputs → same JSON (byte-for-byte after normalization with sorted keys)

**Assumptions:**
- Gate runner will validate output schema after gate returns (M902-01 gate framework responsibility)
- Downstream orchestrator (M903) will parse and consume this bundle for routing decisions and agent invocation
- Bundle is stored as-is (JSON text); gzip compression optional in metadata (no actual compression in this stage)
- issue_id is required and uniquely identifies the change (PR number, branch name, or ticket ID)

**Scope:** Bundle schema, field definitions, and extraction rules only. Downstream consumption (agent invocation, bundling decisions) deferred to M903.

### 2. Acceptance Criteria

1. **Schema complete:** All 20+ fields defined with type, required flag, and description
2. **Extraction scope enumerated:** All 11 mandatory sections (code, imports, ownership, tests, violations, modules, duplication, architecture, async, observability, suppression) documented with extraction rules
3. **Code hunks properly structured:** Preserve line ranges, max 50 lines per hunk, language tagged, truncation flag set
4. **Import graph defined:** Direct imports, affected modules, cycle detection, depth limit enforced, extraction time tracked
5. **Ownership mapping rules:** CODEOWNERS parsing (if exists) or directory-based fallback, source metadata recorded
6. **Test code linking:** Module name prefix-matching + import graph, code snippets included, match source recorded
7. **Violations summary:** Violations from prior gates structured with rule_id, severity, message, file/line (optional)
8. **Metadata complete:** Git state, bundle size, extraction time, truncation info, source method documented
9. **Determinism enforced:** Same inputs → same JSON (byte-for-byte after sorted serialization)
10. **Bundle size bounded:** Max 100KB total; enforced via truncation strategy and priority rules

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Bundle schema evolution:** If schema changes after release, old agents may not parse new bundles. Mitigation: Version field is immutable ("1.0" in this spec). Future changes require new version (v2). Agents must support multiple versions.
- **Import extraction incomplete:** Transitive imports may not be fully captured at 2-hops. Mitigation: 2-hops is heuristic limit (prevents exponential explosion). Most practical dependencies reachable within 2 hops. Tests validate with realistic import graphs.
- **Test code linking misses tests:** Test files not matching heuristic patterns (e.g., using `check_` prefix instead of `test_`) will not be found. Mitigation: Multiple strategies (prefix, imports, grep). Fallback to empty array (not error). Document in metadata which strategy was used.
- **Bundle size enforcement unpredictable:** After truncation, bundle may still exceed 100KB. Mitigation: Prioritize extraction (code > imports > tests > metadata). Truncate lowest-priority sections. Warn in metadata if truncation occurs. Never fail (shadow mode).
- **Violation input schema mismatch:** If prior gates emit violations with unexpected fields, extraction fails. Mitigation: Defensive parsing (try-except on each violation). Skip malformed violations with WARN. Document expected schema in Requirement 01.

**Ambiguities resolved:**
- **Q1: Bundle versioning (what if schema changes)?** → Version field locks schema to "1.0". Future changes require new version (v2). Old bundles remain valid.
- **Q2: Import depth (why 2 hops)?** → Balances coverage (most practical dependencies) vs performance. Prevents exponential explosion. Documented in bundle.
- **Q3: Test code linking accuracy?** → Heuristic; 100% accuracy not required. Multiple strategies + fallback. Document source in bundle.
- **Q4: Code hunk line numbers (are they absolute or relative)?** → Absolute (original file line numbers). Preserved for context and agent understanding.
- **Q5: What if code file is binary or unreadable?** → Filter via git (text files only) and handle decode errors gracefully (skip file, log WARNING, continue).

---

## Requirement 03: Compression and Truncation Strategy

### 1. Spec Summary

**Description:** The bundle must be <100KB total. To achieve this, selective extraction is applied in priority order:

**Extraction Priority Order:**

1. **Code hunks (40KB max):** Essential for semantic review. Max 50 lines per hunk. If hunk >50 lines, include first 50 + ellipsis.
2. **Import graph (30KB max):** Direct imports, affected modules, cycles. Full extraction up to 2 hops.
3. **Related tests (10KB max):** Test function signatures + key test code. Truncate snippets if needed.
4. **Violations summary (5KB max):** All violations from prior gates (not truncated).
5. **Ownership (3KB max):** File-owner mappings (not truncated).
6. **Metadata (2KB max):** Git state, timestamps, extraction metadata (not truncated).

**Total: ~100KB (or less if fewer sections apply)**

**Truncation Rules (if total >100KB):**

1. Omit lowest-priority sections in reverse order:
   - First: omit duplication clusters (low priority)
   - Second: omit observability gaps summary (low priority)
   - Third: truncate test code snippets to 200 chars each
   - Fourth: truncate import graph to direct imports only (omit 2-hop transitive)
   - Fifth: fail extraction (should not happen with above strategy)

2. **Code hunk truncation:** Max 50 lines per hunk. If original hunk >50 lines:
   - Include first 45 lines + "... (hunk truncated, X lines omitted)" + last 5 lines
   - Mark `truncated: true` on that hunk
   - Preserve original line numbers (start_line, end_line)

3. **Metadata truncation flag:** If any truncation occurs, set `metadata.truncated: true` and record reason in `metadata.truncation_reason`.

**Constraints:**
- Total bundle size (JSON, before gzip) must be <100KB (enforced at bundle assembly time)
- If bundle exceeds 100KB even after truncation, warn in metadata and continue (do not fail; shadow mode)
- No lossy compression of critical sections (code, violations, ownership); only omit non-critical sections
- Determinism preserved: truncation is deterministic (same inputs → same truncated output)

**Assumptions:**
- Priority order (code > imports > tests > metadata) is sound (agent can reason with code hunks + violations even without full import graph)
- 2-hop import extraction can be omitted if needed (1-hop direct imports sufficient for context)
- Test code snippets can be truncated or omitted without loss of semantic value (test names sufficient)
- Observability gaps and duplication clusters are informational (not decision-critical); can be omitted

**Scope:** Truncation strategy only. Implementation responsibility in Requirement 01 (gate module).

### 2. Acceptance Criteria

1. **Priority order defined:** All 6 extraction priorities listed with size limits (code 40KB, imports 30KB, tests 10KB, violations 5KB, ownership 3KB, metadata 2KB)
2. **Truncation rules enumerated:** Fallback sequence for omitting sections in priority order
3. **Code hunk truncation specified:** Max 50 lines per hunk, preserve line numbers, mark truncation
4. **Total size bounded:** <100KB constraint enforced in implementation
5. **Metadata flag:** truncated and truncation_reason fields documented
6. **Determinism preserved:** Same inputs → same truncated output (no randomness in truncation decisions)
7. **Non-critical sections identified:** Duplication, observability gaps, transitive imports identified as omittable

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Truncation removes critical context:** If code hunks are truncated too aggressively, agent cannot reason about change. Mitigation: Code hunks are priority 1 (full extraction unless >100KB total). Most changes will not exceed limit.
- **Import graph omission breaks dependency analysis:** If transitive imports omitted, agent misses important context. Mitigation: Direct imports (1 hop) usually sufficient. Tests validate with realistic import graphs.
- **Size enforcement overhead:** Computing bundle size and re-extracting if truncated could be expensive. Mitigation: First-pass extraction respects priority limits. Re-extraction only if total >100KB (rare case).

---

## Requirement 04: Determinism and Stability

### 1. Spec Summary

**Description:** The bundle output must be deterministic: identical inputs (git state, violations, issue_id) must produce identical JSON (byte-for-byte after normalization).

**Determinism Rules:**

1. **No timestamps as decision factors:** Creation time, extraction timestamp, duration (in ms) are recorded for observability, not used in bundle logic.
2. **Sorted arrays:** All arrays must be sorted consistently:
   - `code_hunks`: sorted by file path, then start_line (ascending)
   - `direct_imports`: sorted by `from` field, then `to` field (alphabetical)
   - `affected_modules`: sorted by module name (alphabetical)
   - `assignments` (ownership): sorted by file path (alphabetical)
   - `related_tests`: sorted by file path (alphabetical)
   - `from_prior_gates` (violations): sorted by rule_id (alphabetical)
3. **JSON serialization:** Use `json.dumps(bundle, sort_keys=True, indent=2)` for consistent output
4. **Git commit hash:** Use for versioning bundles (immutable for given git state)
5. **No external state:** Bundle depends only on: git state (diff), violations input, issue_id. No environment variables, random seeds, or external data.

**Validation:** Tests must verify determinism by:
- Running gate twice with identical inputs
- Serializing both outputs with `json.dumps(sort_keys=True)`
- Comparing byte-for-byte (should be identical)
- Parsing both and comparing semantically (should be equal)

**Constraints:**
- All random elements forbidden (no random.shuffle, no uuid generation)
- Floating-point arithmetic should not introduce rounding errors (use integer arithmetic where possible)
- Order-independent inputs (violations array in any order) must produce identical output

**Assumptions:**
- Git state is frozen (same commit hash) between runs
- Violations input is the only varying input (same violations array → same bundle)
- Sorting is stable (Python sort is stable by default)

**Scope:** Determinism rules only. Implementation responsibility in Requirement 01 (gate module).

### 2. Acceptance Criteria

1. **No timestamps as decision factors:** Creation times, durations do not affect bundle content (only metadata)
2. **All arrays sorted:** code_hunks, imports, modules, ownership, tests, violations all have defined sort order
3. **JSON deterministic:** json.dumps(sort_keys=True) produces identical output for identical inputs
4. **Determinism test:** At least one test vector runs gate twice and compares outputs byte-for-byte
5. **Order-independent:** Violations array in different orders produces same bundle
6. **Git commit hash immutable:** Same git state (same commit) produces same bundle

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Rounding errors in floating-point arithmetic:** Duration timestamps may differ slightly between runs. Mitigation: Timestamps are metadata only, not decision factors.
- **Dict insertion order (Python 3.7+):** Dicts are ordered by insertion, not alphabetically. Mitigation: Use json.dumps(sort_keys=True) to ensure consistent serialization.
- **Violations order varies:** Prior gates may emit violations in different orders. Mitigation: Sort violations in bundle output (alphabetical by rule_id).

---

## Requirement 05: Test Vector Coverage

### 1. Spec Summary

**Description:** This requirement specifies 35+ test vectors covering all code paths, edge cases, and non-functional requirements.

**Test Vector Catalog:**

| ID | Scenario | Input | Expected Output | AC Verified |
|---|---|---|---|---|
| TV-01 | No violations, simple single-file change | violations=[], 1 file changed | bundle with 1 code hunk, empty violations array, low risk_score | AC-1, AC-2, AC-6 |
| TV-02 | Single architecture violation (AR-01) | violations=[{rule_id: "AR-01", ...}], 2 files | bundle includes both files, violation in summary, risk_band=ESCALATE | AC-1, AC-2, AC-3 |
| TV-03 | Multi-file refactor (5 files, clean) | 5 files changed, no violations | bundle includes all 5 code hunks, import graph shows 5 changed_files | AC-1, AC-2, AC-7 |
| TV-04 | Circular import (A→B→A) | 2 files with circular imports | bundle includes both files, cycles_detected=true, no infinite loop | AC-1, AC-2, AC-7 |
| TV-05 | Async complexity violation (AS-01) | violations=[{rule_id: "AS-01", ...}], 1 file | bundle includes async violation in summary, risk_band=ESCALATE | AC-1, AC-2 |
| TV-06 | Migration file detected | files=[...alembic/versions/001.py], violations=[] | bundle detected as migration, risk_signals includes "migration_complexity" | AC-1, AC-2 |
| TV-07 | CODEOWNERS file present | change in asset_generation/python/, CODEOWNERS exists | bundle includes ownership from CODEOWNERS, source="CODEOWNERS" | AC-3, AC-4 |
| TV-08 | CODEOWNERS file missing, fallback used | change in asset_generation/web/, no CODEOWNERS | bundle includes ownership via heuristic (web-team), source="heuristic" | AC-3, AC-4 |
| TV-09 | Related test code found via prefix-match | change in module_registry.py, test_module_registry.py exists | bundle includes test_module_registry.py in related_tests, import_match=false | AC-1, AC-3 |
| TV-10 | Related test code found via import | change in service.py, test imports service | bundle includes test file, import_match=true | AC-1, AC-3 |
| TV-11 | Test code not found | change in isolated_util.py, no matching test | bundle has empty related_tests array (no error) | AC-4 |
| TV-12 | Large file (>1000 lines), single hunk | file with 1200 lines, change at lines 500-510 | bundle includes hunk with start=500, end=510 (10-line hunk, not truncated) | AC-1, AC-2 |
| TV-13 | Code hunk >50 lines, truncation | hunk >50 lines (original git diff) | bundle includes first 45 + ellipsis + last 5 lines, truncated=true | AC-2, AC-3 |
| TV-14 | Bundle size <100KB (simple change) | 3 files, minimal violations | bundle_size_bytes < 100000, truncated=false | AC-2 |
| TV-15 | Bundle size boundary (95KB) | complex 10-file change with violations | bundle_size_bytes < 100000, no truncation needed | AC-2 |
| TV-16 | Bundle size >100KB scenario (stress test) | 50 files with violations | bundle truncates non-critical sections, truncated=true, bundle_size_bytes < 100000 | AC-2, AC-3 |
| TV-17 | Import graph with 2-hop limit | change touches file A, which imports B, which imports C | bundle includes A→B (1 hop), B→C (2 hops), does not include C→D (3 hops) | AC-1, AC-2 |
| TV-18 | Violation from M902-12 risk scoring | risk_score=42, risk_band=ESCALATE | bundle includes risk_score and risk_band in output | AC-2, AC-6 |
| TV-19 | Multiple violations (3 different rule_ids) | violations=[{rule_id: "AR-01"}, {rule_id: "AS-01"}, {rule_id: "OB-01"}] | violations_summary has all 3, violation_count=3 | AC-1, AC-3 |
| TV-20 | Malformed violation (missing rule_id) | violations=[{severity: "ERROR", file: "..."}] (no rule_id) | violation skipped with WARN, other violations processed normally | AC-4 |
| TV-21 | Empty violations array | violations=[] | bundle generated normally, violations_summary.from_prior_gates is empty array | AC-1, AC-2 |
| TV-22 | Issue_id missing, fallback | inputs={} (no issue_id) | bundle uses ticket_id or branch name as fallback | AC-2 |
| TV-23 | Git diff with binary file | diff includes .png, .glb files | bundle skips binary files, includes only text files, no error | AC-4 |
| TV-24 | Suppression comments (blobert-ignore) | code has "# blobert-ignore-next-line" comments | bundle includes suppressions in violations_summary or metadata | AC-1, AC-3 |
| TV-25 | Determinism: run gate twice, same inputs | Run twice with identical risk_score, violations, git state | Both bundles are byte-for-byte identical (after json.dumps sort_keys) | AC-1, AC-2, AC-6 |
| TV-26 | Order independence: violations array in different orders | violations=[AR-01, AS-01] then [AS-01, AR-01] | Same bundle output (violations sorted by rule_id) | AC-1, AC-6 |
| TV-27 | Performance: 100+ violations, <5s execution | violations with 100+ entries | extraction_time_ms < 5000 | NFR-01 |
| TV-28 | Performance: large file with many imports, <5s | 100+ import edges from changed files | extraction_time_ms < 5000, import_graph complete | NFR-01 |
| TV-29 | Schema validation: all required fields present | Any valid scenario | Bundle has all 20+ required fields (no missing fields) | AC-6 |
| TV-30 | Schema validation: field types correct | Any scenario | risk_score is int, risk_band is str, code_hunks is array, etc. | AC-6 |
| TV-31 | JSON serializability: json.dumps succeeds | Any scenario | json.dumps(bundle) completes without ValueError | AC-6 |
| TV-32 | Timestamp format: ISO 8601 UTC | Any scenario | metadata git_commit_hash is SHA format (hex), extraction_time_ms is int | AC-6 |
| TV-33 | Change type detection | variety of changes (bugfix, feature, refactor) | bundle.change_summary.change_type correctly classified | AC-1, AC-2 |
| TV-34 | Language detection | Python, JavaScript, GDScript files mixed | code_hunks[].language correctly assigned per file | AC-1, AC-3 |
| TV-35 | Ownership fallback heuristic accuracy | Multiple directories (asset_generation/python, asset_generation/web, scripts/ci) | Each file assigned owner via heuristic with correct team prefix | AC-3, AC-4 |

**Coverage Requirements:**

1. **Simple scenarios:** TV-01 (no violations), TV-02–TV-06 (single violations)
2. **Multi-file scenarios:** TV-03, TV-04, TV-07–TV-11 (refactors, ownership, tests)
3. **File handling:** TV-12–TV-16 (large files, truncation, size boundaries)
4. **Import graphs:** TV-17 (2-hop limit, cycles)
5. **Violations:** TV-18–TV-22 (multiple violations, malformed, empty)
6. **Edge cases:** TV-23–TV-24 (binary files, suppressions)
7. **Determinism:** TV-25–TV-26 (idempotence, order independence)
8. **Non-functional:** TV-27–TV-28 (performance), TV-29–TV-32 (schema), TV-33–TV-35 (language/type detection)

**Total: 35 test vectors covering all ACs and code paths**

**Constraints:**
- Each vector independently testable (no shared state)
- All vectors deterministic (same input always yields same output)
- All vectors use mocked inputs (no external git/file I/O required for test setup)
- Vectors validate both positive (correct behavior) and negative (fallback behavior) cases

**Assumptions:**
- Test suite will use pytest parametrize or equivalent (each vector = one test)
- Mocking strategy: mock `git diff`, `os.path.exists`, `open()` to provide test data
- Expectations are exact values (e.g., bundle_size_bytes < 100000) or predicates (e.g., truncated=true)

**Scope:** Test vector definition only. Implementation is Test Designer/Breaker responsibility.

### 2. Acceptance Criteria

1. **Vector catalog complete:** All 35 vectors defined with scenario, input, expected output, AC verified
2. **Coverage comprehensive:** Simple, multi-file, file handling, imports, violations, edge cases, determinism, NFR vectors all present
3. **Vector traceability:** Each vector references one or more ticket ACs
4. **Determinism emphasized:** 2+ vectors (TV-25, TV-26) explicitly test idempotence and order independence
5. **Edge case coverage:** Binary files, malformed violations, suppressions, missing issue_id all covered
6. **Performance emphasis:** 2+ vectors (TV-27, TV-28) target <5s execution time
7. **Schema emphasis:** 4+ vectors (TV-29–TV-32) validate schema completeness and types

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Test vectors incomplete:** If vectors don't cover a code path, gap exists. Mitigation: Spec includes 35 vectors covering all major paths. Tests may expand beyond this.
- **Vector expectations ambiguous:** If vector specifies "risk_band=ESCALATE" but implementation produces "WARN", test fails. Mitigation: Vector spec is prescriptive; implementation must match expectations.

---

## Requirement 06: Edge Cases and Error Handling

### 1. Spec Summary

**Description:** The gate handles edge cases gracefully, never failing due to data issues (only gate logic errors are failures).

**Edge Case Catalog:**

| Case | Input Condition | Expected Behavior | Mitigation |
|---|---|---|---|
| Missing risk_score | inputs={violations: [...]} | Default risk_score=0; treat as low-risk | Conservative assumption |
| Missing risk_band | inputs={risk_score: 42} | Infer band from score (0–2→EXIT, 3–5→WARN, 6+→ESCALATE) | Deterministic mapping |
| Missing issue_id | inputs={...} | Fallback to ticket_id or branch name; never fail | Use git branch name if available |
| Empty violations array | violations=[] | Bundle generated normally; violations_summary.from_prior_gates=[] | Not an error |
| Malformed violation (missing rule_id) | violations=[{severity: "ERROR", file: "..."}] | Skip violation with WARN log; continue processing | Defensive parsing |
| Malformed violation (invalid severity) | violations=[{rule_id: "AR-01", severity: "UNKNOWN"}] | Accept any severity string; not validated here | M902-01 validates at gate runner level |
| Git diff fails (merge conflict, detached HEAD) | git diff --cached fails with exit code | Log ERROR, skip git extraction; continue with violations only | Degrade gracefully |
| Git diff contains binary files | diff includes .png, .glb files | Filter for text files only (by extension + file magic); skip binary files | Never fail on binary |
| File path unreadable (permission denied) | try to read .py file, permission error | Log WARNING, skip file; continue with other files | Non-blocking |
| CODEOWNERS file missing | CODEOWNERS not found | Use directory-based heuristic fallback; set ownership_source="heuristic" | Expected case |
| CODEOWNERS file malformed (invalid syntax) | CODEOWNERS has unparseable lines | Skip malformed lines with WARN; apply to remaining lines | Partial extraction acceptable |
| Import parsing fails (non-UTF8 file) | Python file with encoding declaration but not UTF-8 | Log WARNING, skip imports from that file; continue | Never fail on encoding |
| AST parsing fails (syntax error in Python file) | File has syntax error (e.g., unmatched parenthesis) | Log WARNING, skip AST extraction; fallback to regex import extraction | Degrade gracefully |
| Test file not found (heuristic match) | test_foo.py doesn't exist for foo.py | Empty related_tests array for that module; not an error | Heuristic is fallible |
| Large file (10K+ lines) | Change in file with 10K lines | Include only relevant hunks (from git diff); not full file | Git diff limits automatically |
| Very deep import chain (10+ hops) | A→B→C→D→...→J (10 levels) | Limit extraction to 2 hops; do not recurse beyond | Hard limit enforced |
| Circular import loop (A→B→A) | Files import each other | Detect via visited set; cycles_detected=true; no infinite loop | Loop prevention built in |
| No code hunks (only config/doc changes) | Change is YAML/JSON/Markdown only | Create minimal code_hunks array with note (no executable code) | Never fail due to file type |
| Suppression comment malformed | # blobert-ignore (incomplete) | Accept as suppression; log if intent unclear | Defensive parsing |
| Violation count extremely high (1000+) | violations=[1000 entries] | Process all; bundle may exceed 100KB; truncate non-critical | Degrade but don't fail |
| Timestamp format inconsistent | violation timestamp in non-ISO format | Accept and store as-is; don't parse/validate (prior gates responsibility) | Non-blocking |

**Error Handling Guarantees:**

1. **Never silent failures:** All exceptions logged at least at WARNING level
2. **Never bare except:** All exceptions caught by type, logged with context, and either re-raised or transformed
3. **Graceful degradation:** Missing optional inputs or malformed data → skip gracefully, continue processing
4. **Always produce output:** Gate always returns a valid success record (status: PASS) with whatever context could be extracted

**Constraints:**
- Exit code always 0 (shadow mode, non-blocking)
- Status always "PASS" (no failures emitted by this gate)
- Exception messages logged to stderr (not stdout)
- All degradation documented in bundle metadata (truncation, fallbacks used)

**Assumptions:**
- M902-01 gate runner handles missing inputs (provides defaults if needed)
- Prior gates (M902-11, M902-12) emit valid violations (validation at gate runner level)
- Git command is available and repo is in valid state

**Scope:** Error handling and edge case behavior only. Implementation responsibility in Requirement 01.

### 2. Acceptance Criteria

1. **Edge case catalog enumerated:** 20+ edge cases identified with expected behavior
2. **Graceful degradation:** No silent failures; all fallback behaviors documented
3. **Logging:** All warnings logged at appropriate level (WARNING, ERROR as needed)
4. **Output guarantee:** Gate always returns valid success record (status: PASS)
5. **Metadata tracking:** Fallbacks documented in bundle metadata (e.g., fallback_used: true)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Fallback behavior masks real issues:** If malformed violations are silently skipped, bugs in prior gates go unnoticed. Mitigation: Log all skipped violations at WARNING level. Tests validate logging.
- **Degradation too aggressive:** If gate skips too much, bundle is nearly empty and useless. Mitigation: Prioritize mandatory sections (code, violations). Skip only non-critical (duplication, observability) when needed.

---

## Non-Functional Requirements

### NFR-01: Performance
- Gate execution (git diff + import graph + bundle assembly) must complete in < 5 seconds for typical changes (10 files, 100+ violations).
- Import graph extraction must complete in < 3 seconds per change (includes 2-hop traversal for all changed files).
- Bundle serialization (json.dumps + file write) must complete in < 500ms.
- Stress test: 100+ file change, 50+ import edges, 100+ violations → target <5s total.

### NFR-02: Reliability
- Gate must not crash on invalid input (produces valid error message and success record with empty bundles).
- Gate must produce deterministic output for identical inputs (byte-for-byte after normalization).
- Gate must not modify any files outside `.semantic_reviews/` directory (read-only except for bundle output).
- Bundle size must be <100KB (enforced via truncation).

### NFR-03: Maintainability
- Gate module must be ≤ 300 lines of code.
- Import graph extraction logic must be ≤ 100 lines (modular helper function).
- Bundle assembly logic must be ≤ 50 lines.
- Test suite must have clear traceability (each test linked to test vector ID).

### NFR-04: Observability
- Gate must log to stderr: gate name, mode, input summary (risk_score, violation count, file count), result status, bundle path, extraction time.
- Bundle output must include `extraction_time_ms` for performance monitoring.
- Bundle output must include `truncation_reason` if truncation occurred (for debugging).
- Gate must include `message` field with human-readable summary (< 300 chars).

### NFR-05: Security
- Bundle must not include secrets (API keys, passwords, tokens) in code hunks or violation messages.
- Gate must not execute arbitrary code from violations (violations are data, not executable).
- Bundle JSON must be human-readable (no encryption, no obfuscation).
- Permissions: bundle files created with mode 0644 (readable by all, writable by owner).

### NFR-06: Correctness
- Bundle JSON must be valid according to schema (all required fields present, types correct).
- Line numbers in code hunks must match original file (preserved from git diff).
- Import graph must not contain duplicate edges (deduplicated by (from, to) tuple).
- Sorted arrays must maintain stable sort order (Python sort is stable).

---

## Risk Register

| Risk ID | Description | Probability | Impact | Mitigation |
|---------|---|---|---|---|
| R1 | Import graph extraction too expensive or cycles infinite-loop | MEDIUM | HIGH | Limit depth to 2 hops, use visited set, timeout 5s per file, fallback (skip import graph if timeout) |
| R2 | Bundle size enforcement hard to achieve (<100KB with many files) | MEDIUM | MEDIUM | Prioritize extraction (code > imports > tests), truncate code to 50 lines, omit non-critical sections if >100KB, warn if truncated |
| R3 | Test code linking heuristic fails (test file doesn't exist) | MEDIUM | MEDIUM | Use multiple strategies (prefix-match, import analysis, grep), log all strategies, fallback empty array (not error) |
| R4 | CODEOWNERS file missing or malformed | LOW | LOW | Fallback to directory-based heuristic, document heuristic in spec, test both cases |
| R5 | Git diff parsing fails (non-UTF8 files, binary diffs) | LOW | MEDIUM | Filter for text files only, handle decode errors gracefully, skip file, log WARNING, never fail extraction |
| R6 | Determinism not preserved (timestamps, dict ordering) | MEDIUM | MEDIUM | Exclude timestamps from bundle logic, sort arrays alphabetically, use json.dumps(sort_keys=True), validate determinism in tests |
| R7 | Prior gate outputs missing or malformed | MEDIUM | MEDIUM | Spec defines input contract (violations schema), treat malformed as skip-with-WARN, code defensively (try-except on each violation) |
| R8 | Performance degradation with large repos (100+ files) | LOW | MEDIUM | Lazy extraction (process only changed files + 2-hop neighbors), cache import graph, stress test with 100+ files, target <5s |
| R9 | Bundle consumed by Stage 6 (agent) but format incompatible | LOW | HIGH | Spec freezes JSON schema in collaboration with M903 (agent review gate), frozen schema matches agent expectations, format versioned |
| R10 | Security: secrets in code hunks | LOW | CRITICAL | Filter code hunks for common secret patterns (API keys, passwords), never include credentials, tests validate secrets not leaked |

---

## Deferred Scope (M903+)

- **Orchestration and routing:** Which changes trigger bundling (risk_score >= 6 threshold decision, per-PR vs per-commit) deferred to orchestrator (M903)
- **Agent invocation:** Bundle delivery to semantic agent review (M902-14 Stage 6) deferred to M903
- **Bundle archival and trending:** Long-term bundle storage, statistical analysis, trending deferred to M903 future
- **Multi-language import extraction:** Python-centric in this spec; JavaScript, GDScript, Java import analysis deferred to M903+
- **Semantic code analysis:** AST-level feature extraction, complexity scoring beyond imports deferred to M904+
- **Machine learning-based refinement:** ML-based heuristic tuning, signal weighting deferred to M905+
- **Interactive agent feedback:** Bundle clarifications, agent follow-up questions deferred to M906+
- **Bundle versioning and change tracking:** Bundle history, delta bundles deferred to M907+

---

## Assumptions

1. **Prior gate outputs conform to M902-01 schema:** M902-12 risk scoring returns dict with violations array, risk_score (0–100), risk_band ("EXIT"/"WARN"/"ESCALATE"). Violations array has rule_id, severity, file, line, message fields.
2. **Git diff provides staged changes:** `git diff --cached` is available locally. Gate analyzes staged changes by default (alternative: commit range deferred to M903).
3. **CODEOWNERS file optional:** GitHub-standard CODEOWNERS file (owner_name path_pattern) parsed if exists. If not found, directory-based heuristic used (asset_generation/python → python-team, etc.).
4. **Import extraction is Python-centric:** ast.parse() for Python files; regex-based for JavaScript (import/require statements); regex for GDScript (import keyword). Multi-language parsing deferred to M903.
5. **Test code linking via module name matching:** test_foo.py matches foo.py; or tests import module. Heuristic; not 100% accurate but reasonable.
6. **Bundle size <100KB enforced by selective extraction:** Code hunks max 50 lines, import depth max 2 hops, duplication/observability summaries high-level. If still >100KB, truncate non-critical sections. Conservative approach: bundle always succeeds (never fails due to size).
7. **Determinism: no timestamps as decision factors:** Bundles identical for same git state + violations. Extraction time, timestamps logged for observability, not used in bundle logic.
8. **Gate output schema extends M902-01:** Output conforms to M902-01 gate success schema with added fields (risk_score, risk_band, bundle metadata).
9. **Bundling per issue_id:** One bundle per logical change (GitHub PR, issue, branch, or ticket). May span multiple files. Not per-file bundles.
10. **Stage 5 runs after Stage 4:** risk_scoring_check.py completes first; if risk_score >= 6 (ESCALATE), Stage 5 extraction triggered. If <6, skip extraction (optimization deferred to M903 orchestrator).

---

## Clarifying Questions

None. Scope and constraints frozen per execution plan and checkpoint protocol resolutions.

---

## Dependencies

| Dependency | Ticket | Status | Nature |
|---|---|---|---|
| M902-01 (Validation Gate Framework) | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/01_validation_gate_framework.md` | COMPLETE | Hard (gate framework, registry, schema) |
| M902-12 (Risk Scoring System) | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/12_stage_4_risk_scoring_system.md` | COMPLETE | Hard (risk_score input, violations schema) |
| code_governance.md Stages 4–5 | `bot_vault/architecture/code_governance.md` | Reference | Soft (extraction scope, signal definitions) |

**No blocking dependencies remain. M902-01 and M902-12 are COMPLETE.**

---

## File Tree (Post-Implementation)

```
ci/scripts/
├── gates/
│   ├── __init__.py
│   └── semantic_extraction_check.py                # Stage 5 Semantic Extraction Gate (NEW)
└── gate_registry.json                              # Updated with semantic_extraction_check entry

project_board/
├── specs/
│   └── 902_13_semantic_extraction_spec.md          # This spec file
├── checkpoints/
│   └── M902-13/
│       └── 2026-05-19T-specification.md             # Spec checkpoint log (THIS RUN)
└── execution_plans/
    └── M902-13_stage_5_semantic_extraction_and_bundling.md (reference)

tests/ci/
├── test_semantic_extraction_check.py               # Behavioral test suite (Task 2)
└── test_semantic_extraction_check_adversarial.py   # Adversarial test suite (Task 3)

.semantic_reviews/                                  # Generated bundle directory (OUTPUT ARTIFACTS, NOT COMMITTED)
├── <issue_id>.json                                 # Example: PR-42.json, M902-13.json
└── ...
```

---

## Spec Exit Gate Checklist

This spec is ready for the spec exit gate (validation by `ci/scripts/spec_completeness_check.py`) when:

- [x] Overview section explains gate purpose and governance pipeline stage
- [x] Requirement 01: Gate module, registry entry, importability, function signature, exception handling, determinism
- [x] Requirement 02: Extraction scope (11 mandatory sections), bundle JSON schema (20+ fields with type/required/description), determinism rules
- [x] Requirement 03: Compression and truncation strategy (priority order, size limits, fallback rules, constraints)
- [x] Requirement 04: Determinism and stability (no timestamps, sorted arrays, JSON serialization, validation rules)
- [x] Requirement 05: Test vector coverage (35 vectors across simple/multi-file/edge cases/determinism/NFR)
- [x] Requirement 06: Edge cases and error handling (20+ cases with expected behavior, graceful degradation, logging)
- [x] Non-functional requirements defined (performance, reliability, maintainability, observability, security, correctness)
- [x] Risk register with 10 identified risks and mitigations
- [x] Dependencies enumerated (hard: M902-01, M902-12; all COMPLETE)
- [x] Clarifying questions resolved via checkpoint protocol
- [x] Deferred scope explicitly listed (M903+: orchestration, agent invocation, archival, multi-language, ML)
- [x] All 7 ticket ACs mapped to requirements and test vectors
- [x] Assumptions stated explicitly (prior gates conform to M902-01, git available, CODEOWNERS optional, import Python-centric, test linking heuristic, size <100KB enforced, determinism via sorted serialization, bundling per issue_id, Stage 5 runs after Stage 4)
- [x] No ambiguities remain (all design decisions frozen in spec and checkpoint log)
- [x] File tree and output structure specified
- [x] No gameplay changes (governance tooling only)
- [x] No new dependencies introduced (pure Python stdlib + git)
- [x] Spec is deterministic and actionable by Test Designer and Implementation agents

**SPECIFICATION FROZEN (v1.0) AND READY FOR TEST_DESIGN.**

---

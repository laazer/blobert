# M902-13 Execution Plan: Stage 5 — Semantic Extraction and Bundling

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/13_stage_5_semantic_extraction_and_bundling.md`  
**Plan Version:** 1.0  
**Created:** 2026-05-19  
**Status:** READY FOR EXECUTION

---

## Overview

This execution plan decomposes M902-13 into 7 sequential, testable tasks. The feature implements Stage 5 of the 8-stage governance pipeline: **Semantic Extraction Layer**. This stage builds focused, compressed review bundles from high-risk changes identified by Stage 4 risk scoring, preparing context for Stage 6 agent semantic review.

The gate must:
1. Ingest high-risk change metadata and violations from Stage 4 (risk_scoring_check.py)
2. Extract and organize: changed code hunks (git diff), dependency neighborhoods (1–2 hop imports), ownership assignments (CODEOWNERS), related test code, affected modules, violation summaries
3. Build compressed JSON bundles (< 100KB) keyed by issue_id under `.semantic_reviews/` directory
4. Eliminate: full repo context, unrelated files, generated artifacts (binary, compiled, cache)
5. Produce deterministic, reproducible bundles suitable for agent context window (max 8K tokens of extracted code)
6. Register as `semantic_extraction_check.py` in gate registry
7. Be tested with complex multi-file changes (refactors, circular imports, async violations)

**Key Constraints:**
- Bundle size < 100KB total (enforced by compression of imports/graph, truncation of unrelated code)
- JSON schema documented and validated
- Deterministic output (no timestamps, consistent ordering)
- No external API calls; pure local analysis (git, file I/O, import graph computation)
- Executed after Stage 4 risk scoring; routes to Stage 6 (semantic agent review) only when risk_score >= 6 (ESCALATE band)

**Dependencies:**
- M902-01 (Validation Gate Framework) — COMPLETE
- M902-12 (Risk Scoring System) — COMPLETE
- Code governance Stage 5 section (if exists; reference fallback to Stage 4)
- Git repo state (staged changes or commit range)

**No gating blockers identified.**

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Specification freeze: Bundle schema, extraction scope, compression strategy, test vectors | Spec Agent | Ticket M902-13, M902-01 gate schema, M902-12 risk scoring spec, acceptance criteria, code governance Stage 4–5 sections | Spec file `project_board/specs/902_13_semantic_extraction_spec.md` (requirements 01–07, acceptance criteria, bundle JSON schema, extraction rules for code/imports/ownership/tests, compression rules, test vectors) | M902-01, M902-12, code_governance.md | Spec completeness check passes; all 7 ticket ACs mapped to requirements; bundle schema documented with 20+ fields; extraction scope (diff, imports, tests, ownership) defined; compression strategy (code truncation, import depth limits, artifact exclusion) specified; <100KB enforcement mechanism documented; at least 30 test vectors provided (simple change, refactor, circular import, async violation, multi-file patterns) | Q1: Which import depth (1, 2, or adaptive)? A: 2 hops (direct + transitive) for import graph extraction. Q2: How to extract code hunks (git diff, AST-based, line-range)? A: git diff for staged changes; map hunks to file line ranges; AST-based dependency extraction for Python (ast.parse). Q3: Which test code is "related"? A: Tests in same module or by import match; prefix-match on module name (e.g., test_*.py matching module_*.py). Q4: How to represent ownership (CODEOWNERS file, git blame, hardcoded)? A: CODEOWNERS file if exists (GitHub standard), fallback to directory-based heuristic (e.g., services/ → services-team). Q5: Bundle size limit enforcement? A: Stage code, imports, tests first (priority); truncate or omit non-critical sections (duplication clusters, observability gaps) if >100KB. Q6: Determinism (no timestamps)? A: Exclude timestamp, duration fields; use git commit hash for version tracking, not timestamp. Q7: Should bundling be per-file or per-change? A: Per issue_id (logical change), potentially spanning multiple files. Q8: Deferred: agent invocation logic (M903). Confidence: MEDIUM-HIGH (schema well-defined in ticket; extraction rules new and need validation). |
| 2 | Test Design: Behavioral test suite for semantic extraction gate | Test Designer Agent | Spec file from Task 1 | Test file `tests/ci/test_semantic_extraction_check.py` with 50+ behavioral tests covering: (a) module signature & output schema, (b) simple single-file changes (formatting, comments), (c) multi-file refactors, (d) circular import scenarios, (e) async complexity changes, (f) migration files, (g) ownership assignment accuracy, (h) test code linking, (i) import graph extraction (depth, cycle handling), (j) bundle size validation (<100KB), (k) JSON schema compliance, (l) determinism (artifact ordering), (m) registry integration, (n) error handling (missing CODEOWNERS, git errors) | Task 1 (Spec) | Tests cover all 7 ticket ACs; test vectors from spec (30+ minimum); deterministic (fixtures for git state, CODEOWNERS, imports); syntax valid; all tests passing locally before handoff; bundle size assertions; schema validation using jsonschema library | Will mock git commands (git diff, git log) and file I/O using fixtures. Import graph will be simulated with static import data. Reference M902-12 and M902-11 test suites for structure and patterns. Focus on bundle contents (code hunks, imports, tests) and size enforcement. Confidence: MEDIUM (import graph extraction new; test code linking heuristic needs validation). |
| 3 | Test Break: Adversarial & mutation test suite for semantic extraction | Test Breaker Agent | Behavioral test suite from Task 2 | Additional test file `tests/ci/test_semantic_extraction_check_adversarial.py` with 40+ adversarial tests covering: (a) bundle size boundary cases (99KB pass, 101KB truncate), (b) circular import loops (A→B→A), (c) deep import chains (A→B→C→D→E, truncate at depth 2), (d) missing CODEOWNERS (fallback to heuristic), (e) empty code hunks, (f) very large files (>10K lines, extract only relevant hunks), (g) binary files in diff (skip gracefully), (h) test code not found, (i) code with special characters/unicode, (j) determinism (same input same output), (k) malformed git diff, (l) schema mutation edge cases (null fields, missing required), (m) performance stress (100+ files, 1000+ import edges), (n) assumption validation | Task 2 (Behavioral tests) | 40+ adversarial tests; all tests passing; designed to catch size enforcement bugs, import cycle handling, truncation edge cases, schema violations; deterministic; no external dependencies | Will focus on boundary conditions (size thresholds, depth limits) and schema compliance. Will create synthetic import graphs with cycles and long chains. Reference M902-12 adversarial suite for strategy. Confidence: MEDIUM. |
| 4 | Implementation: Python module `semantic_extraction_check.py` with diff parsing, import graph analysis, bundle assembly | Implementation Agent | Spec from Task 1, tests from Tasks 2–3 | Module `ci/scripts/gates/semantic_extraction_check.py` with: (a) `run(inputs: dict) -> dict` function matching M902-01 gate schema, (b) git diff parsing (git diff --cached or --diff-filter), (c) import graph extraction (1–2 hops from changed files), (d) test code discovery (prefix-match on module name + import graph), (e) CODEOWNERS parsing (if exists), (f) code hunk extraction with line-range trimming (max 50 lines per hunk, total <100KB), (g) violation/architecture summary from prior gates, (h) JSON bundle assembly with required fields, (i) bundle writing to `.semantic_reviews/<issue_id>.json`, (j) size enforcement (warn if >100KB, truncate if needed), (k) proper error handling (no bare except), (l) logging per code_governance.md | Tasks 2–3 (tests define contract) | Module created; all tests pass (100% pass rate); code review passes (no bare except, proper logging); bundle assembly correct; size enforcement works; JSON schema matches spec; bundling deterministic (same input same output); output conforms to M902-01 gate schema | Will structure as helper functions: _parse_git_diff(), _extract_imports(file_path, depth), _find_related_tests(module), _load_codeowners(), _build_bundle(). Will use ast.parse for Python import extraction. Prior gates (M902-12, M902-11) output violations with rule_ids and architecture scores; this stage augments bundles with those. Conservative: if import graph fails, include code hunks only (not a failure). Confidence: MEDIUM (complex graph traversal; import extraction needs Python-specific handling). |
| 5 | Static QA: Code review, linting, type checking | Spec/Code Review Agent | Implementation from Task 4 | Code review report; module passes all linters (ruff, mypy, wemake rules); no bare except; proper logging; gate schema compliance validated; import graph logic verified against spec; bundle size enforcement spot-checked | Task 4 (Implementation) | No ruff/mypy/wemake violations; no bare except; proper exception propagation; code follows M902-11/M902-12/M902-09 patterns; gate schema matches M902-01; import depth limits enforced (2 hops); bundle size check correct | Reference M902-12 static QA for code review checklist. Verify: (1) import graph depth ≤ 2, (2) bundle size assertion on sample bundles, (3) test code linking heuristic spot-checked, (4) JSON schema field presence/types. Confidence: MEDIUM-HIGH (pattern well-established; graph logic new). |
| 6 | Integration: Register gate in `gate_registry.json`, verify orchestration path | Integration Agent | Module from Task 4 + Static QA from Task 5 | Updated `ci/scripts/gate_registry.json` with entry for `semantic_extraction_check` gate (stage: 5, blocking: false, shadow: true, required_inputs for risk_score threshold); gate is callable by orchestrator; integration tests pass | Tasks 4–5 (implementation & review) | Registry entry created with correct metadata; gate is importable; orchestrator can call `run({violations: [...], risk_score: 7, ...})` (high-risk change) and receive valid JSON bundle; integration tests pass (<5s execution time per test); bundle written to `.semantic_reviews/<issue_id>.json`; no bundling for low-risk changes (risk_score < 6) | Will follow gate_registry.json schema from M902-12 (stage, blocking, shadow, description). semantic_extraction_check is non-blocking (shadow=true); status always PASS. Optional: gate may emit SKIP if risk_score < 6 (low-risk, no extraction needed) or FAIL if bundle >100KB after truncation (should not happen per design). Confidence: MEDIUM-HIGH. |
| 7 | Acceptance Gatekeeper: Verify all 7 ticket ACs met, advance to COMPLETE | Spec Agent / Planner Agent | All deliverables from Tasks 1–6 | Gatekeeper report; ticket Stage advanced to COMPLETE; Revision incremented; Last Updated By set; all 7 ACs verified: (AC1) extracts code, dependencies, tests, ownership, violations, (AC2) generates bundles <100KB in .semantic_reviews/, (AC3) includes file diffs, test code, affected modules, ownership, violation summaries, (AC4) excludes full repo, unrelated files, generated artifacts, (AC5) implemented as semantic_extraction_check.py, (AC6) JSON schema documented, (AC7) tested with complex multi-file changes | Tasks 1–6 (all prior work) | All 7 ACs from ticket verified; implementation COMPLETE; tests passing (100%); code review clean; registry integrated; bundles generated for sample high-risk changes; ticket Stage=COMPLETE | Gatekeeper must validate each AC: (1) spec lists extraction scope (code/deps/tests/ownership/violations), (2) test vectors show <100KB bundles, (3) bundle structure has all required fields (file_diffs, related_tests, ownership, violations summary), (4) spec explicitly excludes unrelated files and artifacts, (5) module path correct (ci/scripts/gates/semantic_extraction_check.py), (6) schema documented in spec or code, (7) test suite covers multi-file refactor + circular import + async scenarios. Use M902-12 gatekeeper log as pattern. Confidence: MEDIUM. |

---

## Notes

### Dependencies & Ordering

- **Strict sequential:** Tasks must complete in order (1 → 2 → 3 → 4 → 5 → 6 → 7)
- **Task 1 (Spec)** requires reading M902-01 gate schema, M902-12 risk scoring spec, and code_governance.md Stage 4–5 sections
- **Tasks 2–3 (Tests)** can be done in parallel after Task 1 completes (though sequenced 2 → 3 per standard workflow)
- **Task 4 (Implementation)** depends on Tasks 2–3 for test contracts
- **Task 5 (Static QA)** depends on Task 4
- **Task 6 (Integration)** depends on Tasks 4–5
- **Task 7 (Acceptance)** depends on all prior tasks

### Semantic Extraction Scope (From Ticket AC-1, AC-2, AC-3)

The gate must extract and bundle:
1. **Changed code:** Git diff hunks from staged changes (or commit range), line-range preserved, max 50 lines per hunk; total <100KB
2. **Dependency neighborhood:** 1–2 hops of imports (direct + transitive) from changed files; include affected modules and class/function signatures (lightweight AST)
3. **Ownership graph:** CODEOWNERS file (if exists) mapped to changed files; team/owner assignments; or directory-based heuristic (e.g., asset_generation/web → web-team)
4. **Related test code:** Test files matching changed modules by name (test_*.py for module_*.py); or tests that import changed modules; code snippets (function signatures, setup/teardown)
5. **Affected modules:** List of modules touched by change; module-level docstrings and exports
6. **Violation summaries:** Violations from prior gates (M902-11 architecture, M902-12 risk scoring); structured as violations array with rule_id, severity, message
7. **Duplication clusters:** If detected by prior gates; high-level summary (files involved, line count), not full code
8. **Architecture violations:** Cross-layer imports, circular dependencies (brief summary with affected modules)
9. **Async boundaries:** Async/sync context mismatches (if detected)
10. **Observability gaps:** Missing logging/audit (if detected)
11. **Suppression history:** blobert-ignore comments in changed code

**Excluded (per AC-4):**
- Full repo context (no commit history, blame, large traversals)
- Unrelated files (only files touched by change or imports from touched files)
- Generated artifacts (compiled .pyc, .class, images, .glb, dist/, build/, cache files)
- Dependencies not in import graph (e.g., random npm packages)
- Sensitive data (secrets, credentials, large test data blobs)

### Bundle JSON Schema (From Spec Task 1 output)

Example bundle at `.semantic_reviews/<issue_id>.json`:
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
    "categories": ["runtime-code", "tests"]
  },
  "code_hunks": [
    {
      "file": "asset_generation/python/src/model_registry/service.py",
      "lines": [45, 80],
      "hunk": "def get_model(model_id: str) -> Model:\n  ...",
      "language": "python",
      "violation_rule_ids": ["AS-01", "OB-01"]
    }
  ],
  "import_graph": {
    "changed_files": ["model_registry/service.py"],
    "direct_imports": [
      {"from": "model_registry.service", "to": "fastapi", "type": "external"},
      {"from": "model_registry.service", "to": "core.config", "type": "internal"}
    ],
    "affected_modules": [
      {
        "module": "model_registry.service",
        "exports": ["get_model", "list_models"],
        "docstring": "Registry service layer..."
      }
    ],
    "depth_limit_2_hops": true
  },
  "ownership": {
    "assignments": [
      {"file": "model_registry/service.py", "owner": "team:backend", "source": "CODEOWNERS"}
    ],
    "codeowners_available": true
  },
  "related_tests": [
    {
      "file": "tests/model_registry/test_service.py",
      "relevant_tests": ["test_get_model", "test_list_models"],
      "code_snippet": "def test_get_model():\n  ..."
    }
  ],
  "violations_summary": {
    "from_prior_gates": [
      {"gate": "architecture_enforcement", "rule_id": "AS-01", "severity": "HIGH", "message": "Blocking I/O in async context"},
      {"gate": "risk_scoring", "rule_id": "OB-01", "severity": "MEDIUM", "message": "Missing audit logging"}
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
    "schema_version": "1.0"
  }
}
```

**Schema fields (20+ total):**
- version (string): bundle schema version
- issue_id (string): GitHub issue/PR number or internal ticket id
- risk_score (number): from M902-12 (0–100)
- risk_band (string): from M902-12 (EXIT, WARN, ESCALATE)
- change_summary (object): files_changed, lines_added/deleted, categories (docs/tests/runtime/etc)
- code_hunks (array): file, lines [start, end], hunk (code snippet), language, violation_rule_ids
- import_graph (object): changed_files, direct_imports, affected_modules, depth_limit_2_hops flag
- ownership (object): assignments (file → owner), codeowners_available boolean
- related_tests (array): file, relevant_tests (test names), code_snippet
- violations_summary (object): from_prior_gates array, violation_count, risk_signals list
- metadata (object): git_commit_hash, staged_changes bool, bundle_size_bytes, extraction_time_ms, compressed bool, schema_version

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Import graph extraction too expensive or cycles infinite-loop | MEDIUM | HIGH | Limit traversal depth to 2 hops. Use visited set to detect cycles. Timeout import extraction at 5s per file. Fallback: skip import graph if timeout. Test with circular imports (A→B→A). |
| Bundle size enforcement hard to achieve (<100KB with many files) | MEDIUM | MEDIUM | Prioritize extraction (code > imports > tests > metadata). Truncate code hunks to 50 lines max. Omit non-critical sections if >100KB. Warn if truncation happens. Test size limits in Task 3. |
| Test code linking heuristic fails (test file doesn't exist or uses different naming) | MEDIUM | MEDIUM | Use multiple strategies: (1) prefix-match (test_foo.py for foo.py), (2) import analysis (test imports module), (3) grep for module name in test directory. Log all strategies used. Fallback: no related tests found (empty array, not error). |
| CODEOWNERS file missing or malformed | LOW | LOW | Fallback to directory-based heuristic (e.g., asset_generation/python/ → python-team, scripts/ci/ → ci-team). Document heuristic in spec. Test both cases. |
| Git diff parsing fails (non-UTF8 files, binary diffs) | LOW | MEDIUM | Use git diff --cached to get staged changes. Filter for text files only (skip .png, .glb, .pyc). Handle decode errors gracefully (log WARNING, skip file). Never fail extraction due to git error; degrade gracefully. |
| Determinism not preserved (timestamps, dict ordering, sorted lists) | MEDIUM | MEDIUM | Exclude timestamp/duration from bundle JSON (include only in metadata for reference, not as decision factor). Sort violations and imports alphabetically. Use json.dumps with sort_keys=True. Validate determinism in Task 3. |
| Prior gate outputs missing or malformed | MEDIUM | MEDIUM | Spec Task 1 must define input contract (what violations look like, what fields required vs optional). Conservative: treat as empty violations (no failure). Log all input parsing. Code defensively (try-except with fallback). |
| Performance degradation with large repos (many files, complex import graphs) | LOW | MEDIUM | Implement lazy extraction (process only changed files + 2-hop neighbors, not whole repo). Cache import graph computation. Stress test in Task 3 with 100+ files. Target <5s per extraction. |
| Semantic bundle consumed by Stage 6 (agent) but format not compatible | LOW | HIGH | Spec Task 1 must define output format in collaboration with Stage 6 requirements (M902-14 agent semantic review gate). Assume agent expects JSON with code hunks, imports, ownership, violations. Format frozen in spec. |

### Assumptions

1. **Prior gate outputs conform to M902-01 schema:** M902-12 returns dict with violations array, risk_score, risk_band. This gate parses that dict and extracts violation data.
2. **Git diff provides staged changes:** run() receives diff or git is available locally. Stage 5 analyzes staged changes (git diff --cached) or specific commit range if provided.
3. **CODEOWNERS file optional:** If exists, parsed as `owner_name file_pattern` per GitHub standard. If not, use directory-based heuristic.
4. **Import graph extraction is Python-centric:** Use ast.parse for Python files. Skip or lightweight for other languages (JS: ESLint import plugin; GDScript: simple regex for import statements).
5. **Test code linking via module name matching:** test_foo.py matches foo.py; or via import graph (test imports module). Not 100% accurate, but reasonable heuristic.
6. **Bundle size < 100KB enforced by selective extraction:** Code hunks truncated to 50 lines; import graph depth=2; duplication/observability summaries high-level only. If still >100KB, truncate non-critical sections.
7. **Determinism: no timestamps, consistent ordering:** Bundles identical for same input (git state, violations). Timestamps logged for reference, not used in bundle comparison.
8. **Gate output schema from M902-01:** Output extends M902-01 gate success schema with risk_score, risk_band, bundle_path, change_summary, violations_summary fields.
9. **Bundling per issue_id:** One bundle per logical change (GitHub PR, issue, ticket). May span multiple files. Not per-file bundles.
10. **Stage 5 runs after Stage 4:** risk_scoring_check.py runs first; if risk_score >= 6 (ESCALATE), Stage 5 extraction triggered. If risk_score < 6, skip extraction (no high-risk bundle needed).

### Deferred Scope (M903+)

- Orchestration and routing decisions based on bundle generation (which changes trigger extraction)
- Agent semantic review invocation and bundle consumption (M902-14 and beyond)
- Interactive agent feedback on bundles (clarifications, refinements)
- Bundle archival and trending analysis
- Machine learning-based extraction heuristic refinement
- Multi-language import graph extraction (beyond Python)
- Semantic code analysis (AST-level feature extraction, not just imports)
- Bundle versioning and change tracking

---

## File Paths (Source of Truth)

**Input files:**
- Ticket: `/Users/jacobbrandt/workspace/blobert/project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/13_stage_5_semantic_extraction_and_bundling.md`
- Gate framework (M902-01): `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md`
- Risk scoring spec (M902-12): `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_12_risk_scoring_spec.md`
- Code governance: `/Users/jacobbrandt/workspace/blobert/bot_vault/architecture/code_governance.md` (Stage 4–5 sections)
- Reference implementation (M902-12): `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/risk_scoring_check.py`
- Reference tests (M902-12): `/Users/jacobbrandt/workspace/blobert/tests/ci/test_risk_scoring_check.py`, `test_risk_scoring_check_adversarial.py`
- Gate registry: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gate_registry.json`

**Output files:**
- Spec: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_13_semantic_extraction_spec.md` (Task 1)
- Behavioral tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_semantic_extraction_check.py` (Task 2)
- Adversarial tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_semantic_extraction_check_adversarial.py` (Task 3)
- Implementation: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/semantic_extraction_check.py` (Task 4)
- Registry: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gate_registry.json` (Task 6, update only)
- Bundles (generated): `/Users/jacobbrandt/workspace/blobert/.semantic_reviews/<issue_id>.json` (output artifacts, not committed)

---

## Execution Readiness Checklist

- [x] All hard dependencies (M902-01, M902-12) are COMPLETE
- [x] Soft dependencies (code_governance.md) readable
- [x] Ticket acceptance criteria clearly stated (7 ACs)
- [x] Scope deferred and assumptions documented
- [x] Each task is small, independent, and testable
- [x] Input/output for each task specified
- [x] Success criteria objectively verifiable
- [x] Risk register identifies blockers and mitigations
- [x] File paths absolute and verified in repo
- [x] No blocking ambiguities; questions resolved in assumptions

**Plan is ready for Spec Agent (Task 1).**

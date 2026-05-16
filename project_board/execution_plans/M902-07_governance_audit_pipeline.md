# EXECUTION PLAN: M902-07 Governance Audit Pipeline and Baseline

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/07_governance_audit_pipeline_and_baseline.md`

**Created:** 2026-05-16

**Planner:** Planner Agent

**Status:** Ready for Spec Agent

---

## Project Summary

Build a governance audit pipeline that:

1. Invokes the existing static analysis gate (M902-02, COMPLETE) to scan the repo.
2. Clusters violations by rule + path prefix to reduce noise.
3. Maintains `.governance-baseline.json` with expiration, ownership, rationale, and rule_id metadata.
4. Detects new violations (outside baseline) and generates remediation reports.
5. Documents baseline update policy and audit event metadata integration.

**Key dependencies:** M902-01 (gate framework, COMPLETE) and M902-02 (static analysis tooling, COMPLETE).

---

## Design Decisions (Frozen)

All decisions documented in scoped checkpoint log at `project_board/checkpoints/M902-07/2026-05-16T00-00-00Z-planning.md`.

| # | Question | Decision | Confidence | Rationale |
|---|----------|----------|------------|-----------|
| 1 | Audit reuse vs. separate pipeline? | Reuse M902-02 gate via gate runner wrapper | HIGH | Preserves investment in static analysis tooling; avoids duplication |
| 2 | Baseline granularity? | Rule + path prefix (e.g., `ruff:F401:asset_generation/python/src/`) | MEDIUM-HIGH | Reduces baseline size, easier to reason about; fine-grained fingerprints deferred to M903 |
| 3 | Expiration policy? | Absolute ISO 8601 dates per entry; optional (no expiration = permanent) | MEDIUM | Reasonable default; enforcement logic in M903 can adjust if needed |
| 4 | Ownership model? | Free-text string (email, team name); no validation enforcement in this ticket | MEDIUM | Simple, extensible; enforcement/notification deferred to M903 |
| 5 | Baseline schema validation? | Yes: JSON Schema at `project_board/schemas/governance-baseline-schema.json` | HIGH | Basic hygiene; prevents silent corruption |
| 6 | Remediation ticket generation? | Audit generates markdown report; ticket creation deferred to M903 | HIGH | Ticket says "outputs markdown snippets"; automation is downstream integration |

---

## Tasks (12 Sequential Specification + Implementation)

All tasks are ordered with explicit dependencies. Each task is small enough for one agent run.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write comprehensive technical specification for audit pipeline architecture, baseline schema, clustering logic, and integration with gate framework. Freeze all design ambiguities. | Spec Agent | Ticket acceptance criteria, M902-02 gate schema, design decisions (frozen above), CLAUDE.md guardrails. | Specification document at `project_board/specs/M902-07_audit_pipeline_spec.md` with FR1–FR8 (audit command, clustering, baseline schema, diff detection, remediation generation, policy docs, event metadata, operator guide), NFR1–NFR3 (determinism, performance, safety), risk taxonomy, assumptions/decisions frozen. | None (parallel start) | Spec passes `spec_completeness_check.py --type generic` with all required sections. All design decisions documented with rationale. Ambiguity resolutions checkpointed with confidence levels. Integration with gate_runner.py and gate schema clearly defined. Clustering algorithm (grouping criteria) specified. | Assumption: Reusing gate runner is viable and gate output is stable (M902-02 spec guarantees this). Assumption: Baseline schema can be validated with jsonschema library (standard). Assumption: Rule identifiers are stable (ruff:F401, etc.). |
| 2 | Audit the existing static analysis gate (M902-02) and gate framework (M902-01) to document: gate runner CLI, JSON schema for violations, tool-to-rule-id mapping, and integration points. Create audit document for Spec Agent. | Spec Agent | M902-02 implementation at `ci/scripts/gates/static_analysis_check.py`, M902-01 gate runner at `ci/scripts/gate_runner.py`, gate registry at `ci/scripts/gate_registry.json`, gate schema fixtures. | Integration audit document with: (1) gate runner CLI interface (arguments, exit codes, JSON output structure), (2) static analysis gate violation schema (rule_id, file, line, severity, message fields), (3) tool→rule_id mapping (ruff→ruff:Exxx, mypy→mypy:type-x, eslint→eslint:xxx, etc.), (4) integration points (how audit will invoke gate runner, how to extract violations, how to wire metadata). Reference paths and schema examples. | Task 1 | Audit document includes concrete code examples (gate runner invocation, sample JSON output, schema validation). Tool rule ID mapping is comprehensive and matches actual gate implementation. Integration points are clear and actionable for implementation agent. | Assumption: M902-02 gate output is JSON with fields matching gate schema (validated). Risk: Tool outputs may vary; baseline may need to normalize rule IDs across tools (e.g., treating ruff:E501 and pylint:line-too-long as equivalent). |
| 3 | Design and document the baseline schema (JSON Schema format) with structure: rule_id, path_prefix, expires_at (optional ISO 8601), owner (string), rationale (string), created_at (ISO 8601), created_by (string). Include 3–5 example baseline entries covering Python, TypeScript, and Godot. | Spec Agent | Design decisions from Task 1, tool rule ID mapping from Task 2, JSON Schema best practices. | Schema definition at `project_board/schemas/governance-baseline-schema.json` with: (1) root object: `entries[]` array, `metadata` object (version, last_updated, audit_host, audit_commit_sha); (2) entry object: rule_id, path_prefix, expires_at (optional), owner, rationale, created_at, created_by, suppression_justification (optional); (3) constraint rules (rule_id required, path_prefix regex pattern, ISO 8601 dates); (4) 5 example entries in `examples.json` showing Python/TS/Godot/jscpd violations; (5) description of immutability policy (baseline entries are append-only; updates require human approval or second-reviewer gate in M903). | Task 1, Task 2 | Schema is valid JSON Schema (schema-of-schema validates). All fields match spec requirements (rule_id, owner, expires_at, rationale). Example entries are realistic and cover tool diversity. Schema documentation explains immutability and governance. | Assumption: jsonschema library is available in Python 3.11+ (standard). Assumption: Path prefixes use forward slashes and regex patterns (e.g., `asset_generation/python/src/.*`). Assumption: Expiration dates are in UTC (Z suffix). |
| 4 | Design clustering algorithm: group violations by (rule_id, path_prefix_cluster) where path_prefix_cluster is derived by stripping N trailing path components (e.g., file basename) until a parent directory reaches a configured depth limit. Document clustering examples and edge cases. | Spec Agent | Spec from Task 1, violation examples from gate implementation, repo directory structure (asset_generation/python/src/, asset_generation/web/frontend/src/, scripts/, etc.). | Algorithm specification document with: (1) grouping logic (e.g., rule_id + top 2 parent dirs for Python files, top 1 for TypeScript, etc.); (2) depth tuning rationale (cluster depth = 2 for backend, 2 for frontend, 1 for Godot scripts); (3) example clustering on 20+ sample violations from different tools (5 ruff, 5 mypy, 5 eslint, 5 jscpd); (4) edge cases (single-file violations, deeply nested paths, generated files, cross-tool rule IDs); (5) pseudocode for clustering algorithm (assume dict(rule_id + cluster_key) → violations[]). Output in `project_board/specs/M902-07_clustering_algorithm.md`. | Task 1, Task 2 | Algorithm is deterministic and reproducible. Clustering examples show realistic remediation bundles (5–15 violations per cluster, suitable for one backlog ticket). Edge cases are handled (generated files not clustered separately, symlinks resolved, etc.). Depth tuning is documented with rationale. | Assumption: Repo structure is stable and clustering depth can be tuned per language (may need M903 refinement). Assumption: Generated files are excluded from analysis (by gate, so clustering does not see them). Risk: Clustering may produce bundles that are too large (>15) or too small (<3); M903 can add auto-tuning. |
| 5 | Design baseline diff detection logic: how to identify "new violations" (not in baseline), "expired violations" (expiration date passed), and "remediated violations" (in baseline but not in latest scan). Specify decision rules for audit status (PASS, WARN, FAIL). | Spec Agent | Baseline schema from Task 3, clustering algorithm from Task 4, spec from Task 1, mode policy (shadow vs blocking). | Diff detection specification document with: (1) violation matching logic (a new violation matches if rule_id and path_prefix_cluster both match a baseline entry); (2) new violation detection (violation not in baseline OR rule_id not in baseline at all → NEW); (3) expired violation handling (expiration_date < now → EXPIRED, treated as if baseline entry is void); (4) remediated violation handling (violation was in baseline but not in latest scan → REMEDIATED); (5) audit status mapping: PASS = no new violations, WARN = expired violations present (advisory), FAIL = new violations present (only in blocking mode, deferred to M903); (6) structured output (JSON with new[], expired[], remediated[], status, summary message). Example diff scenarios in `project_board/specs/M902-07_baseline_diff_spec.md`. | Task 3, Task 4 | Diff logic is deterministic and handles all 4 cases (new, expired, remediated, no change). Status mapping aligns with gate framework shadow/blocking modes (M902-01 schema). Output examples show realistic audit results. Edge cases documented (empty baseline, empty scan, rule ID changes, path normalization). | Assumption: Baseline entries are immutable (no merge/conflict on updates; only human approval adds entries). Assumption: Expiration dates are non-negotiable once set (no auto-extend). Assumption: Path matching is exact (no fuzzy matching). Risk: Path normalization may differ across platforms (Windows vs Linux slashes); M903 can standardize. |
| 6 | Create unified audit command specification: `ci/scripts/audit.py` (or equivalent) that: (1) invokes gate runner with specified flags, (2) parses JSON violations, (3) loads baseline from `.governance-baseline.json`, (4) clusters violations, (5) detects baseline diff, (6) generates audit report (JSON + Markdown), (7) outputs remediation ticket snippets. Spec input/output contract, CLI flags, and exit codes. | Spec Agent | Specs from Tasks 1–5, gate runner interface from Task 2, gate registry, CLAUDE.md patterns (command structure, exit codes, logging). | Audit command specification at `project_board/specs/M902-07_audit_command_spec.md` with: (1) CLI interface (`audit.py --mode shadow/blocking --baseline-path ./.governance-baseline.json --output-dir ./ci/artifacts/ --upstream-agent=Implementation`); (2) invocation sequence (gate runner → JSON parse → baseline load → cluster → diff detect → report generate); (3) output schema (JSON report at `ci/artifacts/audit-report-<timestamp>.json` with violations[], clusters[], baseline_diff, status, summary); (4) markdown report (remediation_tickets[] with markdown snippets suitable for backlog); (5) exit codes (0=PASS, 1=FAIL new violations in blocking mode, 2=config error); (6) error handling (missing baseline file → create empty, missing gate runner → fail with clear message, invalid JSON → skip tool with warning). (7) integration with gate runner metadata schema (M902-01). Pseudocode for main flow. | Task 1–5 | CLI interface matches repo conventions (Taskfile args, gate runner patterns). Output schema is compatible with M902-01 gate framework (or documented as separate artifact). Exit codes are clear and actionable. Error handling covers all failure modes. Report generation examples show readable markdown for backlog. | Assumption: Gate runner is idempotent and can be called multiple times safely. Assumption: Baseline file path is configurable (default `.governance-baseline.json` in repo root). Assumption: Output directory (ci/artifacts/) is gitignored (documented separately). Assumption: Markdown tickets should be human-readable but not auto-created. |
| 7 | Design metadata wiring: define which audit event fields integrate with M902-04 handoff metadata (audit_timestamp, audit_violations_count, audit_clusters, audit_status, baseline_entries_expired). Specify metadata schema extension and gate runner integration points. | Spec Agent | M902-04 metadata schema (v0.2.0 at project_board/specs/902_04_metadata_schema.json), audit command spec from Task 6, gate runner wiring (ci/scripts/gate_runner.py). | Metadata extension specification at `project_board/specs/M902-07_metadata_integration_spec.md` with: (1) new metadata fields (audit_timestamp, audit_violations_count, audit_clusters_count, audit_status, baseline_entries_expired_count, audit_report_path); (2) field definitions (types, allowed values, units); (3) gate runner integration (how audit gate injects metadata into gate-result JSON, matches M902-01 schema); (4) event log integration (ci/scripts/audit_log.py from M902-04; audit events include all new fields); (5) example metadata records showing integration. (6) shadow mode behavior (metadata still emitted, status = PASS even with new violations in shadow). Version number (v0.3.0 if extending 902-04 schema, or leave as separate contract). | Task 1, Task 6, M902-04 COMPLETE | Metadata fields are useful for dashboards/observability (count of violations, expiration status). Integration with gate runner is clear (no schema conflicts, fields are additive). Event log examples show complete audit context. M903 blocking enforcement can consume these fields directly. | Assumption: M902-04 schema is stable and allows extensions. Assumption: Gate runner can pass structured metadata through. Assumption: Audit event logging does not require a separate database (JSON Lines in ci/artifacts/ is sufficient). |
| 8 | Write comprehensive operator guide documenting: how to run audit locally, interpret audit reports, add baseline entries (manual JSON edit + TODO for second-reviewer gate in M903), monitor expiration, troubleshoot. Include decision tree for remediation prioritization. | Spec Agent | All specs from Tasks 1–7, M902-02 README (reference for gate documentation style), CLAUDE.md. | Operator guide at `project_board/specs/M902-07_operator_guide.md` with: (1) quick start (cd repo root && task audit or python ci/scripts/audit.py), (2) understanding audit report (status, clusters, violation counts, baseline matches), (3) reading remediation tickets (why they were generated, how to estimate effort), (4) adding baseline entries manually (JSON format, required fields, no secrets, two-reviewer policy in M903), (5) expiration monitoring (how to identify expired entries, renewal process deferred to M903), (6) troubleshooting (missing gate runner, invalid baseline, permission errors), (7) decision tree (new violations = triage by severity and cluster size; expired = renew or delete, (8) integration with CI/pre-push (deferred to M903), (9) examples: 3 real audit scenarios (all PASS, some WARN, some FAIL+new violations). Links to other specs and gate framework docs. | Task 1–7 | Guide is readable by operators without deep knowledge of gate framework. Examples are realistic and reproducible. Troubleshooting section covers 80% of expected issues. Decision tree is actionable. Deferral to M903 (second-reviewer gate, blocking enforcement) is clear. | Assumption: Operators have Python 3.11+ and bash available. Assumption: Repo.lock files (uv.lock, package-lock.json) are stable. Assumption: M903 will add second-reviewer gate; this guide documents manual process. |
| 9 | Write test design document covering behavioral tests: (1) audit on clean checkout produces deterministic JSON, (2) baseline validation (schema check, missing required fields, invalid dates), (3) clustering correctness (same rule + path prefix grouped, different rules separated), (4) baseline diff (new violations detected, expired entries ignored, remediated violations noted), (5) remediation ticket generation (valid markdown, no secrets), (6) integration (gate runner invocation, metadata wiring). 40–60 behavioral tests organized in 5–6 test classes. | Test Designer Agent | All specs from Tasks 1–8, gate schema examples, sample violations from various tools, baseline fixtures. | Test design document at `project_board/test_designs/M902-07_audit_pipeline_test_design.md` with: (1) test matrix (5–6 test classes, ~50 tests total, organized by feature: audit command, baseline validation, clustering, diff detection, remediation generation, integration); (2) test fixtures (synthetic violations from ruff, mypy, eslint, jscpd; baseline fragments; expected JSON outputs); (3) isolation strategy (mock gate runner or use real gate on fixtures; no live tool invocations); (4) traceability (each test mapped to spec requirement FR1–FR8); (5) edge cases and checkpoint decisions (why certain assumptions are made, e.g., path matching is exact, rule IDs are stable). Test class names and method stubs (pytest format). Note expected failures (will be implemented later). | Task 1–8 | Test design covers all major features and edge cases. Fixtures are realistic and deterministic. Tests are isolated (no file system side effects, no external tool dependencies). Traceability matrix is complete. | Assumption: Test fixtures can be generated from spec examples (no live tool runs in test suite). Assumption: Gate runner can be mocked or a simple test binary can be substituted. Risk: Path handling edge cases (symlinks, relative vs absolute) may need additional tests. |
| 10 | Write adversarial test suite (40–50 tests) covering: (1) schema mutations (invalid baseline entries, missing required fields), (2) diff edge cases (empty baseline, empty scan, rule ID changes, path normalization), (3) clustering mutations (path depth off-by-one, rule ID partial matches), (4) baseline corruptions (malformed JSON, secrets in rationale, circular expiration), (5) gate runner failures (missing binary, timeout, invalid JSON output), (6) metadata wiring (missing fields, type mismatches, duplicate events), (7) remediation generation (unicode in paths, very long paths, special characters). Tests should expose weaknesses in implementation. | Test Breaker Agent | Behavioral tests from Task 9, adversarial test design patterns from M902-01/02/03 completed tickets, spec from Task 1–8. | Adversarial test suite at `tests/ci/test_audit_pipeline_adversarial.py` with 40–50 tests organized in 6–8 test classes covering mutation categories above. Each test is designed to expose a likely implementation bug (e.g., off-by-one in path depth, missing null check on expires_at, shell injection in JSON parsing). Test fixtures include: malformed baseline JSON, tool outputs with unusual rule IDs, paths with unicode/spaces/slashes, expiration dates in past/future/invalid formats. Checkpoint decisions logged (why each edge case is tested, confidence level for exposure). Determinism validated (same random seed produces same output; no flaky tests). | Task 9 | Adversarial suite syntax is valid pytest. All 40–50 tests are executable and deterministic. Coverage matrix documents 50+ attack vectors with detection confidence (HIGH/MEDIUM/LOW). Tests expose realistic weaknesses (off-by-one, missing validation, type errors, JSON parsing). | Assumption: Implementation will use standard libraries (json, datetime, pathlib); tests assume these. Risk: Some edge cases (symlink handling, filesystem permissions) may not be testable in CI; M903 can add integration tests. |
| 11 | Implement audit command and baseline module in `ci/scripts/audit.py` and `ci/scripts/baseline.py` (or combined). Integrate with gate runner, implement clustering, baseline diff detection, report generation. Implement baseline schema validation. Wire audit metadata into gate framework (M902-04 event log). All per implementation spec (Task 6), clustering spec (Task 4), baseline schema (Task 3), and metadata integration (Task 7). Code quality per CLAUDE.md (no bare dicts, proper error handling, logging). | Implementation Agent (Generalist) | All specs from Tasks 1–8, gate runner implementation from M902-02, gate registry from M902-01, event logging module from M902-04 (ci/scripts/audit_log.py), test fixtures from Tasks 9–10. | Implementation deliverables: (1) `ci/scripts/audit.py` (300–400 lines) with audit command, gate runner invocation, baseline loading, clustering, diff detection, report generation; (2) `ci/scripts/baseline.py` (150–200 lines) with baseline schema validation, entry management, expiration checking; (3) `.governance-baseline.json` (root level, empty or with 5 grandfathered entries, gitignored or committed based on M903 policy); (4) Test results: all 50 behavioral tests PASS, all 40–50 adversarial tests PASS (or documented with checkpoint decisions for implementation fixes). (5) Code quality: Ruff PASS (E9, F, I), mypy PASS, no bare dicts, proper exception handling, logging on all error paths. (6) Integration: audit gate registered in `ci/scripts/gate_registry.json`, `ci/scripts/gate_runner.py` integration verified, metadata wiring functional. (7) Git commits: one commit per logical unit (audit command, baseline module, gate registry update, etc.). | Task 9–10 (tests must design before implementation), Task 1–8 (specs), M902-01/02/04 (dependencies). | All tests PASS. Code quality checks PASS (ruff, mypy). Audit command executes without errors on clean repo. Baseline validation catches schema violations. Clustering produces expected groupings (verified by tests). Baseline diff correctly identifies new/expired/remediated violations. Report generation creates valid JSON and markdown. Metadata integration does not break existing gate framework (tests for M902-01/04 still PASS). | Assumption: Gate runner output is stable (M902-02). Assumption: Clustering algorithm can be tuned post-implementation (M903). Risk: Performance on large repos (1000+ violations); implementation should log timing and document scan scope. Assumption: Baseline file can be edited manually (JSON); M903 will add UI or git diff tooling. |
| 12 | Update milestone 902 README with audit command documentation, example baseline fragment, remediation workflow diagram, and links to specs. Register `audit` task in Taskfile.yml. Create example baseline with 3–5 grandfathered entries (Python ruff, mypy, TypeScript eslint, jscpd duplication). Operator guide link. Status: shadow mode, enforcement deferred to M903. | Spec Agent (or Generalist) | Implementation from Task 11, all specs from Tasks 1–8, milestone README structure from M902-02 section. | Deliverables: (1) Updated `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` with: audit command syntax (`task audit` or `python ci/scripts/audit.py`), example invocation and output, remediation workflow, baseline entry example, links to specs and operator guide. (2) New Taskfile.yml task `audit` that runs `python ci/scripts/audit.py --mode shadow --upstream-agent Implementation --output-dir ./ci/artifacts/`. (3) Example baseline at `project_board/specs/M902-07_example_baseline.json` (or in `.governance-baseline.json` if commit strategy decided) with 5 entries covering Python/TS/Godot, showcasing rule_id, path_prefix, owner, rationale, expires_at formats. (4) Optional workflow diagram (ASCII or markdown table) showing audit → baseline diff → remediation ticket generation. (5) Status line: "Shadow mode (enforcement deferred to M903)." | Task 11 (implementation stable), Task 1–8 (specs). | README is readable by operators; CLI instructions are copy-paste ready. Baseline example is valid JSON and matches schema. Taskfile task executes without error. Workflow diagram (if included) is clear and matches implementation. Deferral path to M903 is documented. Links to specs are correct (file paths exist). | Assumption: Milestone README is the canonical place for user-facing docs (per M902-02 precedent). Assumption: Taskfile is preferred over inline bash. Assumption: Example baseline is kept in specs dir (not committed as `.governance-baseline.json` in repo root until M903 policy is finalized). |

---

## Summary of Task Structure

**Phase 1: Specification (Tasks 1–8)** — Design and document all aspects of audit pipeline, baseline, clustering, and metadata integration. Outputs are specs, schemas, and operator guide.

**Phase 2: Test Design & Adversarial (Tasks 9–10)** — Write comprehensive test suites (behavioral + adversarial) to validate implementation.

**Phase 3: Implementation (Task 11)** — Build audit command, baseline module, integration with gate framework and event logging.

**Phase 4: Documentation & Registration (Task 12)** — Update milestone README, register Taskfile task, document baseline entry examples.

---

## Gating & Quality Checkpoints

1. **Spec Completeness (after Task 8):** Run `python ci/scripts/spec_completeness_check.py project_board/specs/M902-07_audit_pipeline_spec.md --type generic`. Must PASS before advancing to TEST_DESIGN.

2. **Test Coverage (after Tasks 9–10):** Verify 80+ tests (50 behavioral + 40–50 adversarial) are pytest-discoverable and syntax-valid. Expected failures documented.

3. **Implementation Quality (after Task 11):** Run full test suite. All tests must PASS. Ruff/mypy checks must PASS. diff-cover baseline (if Python tests) must meet threshold (85%+).

4. **Integration (after Task 12):** Verify Taskfile task executes without error. Verify gate_registry.json includes audit gate entry. Verify README documentation is complete and links resolve.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Clustering algorithm produces bundles that are too large/small | MEDIUM | MEDIUM | Algorithm is configurable and can be tuned in M903; tests validate depth settings. |
| Baseline schema is too rigid or too loose | MEDIUM | MEDIUM | Schema design allows optional fields (expires_at) and free-text rationale; tests validate edge cases. |
| Gate runner output format unstable or incompatible | LOW | HIGH | M902-02 is COMPLETE with 83+ tests; gate runner schema is frozen and tested (M902-01). Risk mitigated. |
| Expiration date handling has off-by-one or timezone bugs | MEDIUM | MEDIUM | Adversarial tests cover boundary cases (expiration_date == now, before/after). Spec uses UTC ISO 8601. |
| Path normalization differs across platforms | MEDIUM | LOW | Spec documents forward-slash paths; tests use pathlib for cross-platform. M903 can standardize further. |
| Audit command timeout on large repos | LOW | MEDIUM | Spec documents scan scope (exclude .venv, node_modules, *.glb per CLAUDE.md). Implementation should log timing. |
| Baseline file accidentally contains secrets | MEDIUM | HIGH | Spec explicitly forbids secrets in baseline (rationale field has doc). Pre-commit hook or secret scanning tool can detect (deferred to M903). |
| Missing second-reviewer policy for baseline updates in this ticket | LOW | LOW | Spec documents manual process; deferral to M903 for second-reviewer gate is explicit and documented. |

---

## Success Criteria (Planner View)

- [ ] All 12 tasks are executed in order; each task produces concrete output (specs, tests, code, docs).
- [ ] Specs pass `spec_completeness_check.py --type generic`.
- [ ] 80+ tests (50 behavioral + 40–50 adversarial) are written, pytest-discoverable, and syntax-valid.
- [ ] All implementation tests PASS.
- [ ] Ruff/mypy checks PASS.
- [ ] Audit command is functional on clean repo (deterministic output).
- [ ] Baseline schema validation works (rejects invalid entries).
- [ ] Clustering, diff detection, remediation generation all verified by tests.
- [ ] Metadata integration with M902-04 does not break existing gate framework.
- [ ] Milestone README updated with audit documentation.
- [ ] Taskfile task `audit` registered and executable.
- [ ] Ticket moved to Stage COMPLETE with all acceptance criteria satisfied.

---

## File Paths (Reference)

**Specifications:**
- `project_board/specs/M902-07_audit_pipeline_spec.md` (main)
- `project_board/specs/M902-07_clustering_algorithm.md`
- `project_board/specs/M902-07_baseline_diff_spec.md`
- `project_board/specs/M902-07_audit_command_spec.md`
- `project_board/specs/M902-07_metadata_integration_spec.md`
- `project_board/specs/M902-07_operator_guide.md`
- `project_board/schemas/governance-baseline-schema.json` (new)

**Tests:**
- `project_board/test_designs/M902-07_audit_pipeline_test_design.md`
- `tests/ci/test_audit_pipeline.py` (behavioral, ~50 tests)
- `tests/ci/test_audit_pipeline_adversarial.py` (adversarial, 40–50 tests)

**Implementation:**
- `ci/scripts/audit.py` (new)
- `ci/scripts/baseline.py` (new)
- `ci/scripts/gate_registry.json` (update: add audit gate entry)
- `.governance-baseline.json` (new, root; commit policy TBD in M903)

**Documentation:**
- `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` (update)
- `Taskfile.yml` (update: add `audit` task)
- `project_board/specs/M902-07_example_baseline.json` (example for docs)

**Checkpoints:**
- `project_board/checkpoints/M902-07/2026-05-16T00-00-00Z-planning.md` (planning log, COMPLETE)
- `project_board/checkpoints/M902-07/<run-id>-<stage>.md` (future runs: spec, test-design, test-break, implementation, acceptance)

---

## Notes for Orchestrator / Human Review

1. **No Destructive API:** This ticket does not involve delete/remove operations; no destructive contract template required.

2. **No Randomness:** No random selection or weighted eligibility; no selection policy freeze required.

3. **Not an Umbrella Ticket:** No child tickets referenced; single feature ticket.

4. **Gating Dependencies:** M902-01 and M902-02 are both COMPLETE and stable. No blocking issues.

5. **Handoff Metadata:** Audit event metadata integrates with M902-04 (gate schema v0.2.0); no conflicts expected. Version may be bumped to v0.3.0 or kept as separate contract; Spec Agent decides in Task 7.

6. **Deferral to M903:** Several features are explicitly deferred (second-reviewer gate for baseline updates, blocking enforcement, auto-remediation ticket creation, expiration renewal policy). These are documented in specs and operator guide.

7. **Baseline Commit Policy:** Not decided in this ticket. Option 1: Commit `.governance-baseline.json` to repo root (public, auditable). Option 2: Keep in `project_board/` as documentation (not on critical path). M903 decides. Implementation in Task 11 creates example; actual baseline commit policy is TBD.

---

End of execution plan. Ready for Spec Agent.

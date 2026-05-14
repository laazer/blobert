# Spec: Validation Gate Framework — Gate Runner, Schemas, Registry, and Shadow Wiring

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/01_validation_gate_framework.md`
**Milestone:** 902 — Agent Predictability Improvements
**Agent:** Spec Agent
**Date:** 2026-05-14
**Status:** SPECIFICATION

---

## Overview

This spec defines the **validation gate framework** for blobert's multi-agent workflow. The framework provides:

1. A deterministic **gate runner** CLI that executes named gates with stable flags.
2. **Structured record schemas** (success and failure) for machine-readable gate outputs.
3. A **gate registry** that discovers and configures available gates.
4. **Shadow mode** semantics for non-blocking rollout.
5. A **wired handoff** (spec → test_design) in shadow mode as the first consumer.

All implementation must live under `ci/scripts/` (gate runner) and `ci/scripts/gate_schemas/` (schema fixtures), with output artifacts under `project_board/checkpoints/<ticket-id>/`.

---

## Assumptions and Checkpoint Resolutions

The following assumptions are made per the checkpoint protocol. Each resolves an ambiguity that would otherwise require human input.

| # | Ambiguity | Assumption | Confidence |
|---|-----------|------------|------------|
| A1 | Where does the gate runner live? | Under `ci/scripts/gate_runner.py` — consistent with `spec_completeness_check.py` and `diff_cover_preflight.sh` conventions. | High |
| A2 | Where do gate result artifacts go? | Under `project_board/checkpoints/<ticket-id>/gate-results/` (one JSON file per gate execution). Ticket ID is the short tag (e.g., `M902-01`). | High |
| A3 | Where does the gate registry live? | Under `ci/scripts/gate_registry.json` — a single JSON file that maps gate names to their module paths, required inputs, and default mode. | High |
| A4 | Which handoff is wired first? | The **spec → test_design** handoff (i.e., the `spec_completeness_check.py` gate that already exists). It is wired in **shadow mode** — producing a result file but not blocking stage advance. | High |
| A5 | What is "artifact" in this repo? | Artifacts are **filesystem paths** (files under `project_board/`, `ci/scripts/`, `asset_generation/`, `scripts/`, `tests/`) and their SHA-256 hashes. Git diffs are **not** treated as artifacts for this ticket's scope (that belongs to M903). | Medium |
| A6 | What Python version and dependencies? | Python 3.11+ (already the repo default). No new third-party dependencies — only stdlib (`json`, `hashlib`, `argparse`, `pathlib`, `typing`, `dataclasses`). | High |
| A7 | How does shadow mode differ from blocking mode? | Shadow mode: gate runs, produces a result file, **always exits 0 regardless of violations**. Blocking mode: gate runs, produces a result file, **exits non-zero on FAIL status**. A `--mode shadow|blocking` CLI flag controls this. | High |
| A8 | Who owns the gate registry? | The gate runner reads it at startup. No agent modifies it — it is a static configuration file. Manual edits are the only supported path. | High |

---

## Requirement 01: Gate Runner CLI

### 1. Spec Summary

**Description:** A Python script (`ci/scripts/gate_runner.py`) that executes a named gate by looking it up in the gate registry. It loads the gate's module, calls its `run()` function with the specified inputs, captures the result, writes it to a structured output file, and exits with the appropriate code.

The gate runner is the **single documented entry surface** for all gates. Every gate must be invocable via:

```bash
python ci/scripts/gate_runner.py <gate-name> \
  --upstream-agent <agent-name> \
  --downstream-agent <agent-name> \
  --ticket-id <ticket-id> \
  --mode shadow|blocking \
  [--input <path-or-json>] \
  [--output-dir <path>]
```

**Constraints:**
- Must use only Python stdlib (no pip dependencies).
- Must exit 0 on success (blocking mode) or shadow mode; non-zero on FAIL in blocking mode.
- Must write result files deterministically under `project_board/checkpoints/<ticket-id>/gate-results/`.
- Must not modify any source files under `agent_context/`.
- Must not break existing CI: adding this script must not affect `run_tests.sh`, `diff_cover_preflight.sh`, or `spec_completeness_check.py`.
- Gate modules must be importable from `ci/scripts/gates/` (a new package directory).

**Assumptions:**
- The gate runner is invoked from the repo root.
- The gate registry is at `ci/scripts/gate_registry.json` relative to repo root.
- Gate modules implement a `run(inputs: dict) -> dict` function that returns a result dict conforming to the success/failure schemas.

**Scope:** Applies to all gates in the milestone 902 pipeline (current ticket + subsequent tickets 02–08).

### 2. Acceptance Criteria

- **AC-01.1:** Running `python ci/scripts/gate_runner.py --help` prints usage information and exits 0.
- **AC-01.2:** Running `python ci/scripts/gate_runner.py <unknown-gate>` exits non-zero with an error message naming the unknown gate.
- **AC-01.3:** Running with required flags (`--upstream-agent`, `--downstream-agent`, `--ticket-id`) and a valid gate name produces a result file under `project_board/checkpoints/<ticket-id>/gate-results/` with a valid JSON structure matching the success or failure schema.
- **AC-01.4:** In `--mode blocking` mode, if the gate returns a FAIL status, the runner exits non-zero (exit code 1).
- **AC-01.5:** In `--mode shadow` mode, the runner always exits 0, even if the gate returns a FAIL status.
- **AC-01.6:** The result file name follows the pattern `<gate-name>_<timestamp>.json` (timestamp in ISO 8601 format, e.g., `2026-05-14T10-30-00Z`).
- **AC-01.7:** The gate runner reads the gate registry from `ci/scripts/gate_registry.json` and raises a clear error if the registry file is missing or malformed JSON.
- **AC-01.8:** The `--input` flag accepts either a file path (JSON) or inline JSON (must not contain newlines for inline mode). If `--input` is omitted, the gate receives an empty dict `{}`.
- **AC-01.9:** The `--output-dir` flag overrides the default output directory. If specified, the result file is written there instead of `project_board/checkpoints/<ticket-id>/gate-results/`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gate module import errors (e.g., missing module, syntax error) | Gate runner crashes silently or with confusing traceback | Wrap all imports in try/except; log clear error to stderr; exit 2 for setup errors |
| Registry file missing or malformed | Gate runner cannot find gates | Validate registry on startup; exit 2 with clear error message |
| Result file write failures (disk full, permissions) | Agent cannot consume gate output | Check output directory exists before writing; create if needed; catch and report errors |
| Shadow mode masks real failures in CI | Teams may not notice broken gates | Document shadow mode limitations; require periodic manual review of shadow results |
| Gate naming collisions | Two gates with the same name in different categories | Gate names must be globally unique within the registry; enforce at write time |

### 4. Clarifying Questions

- **Q1:** Should the gate runner support `--dry-run` (print what it would do without executing)? *Assumption: No. The `--mode shadow` flag serves this purpose.*
- **Q2:** Should the gate runner validate the gate registry schema at startup? *Assumption: Yes, but minimally — check that each entry has `name`, `module`, `required_inputs`. Full schema validation is deferred to M903.*

---

## Requirement 02: Success Record Schema

### 1. Spec Summary

**Description:** A JSON schema and corresponding example output that defines the structure of a gate success record. This schema is checked into the repo as a documentation fixture at `ci/scripts/gate_schemas/gate-result-success.json`.

**Constraints:**
- Must be valid JSON (no YAML, no TOML).
- Must be self-describing (include `$schema` field pointing to JSON Schema draft-07 or a descriptive comment).
- Must be minimal — only include fields necessary for downstream consumption.
- Must be versioned (`version` field).

**Assumptions:**
- The schema is a JSON file with inline documentation (comments are not valid in JSON, so use a `"_comment"` field).
- The schema fixture is both documentation AND a test fixture (used by a test to validate example output).

**Scope:** Applies to all gates that produce success records.

### 2. Acceptance Criteria

- **AC-02.1:** The file `ci/scripts/gate_schemas/gate-result-success.json` exists and contains valid JSON.
- **AC-02.2:** The success record schema includes the following top-level fields: `version` (string), `status` (must be `"PASS"`), `gate` (string), `upstream_agent` (string), `downstream_agent` (string), `timestamp` (ISO 8601 string), `ticket_id` (string), `artifacts` (array of objects with `path` and `sha256`), `duration_ms` (integer), `message` (string).
- **AC-02.3:** An example success record is included in the same file under an `"_example"` key, and the example is valid against the schema.
- **AC-02.4:** All fields in the example are non-null and have sensible default values (e.g., `status: "PASS"`, `gate: "spec_completeness_check"`).
- **AC-02.5:** A test exists that loads the example from the schema file and validates each field's type and format (e.g., `status` must equal `"PASS"`, `timestamp` matches ISO 8601 pattern, `sha256` is 64 hex chars).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema drift between versions | Downstream consumers break | Require `version` field; enforce backward compatibility in M903 |
| SHA-256 computation on large files | Performance impact | Compute only on files < 10MB; skip hash for larger files (record `"sha256": null` with a note) |
| Example not kept in sync | Schema documentation is misleading | Test (AC-02.5) validates the example against the schema |

### 4. Clarifying Questions

- **Q3:** Should `artifacts` include directory hashes or only file hashes? *Assumption: Only file hashes. Directory traversal is handled by the gate, not the schema.*

---

## Requirement 03: Failure Record Schema

### 1. Spec Summary

**Description:** A JSON schema and corresponding example output that defines the structure of a gate failure record. This schema is checked into the repo as a documentation fixture at `ci/scripts/gate_schemas/gate-result-failure.json`.

**Constraints:**
- Must be valid JSON.
- Must include all fields from the success schema, plus failure-specific fields.
- Must include `violations[]` array with file/line/rule/message per violation.
- Must include `remediation_hints[]` array with actionable strings.
- Must be versioned (`version` field).

**Assumptions:**
- The failure schema extends the success schema (same base fields, plus `violations` and `remediation_hints`).
- The `violations` array is ordered by severity (highest first).
- Each violation has: `file` (string, relative to repo root), `line` (integer or null), `rule` (string, the gate rule that was violated), `message` (string, human-readable description), `severity` (string: `"ERROR"`, `"WARN"`, `"INFO"`).

**Scope:** Applies to all gates that produce failure records.

### 2. Acceptance Criteria

- **AC-03.1:** The file `ci/scripts/gate_schemas/gate-result-failure.json` exists and contains valid JSON.
- **AC-03.2:** The failure record schema includes all fields from the success schema (AC-02.2), plus: `violations` (array of objects with `file`, `line`, `rule`, `message`, `severity`), `remediation_hints` (array of strings).
- **AC-03.3:** An example failure record is included in the same file under an `"_example"` key, and the example is valid against the schema.
- **AC-03.4:** The example failure record includes at least 2 violations with different severities and at least 1 remediation hint.
- **AC-03.5:** A test exists that validates the example against the schema, including: each violation has all required fields, `severity` is one of `["ERROR", "WARN", "INFO"]`, `file` is a non-empty string, `rule` is a non-empty string.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Violation format too rigid (file/line) | Some linters/tools don't produce line numbers | Allow `line: null`; document that line is optional |
| Remediation hints too vague | Agents can't act on them | Require hints to reference specific files, rules, or lines |
| Schema bloat over time | Hard to maintain | Version the schema; deprecate old fields rather than removing them |

### 4. Clarifying Questions

- **Q4:** Should `remediation_hints` support structured data (e.g., file paths, rule names) or just plain strings? *Assumption: Plain strings for MVP. Structured data is deferred to M903.*

---

## Requirement 04: Gate Registry

### 1. Spec Summary

**Description:** A JSON file (`ci/scripts/gate_registry.json`) that maps gate names to their implementation details. The gate runner reads this file at startup to discover and invoke gates.

Each gate entry has:
- `name` (string): Unique gate identifier (e.g., `spec_completeness_check`).
- `module` (string): Python module path relative to `ci/scripts/gates/` (e.g., `spec_completeness.py`).
- `required_inputs` (array of strings): Names of input fields the gate expects (e.g., `["spec_file"]`).
- `default_mode` (string): `"shadow"` or `"blocking"` — the default mode if `--mode` is not specified.
- `description` (string): Human-readable description of what the gate checks.
- `category` (string): One of `["workflow", "static_analysis", "governance", "per_stage"]`.

**Constraints:**
- The registry is read-only at runtime (never modified by the gate runner).
- The registry must be valid JSON.
- Gate names must be unique within the registry.
- Module paths must resolve to existing Python files under `ci/scripts/gates/`.

**Assumptions:**
- The registry is a flat list (no nesting). Gates are identified by name.
- Adding a new gate requires: creating the gate module, adding an entry to the registry, and optionally adding a test.
- The registry is not versioned (no `version` field). This is intentional — the registry is an implementation detail of the gate runner, not a public API.

**Scope:** Applies to all gates in milestone 902.

### 2. Acceptance Criteria

- **AC-04.1:** The file `ci/scripts/gate_registry.json` exists and contains valid JSON with a top-level array of gate entries.
- **AC-04.2:** Each gate entry has all required fields: `name`, `module`, `required_inputs`, `default_mode`, `description`, `category`.
- **AC-04.3:** All `name` values are unique within the registry.
- **AC-04.4:** All `module` values resolve to an existing file under `ci/scripts/gates/` (e.g., `ci/scripts/gates/spec_completeness.py`).
- **AC-04.5:** All `category` values are one of the allowed categories: `["workflow", "static_analysis", "governance", "per_stage"]`.
- **AC-04.6:** The `spec_completeness_check` gate is registered in the initial registry (as the first wired gate).
- **AC-04.7:** A test exists that validates the registry file: checks JSON validity, required fields, uniqueness of names, and module file existence.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Registry becomes stale (modules deleted, names changed) | Gate runner fails at runtime | Test (AC-04.7) validates registry on every CI run |
| Registry grows unbounded | Hard to navigate | Require `category` grouping; document retention policy in M903 |
| Module import path conflicts | Two modules with same name in different subdirectories | Restrict gate modules to flat `ci/scripts/gates/` directory (no subdirectories) |

### 4. Clarifying Questions

- **Q5:** Should the registry support gate parameters (e.g., thresholds, paths) inline, or should parameters be passed via `--input` at runtime? *Assumption: Parameters are passed via `--input` at runtime. The registry only declares `required_inputs` names, not values.*

---

## Requirement 05: Shadow Mode Semantics

### 1. Spec Summary

**Description:** Shadow mode is a non-blocking execution mode for gates. In shadow mode:

1. The gate runs normally (same logic, same checks, same violations).
2. The result is written to the output directory (same as blocking mode).
3. The gate runner **always exits 0**, regardless of the gate's internal result.
4. The result file includes a `"mode": "shadow"` field to distinguish it from blocking mode output.
5. A `"_shadow_mode": true` field is added to the result record.

**Constraints:**
- Shadow mode must not alter the gate's internal logic — only the exit code and output metadata.
- Shadow mode results must be clearly distinguishable from blocking mode results (via the `mode` and `_shadow_mode` fields).
- Shadow mode is the **default** for the initial handoff wiring (spec → test_design).

**Assumptions:**
- Shadow mode is a gate runner concern, not a gate concern. Gates should not need to know whether they are running in shadow or blocking mode.
- The `--mode` flag defaults to `"shadow"` if not specified (conservative by default).

**Scope:** Applies to all gates during the rollout phase (M902). M903 may change the default.

### 2. Acceptance Criteria

- **AC-05.1:** Running the gate runner with `--mode shadow` on any gate produces a result file with `"mode": "shadow"` and `"_shadow_mode": true` fields.
- **AC-05.2:** Running the gate runner with `--mode shadow` on a gate that would return FAIL in blocking mode exits 0 (not non-zero).
- **AC-05.3:** Running the gate runner with `--mode blocking` on a gate that returns FAIL exits non-zero (exit code 1).
- **AC-05.4:** The default `--mode` (when `--mode` is omitted) is `"shadow"`.
- **AC-05.5:** Shadow mode results are written to the same output directory as blocking mode results (no separate shadow output directory).
- **AC-05.6:** A test exists that verifies: (a) shadow mode exits 0 on a FAIL gate, (b) blocking mode exits 1 on a FAIL gate, (c) both modes produce result files with the correct `mode` field.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Shadow mode masks real failures | Teams may not notice broken gates | Document shadow mode limitations; require periodic review of shadow results in M903 |
| Shadow results mixed with blocking results | Hard to distinguish which results are from which mode | The `mode` and `_shadow_mode` fields in the result file distinguish them |
| Default-to-shadow is too conservative | Teams may not realize gates are not blocking | Document the default in the gate runner `--help` output and in the milestone README |

### 4. Clarifying Questions

- **Q6:** Should shadow mode log to a separate file (e.g., `shadow.log`) for easy review? *Assumption: No. The result JSON file is sufficient; a separate log is deferred to M903.*

---

## Requirement 06: Spec → Test Design Handoff Wiring

### 1. Spec Summary

**Description:** The existing `spec_completeness_check.py` script (at `ci/scripts/spec_completeness_check.py`) is wired as a gate in the framework. This is the **first consumer** of the gate framework.

The wiring involves:

1. Creating a gate wrapper module at `ci/scripts/gates/spec_completeness.py` that:
   - Accepts inputs: `spec_file` (path to the spec .md file), `ticket_type` (string: one of `api`, `destructive`, `randomness`, `load-open`, `generic`).
   - Invokes `spec_completeness_check.py` as a subprocess (or imports its `check()` function).
   - Returns a result dict conforming to the success or failure schema.
   - Exits with the appropriate code (0 for pass, 1 for fail).

2. Registering the gate in `ci/scripts/gate_registry.json`.

3. Wiring the gate to run in **shadow mode** by default (non-blocking).

4. Documenting the wired handoff in the milestone README.

**Constraints:**
- The wiring must not break the existing `spec_completeness_check.py` script (it must still work as a standalone tool).
- The gate wrapper must produce results that conform to the failure schema (AC-03.2) when the spec check fails.
- The gate must be runnable both as a standalone script and as a gate via the gate runner.
- The wiring must not introduce new dependencies.

**Assumptions:**
- The gate wrapper invokes `spec_completeness_check.py` as a subprocess (not import) to avoid Python path issues and to reuse the existing CLI.
- The `spec_file` input is passed as `--spec-file` (or positional argument) to the existing script.
- The `ticket_type` input is passed as `--type` to the existing script.
- The gate wrapper maps the subprocess exit code to a result dict: exit 0 → success record, exit 1 → failure record, exit 2 → error record.

**Scope:** Applies to the spec → test_design handoff for all specs under `project_board/` and `agent_context/specs/`.

### 2. Acceptance Criteria

- **AC-06.1:** The file `ci/scripts/gates/spec_completeness.py` exists and is a valid Python module.
- **AC-06.2:** Running the gate via the gate runner (`python ci/scripts/gate_runner.py spec_completeness_check --input '{"spec_file": "<path>", "ticket_type": "generic"}'`) produces a valid result file.
- **AC-06.3:** When the spec file passes the completeness check, the result is a success record (status: `"PASS"`).
- **AC-06.4:** When the spec file fails the completeness check, the result is a failure record (status: `"FAIL"`, with `violations` listing the missing sections).
- **AC-06.5:** The gate is registered in `ci/scripts/gate_registry.json` with `default_mode: "shadow"`.
- **AC-06.6:** The existing `spec_completeness_check.py` script still works standalone (unchanged behavior).
- **AC-06.7:** A test exists that verifies the gate wrapper produces correct results for both pass and fail cases.
- **AC-06.8:** The milestone README (`project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md`) is updated with a section documenting the wired handoff.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Subprocess invocation fails (missing script, wrong path) | Gate produces no result | Validate script existence at gate startup; exit 2 with clear error |
| Existing `spec_completeness_check.py` behavior changes | Gate wrapper produces unexpected results | Test (AC-06.6) ensures standalone behavior is unchanged |
| Gate wrapper adds complexity without benefit | Maintenance burden | The wrapper is thin (50-100 lines); it only translates between gate runner inputs/outputs and the existing script |

### 4. Clarifying Questions

- **Q7:** Should the gate wrapper also capture and include the subprocess stdout/stderr in the result file? *Assumption: Yes — include `stdout` and `stderr` fields in the result for debugging. This is consistent with the "actionable remediation context" requirement.*

---

## Requirement 07: Documentation and Example Schema Fixture

### 1. Spec Summary

**Description:** Documentation and example fixtures for the gate framework. This includes:

1. An example gate result file (`ci/scripts/gate_schemas/gate-result-success.json` and `ci/scripts/gate_schemas/gate-result-failure.json`) that serves as both documentation and test fixture.
2. A short operator documentation section in the milestone README (`project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md`) documenting:
   - How to run the gate runner.
   - How to add a new gate.
   - How to interpret result files.
   - The shadow vs blocking mode difference.
   - The wired handoff (spec → test_design).

**Constraints:**
- Documentation must be concise (≤ 50 lines for the README section).
- Example files must be valid JSON.
- Documentation must not duplicate content from the agent operating docs (it references them).
- No new files under `agent_context/`.

**Assumptions:**
- The milestone README already exists and should be updated (not created).
- The documentation section is titled "## Gate Runner" in the milestone README.
- The example files include inline comments (via a `"_comment"` field) explaining each field.

**Scope:** Applies to the entire gate framework (all gates, all schemas, all modes).

### 2. Acceptance Criteria

- **AC-07.1:** The file `ci/scripts/gate_schemas/gate-result-success.json` exists with a valid example success record.
- **AC-07.2:** The file `ci/scripts/gate_schemas/gate-result-failure.json` exists with a valid example failure record.
- **AC-07.3:** The milestone README includes a "## Gate Runner" section with: usage example, how to add a gate, shadow vs blocking explanation, and the wired handoff reference.
- **AC-07.4:** The README section includes the exact CLI command for running the gate runner (from AC-01.3).
- **AC-07.5:** A test exists that loads both example files and validates them against their respective schemas.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Documentation drifts from implementation | Misleading for users | Tests (AC-07.5) validate examples; CI runs these tests |
| README section too long | Hard to read | Limit to ≤ 50 lines; link to detailed docs if needed |
| Example files become stale | Examples don't match real output | Tests validate examples against schemas on every CI run |

### 4. Clarifying Questions

- **Q8:** Should the documentation include a Mermaid diagram of the gate flow? *Assumption: No. That belongs to ticket 08 (workflow visualization). This ticket's documentation is CLI + schema focused.*

---

## Non-Functional Requirements

### NFR-01: Performance
- Gate runner startup + gate execution must complete in < 5 seconds for the spec_completeness_check gate (the slowest expected gate in M902).
- SHA-256 computation must complete in < 2 seconds per file for files up to 10MB.

### NFR-02: Reliability
- Gate runner must not crash on invalid input (must produce a clear error message and exit 2).
- Gate runner must not modify any files outside the output directory (except reading the registry and gate modules).
- Gate results must be deterministic for the same inputs (same file hashes, same timestamps in ISO 8601 format).

### NFR-03: Maintainability
- Gate modules must be ≤ 200 lines each.
- Gate registry must be ≤ 50 entries (enforce via test).
- No new third-party dependencies.

### NFR-04: Observability
- Gate results must include `duration_ms` for performance monitoring.
- Gate results must include `timestamp` in ISO 8601 format.
- Gate runner must log to stderr: gate name, mode, input summary, result status.

### NFR-05: Security
- Gate results must not include secrets (API keys, passwords, tokens).
- Gate runner must not execute arbitrary code from the registry (only import known gate modules).
- Gate result files must have permissions `0644` (readable by all, writable by owner).

---

## Risk Register

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R1 | Gate framework adds complexity to existing CI | Medium | Shadow mode by default; no blocking until M903 |
| R2 | Gate modules drift from registry | Medium | Registry validation test (AC-04.7) |
| R3 | Schema versioning conflicts with M903 | Low | Schema is versioned; M903 can introduce v2 |
| R4 | Shadow mode results accumulate in checkpoints | Low | Document cleanup policy in M903 |
| R5 | Subprocess invocation of `spec_completeness_check.py` is fragile | Medium | Validate script existence at gate startup; test (AC-06.6) |

---

## Dependencies

| Dependency | Ticket | Status |
|------------|--------|--------|
| Handoff metadata schema and risk-based escalation | `04_handoff_metadata_and_risk_escalation.md` | Backlog (M903) |
| Per-stage gate improvements | `06_per_stage_gate_improvements.md` | Backlog (M903) |
| Workflow visualization and agent runbook updates | `08_workflow_visualization_and_agent_runbook_updates.md` | Backlog (M903) |

**Note:** The current ticket (01) has no hard dependencies on other backlog tickets. The other tickets build on this one.

---

## File Tree (Post-Implementation)

```
ci/scripts/
├── gate_runner.py                          # Gate runner CLI
├── gate_registry.json                      # Gate registry
├── gate_schemas/
│   ├── gate-result-success.json            # Success record schema + example
│   └── gate-result-failure.json            # Failure record schema + example
└── gates/
    ├── __init__.py                         # Empty or minimal
    └── spec_completeness.py                # spec_completeness_check gate wrapper

project_board/
└── 902_milestone_902_agent_predictabilitiy_improvements/
    ├── README.md                           # Updated with Gate Runner section
    └── specs/
        └── 902_01_gate_runner_spec.md      # This spec file

project_board/checkpoints/
└── <ticket-id>/
    └── gate-results/
        ├── spec_completeness_check_2026-05-14T10-30-00Z.json
        └── ...
```

---

## Spec Exit Gate Checklist

This spec is ready for the spec exit gate when:

- [x] All requirements have Acceptance Criteria (ACs) that are measurable, unambiguous, and independently verifiable.
- [x] All Acceptance Criteria reference concrete, testable behavior (not prose).
- [x] No assumptions are left unstated (all logged in the Assumptions table).
- [x] Risks and edge cases are identified with mitigations.
- [x] Clarifying questions are documented with assumptions.
- [x] Non-functional requirements are defined (performance, reliability, maintainability, observability, security).
- [x] Dependencies are enumerated.
- [x] File tree is specified.
- [x] No gameplay changes are included (workflow tooling only).
- [x] No new third-party dependencies are introduced.
- [x] Schema files are self-contained JSON fixtures (no external schema references required for basic validation).

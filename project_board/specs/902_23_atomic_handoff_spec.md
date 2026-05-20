# Spec: Atomic Handoff Checkpoint — Structured YAML Checklists and Handoff Validation Gate

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/23_atomic_handoff_checkpoint.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-23_atomic_handoff_checkpoint.md`

**Agent:** Spec Agent

**Date:** 2026-05-20

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines the **atomic handoff checkpoint** contract for blobert's multi-agent pipeline. Each finishing agent must emit a structured handoff checklist before the next agent starts. A validation gate reads that artifact and **FAILs** when required items are missing, incomplete, or blocked.

Deliverables covered by this spec:

1. **Handoff YAML schema** (`handoff` root) stored under `project_board/checkpoints/<ticket_id>/`
2. **Seven frozen handoff catalogs** (Planner→Spec through Learning→Complete) with machine-checkable item keys and evidence rules
3. Public validator API: `validate_handoff_checklist(ticket_id: str, from_agent: str, to_agent: str) -> GateResult`
4. Gate module: `ci/scripts/gates/handoff_validation_check.py` with `run(inputs) -> dict`
5. Registry entry: `handoff_validation_check` (shadow default)
6. **Composition** with M902-20 `todo_validation_check` (sequential: todos then handoff)
7. Snapshot **writer** contract, agent **runbook**, good/bad **examples**, and **test scenario matrix** (minimum nine core cases + three distinct pair vectors)

**Prerequisites:** M902-01 gate runner/registry/schemas; M902-20 todo validation gate; `agent_context/agents/common_assets/checkpoint_protocol_v1.md`; `workflow_enforcement_v1.md` stage enum.

**Orthogonal:** M902-04 handoff **metadata** (risk scores on gate JSON) does not replace YAML checklist content.

---

## Assumptions and Checkpoint Resolutions

| # | Ambiguity | Assumption | Confidence |
|---|-----------|------------|------------|
| A1 | YAML parser dependency | Add `PyYAML>=6.0,<7` to `asset_generation/python/pyproject.toml` `[project.optional-dependencies] dev`. Gate uses `yaml.safe_load` only. No custom YAML tags/constructors. | High |
| A2 | Missing handoff artifact | **Fail-closed** in blocking mode: `FAIL` with `rule: handoff_artifact_missing`. In shadow mode, vacuous PASS allowed only when gate input `handoff_optional: true` (boolean, default `false`). | High |
| A3 | Subjective checklist items | Gate validates **structure and status** plus evidence **presence** (non-empty string). It does **not** execute pytest/ruff/diff-cover to verify prose claims unless `evidence_type: path` and path exists. | High |
| A4 | Agent name normalization | Reuse the same canonical keys as `AGENT_ALIAS_MAP` in `ci/scripts/gates/todo_validation_check.py` (`planner`, `spec`, `test_designer`, `test_breaker`, `implementation`, `static_qa`, `learning`, `ac_gatekeeper`). Unknown agents → FAIL `handoff_agent_unknown`. | High |
| A5 | Review agent identity | Ticket "Review" maps to downstream agent key `static_qa` (Static QA / code-reviewer). | High |
| A6 | Learning→Complete downstream | Downstream agent key `ac_gatekeeper` (Acceptance Criteria Gatekeeper). Stage may be INTEGRATION→COMPLETE per orchestrator. | High |
| A7 | Planner "timeline estimated" | Minimum evidence: path to execution plan file under `project_board/execution_plans/` and plan header contains `Revision:` and `Estimated Effort:` or `Estimated Effort` table row. Gate checks path exists when `evidence_type: path`. | Medium |
| A8 | Test Designer "coverage > 80%" | Machine-checkable proxy defined in Catalog 03 (Requirement 05); gate checks evidence pattern, not live coverage execution. | High |
| A9 | Counter fields | `required_items_met` and `total_required_items` must match computed counts from checklist; mismatch → FAIL `handoff_counter_mismatch`. | High |
| A10 | Dual writers | Finishing agent writes `handoff-latest.yaml` immediately before gate invocation; orchestrator does not mutate checklist files. | High |

---

## Requirement 01: Public API — `validate_handoff_checklist`

### 1. Spec Summary

- **Description:** Loads the effective handoff artifact for `(ticket_id, from_agent, to_agent)`, validates against the frozen catalog for that pair, and returns PASS only when every **required** checklist item has `status: complete` with valid evidence.

- **Signature (implementation contract):**

```python
def validate_handoff_checklist(
    ticket_id: str,
    from_agent: str,
    to_agent: str,
    *,
    checkpoints_dir: str = "project_board/checkpoints",
    handoff_optional: bool = False,
) -> GateResult:
    ...
```

- **Parameters:**
  - `ticket_id`: Short tag (e.g. `M902-23`). Normalized to `M902-23` (uppercase, hyphen).
  - `from_agent`: Finishing upstream agent (human label or canonical key).
  - `to_agent`: Expected downstream agent (human label or canonical key).
  - `checkpoints_dir`: Root checkpoints directory (default `project_board/checkpoints`).
  - `handoff_optional`: When `True` and no artifact exists, return vacuous PASS (shadow rollout only).

- **Return (`GateResult`):** Dict including at minimum:
  - `version` (string, gate module version e.g. `"0.1.0"`)
  - `status` (`"PASS"` | `"FAIL"`)
  - `gate` (string, `"handoff_validation_check"`)
  - `ticket_id`, `timestamp`, `message`, `duration_ms`
  - `violations` (list, empty on PASS)
  - `remediation_hints` (list of strings, non-empty on FAIL)
  - `gaps[]` **or** `missing_items[]` (list, empty on PASS) — supplementary human ergonomics; each entry includes `item_key`, `item`, `status`, `required`
  - `from_agent`, `to_agent` (canonical keys after normalization)
  - `artifacts` (list of `{path, sha256}` for handoff files read)

- **Constraints:**
  - Read-only; no mutation of checkpoint files.
  - Path guards identical to M902-20 (`..`, traversal, checkpoints_dir under repo/cwd).
  - Must not import Godot or invoke subprocesses for evidence verification.

- **Assumptions:** Invoked from repo root or test `tmp_path` sandboxes.

- **Scope:** All multi-agent tickets using checkpoint handoff artifacts.

### 2. Acceptance Criteria

- **AC-01.1:** All required items `complete` with valid evidence for valid pair → `status: "PASS"`.
- **AC-01.2:** One required item `incomplete` → `status: "FAIL"` with that item in `gaps`/`missing_items` and `violations[].rule == "handoff_item_missing"`.
- **AC-01.3:** One required item `blocked` → `status: "FAIL"` with `violations[].rule == "handoff_blocked"`.
- **AC-01.4:** `from_agent`/`to_agent` in file do not match gate inputs after normalization → `FAIL` with `rule: handoff_pair_mismatch`.
- **AC-01.5:** Missing artifact with `handoff_optional=False` → `FAIL` with `rule: handoff_artifact_missing`.
- **AC-01.6:** Malformed YAML → `FAIL` with `rule: handoff_artifact_invalid`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| False PASS on empty evidence | Silent handoff | Require non-empty `evidence` when `status==complete` |
| Stale `handoff-latest.yaml` from prior pair | Wrong transition | Pair mismatch check + writer overwrites whole file |

### 4. Clarifying Questions

- None (resolved A1–A10).

---

## Requirement 02: Handoff Artifact Schema (YAML)

### 1. Spec Summary

- **Description:** Canonical on-disk checklist format for agent handoffs.

- **Primary artifact:**

  Path: `project_board/checkpoints/<ticket_id>/handoff-latest.yaml`

  Encoding: UTF-8 YAML, root key `handoff` (object).

- **Optional history:**

  Path: `project_board/checkpoints/<ticket_id>/handoff-<run-id>.yaml` (same schema; gate does not merge when `handoff-latest.yaml` exists).

- **Root schema (`HandoffDocument`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff.from_agent` | string | yes | Canonical agent key (see Requirement 04) |
| `handoff.to_agent` | string | yes | Canonical agent key |
| `handoff.checklist` | array | yes | Non-empty list of checklist items |
| `handoff.required_items_met` | integer | yes | Count of required items with `status: complete` |
| `handoff.total_required_items` | integer | yes | Count of required items in catalog for this pair |
| `handoff.validated_at` | string | yes | ISO 8601 UTC when upstream agent finalized checklist |
| `handoff.schema_version` | string | yes | Must be `"1.0"` for this revision |
| `handoff.ticket_id` | string | yes | Must match normalized gate `ticket_id` |

- **Checklist item schema (`HandoffChecklistItem`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_key` | string | yes | Stable key from frozen catalog (Requirement 05–11) |
| `item` | string | yes | Human-readable label (must match catalog text for key) |
| `required` | boolean | yes | Must match catalog default for that key |
| `status` | string | yes | One of: `complete`, `incomplete`, `deferred`, `blocked` |
| `evidence` | string | yes when `status==complete` | Attestation: path, command summary, or gate result path |
| `defer_reason` | string | yes when `status==deferred` | Required for deferred items |
| `block_reason` | string | yes when `status==blocked` | Required for blocked items |
| `evidence_type` | string | no | One of: `attestation` (default), `path`. When `path`, gate checks `evidence` path exists relative to repo root |

- **Discovery precedence:**
  1. `handoff-latest.yaml` if present and parseable
  2. Else newest by mtime among `handoff-*.yaml` excluding `handoff-latest.yaml`
  3. Else fenced YAML in `project_board/checkpoints/<ticket_id>/*.md`:

     ` ```yaml handoff ` … ` ``` `

     or legacy alias ` ```yaml handoff-checklist ` … ` ``` `

     Use newest file by mtime; if same file, use **last** fence block.
  4. Else no artifact → Requirement 01 / A2

- **Constraints:**
  - Duplicate `item_key` in one document → FAIL `handoff_artifact_invalid`
  - Unknown `item_key` for pair → FAIL `handoff_unknown_item`
  - Missing catalog-required keys → FAIL `handoff_item_missing` (synthetic incomplete entries)
  - `status` not in enum → FAIL `handoff_artifact_invalid`
  - `deferred` on `required: true` unless catalog `deferrable: true` → FAIL `handoff_deferred_not_allowed`
  - `blocked` on any **required** item → FAIL `handoff_blocked` (never proceed)

- **Assumptions:** PyYAML `safe_load` only (A1).

- **Scope:** Checkpoint tree for ticket id; not `project_board/CHECKPOINTS.md`.

### 2. Acceptance Criteria

- **AC-02.1:** Valid example document (see Requirement 12) parses and PASSes when all required items complete.
- **AC-02.2:** `handoff-latest.yaml` selected over older `handoff-2026-05-20T-spec.yaml`.
- **AC-02.3:** Fenced YAML in `.md` used when no standalone YAML files exist.
- **AC-02.4:** `schema_version` other than `"1.0"` → FAIL invalid artifact.
- **AC-02.5:** `ticket_id` mismatch directory/name → FAIL invalid artifact.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| YAML alias/anchor tricks | Parser surprises | safe_load + reject non-scalar unexpected types |
| Concurrent writers | Corrupt file | Fail-closed parse errors |

### 4. Clarifying Questions

- None.

---

## Requirement 03: Status Semantics and Blocking Rules

### 1. Spec Summary

- **Description:** Defines PASS/FAIL from per-item `status`.

- **PASS conditions (all must hold):**
  - Artifact discovered and schema-valid
  - `handoff.from_agent` / `handoff.to_agent` match normalized gate inputs
  - Every catalog-required `item_key` present
  - Every item with `required: true` has `status: complete` and non-empty `evidence` (and path exists if `evidence_type: path`)
  - `required_items_met ==` count(required items with `complete`)
  - `total_required_items ==` catalog required count for pair
  - No required item `blocked` or `incomplete` or `deferred` (unless deferrable)

- **FAIL drivers:**

| Condition | `violations[].rule` |
|-----------|---------------------|
| Required item `incomplete` or absent | `handoff_item_missing` |
| Required item `blocked` | `handoff_blocked` |
| Required item `deferred` when not deferrable | `handoff_deferred_not_allowed` |
| `complete` without evidence | `handoff_evidence_missing` |
| Pair mismatch | `handoff_pair_mismatch` |
| No artifact (not optional) | `handoff_artifact_missing` |
| Parse/schema errors | `handoff_artifact_invalid` |
| Counter mismatch | `handoff_counter_mismatch` |
| Unknown agent | `handoff_agent_unknown` |

- **Optional items (`required: false`):** May be `deferred` with `defer_reason`; do not block PASS. May be `complete` or omitted from checklist (gate treats omitted optional as not applicable, not FAIL).

- **Assumptions:** Upstream agent never sets required item to `deferred` without catalog permission.

- **Scope:** All pairs in Requirement 05–11.

### 2. Acceptance Criteria

- **AC-03.1:** All required `complete` → PASS.
- **AC-03.2:** One required `incomplete` → FAIL with gap list length ≥ 1.
- **AC-03.3:** Required `blocked` → FAIL; never PASS.
- **AC-03.4:** Optional `deferred` with `defer_reason` → PASS if all required complete.
- **AC-03.5:** Required `deferred` on non-deferrable item → FAIL.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent marks complete without work | Process gap | Human review; future machine hooks in M903 |

### 4. Clarifying Questions

- None.

---

## Requirement 04: Agent Normalization and Valid Pairs

### 1. Spec Summary

- **Description:** Normalize `from_agent` / `to_agent` using the same alias table as `todo_validation_check.AGENT_ALIAS_MAP`. Canonical keys:

`planner`, `spec`, `test_designer`, `test_breaker`, `implementation`, `static_qa`, `learning`, `ac_gatekeeper`

- **Frozen valid pairs (exactly seven):**

| `from_agent` | `to_agent` | Workflow transition (typical) |
|--------------|------------|-------------------------------|
| `planner` | `spec` | PLANNING → SPECIFICATION |
| `spec` | `test_designer` | SPECIFICATION → TEST_DESIGN |
| `test_designer` | `test_breaker` | TEST_DESIGN → TEST_BREAK |
| `test_breaker` | `implementation` | TEST_BREAK → IMPLEMENTATION_* |
| `implementation` | `static_qa` | IMPLEMENTATION_* → STATIC_QA |
| `static_qa` | `learning` | STATIC_QA → INTEGRATION |
| `learning` | `ac_gatekeeper` | INTEGRATION → COMPLETE |

- **Constraints:** Gate called with pair not in table → FAIL `handoff_pair_unknown` before catalog lookup.

- **Assumptions:** Implementation stage variants (`IMPLEMENTATION_GENERALIST`, etc.) still use `implementation` as finishing key.

- **Scope:** Gate inputs and YAML `from_agent`/`to_agent` fields.

### 2. Acceptance Criteria

- **AC-04.1:** `"Spec Agent"` normalizes to `spec`.
- **AC-04.2:** `"Code Reviewer"` normalizes to `static_qa`.
- **AC-04.3:** `"Acceptance Criteria Gatekeeper"` normalizes to `ac_gatekeeper`.
- **AC-04.4:** Valid pair list has exactly seven entries.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| New agent types | Pair table drift | Planner updates spec revision |

### 4. Clarifying Questions

- None.

---

## Requirement 05: Frozen Catalog — Planner → Spec

### 1. Spec Summary

- **Description:** Checklist items when Planner hands off to Spec Agent.

- **Catalog ID:** `pair_planner_spec`

| item_key | item (normative label) | required | deferrable | evidence_type | Evidence rules |
|----------|------------------------|----------|------------|---------------|----------------|
| `planner_ticket_decomposed` | Ticket decomposed into execution plan tasks | yes | no | path | `evidence` is repo-relative path to `project_board/execution_plans/M<nnn>-<slug>.md`; file must exist |
| `planner_dependencies_clear` | Dependencies clear (acyclic or documented WARN) | yes | no | attestation | `evidence` cites execution plan section `Dependency Matrix` or `Dependencies` |
| `planner_timeline_estimated` | Timeline estimated | yes | no | path | Same execution plan path; file contains substring `Estimated Effort` or `Estimated Effort:` |

- **Constraints:** All three keys required in checklist.

- **Assumptions:** Execution plan created during PLANNING (A7).

- **Scope:** `planner` → `spec` only.

### 2. Acceptance Criteria

- **AC-05.1:** Three required keys all `complete` with valid paths → PASS.
- **AC-05.2:** Missing `planner_timeline_estimated` → FAIL.
- **AC-05.3:** Execution plan path does not exist → FAIL `handoff_evidence_missing` or path-specific violation.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Subjective "dependencies clear" | False PASS | Path + section citation still required |

### 4. Clarifying Questions

- None.

---

## Requirement 06: Frozen Catalog — Spec → Test Designer

### 1. Spec Summary

- **Description:** Checklist when Spec Agent hands off to Test Designer.

- **Catalog ID:** `pair_spec_test_designer`

| item_key | item | required | deferrable | evidence_type | Evidence rules |
|----------|------|----------|------------|---------------|----------------|
| `spec_acceptance_criteria` | Acceptance criteria defined | yes | no | path | `evidence` path to `project_board/specs/<spec>.md`; file contains `Acceptance Criteria` or `### 2. Acceptance Criteria` |
| `spec_test_strategy` | Test strategy documented | yes | no | attestation | `evidence` references spec section `Test` or requirement describing test approach (section title substring) |
| `spec_edge_cases` | Edge cases listed | yes | no | attestation | `evidence` references `Risk & Ambiguity` or `Edge` in spec |

- **Scope:** `spec` → `test_designer`.

### 2. Acceptance Criteria

- **AC-06.1:** Spec file path in evidence exists → PASS when all complete.
- **AC-06.2:** Missing `spec_edge_cases` entry → FAIL.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Generic spec without edge section | FAIL until spec updated | Spec exit gate already requires risk sections |

### 4. Clarifying Questions

- None.

---

## Requirement 07: Frozen Catalog — Test Designer → Test Breaker

### 1. Spec Summary

- **Description:** Checklist when Test Designer hands off to Test Breaker. Includes frozen **coverage > 80%** proxy (ticket AC).

- **Catalog ID:** `pair_test_designer_test_breaker`

| item_key | item | required | deferrable | evidence_type | Evidence rules |
|----------|------|----------|------------|---------------|----------------|
| `test_suite_complete` | Test suite complete per spec test plan | yes | no | path | `evidence` lists one or more repo-relative test module paths (comma-separated or JSON array string); each path must exist |
| `test_coverage_threshold` | Coverage threshold met (>80% proxy) | yes | no | attestation | **Python in scope:** `evidence` contains `coverage:` followed by integer ≥ 80 OR substring `diff_cover_preflight PASS` OR path under `gate-results/` ending in `.json` that exists. **Godot-only scope:** `evidence` contains `godot` and `run_tests` and `PASS`. **Docs-only ticket:** `evidence` exactly `docs-only:N/A` |
| `test_all_runnable` | All tests runnable | yes | no | attestation | `evidence` contains `pytest` collection PASS or `godot --headless` test invocation PASS with ISO timestamp |

- **Scope determination (for gate):** Read ticket spec path from `spec_acceptance_criteria` evidence if present in same document; else assume mixed. If any listed test path ends with `.gd` → Godot branch; if any `.py` under `tests/` or `asset_generation/` → Python branch.

- **Scope:** `test_designer` → `test_breaker`.

### 2. Acceptance Criteria

- **AC-07.1:** `test_coverage_threshold` evidence `coverage: 85` → PASS (when other items complete).
- **AC-07.2:** `coverage: 75` → FAIL `handoff_item_missing` on that key.
- **AC-07.3:** `test_suite_complete` path missing on disk → FAIL.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Inflated coverage string | False PASS | Test-breaker adversarial cases; M903 machine diff-cover hook |

### 4. Clarifying Questions

- None.

---

## Requirement 08: Frozen Catalog — Test Breaker → Implementation

### 1. Spec Summary

- **Catalog ID:** `pair_test_breaker_implementation`

| item_key | item | required | deferrable | evidence_type | Evidence rules |
|----------|------|----------|------------|---------------|----------------|
| `breaker_gaps_documented` | All discovered gaps documented | yes | no | path | Path to adversarial test module or checkpoint log listing gaps (`*adversarial*` or `checkpoints/<ticket>/*.md`) |
| `breaker_impl_notes` | Implementation notes created | yes | no | attestation | `evidence` references spec section, execution plan task notes, or checkpoint `Implementation notes` |

- **Scope:** `test_breaker` → `implementation`.

### 2. Acceptance Criteria

- **AC-08.1:** Both items complete → PASS.
- **AC-08.2:** `breaker_gaps_documented` incomplete → FAIL.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Empty gap list claimed | Process | Test-breaker checkpoint template |

### 4. Clarifying Questions

- None.

---

## Requirement 09: Frozen Catalog — Implementation → Review (Static QA)

### 1. Spec Summary

- **Catalog ID:** `pair_implementation_static_qa`

| item_key | item | required | deferrable | evidence_type | Evidence rules |
|----------|------|----------|------------|---------------|----------------|
| `impl_ac_complete` | All acceptance criteria implemented | yes | no | attestation | `evidence` lists AC ids (e.g. `AC-01.1, AC-02.3`) or checkpoint AC matrix path |
| `impl_tests_passing` | All tests passing | yes | no | attestation | `evidence` contains test command + `PASS` + timestamp (ISO-8601 substring) |
| `impl_linter_clean` | No linter violations | yes | no | path | Path to `gate-results/static_analysis_*.json` or attestation with `ruff`/`mypy`/`0 errors` |
| `impl_checkpoint_logged` | Checkpoint logged | yes | no | path | Repo-relative path to `project_board/checkpoints/<ticket_id>/<run-id>.md` |

- **Optional (catalog, not required for PASS):**

| item_key | item | required | deferrable |
|----------|------|----------|------------|
| `impl_docstrings` | Docstrings/comments on complex logic | no | yes |

- **Scope:** `implementation` → `static_qa`.

### 2. Acceptance Criteria

- **AC-09.1:** Four required items complete → PASS.
- **AC-09.2:** `impl_tests_passing` blocked → FAIL `handoff_blocked`.
- **AC-09.3:** Optional `impl_docstrings` deferred with reason → still PASS if required met.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Claimed PASS without running tests | Quality | Integration stage re-runs suite |

### 4. Clarifying Questions

- None.

---

## Requirement 10: Frozen Catalog — Review → Learning

### 1. Spec Summary

- **Catalog ID:** `pair_static_qa_learning`

| item_key | item | required | deferrable | evidence_type | Evidence rules |
|----------|------|----------|------------|---------------|----------------|
| `review_feedback_incorporated` | Feedback incorporated | yes | no | attestation | `evidence` references review checkpoint or `gate-results/agent_review_*.json` |
| `review_code_reviewed` | Code reviewed | yes | no | attestation | `evidence` names reviewer agent and scoped checkpoint path |
| `review_merge_ready` | Merge-ready | yes | no | attestation | `evidence` contains `git status` clean or `merge-ready` with branch name |

- **Scope:** `static_qa` → `learning`.

### 2. Acceptance Criteria

- **AC-10.1:** Three required complete → PASS.
- **AC-10.2:** `review_merge_ready` incomplete → FAIL.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Merge-ready subjective | AC Gatekeeper verifies git push before COMPLETE |

### 4. Clarifying Questions

- None.

---

## Requirement 11: Frozen Catalog — Learning → Complete

### 1. Spec Summary

- **Catalog ID:** `pair_learning_ac_gatekeeper`

| item_key | item | required | deferrable | evidence_type | Evidence rules |
|----------|------|----------|------------|---------------|----------------|
| `learning_insights_documented` | Insights documented | yes | no | path | Path to `project_board/LEARNINGS.md` or checkpoint learning section |
| `learning_rationale_recorded` | Decision rationale recorded | yes | no | attestation | `evidence` references checkpoint `Assumption made` entries or spec assumptions table |
| `learning_checklist_validated` | Handoff checklist validated | yes | no | attestation | `evidence` contains `handoff_validation_check PASS` with ticket id |

- **Scope:** `learning` → `ac_gatekeeper`.

### 2. Acceptance Criteria

- **AC-11.1:** All three complete → PASS.
- **AC-11.2:** Missing `learning_checklist_validated` → FAIL.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Self-referential PASS claim | Circular | AC Gatekeeper runs gate independently |

### 4. Clarifying Questions

- None.

---

## Requirement 12: Normative YAML Example (Implementation → Review)

### 1. Spec Summary

- **Description:** Reference document for writers and tests (Implementation → Static QA pair).

```yaml
handoff:
  schema_version: "1.0"
  ticket_id: "M902-23"
  from_agent: implementation
  to_agent: static_qa
  validated_at: "2026-05-20T14:35:00Z"
  checklist:
    - item_key: impl_ac_complete
      item: All acceptance criteria implemented
      required: true
      status: complete
      evidence: "AC-01.1 through AC-09.3 complete per checkpoint 2026-05-20T-impl-run.md"
    - item_key: impl_tests_passing
      item: All tests passing
      required: true
      status: complete
      evidence: "timeout 300 ci/scripts/run_tests.sh PASS 2026-05-20T14:30:00Z"
    - item_key: impl_linter_clean
      item: No linter violations
      required: true
      status: complete
      evidence: "project_board/checkpoints/M902-23/gate-results/static_analysis_2026-05-20.json"
      evidence_type: path
    - item_key: impl_checkpoint_logged
      item: Checkpoint logged
      required: true
      status: complete
      evidence: "project_board/checkpoints/M902-23/2026-05-20T-impl-run.md"
      evidence_type: path
    - item_key: impl_docstrings
      item: Docstrings/comments on complex logic
      required: false
      status: deferred
      evidence: ""
      defer_reason: "Defer doc pass to M903 documentation ticket"
  required_items_met: 4
  total_required_items: 4
```

- **Assumptions:** Paths relative to repo root.

- **Scope:** Example only; catalogs in Req 05–11 are authoritative for keys.

### 2. Acceptance Criteria

- **AC-12.1:** Example validates PASS for `implementation` → `static_qa` when paths exist in fixture repo.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 13: Gate Module — `handoff_validation_check` and `run()`

### 1. Spec Summary

- **Description:** Implement `ci/scripts/gates/handoff_validation_check.py` mirroring `todo_validation_check.py` structure: discovery, normalization, catalog lookup, violations, `run(inputs)`.

- **Module constants:**
  - `GATE_NAME = "handoff_validation_check"`
  - `GATE_VERSION = "0.1.0"`
  - `DEFAULT_CHECKPOINTS_DIR = "project_board/checkpoints"`
  - `HANDOFF_SCHEMA_VERSION = "1.0"`
  - `VALID_STATUSES = frozenset({"complete", "incomplete", "deferred", "blocked"})`
  - `FENCE_PATTERN` for `yaml handoff` blocks (regex analogous to todo JSON fences)

- **`run(inputs)` required keys:** `ticket_id`, `from_agent`, `to_agent`

- **`run(inputs)` optional keys:** `checkpoints_dir`, `upstream_agent`, `downstream_agent`, `mode`, `handoff_optional`

- **FAIL remediation hints (minimum three):**
  1. Complete or block required checklist items; never hand off with required `blocked`.
  2. Refresh `project_board/checkpoints/<ticket_id>/handoff-latest.yaml` from frozen catalog templates.
  3. Re-run `python ci/scripts/gate_runner.py handoff_validation_check ...` after update.

- **Assumptions:** PyYAML import from active venv (A1).

- **Scope:** `ci/scripts/gates/` package.

### 2. Acceptance Criteria

- **AC-13.1:** `run()` missing `ticket_id` → FAIL `missing_required_input`.
- **AC-13.2:** Public function name exactly `validate_handoff_checklist`.
- **AC-13.3:** FAIL payload includes both `violations[]` and `gaps[]` or `missing_items[]`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Catalog drift vs templates | False results | Single source: spec catalogs copied to `agent_context/.../handoff_catalogs/` |

### 4. Clarifying Questions

- None.

---

## Requirement 14: Gate Registry Entry

### 1. Spec Summary

- **Description:** Register gate in `ci/scripts/gate_registry.json`.

- **Normative registry entry:**

```json
{
  "name": "handoff_validation_check",
  "module": "handoff_validation_check",
  "required_inputs": ["ticket_id", "from_agent", "to_agent"],
  "optional_inputs": ["checkpoints_dir", "upstream_agent", "downstream_agent", "mode", "handoff_optional"],
  "default_mode": "shadow",
  "description": "Validates atomic handoff YAML checklists: FAIL when required items missing, incomplete, or blocked for the finishing agent pair.",
  "category": "workflow"
}
```

- **CLI smoke:**

```bash
python ci/scripts/gate_runner.py handoff_validation_check \
  --upstream-agent "Spec Agent" \
  --downstream-agent "Test Designer Agent" \
  --ticket-id M902-23 \
  --mode shadow \
  --input '{"ticket_id":"M902-23","from_agent":"spec","to_agent":"test_designer"}'
```

- **Assumptions:** Shadow until M903 blocking enforcement.

- **Scope:** Registry + `tests/ci/test_gate_registry.py` update (implementation task).

### 2. Acceptance Criteria

- **AC-14.1:** Registry lists `handoff_validation_check` with required inputs above.
- **AC-14.2:** Shadow mode exit 0 on FAIL per M902-01.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 15: Composition with M902-20 Todo Gate

### 1. Spec Summary

- **Description:** At each stage transition, orchestrator/autopilot runs gates in **fixed order:**

1. `todo_validation_check` with `expected_agent` = finishing agent (human label)
2. `handoff_validation_check` with `from_agent` / `to_agent` = pair for transition

- **Failure handling:** If either gate FAILs in blocking mode, set ticket Stage `BLOCKED`, paste remediation and artifact paths in Blocking Issues, do not advance.

- **Shadow mode:** Both may exit 0 while reporting FAIL; agents must still remediate before handoff.

- **Assumptions:** Distinct concerns — todos vs structured checklist.

- **Scope:** `.claude/skills/autopilot/SKILL.md`, `.claude/skills/feature/SKILL.md` (implementation Task 7).

### 2. Acceptance Criteria

- **AC-15.1:** Runbook documents order todos → handoff.
- **AC-15.2:** Autopilot table lists both commands per stage (Requirement 17).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Skipping todo gate | in_progress leaks | Explicit sequence in runbook |

### 4. Clarifying Questions

- None.

---

## Requirement 16: Snapshot Writer Contract

### 1. Spec Summary

- **Description:** Finishing agent (or orchestrator immediately after agent completes) must write/overwrite `handoff-latest.yaml` **before** invoking `handoff_validation_check`.

- **Writer steps:**
  1. Copy frozen template for pair from `agent_context/agents/common_assets/handoff_catalogs/<from>__<to>.yaml` (implementation Task 5)
  2. Set each `item_key` status and evidence
  3. Compute `required_items_met` / `total_required_items` from catalog (do not inflate)
  4. Set `validated_at` to current UTC ISO 8601
  5. Optionally copy same bytes to `handoff-<run-id>.yaml` for history
  6. Refresh `todos-latest.json` per M902-20 in same commit/handoff (same run)

- **Constraints:** One active pair per `handoff-latest.yaml` file.

- **Assumptions:** Templates match spec catalogs item-for-item.

- **Scope:** All seven transitions.

### 2. Acceptance Criteria

- **AC-16.1:** Runbook states writer runs before gate.
- **AC-16.2:** Optional CLI `ci/scripts/handoff_snapshot.py` (if implemented) validates without writing when `--validate-only`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Forgotten writer | FAIL artifact missing | BLOCKED stage with remediation |

### 4. Clarifying Questions

- None.

---

## Requirement 17: Autopilot Invocation Table

### 1. Spec Summary

| Upstream Stage (finishing) | Next Stage | `expected_agent` (todo gate) | `from_agent` → `to_agent` (handoff gate) |
|----------------------------|------------|------------------------------|----------------------------------------|
| PLANNING | SPECIFICATION | Planner Agent | planner → spec |
| SPECIFICATION | TEST_DESIGN | Spec Agent | spec → test_designer |
| TEST_DESIGN | TEST_BREAK | Test Designer Agent | test_designer → test_breaker |
| TEST_BREAK | IMPLEMENTATION_GENERALIST | Test Breaker Agent | test_breaker → implementation |
| IMPLEMENTATION_* | STATIC_QA | Implementation Agent | implementation → static_qa |
| STATIC_QA | INTEGRATION | Static QA / Code Reviewer | static_qa → learning |
| INTEGRATION | COMPLETE | Learning Agent | learning → ac_gatekeeper |

- **Note:** IMPLEMENTATION_* uses whichever implementation stage is active; finishing key remains `implementation`.

- **Scope:** Orchestrator documentation and skill updates.

### 2. Acceptance Criteria

- **AC-17.1:** Table has seven rows matching Requirement 04 pairs.
- **AC-17.2:** Each row includes example `gate_runner` command with ticket id placeholder.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 18: Test Contract (Behavioral)

### 1. Spec Summary

- **Description:** Executable tests in `tests/ci/test_handoff_validation_gate.py` (docstring traces M902-23 and this spec). Use `tmp_path` + `unittest.mock`; **no assertions on ticket markdown prose**.

- **Core scenario matrix (minimum nine):**

| ID | Scenario | Pair | Expected status | Primary rule |
|----|----------|------|-----------------|--------------|
| H1 | All required complete | planner → spec | PASS | — |
| H2 | One required incomplete | spec → test_designer | FAIL | handoff_item_missing |
| H3 | Required blocked | implementation → static_qa | FAIL | handoff_blocked |
| H4 | Optional deferred with reason | implementation → static_qa | PASS | — |
| H5 | Pair mismatch in file | spec → test_designer (file says test_breaker) | FAIL | handoff_pair_mismatch |
| H6 | Missing artifact | any | FAIL | handoff_artifact_missing |
| H7 | Malformed YAML | any | FAIL | handoff_artifact_invalid |
| H8 | Inflated `required_items_met` | test_breaker → implementation | FAIL | handoff_counter_mismatch |
| H9 | `run()` + gate_runner smoke | spec → test_designer | PASS/FAIL per fixture | integration |

- **Three distinct pair vectors (ticket AC — e2e catalog fidelity):**

| Vector | Pair | Distinguishing required key |
|--------|------|------------------------------|
| V1 | spec → test_designer | `spec_edge_cases` |
| V2 | test_breaker → implementation | `breaker_gaps_documented` |
| V3 | implementation → static_qa | `impl_linter_clean` |

- **Test-breaker additions (Task 3, advisory):** empty evidence on complete, deferred required without deferrable, duplicate keys, path traversal ticket_id, fenced YAML vs file precedence, mixed-case agent names.

- **Assumptions:** Tests import `validate_handoff_checklist` and `run` from gate module; red before implementation.

- **Scope:** `tests/ci/` only.

### 2. Acceptance Criteria

- **AC-18.1:** ≥ 9 test functions or parametrized cases H1–H9.
- **AC-18.2:** V1–V3 each assert pair-specific `item_key` in FAIL or PASS fixtures.
- **AC-18.3:** No test reads `23_atomic_handoff_checkpoint.md` body for assertions.
- **AC-18.4:** Adversarial suite `tests/ci/test_handoff_validation_gate_adversarial.py` (+10 cases) per execution plan Task 3.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Fixture/catalog drift | False green | Copy item_keys from Req 05–11 verbatim |

### 4. Clarifying Questions

- None.

---

## Requirement 19: Agent Runbook

### 1. Spec Summary

- **Description:** Standalone runbook for operators (implementation path: `project_board/checkpoints/M902-23/HANDOFF_RUNBOOK.md`).

- **Must include:**
  - When to write `handoff-latest.yaml` (Requirement 16)
  - Per-pair checklist summary table (item_key + required + evidence type) — all seven catalogs
  - FAIL interpretation: read `message`, `gaps`/`missing_items`, `violations`, `remediation_hints`
  - Composition with todo gate (Requirement 15)
  - Shadow vs blocking (M903)
  - Good/bad example pointers (Requirement 20)
  - Retry policy: unlimited deterministic retries until PASS or human escalation after 3 attempts
  - Escalation: never proceed with required item `blocked`

- **Assumptions:** Agents can edit checkpoint dir under ticket id.

- **Scope:** Human and autonomous agents.

### 2. Acceptance Criteria

- **AC-19.1:** Runbook lists all seven pairs without requiring Python source.
- **AC-19.2:** Documents `handoff_optional` shadow behavior.
- **AC-19.3:** Links to frozen templates under `agent_context/agents/common_assets/handoff_catalogs/`.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 20: Good/Bad Checkpoint Examples

### 1. Spec Summary

- **Description:** Example artifacts for training and tests (implementation Task 8).

- **Paths (normative):**
  - `project_board/checkpoints/M902-23/examples/good/` — at least one valid handoff per **three** stages: SPECIFICATION (planner→spec or spec→test_designer), TEST_DESIGN (test_designer→test_breaker), IMPLEMENTATION (implementation→static_qa)
  - `project_board/checkpoints/M902-23/examples/bad/` — matching **bad** examples (missing required, blocked item, counter mismatch)
  - `project_board/checkpoints/M902-23/examples/README.md` — index with expected gate outcome PASS/FAIL

- **Constraints:** Examples must validate against Requirement 02 schema; bad examples must FAIL with named rule.

- **Assumptions:** Created during implementation, not spec stage.

- **Scope:** Documentation and optional pytest parametrization.

### 2. Acceptance Criteria

- **AC-20.1:** ≥ 3 stages represented in good examples.
- **AC-20.2:** Each bad example documents expected `violations[].rule`.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Non-Functional Requirements

### NFR-1: Determinism

Same artifact bytes + same `(ticket_id, from_agent, to_agent)` → identical `status`, `gaps` ordering (sort by `item_key`), and `violations` ordering.

### NFR-2: Performance

Complete in < 500 ms for checklists with ≤ 50 items on developer hardware.

### NFR-3: Security

- Reject path traversal in `ticket_id` and `checkpoints_dir` (same rules as M902-20).
- `yaml.safe_load` only; reject unexpected top-level types.
- No execution of evidence strings.

### NFR-4: Observability

Log INFO: artifact path chosen, pair, required count, PASS/FAIL. Log WARN: fallback to fenced YAML or secondary `handoff-*.yaml`.

---

## Deferred Boundary Statement

- **M903:** Blocking `default_mode` at CI; machine verification hooks for coverage/linter evidence.
- **M902-04:** Risk metadata on gate JSON remains separate from checklist YAML.
- **PyYAML absent in env:** Implementation must fail fast with remediation hint to `uv sync --extra dev` — no silent skip.

---

## Ticket Acceptance Criteria Traceability

| Ticket AC | Spec requirement |
|-----------|------------------|
| Per-agent handoff checklists (7 pairs) | Req 04–11 |
| YAML in checkpoint, structured validation | Req 02, 13 |
| `validate_handoff_checklist(...)` | Req 01, 13 |
| FAIL + gap list | Req 01, 03, 13 |
| 3+ pairs tested e2e | Req 18 (V1–V3 + H1–H9) |
| Agent runbook | Req 19 |
| Good/bad checkpoint examples | Req 20 |

---

## Spec Exit Gate

Before TEST_DESIGN, orchestrator runs:

```bash
python ci/scripts/spec_completeness_check.py project_board/specs/902_23_atomic_handoff_spec.md --type generic
```

Expected: exit 0.

---

## Revision History

| Revision | Date | Author | Notes |
|----------|------|--------|-------|
| 1 | 2026-05-20 | Spec Agent | Initial specification: seven catalogs, schema, API, registry, tests, runbook |

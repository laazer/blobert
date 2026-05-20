# Spec: TODO Validation Gate — TodoWrite Checkpoint Validation at Agent Handoffs

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/20_todo_validation_gates.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-20_todo_validation_gates.md`

**Agent:** Spec Agent

**Date:** 2026-05-20

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines the **`todo_validation_check`** validation gate. The gate reads TodoWrite checkpoint artifacts under `project_board/checkpoints/<ticket_id>/` and **blocks agent handoffs** (in blocking mode) when any todo **attributed to the finishing agent** remains in `in_progress` status.

Deliverables covered by this spec:

1. Public validator API: `validate_todos(ticket_id: str, expected_agent: str) -> GateResult`
2. Gate module entrypoint: `run(inputs: dict[str, Any]) -> dict[str, Any]` in `ci/scripts/gates/todo_validation_check.py`
3. Registry name: `todo_validation_check` (shadow mode default per M902-06/M903 rollout)
4. M902-01-aligned structured FAIL output with supplementary `incomplete_tasks[]`
5. Five or more explicit test scenarios with fixture inputs and expected outputs
6. Optional per-task completion timing (non-blocking)
7. Agent-facing runbook for FAIL interpretation and retry

**Out of scope (M902-20):** Calling the Cursor TodoWrite API; writing snapshots from the gate; autopilot wiring at every stage transition (documented for M902-23; gate module + registry + runbook only).

**Prerequisites:** M902-01 Validation Gate Framework (`ci/scripts/gate_runner.py`, `ci/scripts/gate_registry.json`, gate result schemas).

---

## Assumptions and Checkpoint Resolutions

| # | Ambiguity | Assumption | Confidence |
|---|-----------|------------|------------|
| A1 | Canonical on-disk TodoWrite format | Primary artifact: `project_board/checkpoints/<ticket_id>/todos-latest.json`. Optional history: `todos-<run-id>.json`. Secondary fallback: fenced JSON block in ticket-scoped `.md` checkpoint logs (see Requirement 02). | Medium |
| A2 | FAIL payload shape | Emit **both** `incomplete_tasks[]` (agent ergonomics) and `violations[]` with `rule: "todo_incomplete"` (M902-01 audit). | High |
| A3 | Optional completion timing | Non-blocking enhancement. If `started_at` / `completed_at` present, gate may attach `timing_diagnostics` on PASS/FAIL; absence does not affect PASS/FAIL. | High |
| A4 | Orchestrator wiring | M902-20 delivers gate + registry + runbook. Autopilot must **document** invocation at stage transitions; automatic wiring lands in M902-23 unless expanded later. | Medium |
| A5 | Malformed artifacts | **Fail-closed:** unreadable or schema-invalid primary artifact → `FAIL` with `rule: "todo_artifact_invalid"` (not vacuous PASS). | High |
| A6 | Unattributed todos | Todos with no resolvable agent attribution are **excluded** from validation (neither PASS nor FAIL driver for `expected_agent`). | High |
| A7 | `GateResult` type | `GateResult` is a `TypedDict` / `dict[str, Any]` conforming to M902-01 gate output fields; `validate_todos` returns the gate payload **before** gate_runner envelope merge (runner adds `upstream_agent`, `downstream_agent`, `mode`, artifact paths). | High |

---

## Requirement 01: Public API — `validate_todos`

### 1. Spec Summary

- **Description:** Pure function that loads the effective todo snapshot for a ticket, filters todos to those attributed to `expected_agent`, and returns PASS if none remain `in_progress`; otherwise FAIL with structured incomplete-task detail.

- **Signature (implementation contract):**

```python
def validate_todos(ticket_id: str, expected_agent: str) -> GateResult:
    ...
```

- **Parameters:**
  - `ticket_id`: Short ticket tag (e.g. `M902-20`). Normalized to uppercase with hyphen (`M902_20` → `M902-20`). Used to resolve `project_board/checkpoints/<ticket_id>/`.
  - `expected_agent`: Human agent name of the **finishing** upstream agent (e.g. `Spec Agent`, `Implementation Agent (Generalist)`). Normalized per Requirement 04 before matching.

- **Return (`GateResult`):** Dict including at minimum:
  - `version` (string, `"0.1.0"`)
  - `status` (`"PASS"` | `"FAIL"`)
  - `gate` (string, `"todo_validation_check"`)
  - `ticket_id` (string, normalized)
  - `timestamp` (ISO 8601 UTC)
  - `message` (string)
  - `violations` (list, empty on PASS)
  - `remediation_hints` (list of strings)
  - `incomplete_tasks` (list, empty on PASS) — supplementary; see Requirement 06
  - `artifacts` (list of `{path, sha256}` for snapshot files read; may be empty on vacuous PASS)
  - `duration_ms` (integer)

- **Constraints:**
  - Stdlib + existing repo patterns only; no TodoWrite API calls.
  - Must not mutate checkpoint files.
  - Path resolution must reject directory traversal (`..`, absolute paths outside repo root).
  - Default checkpoints root: `project_board/checkpoints/<ticket_id>/` relative to repo root.

- **Assumptions:** Repo root is cwd when invoked from `gate_runner` or tests.

- **Scope:** All multi-agent tickets using TodoWrite snapshots under `project_board/checkpoints/`.

### 2. Acceptance Criteria

- **AC-01.1:** `validate_todos("M902-20", "Spec Agent")` with all attributed todos `completed` returns `status: "PASS"`.
- **AC-01.2:** One attributed todo `in_progress` returns `status: "FAIL"` and exactly one entry in `incomplete_tasks`.
- **AC-01.3:** Multiple attributed `in_progress` todos return `status: "FAIL"` with all listed in `incomplete_tasks` (stable sort by `id`, then `content`).
- **AC-01.4:** No snapshot files under ticket directory returns `status: "PASS"` (vacuous) with `message` indicating no todos found.
- **AC-01.5:** Snapshot with `"todos": []` returns `status: "PASS"` (vacuous empty list).
- **AC-01.6:** Prior-agent `in_progress` todos (different agent attribution) do not cause FAIL when `expected_agent` todos are all `completed`.
- **AC-01.7:** Invalid JSON in primary artifact returns `status: "FAIL"` with `violations[].rule == "todo_artifact_invalid"`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agents never write snapshots | Gate always vacuous PASS | Runbook + M902-23 writer; tests use fixtures |
| Agent name drift | False PASS (no match) or false FAIL | Normalization table (Requirement 04) |
| Stale `todos-latest.json` | Wrong handoff decision | Document orchestrator must refresh snapshot before gate call |

### 4. Clarifying Questions

- None (resolved via checkpoint protocol A1–A7).

---

## Requirement 02: Todo Snapshot Artifact Contract

### 1. Spec Summary

- **Description:** Defines the canonical on-disk format agents/orchestrators write after TodoWrite usage so the gate can read deterministic state.

- **Primary artifact (authoritative):**

  Path: `project_board/checkpoints/<ticket_id>/todos-latest.json`

  Encoding: UTF-8 JSON object (not array at root).

- **Envelope schema (`TodoSnapshot`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Must be `"1.0"` for this spec revision |
| `ticket_id` | string | yes | Must match directory name after normalization |
| `agent` | string | yes | Agent that produced this snapshot (envelope attribution) |
| `captured_at` | string | yes | ISO 8601 UTC timestamp when snapshot was written |
| `todos` | array | yes | List of todo records (may be empty) |

- **Todo record schema (`TodoRecord`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Stable todo id (opaque string; unique within snapshot) |
| `content` | string | yes | Imperative task description |
| `status` | string | yes | One of: `pending`, `in_progress`, `completed`, `cancelled` |
| `activeForm` | string | no | Present-tense form for UI; if omitted, use `content` in outputs |
| `agent` | string | no | Per-todo attribution override; if omitted, inherit envelope `agent` |
| `updated_at` | string | no | ISO 8601 UTC last status change |
| `started_at` | string | no | ISO 8601 UTC when moved to `in_progress` (optional timing) |
| `completed_at` | string | no | ISO 8601 UTC when moved to `completed` (optional timing) |

- **Optional history artifacts:** `project_board/checkpoints/<ticket_id>/todos-<run-id>.json` — same schema as `todos-latest.json`. Gate **does not merge** history files when `todos-latest.json` exists.

- **Discovery precedence (effective snapshot):**
  1. `todos-latest.json` if present and valid JSON object
  2. Else newest by file mtime among `todos-*.json` excluding `todos-latest.json`
  3. Else newest fenced JSON block in `*.md` under the ticket checkpoint directory (see below)
  4. Else no snapshot → vacuous PASS (Requirement 05)

- **Fenced JSON fallback (secondary):** In `project_board/checkpoints/<ticket_id>/*.md`, locate blocks:

  ` ```json todos ` … ` ``` `

  or legacy alias ` ```json todo-snapshot ` … ` ``` `

  Parse inner JSON as `TodoSnapshot`. If multiple blocks exist, use the block from the **newest file by mtime**; if same file, use the **last** block in file.

- **Constraints:**
  - Gate read-only.
  - `ticket_id` in envelope must match normalized gate input or artifact is invalid (`FAIL`).
  - Unknown `status` values → treat as invalid record → `FAIL` (`todo_artifact_invalid`).
  - Duplicate `id` in one snapshot → `FAIL` (`todo_artifact_invalid`).

- **Assumptions:** Writers refresh `todos-latest.json` on each TodoWrite batch at end of agent run (orchestrator responsibility per M902-23).

- **Scope:** Checkpoint tree only; not `project_board/CHECKPOINTS.md` index.

### 2. Acceptance Criteria

- **AC-02.1:** Valid `todos-latest.json` is selected over older `todos-2026-05-20T-spec.json`.
- **AC-02.2:** Missing `todos-latest.json` falls back to newest `todos-*.json` by mtime.
- **AC-02.3:** Example envelope with two todos parses both records.
- **AC-02.4:** Markdown fenced block is parsed when no JSON files exist.
- **AC-02.5:** `schema_version` other than `"1.0"` → FAIL invalid artifact.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dual writers race on `todos-latest.json` | Corrupt JSON | Fail-closed invalid JSON handling |
| Large todo lists | Slow gate | NFR: complete < 500 ms for 500 todos |

### 4. Clarifying Questions

- None.

---

## Requirement 03: Validation Semantics — Status and Blocking Rules

### 1. Spec Summary

- **Description:** Defines which todo statuses constitute a handoff violation for the finishing agent.

- **Blocking rule:** For todos **attributed** to `expected_agent` (Requirement 04), any record with `status == "in_progress"` causes **FAIL**.

- **Non-blocking statuses (do not fail):**
  - `completed` — task done
  - `pending` — not started or explicitly deferred
  - `cancelled` — explicitly abandoned

- **Vacuous PASS conditions:**
  - No snapshot discovered (Requirement 02 step 4)
  - Snapshot exists with `"todos": []`
  - No todos attributed to `expected_agent` after filtering (e.g. only other agents' todos)

- **Handoff intent:** Agents must move finished work to `completed` before stage advance. Using `pending` or `cancelled` instead of leaving `in_progress` is allowed and does not block.

- **Constraints:** Gate does not require historical proof that status transitioned from `in_progress` → `completed`; it only inspects **current** snapshot state.

- **Assumptions:** TodoWrite tool statuses align with Cursor: `pending`, `in_progress`, `completed`, `cancelled`.

- **Scope:** Attributed todos only.

### 2. Acceptance Criteria

- **AC-03.1:** All attributed todos `completed` → PASS.
- **AC-03.2:** One attributed `in_progress` → FAIL.
- **AC-03.3:** Attributed `pending` and `cancelled` with zero `in_progress` → PASS.
- **AC-03.4:** Empty todos array → PASS.
- **AC-03.5:** No artifacts → PASS with message containing `no todo` (case-insensitive substring acceptable).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent leaves work in `pending` though unfinished | Silent handoff | Out of scope; human review / future strict mode |
| `in_progress` with wrong agent label | Bypass attempt | Attribution rules + test-breaker cases |

### 4. Clarifying Questions

- None.

---

## Requirement 04: Agent Attribution and Name Normalization

### 1. Spec Summary

- **Description:** Only todos owned by `expected_agent` are validated. Prior agents' `in_progress` items must not block the current handoff.

- **Attribution resolution (per todo, first match wins):**
  1. Todo record `agent` field if non-empty string
  2. Else envelope `agent` on `TodoSnapshot`
  3. Else **unattributed** → exclude from validation set

- **Normalization:** Map both `expected_agent` and resolved todo agent through `normalize_agent_name()`:

  - Trim whitespace
  - Lowercase for comparison key
  - Strip parenthetical qualifiers for key only: `(Generalist)` removed from key
  - Map aliases to canonical keys via table below
  - Comparison uses canonical **key** equality

- **Canonical agent keys and aliases:**

| Canonical key | Accepted aliases (case-insensitive) |
|---------------|-------------------------------------|
| `planner` | Planner Agent, planner agent, planner |
| `spec` | Spec Agent, spec agent, specification agent |
| `test_designer` | Test Designer Agent, test designer, test-designer |
| `test_breaker` | Test Breaker Agent, test breaker |
| `implementation` | Implementation Agent, Implementation Agent (Generalist), implementation agent, generalist |
| `static_qa` | Static QA, Code Reviewer, python-reviewer |
| `integration` | Integration Agent, Documenter |
| `learning` | Learning Agent |
| `ac_gatekeeper` | AC Gatekeeper, Acceptance Criteria Gatekeeper |

- **Display name in output:** Use original `expected_agent` string in `violations` / messages where agent label is shown; include normalized key in `incomplete_tasks[].agent_key` (see Requirement 06).

- **Constraints:** Unknown agent strings normalize to a slug key: lowercase, spaces → underscores (e.g. `"Custom Agent"` → `custom_agent`). Matching is exact on slug key after normalization.

- **Assumptions:** Orchestrator passes the same agent string used in ticket `Last Updated By` when possible.

- **Scope:** All gate invocations.

### 2. Acceptance Criteria

- **AC-04.1:** `expected_agent="Spec Agent"` matches todo with envelope `agent: "spec agent"`.
- **AC-04.2:** `in_progress` todo with `agent: "Planner Agent"` does not fail gate for `expected_agent="Spec Agent"`.
- **AC-04.3:** Todo with no `agent` field uses envelope agent for attribution.
- **AC-04.4:** Todo with no resolvable agent is excluded; gate PASS if no other attributed `in_progress`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| New agent types not in table | Slug fallback still deterministic | Extend table in registry doc when agents added |

### 4. Clarifying Questions

- None.

---

## Requirement 05: Gate Module — `run()` and `gate_runner` Integration

### 1. Spec Summary

- **Description:** Gate module `ci/scripts/gates/todo_validation_check.py` exposes `run(inputs) -> dict` that delegates to `validate_todos` and returns M902-01-compatible dict for `gate_runner`.

- **`run(inputs)` contract:**

| Input key | Required | Description |
|-----------|----------|-------------|
| `ticket_id` | yes | Short ticket id |
| `expected_agent` | yes | Finishing upstream agent |
| `checkpoints_dir` | no | Override root; default `project_board/checkpoints` |
| `upstream_agent` | no | Echoed in output; default `expected_agent` |
| `downstream_agent` | no | Echoed in output; default `""` |
| `mode` | no | `shadow` or `blocking`; echoed in output |

- **`run()` behavior:**
  1. Resolve `checkpoints_dir / ticket_id /` (normalized ticket id)
  2. Call `validate_todos(ticket_id, expected_agent)` with resolved paths
  3. Merge runner-provided `upstream_agent`, `downstream_agent`, `mode` into result if present in `inputs`
  4. Set `gate` to `"todo_validation_check"`
  5. Return dict

- **Gate runner invocation:**

```bash
python ci/scripts/gate_runner.py todo_validation_check \
  --upstream-agent "Spec Agent" \
  --downstream-agent "Test Designer Agent" \
  --ticket-id M902-20 \
  --mode shadow \
  --input '{"ticket_id":"M902-20","expected_agent":"Spec Agent"}'
```

- **Exit codes (via gate_runner):** Shadow: 0 even on FAIL. Blocking: 1 on FAIL.

- **Constraints:** Module must be importable from `ci/scripts/gates/` without extra dependencies.

- **Assumptions:** M902-01 gate_runner writes results to `project_board/checkpoints/<ticket_id>/gate-results/`.

- **Scope:** CLI and programmatic test invocation.

### 2. Acceptance Criteria

- **AC-05.1:** `run({"ticket_id": "M902-20", "expected_agent": "Spec Agent"})` returns dict with `gate == "todo_validation_check"`.
- **AC-05.2:** Missing `ticket_id` or `expected_agent` → FAIL with `rule: "missing_required_input"`.
- **AC-05.3:** `gate_runner` smoke command succeeds (exit 0 in shadow) once module registered.
- **AC-05.4:** `checkpoints_dir` override used in tests via `tmp_path` without touching repo checkpoints.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Required input validation diverges from registry | Runner confusion | Registry `required_inputs` aligned in Requirement 07 |

### 4. Clarifying Questions

- None.

---

## Requirement 06: FAIL Payload — `incomplete_tasks`, `violations`, Remediation

### 1. Spec Summary

- **Description:** Structured FAIL output for agents and audit systems.

- **`incomplete_tasks[]` entry schema:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Todo id |
| `content` | string | Todo content |
| `activeForm` | string | `activeForm` or `content` |
| `status` | string | Always `"in_progress"` for this array |
| `agent` | string | Display agent name (resolved attribution) |
| `agent_key` | string | Normalized canonical key |

- **Parallel `violations[]` entry (one per incomplete todo):**

| Field | Value |
|-------|-------|
| `file` | Path to effective snapshot file, or `project_board/checkpoints/<ticket_id>/` if vacuous path N/A use directory path |
| `line` | `null` |
| `rule` | `"todo_incomplete"` |
| `message` | `"Todo still in_progress: <content> (agent=<agent>)"` |
| `severity` | `"ERROR"` |

- **Top-level FAIL fields:**

| Field | Requirement |
|-------|-------------|
| `status` | `"FAIL"` |
| `message` | `"<N> task(s) remain in_progress for <expected_agent>. Agent should complete or explicitly move to pending/cancelled."` where N = len(incomplete_tasks) |
| `remediation_hints` | At least: (1) Run TodoWrite to set finished items to `completed`; (2) Defer with `pending` or abandon with `cancelled` — never leave finished work in `in_progress`; (3) Refresh `todos-latest.json` before re-running gate |
| `remediation` | Optional duplicate of primary hint string for ticket example compatibility |

- **Example FAIL (normative shape):**

```json
{
  "version": "0.1.0",
  "status": "FAIL",
  "gate": "todo_validation_check",
  "ticket_id": "M902-20",
  "timestamp": "2026-05-20T18:00:00Z",
  "message": "2 task(s) remain in_progress for Spec Agent. Agent should complete or explicitly move to pending/cancelled.",
  "incomplete_tasks": [
    {
      "id": "t1",
      "content": "Draft acceptance criteria section",
      "activeForm": "Drafting acceptance criteria section",
      "status": "in_progress",
      "agent": "Spec Agent",
      "agent_key": "spec"
    },
    {
      "id": "t2",
      "content": "Map test scenarios to AC ids",
      "activeForm": "Mapping test scenarios to AC ids",
      "status": "in_progress",
      "agent": "Spec Agent",
      "agent_key": "spec"
    }
  ],
  "violations": [
    {
      "file": "project_board/checkpoints/M902-20/todos-latest.json",
      "line": null,
      "rule": "todo_incomplete",
      "message": "Todo still in_progress: Draft acceptance criteria section (agent=Spec Agent)",
      "severity": "ERROR"
    },
    {
      "file": "project_board/checkpoints/M902-20/todos-latest.json",
      "line": null,
      "rule": "todo_incomplete",
      "message": "Todo still in_progress: Map test scenarios to AC ids (agent=Spec Agent)",
      "severity": "ERROR"
    }
  ],
  "remediation_hints": [
    "Run TodoWrite to move completed tasks to 'completed' status before handing off.",
    "For deferred work use 'pending' or 'cancelled' — do not leave finished work in 'in_progress'.",
    "Update project_board/checkpoints/<ticket_id>/todos-latest.json then re-run todo_validation_check."
  ],
  "artifacts": [],
  "duration_ms": 3
}
```

- **PASS message:** `"All todos completed for <expected_agent>."` or vacuous: `"No todo snapshots found for <ticket_id>; vacuous PASS."` / `"Empty todo list; vacuous PASS."`

- **Assumptions:** `gate_name` in ticket example maps to `gate` field per M902-01.

- **Scope:** All FAIL paths.

### 2. Acceptance Criteria

- **AC-06.1:** FAIL includes `incomplete_tasks` length equal to count of attributed `in_progress` todos.
- **AC-06.2:** Each incomplete todo has a matching `violations` entry with `rule: "todo_incomplete"`.
- **AC-06.3:** `remediation_hints` length >= 3 on FAIL.
- **AC-06.4:** PASS has empty `incomplete_tasks` and `violations`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Duplicate fields drift from M902-01 schema | Consumer breakage | Test against gate schema fixtures |

### 4. Clarifying Questions

- None.

---

## Requirement 07: Gate Registry Entry

### 1. Spec Summary

- **Description:** Register `todo_validation_check` in `ci/scripts/gate_registry.json`.

- **Registry entry (normative):**

```json
{
  "name": "todo_validation_check",
  "module": "todo_validation_check",
  "required_inputs": ["ticket_id", "expected_agent"],
  "optional_inputs": ["checkpoints_dir", "upstream_agent", "downstream_agent", "mode"],
  "default_mode": "shadow",
  "description": "Validates TodoWrite checkpoint snapshots: blocks handoff when todos attributed to the finishing agent remain in_progress.",
  "category": "workflow"
}
```

- **Constraints:** `name` globally unique; `module` resolves to `ci/scripts/gates/todo_validation_check.py`.

- **Assumptions:** Shadow mode until M903 enforcement ticket enables blocking at transitions.

- **Scope:** Registry file + doc tests enumerating gate names.

### 2. Acceptance Criteria

- **AC-07.1:** Registry contains entry with `name: "todo_validation_check"`.
- **AC-07.2:** `tests/ci/test_gate_registry.py` includes new gate after implementation.
- **AC-07.3:** Documentation structure tests updated in same change set as registry (per execution plan Task 5).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Doc test drift | CI fail | Single commit updates all gate name lists |

### 4. Clarifying Questions

- None.

---

## Requirement 08: Test Scenarios (Behavioral, Minimum Five)

### 1. Spec Summary

- **Description:** Executable tests in `tests/ci/test_todo_validation_gate.py` (module docstring traces M902-20 and this spec path). Tests use `tmp_path` fixtures; **no assertions on ticket markdown prose**.

- **Scenario matrix (minimum seven cases):**

| ID | Scenario | Fixture setup | `expected_agent` | Expected `status` | Expected `incomplete_tasks` count |
|----|----------|---------------|------------------|-------------------|-----------------------------------|
| T1 | All completed | 2 todos, both `completed`, envelope `agent: Spec Agent` | Spec Agent | PASS | 0 |
| T2 | One incomplete | 1 todo `in_progress`, 1 `completed` | Spec Agent | FAIL | 1 |
| T3 | Multiple incomplete | 3 todos `in_progress` | Spec Agent | FAIL | 3 |
| T4 | No artifacts | Empty ticket dir | Spec Agent | PASS (vacuous) | 0 |
| T5 | Empty list | `todos: []` | Spec Agent | PASS (vacuous) | 0 |
| T6 | Prior-agent regression | Planner `in_progress` + Spec all `completed` | Spec Agent | PASS | 0 |
| T7 | Malformed artifact | Invalid JSON in `todos-latest.json` | Spec Agent | FAIL | 0 (use `violations` `todo_artifact_invalid`) |

- **Additional test-breaker targets (Task 3, not all required for M902-20 COMPLETE):** duplicate ids, conflicting snapshots (latest wins), wrong expected_agent, case/whitespace names, `pending`/`cancelled` not failing, missing `status`, fenced JSON in `.md`.

- **Assumptions:** Tests call `validate_todos` and `run()` directly.

- **Scope:** `tests/ci/` only.

### 2. Acceptance Criteria

- **AC-08.1:** At least 7 test functions or parametrized cases covering T1–T7.
- **AC-08.2:** Tests fail (red) before `todo_validation_check.py` exists.
- **AC-08.3:** T6 proves planner `in_progress` does not fail Spec Agent gate.
- **AC-08.4:** No test reads `project_board/**/20_todo_validation_gates.md` content for assertions.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Fixture/schema drift | False green tests | Copy envelope examples from Requirement 02 verbatim |

### 4. Clarifying Questions

- None.

---

## Requirement 09: Optional Completion Timing Diagnostics

### 1. Spec Summary

- **Description:** When todo records include `started_at` and/or `completed_at`, the gate may compute non-blocking diagnostics.

- **Rules:**
  - If `completed_at` and `started_at` present: `duration_seconds = (completed_at - started_at).total_seconds()`
  - Flag `slow_task` when `duration_seconds > 3600` (1 hour) — threshold fixed constant in module
  - Attach on result: `timing_diagnostics: { "slow_tasks": [ { "id", "content", "duration_seconds" } ] }` only when at least one slow task exists
  - **Does not change** PASS/FAIL status

- **Constraints:** Missing timestamps → omit diagnostics silently.

- **Assumptions:** AC Gatekeeper may mark optional AC N/A if not implemented.

- **Scope:** Enhancement only.

### 2. Acceptance Criteria

- **AC-09.1:** If not implemented, gate still passes all T1–T7 without `timing_diagnostics` key.
- **AC-09.2:** If implemented, slow task listed only when duration > 3600s; PASS/FAIL unchanged.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Clock skew in timestamps | Nonsense durations | Ignore negative durations |

### 4. Clarifying Questions

- None.

---

## Requirement 10: Agent Runbook — FAIL Interpretation and Retry

### 1. Spec Summary

- **Description:** Agents must interpret FAIL without reading source. Runbook lives in this spec (summary) and **`project_board/checkpoints/M902-20/TODO_VALIDATION_RUNBOOK.md`** (implementation Task 8 copies or expands).

- **When to run:** After upstream agent completes work, before advancing ticket Stage to next agent (orchestrator/autopilot; full wiring M902-23).

- **FAIL interpretation steps:**
  1. Read `message` for count and agent
  2. For each `incomplete_tasks[]` item, finish work or change status via TodoWrite
  3. Apply `remediation_hints` in order
  4. Persist `todos-latest.json` under ticket checkpoint dir
  5. Re-invoke `gate_runner.py todo_validation_check` with same `ticket_id` and `expected_agent`

- **Retry policy:** Unlimited retries until PASS or human escalation; gate is deterministic on same snapshot bytes.

- **Shadow vs blocking:** Until M903, FAIL is informational (exit 0). Agents should still remediate before handoff.

- **Escalation:** If FAIL persists after 3 remediation attempts with confirmed completed work, set ticket `Blocking Issues` with gate output path and route Human.

- **Assumptions:** Agents have TodoWrite tool in Cursor.

- **Scope:** Multi-agent workflow operators.

### 2. Acceptance Criteria

- **AC-10.1:** Runbook section lists all FAIL JSON fields agents need (`status`, `incomplete_tasks`, `violations`, `remediation_hints`).
- **AC-10.2:** Runbook documents `pending`/`cancelled` as acceptable alternatives to `completed` for deferred/abandoned work.
- **AC-10.3:** Runbook includes example `gate_runner` command from Requirement 05.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Runbook not created in Task 8 | Agents lack standalone doc | This requirement duplicates minimum content |

### 4. Clarifying Questions

- None.

---

## Non-Functional Requirements

### NFR-1: Determinism

Same snapshot bytes + same `expected_agent` → identical `status`, `incomplete_tasks`, and `violations` ordering.

### NFR-2: Performance

Complete in < 500 ms for snapshots with ≤ 500 todos on developer hardware.

### NFR-3: Security

- Resolve paths under repo root only; reject `..` segments in `checkpoints_dir` and `ticket_id`.
- No code execution from snapshot content.

### NFR-4: Observability

Log at INFO: snapshot path chosen, todo count, attributed count, PASS/FAIL. Log at WARN: fallback to fenced JSON or secondary `todos-*.json`.

---

## Deferred Boundary Statement

- **M902-23:** Autopilot atomic handoff may own snapshot **writer** and automatic gate invocation at every transition.
- **M903:** Blocking enforcement (`default_mode: "blocking"`) at CI/orchestrator level.
- **TodoWrite API:** No direct tool integration in M902-20.

---

## Ticket Acceptance Criteria Traceability

| Ticket AC | Spec requirement |
|-----------|------------------|
| `validate_todos(...)` API | Req 01 |
| in_progress → completed validation | Req 03 |
| Detect incomplete / block | Req 03, 06 |
| Structured error + remediation | Req 06 |
| Registry `todo_validation_check` | Req 07 |
| 5+ test scenarios | Req 08 (T1–T7) |
| Optional completion timing | Req 09 |
| Runbook | Req 10 |

---

## Spec Exit Gate

Before TEST_DESIGN, orchestrator runs:

```bash
python ci/scripts/spec_completeness_check.py project_board/specs/902_20_todo_validation_spec.md --type generic
```

Expected: exit 0 (generic type has no mandatory extra sections).

---

## Revision History

| Revision | Date | Author | Notes |
|----------|------|--------|-------|
| 1 | 2026-05-20 | Spec Agent | Initial specification |

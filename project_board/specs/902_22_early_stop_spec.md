# Spec: Early-Stop Detection — Agent Loop Stagnation & Escalation

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/22_early_stop_detection.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-22_early_stop_detection.md`

**Agent:** Spec Agent

**Date:** 2026-05-20

**Status:** SPECIFICATION

**Revision:** 1

**Ticket type:** `generic`

---

## Executive Summary

This specification defines **post-invocation** detection of agent-loop stagnation: repeated errors, identical diffs, no-op tool rounds, and max-iteration ceilings. It persists per-loop evidence at `project_board/checkpoints/<ticket_id>/agent_iterations.json`, evaluates heuristics after each iteration when `loop_mode` is active, logs detections with full context, and returns a structured escalation payload so the orchestrator **breaks the loop** and hands off to an alternate agent or Human.

**In scope:**

1. Recorder + evaluator module `ci/scripts/early_stop_tracker.py` (`record_iteration`, `evaluate_early_stop`)
2. Middleware hook `_maybe_record_early_stop_iteration` in `ci/scripts/agent_invocation_middleware.py` (sibling to `_maybe_record_context_budget`)
3. `agent_iterations.json` schema, merge semantics, path safety (reuse `context_budget_tracker` helpers)
4. Error normalization, `diff_hash`, `modified_files` discovery contract
5. Heuristics: same normalized error **3×** consecutive → escalate; same `diff_hash` **3×** → escalate; tools invoked + no file changes **2×** → **flag only**; `max_iterations` default **5** → escalate
6. Escalation payload + append-only escalation event log under ticket checkpoint dir
7. Orchestrator/autopilot contract (`loop_mode`, break-loop duty)
8. Normative agent runbook content (implementation may materialize as `project_board/checkpoints/M902-22/EARLY_STOP_RUNBOOK.md`)

**Out of scope:**

- M902-23 atomic handoff gate wiring (may consume same checkpoint paths later)
- Registering `early_stop_check` in `gate_registry.json` by default (orchestrator-direct evaluate; optional gate module only if a follow-up ticket mandates M902-01 symmetry)
- Per-gate PASS/FAIL risk scoring (`escalation_detectors.py`, M902-15 override suppression)
- Changing `context_budget_tracker.py` behavior beyond shared import of path helpers

**Prerequisites (satisfied):** M902-01 Validation Gate Framework; M902-18a Framework Integration (`agent_invocation_middleware.py`); M902-21 Context Budget Tracking (checkpoint path patterns).

---

## Assumptions and Checkpoint Resolutions

| # | Ambiguity | Resolution (normative) | Confidence |
|---|-----------|------------------------|------------|
| A1 | `diff_hash` source | Prefer orchestrator-injected `diff_hash` + `modified_files` in `iteration_context`; else compute from repo `git status --porcelain` + bounded `git diff` (Requirement 04). Empty tree → `EMPTY_DIFF_HASH` constant. | Medium |
| A2 | No-op severity | Two consecutive no-op iterations set `no_op_flag` and rollup `no_op_streak`; **`should_escalate` remains `false`** unless `max_iterations` or error/diff repetition triggers. Ticket “flag” ≠ loop break alone. | High |
| A3 | Gate vs orchestrator | **`evaluate_early_stop()`** is invoked from middleware/orchestrator; not required in `gate_runner` shadow path for M902-22. | High |
| A4 | `loop_mode` | Early-stop hook runs **only** when `framework_kwargs["loop_mode"] is True`. Missing/false → skip record and evaluate (DEBUG once per process). | High |
| A5 | Error text source | Extraction order in Requirement 03; stderr-only failures must be supplied by orchestrator in `iteration_context` or `framework_kwargs`. | Medium |
| A6 | `workflow_enforcement_v1.md` | Referenced in execution plan; file not present in repo at spec time — workflow rules in ticket NEXT ACTION and this spec govern handoff. | Low |

---

## Deferred Boundary Statement

- **M902-23 handoff checklist:** Escalation file format for atomic handoff is not frozen here; M902-23 may read `agent_iterations.json` and `early_stop_events.jsonl`.
- **Gate runner registration:** Default delivery is orchestrator-direct; no `gate_registry.json` entry required for AC satisfaction.
- **Failed framework invocations:** Iteration is recorded only after **successful** `framework_invocation_fn` return (same as M902-21). Failed calls are out of scope unless orchestrator passes `iteration_context` on a separate failure hook (future ticket).
- **Single-shot planner/spec/test-designer calls:** No `loop_mode` → no early-stop side effects.

---

## Requirement 01: Artifact Path & File Lifecycle

### 1. Spec Summary

- **Description:** Each ticket loop accumulates iterations in one JSON file under its checkpoint directory. Escalation events append to a JSONL sibling.

- **Paths:**
  - `project_board/checkpoints/<ticket_id>/agent_iterations.json`
  - `project_board/checkpoints/<ticket_id>/early_stop_events.jsonl` (append-only, one JSON object per line)

- **ticket_id normalization:** Reuse `normalize_ticket_id` from `ci/scripts/context_budget_tracker.py` (e.g. `M902_22` → `M902-22`; reject `/`, `..`, NUL).

- **checkpoints_root:** Optional override via `checkpoints_root` in kwargs; must pass `checkpoints_root_allowed()` (repo root or cwd anchor).

- **Constraints:**
  - UTF-8 JSON, `indent=2`, `ensure_ascii=False` for `agent_iterations.json`.
  - Thread-safe merge via per-path lock (same pattern as `context_budget_tracker._lock_for`).
  - Tracking exceptions in middleware **must not** break invocations (log + swallow).

- **Assumptions:** CWD is repository root for middleware and tests.

- **Scope:** Multi-iteration implementation loops with `loop_mode=true`.

### 2. Acceptance Criteria

- **AC-01.1:** First `record_iteration` for `M902-22` creates `project_board/checkpoints/M902-22/agent_iterations.json` with normalized `ticket_id`.
- **AC-01.2:** Second iteration **appends** to `iterations[]` without removing prior entries (same `loop_run_id`).
- **AC-01.3:** Invalid `ticket_id` → `ValueError`; no file written outside checkpoints root.
- **AC-01.4:** Corrupt existing JSON on merge → `ValueError` or `json.JSONDecodeError`; no partial overwrite.

### 3. Risk & Ambiguity Analysis

- Concurrent loops on same ticket with different `loop_run_id` — Requirement 05 resets iteration list.

### 4. Clarifying Questions

- None.

---

## Requirement 02: `agent_iterations.json` Schema

### 1. Spec Summary

- **Description:** Normative JSON structure for loop iteration history and rollup fields recomputed on every merge.

#### Top-level object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Always `"1.0.0"` for M902-22 |
| `ticket_id` | string | yes | Normalized ticket id |
| `ticket_path` | string \| null | no | Repo-relative ticket `.md` if known |
| `agent` | string | yes | Normalized agent type for this loop (e.g. `implementation`) |
| `loop_run_id` | string | yes | UUID or orchestrator run id; change resets `iterations` |
| `created_at` | string | yes | ISO 8601 UTC; set on first write |
| `updated_at` | string | yes | ISO 8601 UTC; refreshed each merge |
| `iterations` | array | yes | Ordered iteration records (below) |
| `rollup` | object | yes | Recomputed each merge (below) |
| `last_evaluation` | object \| null | no | Snapshot of latest `evaluate_early_stop` result |

#### Iteration record (`iterations[]` element)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `iteration` | int | yes | 1-based index within current `loop_run_id` |
| `agent_run_id` | string | yes | Unique id for this invocation |
| `recorded_at` | string | yes | ISO 8601 UTC |
| `error` | string | yes | **Normalized** error for repetition compare (may be `""`) |
| `diff_hash` | string | yes | 64-char lowercase hex SHA-256 (Requirement 04) |
| `modified_files` | array of string | yes | Repo-relative paths; sorted unique ascending |
| `tools_invoked` | bool | yes | True if agent reported tool use this iteration |
| `no_op_flag` | bool | no | True when `tools_invoked` and `modified_files` empty |
| `escalation_triggered` | bool | no | True when evaluate set escalate on this iteration |
| `reason` | string \| null | no | Machine reason code when `escalation_triggered` |

#### Rollup object (`rollup`)

| Field | Type | Description |
|-------|------|-------------|
| `iteration_count` | int | `len(iterations)` |
| `last_error` | string | `error` from last iteration |
| `last_diff_hash` | string | `diff_hash` from last iteration |
| `error_repeat_streak` | int | Length of trailing consecutive iterations with same non-empty normalized `error` |
| `diff_repeat_streak` | int | Length of trailing consecutive iterations with same `diff_hash` |
| `no_op_streak` | int | Length of trailing consecutive iterations with `no_op_flag` |
| `should_escalate` | bool | Result of evaluate after last record (default `false`) |
| `escalate_reason` | string \| null | Primary reason code if `should_escalate` |

#### Example (normative shape; aligns with ticket)

```json
{
  "schema_version": "1.0.0",
  "ticket_id": "M902-09",
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/09_example.md",
  "agent": "implementation",
  "loop_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-05-20T14:00:00Z",
  "updated_at": "2026-05-20T14:12:00Z",
  "iterations": [
    {
      "iteration": 1,
      "agent_run_id": "run-001",
      "recorded_at": "2026-05-20T14:01:00Z",
      "error": "ruff: E501 line too long",
      "diff_hash": "abc123def4567890abcdef1234567890abcdef1234567890abcdef1234567890",
      "modified_files": ["asset_generation/python/src/main.py"],
      "tools_invoked": true,
      "no_op_flag": false
    },
    {
      "iteration": 2,
      "agent_run_id": "run-002",
      "recorded_at": "2026-05-20T14:05:00Z",
      "error": "ruff: E501 line too long",
      "diff_hash": "abc123def4567890abcdef1234567890abcdef1234567890abcdef1234567890",
      "modified_files": ["asset_generation/python/src/main.py"],
      "tools_invoked": true,
      "no_op_flag": false
    },
    {
      "iteration": 3,
      "agent_run_id": "run-003",
      "recorded_at": "2026-05-20T14:12:00Z",
      "error": "ruff: E501 line too long",
      "diff_hash": "abc123def4567890abcdef1234567890abcdef1234567890abcdef1234567890",
      "modified_files": ["asset_generation/python/src/main.py"],
      "tools_invoked": true,
      "no_op_flag": false,
      "escalation_triggered": true,
      "reason": "repeated_error"
    }
  ],
  "rollup": {
    "iteration_count": 3,
    "last_error": "ruff: E501 line too long",
    "last_diff_hash": "abc123def4567890abcdef1234567890abcdef1234567890abcdef1234567890",
    "error_repeat_streak": 3,
    "diff_repeat_streak": 3,
    "no_op_streak": 0,
    "should_escalate": true,
    "escalate_reason": "repeated_error"
  },
  "last_evaluation": null
}
```

- **Constraints:** Unknown fields in incoming payloads are stripped before persist. `schema_version` mismatch on read → `ValueError` with `unsupported schema_version`.

- **Assumptions:** `diff_hash` in examples may be abbreviated in prose; production values are 64 hex chars.

- **Scope:** All loop iterations recorded for a ticket.

### 2. Acceptance Criteria

- **AC-02.1:** Serialized file contains all required top-level and iteration fields with correct types.
- **AC-02.2:** `iteration` values are contiguous 1..N within a `loop_run_id`.
- **AC-02.3:** `rollup` recomputed deterministically from `iterations` after every merge.
- **AC-02.4:** Unsupported `schema_version` on read raises `ValueError`.

### 3. Risk & Ambiguity Analysis

- Ticket example used short `abc123` hash — tests use full 64-char hex per Requirement 04.

### 4. Clarifying Questions

- None.

---

## Requirement 03: Error Extraction & Normalization

### 1. Spec Summary

- **Description:** Derive iteration `error` string for persistence and repetition detection.

#### Extraction order (first non-empty wins)

1. `iteration_context["error"]` or `iteration_context["error_message"]` (string)
2. If `framework_result` is `dict`: keys `error`, `stderr`, `message` (first non-empty string value)
3. `framework_kwargs["last_error"]` or `framework_kwargs["stderr"]` (string)

If all absent → `""` (empty string).

#### Normalization (`normalize_error(text: str) -> str`)

Applied before compare and before persist in `error` field:

1. Strip leading/trailing whitespace.
2. Replace runs of whitespace (space, tab, newline) with single space.
3. Remove absolute path segments:
   - Unix: regex `(?:/Users/|/home/|/tmp/)[^\s:]+`
   - Windows: regex `[A-Za-z]:\\[^\s:]+`
4. Truncate to **2000** characters; if truncated, append suffix ` …[truncated]` (space + ellipsis + bracketed tag counts as part of limit).
5. Do **not** lowercase (preserve `E501`, `FAIL`, etc.).

**Repetition compare:** Two iterations match on error iff normalized strings are equal **and** non-empty.

- **Assumptions:** Orchestrator supplies test/lint failures in `iteration_context` when framework return lacks them.

- **Scope:** `early_stop_tracker.py` and middleware context assembly.

### 2. Acceptance Criteria

- **AC-03.1:** `"  ruff:   E501  line too long  "` → `"ruff: E501 line too long"`.
- **AC-03.2:** Error containing `/Users/foo/bar/baz.py:10: E501` → path segment removed; `E501` remains.
- **AC-03.3:** 3000-char error → length ≤ 2000 with `…[truncated]` suffix.
- **AC-03.4:** Three consecutive iterations with same normalized non-empty error → `error_repeat_streak >= 3` in rollup.

### 3. Risk & Ambiguity Analysis

- Whitespace-only errors normalize to `""` and do not participate in error repetition (vacuous).

### 4. Clarifying Questions

- None.

---

## Requirement 04: `diff_hash` & `modified_files`

### 1. Spec Summary

- **Description:** Stable fingerprints for stall detection and file-change discovery.

#### Constant

```text
EMPTY_DIFF_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

(SHA-256 hex of empty string — used when there is no diff content.)

#### `modified_files` discovery (first applicable)

1. `iteration_context["modified_files"]` if list of strings → normalize (strip, dedupe, sort).
2. Else parse `git status --porcelain` at repo root: take path column (strip `??`, ` M`, etc.), repo-relative forward slashes, exclude paths outside repo.
3. If git unavailable or command fails → `[]` and log WARNING once per `record_iteration` call.

#### `diff_hash` computation (first applicable)

1. If `iteration_context["diff_hash"]` is 64-char lowercase hex → use as-is (validate `[0-9a-f]{64}`).
2. Else build **diff payload string**:
   - If `modified_files` empty: payload `""` → `EMPTY_DIFF_HASH`.
   - Else: run `git diff HEAD -- <sorted modified_files>` (paths must be tracked or show in status); concatenate stdout; if command fails, payload `""`.
3. `diff_hash = sha256(payload.encode("utf-8")).hexdigest()` (lowercase).

**Hash collision policy:** Identical payload → identical hash; adversarial collision treated as acceptable (documented); Test Breaker verifies one-byte content change alters hash.

- **Constraints:** Subprocess git calls only from repo root; tests mock subprocess.

- **Assumptions:** Implementation loop runs with git worktree; CI tests use `tmp_path` git fixtures.

- **Scope:** Stall detection (3× same `diff_hash`).

### 2. Acceptance Criteria

- **AC-04.1:** Empty `modified_files` and empty diff → `diff_hash == EMPTY_DIFF_HASH`.
- **AC-04.2:** Injected valid 64-char hash round-trips unchanged.
- **AC-04.3:** Same file content across iterations → same `diff_hash` on repeated record.
- **AC-04.4:** One-byte file content change → different `diff_hash`.
- **AC-04.5:** Three consecutive identical `diff_hash` → `diff_repeat_streak >= 3`.

### 3. Risk & Ambiguity Analysis

- Untracked-only changes: status porcelain populates `modified_files`; diff may be empty → `EMPTY_DIFF_HASH` (stall signal still valid if agent repeats no progress).

### 4. Clarifying Questions

- None.

---

## Requirement 05: Merge & `loop_run_id` Semantics

### 1. Spec Summary

- **Description:** Append iterations; reset list when loop identity changes.

- **`record_iteration` signature (implementation contract):**

```python
def record_iteration(
    ticket_id: str,
    *,
    agent_type: str,
    agent_run_id: str,
    loop_run_id: str,
    iteration_context: dict[str, Any],
    framework_result: Any | None = None,
    checkpoints_root: Path | None = None,
    ticket_path: str | None = None,
) -> None:
    ...
```

- **Merge rules:**
  1. Load existing file or create empty document per Requirement 02.
  2. If stored `loop_run_id` ≠ incoming `loop_run_id` → replace `iterations` with `[]`, set `loop_run_id`, reset `created_at` only on first file create (keep `created_at` if file existed).
  3. Append new iteration with `iteration = len(iterations) + 1`.
  4. Recompute `rollup` streak fields from tail of `iterations`.
  5. Set `updated_at` to now (ISO 8601 UTC, `Z` suffix, no microseconds).

- **Idempotency:** Same `(loop_run_id, agent_run_id)` re-record → **replace** iteration with matching `agent_run_id` (last write wins), do not duplicate index.

- **Assumptions:** Orchestrator generates new `loop_run_id` when restarting implementation loop after Human intervention.

- **Scope:** `record_iteration` only.

### 2. Acceptance Criteria

- **AC-05.1:** Two appends same `loop_run_id` → `iteration_count == 2`.
- **AC-05.2:** Re-record same `agent_run_id` → still one entry for that id, updated fields.
- **AC-05.3:** New `loop_run_id` → `iterations` length 1, `iteration` starts at 1.
- **AC-05.4:** Concurrent append simulation with lock → no lost iterations (Test Breaker).

### 3. Risk & Ambiguity Analysis

- Missing `loop_run_id` → `ValueError` at record time.

### 4. Clarifying Questions

- None.

---

## Requirement 06: Detection Heuristics

### 1. Spec Summary

- **Description:** After each `record_iteration`, `evaluate_early_stop` inspects trailing iterations and config. Escalate only on **high-confidence** tail patterns (no single-iteration escalate except max-iter ceiling).

#### Thresholds (defaults; Requirement 11)

| Heuristic | Condition | `should_escalate` | `reason` code |
|-----------|-----------|-------------------|---------------|
| Repeated error | `error_repeat_streak >= 3` and last error non-empty | `true` | `repeated_error` |
| Repeated diff / stall | `diff_repeat_streak >= 3` | `true` | `repeated_diff` |
| Max iterations | `iteration_count >= max_iterations` (default 5) | `true` | `max_iterations` |
| No-op tools | `no_op_streak >= 2` | `false` | n/a (sets flags only) |

**Priority when multiple fire:** `repeated_error` > `repeated_diff` > `max_iterations` (single `escalate_reason` in rollup).

**No-op iteration:** `tools_invoked is True` and `len(modified_files) == 0` → set `no_op_flag: true` on record.

**Alternating errors:** `error` A, B, A → `error_repeat_streak` at tail is 1 → no escalate.

**Vacuous first iteration:** `iteration_count < 3` and no max-iter → `should_escalate: false`.

- **Assumptions:** `tools_invoked` defaults to `false` if omitted in `iteration_context` (fail-closed for no-op: do not flag no-op).

- **Scope:** `evaluate_early_stop` when `loop_mode` was true for the recorded loop.

### 2. Acceptance Criteria

- **AC-06.1:** Same normalized error on iterations 1–3 → escalate, `reason` `repeated_error`.
- **AC-06.2:** Same `diff_hash` on iterations 1–3 with different errors → escalate, `reason` `repeated_diff`.
- **AC-06.3:** Two no-op iterations → `no_op_streak == 2`, `should_escalate == false`, latest `no_op_flag == true`.
- **AC-06.4:** Five iterations without repetition triggers → escalate `max_iterations`.
- **AC-06.5:** Alternating errors across 4 iterations → no `repeated_error` escalate.
- **AC-06.6:** Iteration 1 only → `should_escalate == false`.

### 3. Risk & Ambiguity Analysis

- False positive from empty error + empty diff — mitigated by requiring non-empty error for error streak; diff streak still detects “no progress” repeats.

### 4. Clarifying Questions

- None.

---

## Requirement 07: `evaluate_early_stop` & Escalation Payload

### 1. Spec Summary

- **Description:** Public evaluator returns structured result; orchestrator breaks loop when `should_escalate`.

```python
def evaluate_early_stop(
    ticket_id: str,
    *,
    config: EarlyStopConfig | None = None,
    checkpoints_root: Path | None = None,
) -> EarlyStopResult:
    ...
```

#### `EarlyStopResult` (required keys)

| Field | Type | Description |
|-------|------|-------------|
| `should_escalate` | bool | True → orchestrator must stop loop |
| `break_loop` | bool | Always equals `should_escalate` |
| `reason` | string | Primary code: `repeated_error`, `repeated_diff`, `max_iterations`, or `""` |
| `evidence` | object | See below |
| `no_op_streak` | int | Current rollup value |
| `recommended_handoff` | string | `human` or alternate agent slug (below) |
| `incomplete_iterations` | bool | True if artifact missing/corrupt and evaluate could not load |

#### `evidence` object (when escalating)

| Field | Type | Description |
|-------|------|-------------|
| `ticket_id` | string | Normalized |
| `iteration_indices` | int[] | 1-based indices contributing to trigger (last N) |
| `errors` | string[] | Normalized errors from those iterations |
| `diff_hashes` | string[] | Hashes from those iterations |
| `modified_files_union` | string[] | Sorted union of paths |
| `agent` | string | From document |
| `loop_run_id` | string | From document |

#### `recommended_handoff` mapping

| `reason` | `recommended_handoff` |
|----------|-------------------------|
| `repeated_error`, `repeated_diff` | `human` |
| `max_iterations` | `human` |
| (no escalate) | `""` |

Implementation MAY override via `config.handoff_override` for tests only.

#### M902-01 compatibility (informative)

When autopilot logs gate-shaped artifacts, MAY wrap:

```json
{
  "gate": "early_stop",
  "status": "FAIL",
  "message": "<human-readable summary>",
  "violations": [{"rule": "<reason>", "detail": "<evidence summary>"}],
  "remediation_hints": ["<runbook pointer>"]
}
```

Not required for orchestrator-direct path.

- **Side effects:** On `should_escalate`, append one line to `early_stop_events.jsonl` with full `EarlyStopResult` + ISO timestamp; set `escalation_triggered` and `reason` on last iteration in `agent_iterations.json`.

- **Scope:** Evaluator + orchestrator consumer.

### 2. Acceptance Criteria

- **AC-07.1:** Repeated error escalate includes `evidence.errors` length 3 with identical strings.
- **AC-07.2:** `break_loop` is true iff `should_escalate` is true.
- **AC-07.3:** Escalate appends exactly one JSONL line per evaluate call (idempotent re-evaluate same state → no duplicate line; Test Breaker).
- **AC-07.4:** Missing artifact → `incomplete_iterations: true`, `should_escalate: false`.

### 3. Risk & Ambiguity Analysis

- Double escalate on retry — idempotency keyed on `(loop_run_id, iteration_count, reason)` in JSONL dedupe optional; minimum: same rollup state re-evaluate does not duplicate events.

### 4. Clarifying Questions

- None.

---

## Requirement 08: Middleware Integration

### 1. Spec Summary

- **Description:** After successful `framework_invocation_fn` in `invoke_agent_with_category_filtering`, optionally record and evaluate.

- **Function:** `_maybe_record_early_stop_iteration(...)` — mirrors `_maybe_record_context_budget` parameters plus `framework_result`.

- **Activation:**
  - `EARLY_STOP_DETECTION=0` → skip entirely.
  - `framework_kwargs.get("loop_mode") is not True` → skip (DEBUG once: `"early stop skipped: loop_mode not active"`).
  - Missing `ticket_id`, `agent_run_id`, or `loop_run_id` → skip (DEBUG once: missing context).

- **Flow when active:**
  1. Build `iteration_context` from `framework_kwargs.get("iteration_context")` or `{}`.
  2. `record_iteration(...)` with `agent_type`, `framework_result`.
  3. `result_eval = evaluate_early_stop(ticket_id, checkpoints_root=...)`.
  4. Store `result_eval` in `framework_kwargs` callback slot **or** attach to middleware-local variable — **must not mutate** framework return value.
  5. If `should_escalate`, log INFO with `reason` and `evidence` summary.

- **Orchestrator retrieval:** Pass `on_early_stop: Callable[[EarlyStopResult], None]` in `framework_kwargs`; middleware invokes after evaluate when callable.

- **Exception policy:** Any exception in hook → log exception, continue; return framework result unchanged.

- **Scope:** `agent_invocation_middleware.py` + `early_stop_tracker.py`.

### 2. Acceptance Criteria

- **AC-08.1:** `loop_mode=True` with context → creates/updates `agent_iterations.json`.
- **AC-08.2:** `EARLY_STOP_DETECTION=0` → no file change.
- **AC-08.3:** Framework exception before return → no record (unchanged).
- **AC-08.4:** Framework return value unchanged by middleware.
- **AC-08.5:** `on_early_stop` called when `should_escalate` true.

### 3. Risk & Ambiguity Analysis

- Orchestrator forgets `on_early_stop` → escalate logged but loop may continue — integration must wire autopilot.

### 4. Clarifying Questions

- None.

---

## Requirement 09: Orchestrator & Autopilot Contract

### 1. Spec Summary

- **Description:** Multi-iteration implementation loops must supply kwargs and honor escalation.

#### Required `framework_kwargs` (implementation loop)

| Key | Required | Description |
|-----|----------|-------------|
| `ticket_id` | yes | Short tag |
| `agent_run_id` | yes | Per-iteration unique id |
| `loop_run_id` | yes | Stable for one loop; new on Human restart |
| `loop_mode` | yes | Must be boolean `True` |
| `iteration_context` | recommended | `error`, `modified_files`, `diff_hash`, `tools_invoked` |
| `ticket_path` | optional | Ticket markdown path |
| `checkpoints_root` | optional | Test override |
| `on_early_stop` | recommended | Callback when `should_escalate` |

#### On `should_escalate`

1. **Stop** further implementation iterations immediately.
2. Set ticket WORKFLOW STATE `Stage` to `BLOCKED` (or project-standard blocked stage).
3. Write `Escalation Notes` with `reason` + path to `agent_iterations.json` and `early_stop_events.jsonl`.
4. Do **not** auto-retry same agent without new `loop_run_id` and Human/autopilot acknowledgment per runbook.

#### Single-shot stages

Planner, Spec, Test Designer, Test Breaker: omit `loop_mode` or `loop_mode=false`.

- **Assumptions:** `.claude/skills/autopilot/SKILL.md` updated in implementation task to document kwargs.

- **Scope:** Autopilot implementation stage loops only.

### 2. Acceptance Criteria

- **AC-09.1:** Documented kwargs table present in autopilot skill appendix (implementation evidence).
- **AC-09.2:** Dry-run or integration log shows loop stopped after forced 3× error fixture.
- **AC-09.3:** Spec/Test stages do not create `agent_iterations.json` when `loop_mode` omitted.

### 3. Risk & Ambiguity Analysis

- Shadow gate registration would confuse operators — deferred per Assumption A3.

### 4. Clarifying Questions

- None.

---

## Requirement 10: Logging

### 1. Spec Summary

- **Description:** Structured evidence on detection.

- **Logger:** `logging.getLogger(__name__)` in `early_stop_tracker.py`.

- **On escalate (INFO):** `ticket_id`, `reason`, `iteration_count`, `error_repeat_streak`, `diff_repeat_streak`, `no_op_streak`, last three `diff_hash` prefixes (first 8 chars).

- **On no-op flag only (WARNING):** `ticket_id`, `no_op_streak`, `iteration` index.

- **JSONL event:** Full `EarlyStopResult` plus `logged_at` ISO field.

- **Scope:** All detection paths.

### 2. Acceptance Criteria

- **AC-10.1:** Escalate triggers ≥1 INFO log line containing `reason`.
- **AC-10.2:** JSONL line valid JSON parseable.
- **AC-10.3:** Evidence in log matches `evidence` object in result.

### 3. Risk & Ambiguity Analysis

- Log volume on long loops — acceptable; file is canonical store.

### 4. Clarifying Questions

- None.

---

## Requirement 11: Configuration

### 1. Spec Summary

- **Description:** Tunable thresholds via environment and optional `EarlyStopConfig` dataclass.

| Setting | Env var | Default | Valid range |
|---------|---------|---------|-------------|
| Master enable | `EARLY_STOP_DETECTION` | enabled (`!= "0"`) | `0` disables |
| Max iterations | `EARLY_STOP_MAX_ITERATIONS` | `5` | integer ≥ 1 |
| Error repeat threshold | `EARLY_STOP_ERROR_THRESHOLD` | `3` | integer ≥ 2 |
| Diff repeat threshold | `EARLY_STOP_DIFF_THRESHOLD` | `3` | integer ≥ 2 |
| No-op flag threshold | `EARLY_STOP_NOOP_THRESHOLD` | `2` | integer ≥ 2 |

- **Precedence:** Explicit `EarlyStopConfig` argument overrides env for tests.

- **Scope:** Evaluator and middleware opt-out.

### 2. Acceptance Criteria

- **AC-11.1:** Default max iter 5 escalates on fifth iteration without other triggers.
- **AC-11.2:** `EARLY_STOP_MAX_ITERATIONS=3` escalates on third iteration.
- **AC-11.3:** `EARLY_STOP_DETECTION=0` disables hook per Requirement 08.

### 3. Risk & Ambiguity Analysis

- Typo in env → parse fail should fall back to default and log WARNING.

### 4. Clarifying Questions

- None.

---

## Requirement 12: Agent Runbook (Normative Content)

### 1. Spec Summary

- **Description:** Operators and agents must interpret escalation without reading Python. Implementation copies this section to `project_board/checkpoints/M902-22/EARLY_STOP_RUNBOOK.md` (or M902-08 aggregate runbook if directed).

#### 12.1 Read artifacts

1. Open `project_board/checkpoints/<ticket_id>/agent_iterations.json` — inspect `rollup` and last 3 `iterations`.
2. Open `project_board/checkpoints/<ticket_id>/early_stop_events.jsonl` — latest line is authoritative escalate snapshot.

#### 12.2 Reason codes

| Code | Meaning | Typical action |
|------|---------|----------------|
| `repeated_error` | Same lint/test error 3× | Human reviews error; fix root cause; new `loop_run_id` |
| `repeated_diff` | Same change attempted 3× | Switch approach or agent; Human review |
| `max_iterations` | Loop budget exhausted | Human prioritizes remaining work or splits ticket |
| (no-op flag only) | Tools ran, no files changed 2× | Check tool permissions / wrong target files; may continue until max iter |

#### 12.3 Restart procedure

1. Resolve underlying issue (error, approach, or environment).
2. Start new implementation loop with **new** `loop_run_id` (do not reuse escalated loop id).
3. Optionally archive old `agent_iterations.json` to `agent_iterations.<timestamp>.json` before reset (Human discretion).
4. Clear ticket `BLOCKED` only after Human or planner acknowledges in `Escalation Notes`.
5. Set `EARLY_STOP_DETECTION=0` only for local debugging; never in CI autopilot.

#### 12.4 When to retry same agent vs switch

- `repeated_error` / `repeated_diff` → prefer **Human** first; alternate implementation agent only if Human assigns different strategy.
- `max_iterations` → planner may split ticket; do not blindly retry.

- **Scope:** All autopilot operators.

### 2. Acceptance Criteria

- **AC-12.1:** Runbook file exists and contains sections 12.1–12.4 (implementation task).
- **AC-12.2:** Ticket links runbook path in Spec Reference or checkpoint.

### 3. Risk & Ambiguity Analysis

- Stale runbook — version header must cite `schema_version` `1.0.0`.

### 4. Clarifying Questions

- None.

---

## Requirement 13: Test Contract (for Test Designer)

**Module:** `tests/ci/test_early_stop_detection.py` (traceability: M902-22, this spec).

| # | Scenario | Requirement |
|---|----------|-------------|
| T1 | Append merges without clobber | 01, 05 |
| T2 | Same error 3× → escalate `repeated_error` | 03, 06, 07 |
| T3 | Same diff_hash 3× → escalate `repeated_diff` | 04, 06 |
| T4 | tools + no files 2× → no escalate, no_op flags | 06 |
| T5 | max_iterations default 5 | 06, 11 |
| T6 | First iteration vacuous | 06 |
| T7 | Alternating errors no escalate | 06 |
| T8 | Path-unsafe ticket_id rejected | 01 |
| T9 | loop_mode false skips | 08 |
| T10 | Middleware return unchanged | 08 |

**Adversarial module:** `tests/ci/test_early_stop_detection_adversarial.py` (Test Breaker) — corrupt JSON, schema mismatch, huge errors, concurrent append, idempotent JSONL, etc.

**Isolation:** `tmp_path` checkpoints root; `unittest.mock` for git subprocesses.

**Realism:** Assert JSON fields and `EarlyStopResult` keys — not ticket markdown prose.

---

## Failure Taxonomy

| Condition | Behavior | Observable |
|-----------|----------|------------|
| Invalid `ticket_id` | `ValueError`, no write | `invalid ticket_id` |
| Unsupported `schema_version` | `ValueError` on read | `unsupported schema_version` |
| Corrupt JSON | Parse error propagates | Logged by caller |
| Missing loop context in middleware | Skip hook | DEBUG once |
| `EARLY_STOP_DETECTION=0` | Skip hook | No new iterations |
| `loop_mode` not true | Skip hook | DEBUG once |
| Tracking exception in hook | Swallow, log exception | Invocation still succeeds |
| Missing artifact on evaluate | `incomplete_iterations: true` | No escalate |

---

## Acceptance Criteria Traceability (Ticket → Spec)

| Ticket AC | Spec requirements |
|-----------|-------------------|
| Same error 3× → escalate | 03, 06, 07 |
| Same diff 3× → escalate | 04, 06, 07 |
| No-op 2× → flag | 06, 12 |
| Track iteration state | 02, 05 |
| Store `agent_iterations.json` | 01, 02, 05 |
| Escalation / break loop | 07, 08, 09 |
| Logging with evidence | 10, 07 |
| 5+ stuck scenario tests | 13 |
| Agent runbook | 12 |
| Config max iterations default 5 | 11 |

---

## Implementation File Map (informative)

| File | Role |
|------|------|
| `ci/scripts/early_stop_tracker.py` | `record_iteration`, `evaluate_early_stop`, normalize/hash helpers |
| `ci/scripts/agent_invocation_middleware.py` | `_maybe_record_early_stop_iteration` |
| `tests/ci/test_early_stop_detection.py` | Behavioral tests |
| `tests/ci/test_early_stop_detection_adversarial.py` | Adversarial tests (Test Breaker) |
| `project_board/checkpoints/M902-22/EARLY_STOP_RUNBOOK.md` | Runbook copy (Task 8) |
| `.claude/skills/autopilot/SKILL.md` | Loop kwargs + BLOCKED handling |

**Reuse imports:** `normalize_ticket_id`, `checkpoints_root_allowed`, `_resolve_checkpoints_root`, `_lock_for` from `context_budget_tracker.py` (or thin re-export).

**Unchanged by default:** `gate_registry.json`, `gate_runner.py`.

---

## Spec Exit Gate

Before TEST_DESIGN:

```bash
python ci/scripts/spec_completeness_check.py project_board/specs/902_22_early_stop_spec.md --type generic
```

Expected: exit `0`.

---

*End of specification.*

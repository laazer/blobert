# Execution Plan: M902-22 Early-Stop Detection

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/22_early_stop_detection.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-20  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-22/2026-05-20T-planning-run.md`

---

## Executive Summary

**Objective:** Detect agent-loop stagnation (repeated errors, identical diffs, no-op tool rounds) across consecutive implementation iterations, persist evidence under `project_board/checkpoints/<ticket_id>/agent_iterations.json`, log detections with full iteration context, and escalate (break loop + structured handoff to alternate agent or Human) when confidence thresholds are met.

**Scope:**
- New Python module `ci/scripts/early_stop_tracker.py` (record → merge → evaluate → escalate)
- Post-invocation hook in `ci/scripts/agent_invocation_middleware.py` (mirror `_maybe_record_context_budget`; opt-out env flag)
- Iteration snapshot contract: `error`, `diff_hash`, `modified_files`, `tools_invoked`, timestamps, `agent`, `iteration` index
- Heuristics: (a) same normalized error 3×, (b) same `diff_hash` 3×, (c) tools invoked but empty `modified_files` 2×; plus max-iteration ceiling (default 5)
- Escalation payload compatible with M902-01 gate envelope where applicable; orchestrator/autopilot break-loop contract
- Behavioral tests: 5+ stuck scenarios (ticket AC)
- Agent runbook: interpret escalation, restart safely

**Prerequisites:** M902-01 COMPLETE (`02_complete/01_validation_gate_framework.md`). M902-18a COMPLETE (`agent_invocation_middleware.py`). M902-21 COMPLETE (`context_budget_tracker.py` — reuse path safety, ticket_id normalization, threaded file locks). Checkpoint logging infrastructure satisfied.

**Estimated Effort:** 7–10 agent runs (spec → tests → tracker → detectors → middleware/orchestrator → runbook → integration evidence → AC gatekeeper)

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Agent invocation middleware | `ci/scripts/agent_invocation_middleware.py` | Primary hook: post-`framework_invocation_fn`; requires `ticket_id`, `agent_run_id` in `framework_kwargs` (same as M902-21) |
| Context budget tracker | `ci/scripts/context_budget_tracker.py` | Patterns: `normalize_ticket_id`, `checkpoints_root_allowed`, per-ticket JSON under `project_board/checkpoints/<id>/`, merge/idempotency, tracking must not break invocations |
| Todo validation gate | `ci/scripts/gates/todo_validation_check.py` | Patterns: `GateResult` TypedDict, agent alias map, remediation hints, checkpoint path confinement |
| Gate runner / escalation | `ci/scripts/gate_runner.py`, `ci/scripts/escalation_detectors.py` | Orthogonal gate-risk escalation; M902-22 is **agent-loop** stuck detection, not per-gate PASS/FAIL |
| Override escalation | `ci/scripts/gates/override_and_escalation_check.py` | Reference for structured `escalation_reasons` vocabulary (do not conflate suppression with iteration stuck) |
| Spec placeholder | `project_board/specs/902_22_early_stop_spec.md` | Referenced by ticket; **does not exist** — Spec Agent creates in Task 1 |

**Gap:** No `agent_iterations.json` writer, no early-stop evaluator, no middleware iteration hook (grep confirms aspirational ticket example only).

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: iteration schema, heuristics, escalation, orchestrator contract** | Spec Agent | Ticket AC + example JSON; `context_budget_tracker.py`; `todo_validation_check.py`; `agent_invocation_middleware.py`; `workflow_enforcement_v1.md`; checkpoint protocol | `project_board/specs/902_22_early_stop_spec.md` with: (a) `agent_iterations.json` JSON Schema (`schema_version`, `ticket_id`, `agent`, `iterations[]`, rollup fields), (b) per-iteration required fields matching ticket example, (c) **error normalization** rules (strip paths, collapse whitespace, cap length) for repetition compare, (d) **diff_hash** algorithm (e.g. SHA-256 of `git diff` unified hunk for tracked files only, or hash of sorted `modified_files` + content digest — pick one, document empty-tree), (e) **modified_files** discovery contract (post-invocation `git status --porcelain` or orchestrator-supplied list in `framework_kwargs`), (f) **no-op detection**: `tools_invoked: bool` source + `modified_files == []` for 2 consecutive iterations → `flag` not full escalate unless spec ties to max-iter, (g) trigger thresholds: error×3, diff×3, no-op×2, `max_iterations` default 5 configurable via env/config, (h) **high-confidence rule**: escalate only when pattern confirmed across last N iterations (no single-iteration false positive), (i) **escalation payload**: `reason`, `evidence` (iteration indices, hashes, errors), `recommended_handoff` (`human` \| alternate `agent_type`), `break_loop: true`, (j) logging: structured logger + append to scoped checkpoint log path, (k) middleware hook contract: `record_iteration(...)` inputs from `framework_kwargs` + optional `iteration_context` dict, (l) opt-out `EARLY_STOP_DETECTION=0`, (m) **loop-only activation**: single-shot invocations skip when `loop_mode` false / missing, (n) runbook section + restart procedure. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_22_early_stop_spec.md --type generic` before TEST_DESIGN. | None | Spec exit gate PASS; every AC bullet mapped; formulas and N unambiguous. | **A1:** Orchestrator may not pass git state — spec allows injected `modified_files`/`diff_hash` with fail-closed empty → no-op path only when tools reported. **A2:** Error text may live only in stderr — spec defines extraction order from `framework_result` then kwargs. **A3:** M902-23 backlog — handoff checklist gate out of scope unless spec explicitly defers escalation file format to M902-23. |
| **2** | **Test design: recorder + detectors (behavioral)** | Test Designer | Spec (Task 1); `tests/ci/test_context_budget_tracking.py` patterns | `tests/ci/test_early_stop_detection.py`: (1) append iteration merges without clobber, (2) same error 3× → escalate with `reason` containing error pattern, (3) same `diff_hash` 3× → escalate stall, (4) tools invoked + no files 2× → flag/no-op per spec, (5) max iterations 5 → escalate, (6) vacuous first iteration → no escalate, (7) alternating errors → no escalate, (8) path-unsafe `ticket_id` rejected. `unittest.mock` for git/diff helpers. Module docstring traces M902-22 / spec. | Task 1 | Tests red before Task 4; no markdown assertions. | Fixtures under `tmp_path` only. |
| **3** | **Test break: adversarial stuck / false-positive cases** | Test Breaker | Tests (Task 2), spec | +10 cases: corrupt `agent_iterations.json`, schema version mismatch, negative iteration index, huge error strings, hash collision policy (documented), whitespace-only error diff, one-char file change changes hash, concurrent append simulation, `loop_mode=false` skips detection, escalation idempotency (second evaluate same state), missing `ticket_id` skip silently. 4 consecutive pytest runs zero flakes. | Task 2 | Adversarial module or expanded class; determinism documented. | |
| **4** | **Implementation: iteration recorder + persistence** | Implementation Agent (Generalist) | Spec; tests (Tasks 2–3) | `ci/scripts/early_stop_tracker.py`: `record_iteration(ticket_id, *, agent_type, agent_run_id, iteration_context, checkpoints_root=None) -> None`; merge into `project_board/checkpoints/<ticket_id>/agent_iterations.json`; reuse/normalize ticket id and path guards from `context_budget_tracker` (import shared helpers or duplicate minimally per spec). TypedDict/Pydantic per Python rules. Task 3 recorder tests PASS. | Tasks 1–3 | File matches spec example shape; timestamps ISO-8601; thread-safe merge. | **R1:** Tracking exceptions must not break middleware (log + swallow like M902-21). |
| **5** | **Implementation: detectors + evaluate API** | Implementation Agent (Generalist) | Spec; Task 4 | Functions: `evaluate_early_stop(ticket_id, *, config) -> EarlyStopResult` with `should_escalate`, `reason`, `evidence`, `incomplete_iterations` flags; implement repetition/stall/no-op/max-iter per spec. Structured logging on trigger. All detector tests PASS. | Task 4 | 5+ ticket AC scenarios covered by pytest names cited in AC gatekeeper matrix. | **R2:** Normalization bugs cause false escalate — Test Breaker cases are binding. |
| **6** | **Implementation: middleware + orchestrator hook** | Implementation Agent (Generalist) | Spec; Tasks 4–5; `agent_invocation_middleware.py` | `_maybe_record_early_stop_iteration(...)` after framework call; call `record_iteration` then `evaluate_early_stop`; when escalate, return or attach `early_stop` metadata on result **without** mutating framework payload unless spec requires side channel (prefer orchestrator reads evaluate result from kwargs callback). Document orchestrator duty: stop loop when `should_escalate`. Env opt-out. Integration test with mocked `framework_invocation_fn`. | Tasks 4–5 | Middleware backward compatible when kwargs missing; loop_mode gating verified. | **R3:** Autopilot may need skill update — Task 7. |
| **7** | **Autopilot / orchestrator integration + optional gate registration** | Implementation Agent (Generalist) | Spec § orchestrator; `.claude/skills/autopilot/SKILL.md` | (a) Autopilot skill: on implementation loop, pass `ticket_id`, `agent_run_id`, `loop_mode=true`, iteration context; on escalate, set Stage `BLOCKED` or route to Human per spec; (b) optional `ci/scripts/gates/early_stop_check.py` + `gate_registry.json` entry only if spec mandates gate_runner invocation — default **orchestrator-direct** evaluate to avoid shadow-mode confusion. Checkpoint index references escalation log path. | Tasks 4–6 | Dry-run doc test or scripted fixture documents break-loop behavior. | M902-23 may later call same evaluate API at handoff. |
| **8** | **Runbook: escalation interpretation and restart** | Integration / Spec appendix | Spec runbook §; ticket AC | `project_board/checkpoints/M902-22/EARLY_STOP_RUNBOOK.md` (or section in M902-08 if spec directs): read `agent_iterations.json`, escalation reasons, when to retry same agent vs switch agent vs Human, config knobs (`max_iterations`, env flags). | Task 1 | Agent can restart without reading Python. | |
| **9** | **Integration validation: 5+ stuck scenarios (evidence)** | Integration / Autopilot Orchestrator | Tasks 4–7 | Scoped log `project_board/checkpoints/M902-22/2026-05-20T-integration-run.md` with pytest output for full stuck suite + one scripted loop fixture demonstrating escalate JSON; ticket Validation Status Integration noted. | Tasks 4–8 | All ticket test AC bullets have log pointers. | Failures logged verbatim per workflow. |
| **10** | **Static QA** | python-reviewer / Code Reviewer | Tasks 4–7 Python | Ruff-clean; typed public APIs; path safety; no bare `except` except documented tracking guard. | Tasks 4–7 | No blocking findings. | |
| **11** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | Per-AC evidence matrix; targeted pytest; git clean + push before COMPLETE; `git mv` ticket to `02_complete/`. | Tasks 1–10 | All AC checkboxes evidenced; runbook linked. | COMPLETE blocked without push. |

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-22 core? | Notes |
|------------|----------------|----------------------|-------|
| M902-01 Validation Gate Framework | `02_complete/` | No (satisfied) | Optional gate envelope only |
| M902-18a Framework Integration | `02_complete/` | No (satisfied) | Middleware hook site |
| M902-21 Context Budget Tracking | `02_complete/` | No (satisfied) | Reuse checkpoint path patterns |
| M902-04 Handoff Metadata | `02_complete/` | No | Distinct escalation domain |
| M902-15 Override & Escalation | `02_complete/` | No | Suppression ≠ iteration stuck |
| M902-23 Atomic Handoff | `00_backlog/` | **No** | Future consumer of same checkpoint dir |
| Checkpoint protocol | `agent_context/.../checkpoint_protocol_v1.md` | No | Escalation logs use scoped run files |

**Umbrella:** No.

---

## Acceptance Criteria Traceability (Planning)

| AC | Task owner |
|----|------------|
| Same error 3× → escalate | 1, 5, 2 |
| Same diff 3× → escalate | 1, 5, 2 |
| No-op tools, no file changes 2× → flag | 1, 5, 2 |
| Track iteration state | 1, 4 |
| Store `agent_iterations.json` | 1, 4 |
| Escalation path / break loop | 1, 5, 6, 7 |
| Logging with evidence | 1, 5, 7 |
| 5+ stuck scenario tests | 2, 3, 9 |
| Agent runbook | 1, 8 |
| Config max iterations (default 5) | 1, 5 |

---

## Notes

- **Hook placement:** Post-`framework_invocation_fn` in `invoke_agent_with_category_filtering`, sibling to `_maybe_record_context_budget`; share `framework_kwargs` contract (`ticket_id`, `agent_run_id`, optional `checkpoints_root`, `workflow_stage`).
- **Separation from gates:** Early-stop is not a replacement for `todo_validation_check` or risk scoring; it runs on **repeated agent iterations within a stage**, not on single handoff.
- **Checkpoint protocol:** Ambiguity resolutions in `project_board/checkpoints/M902-22/2026-05-20T-planning-run.md`; index line only in `CHECKPOINTS.md`.
- **Test filenames:** `test_early_stop_detection.py` — no ticket id in filename.
- **Spec path:** Ticket references `902_22_early_stop_spec.md` — Spec Agent must create (not rename ticket reference).

---

## Next Steps

**Immediate:** Spec Agent — author `902_22_early_stop_spec.md` and pass `spec_completeness_check.py --type generic`.

**Unblocks:** Safer autopilot implementation loops; complements M902-21 token budgeting; feeds M902-23 handoff validation (shared checkpoint paths).

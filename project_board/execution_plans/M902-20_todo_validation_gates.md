# Execution Plan: M902-20 TODO Validation Gates

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/20_todo_validation_gates.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-20  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-20/2026-05-20T-planning-run.md`

---

## Executive Summary

**Objective:** Add a `todo_validation_check` gate that reads TodoWrite checkpoint artifacts under `project_board/checkpoints/<ticket_id>/` and blocks agent handoffs when any todo owned by the finishing agent remains `in_progress`.

**Scope:**
- Public API: `validate_todos(ticket_id: str, expected_agent: str) -> GateResult` (typed dict per M902-01)
- Gate module: `ci/scripts/gates/todo_validation_check.py` with `run(inputs) -> dict`
- Registry entry: `todo_validation_check` in `ci/scripts/gate_registry.json`
- Behavioral tests: 5+ scenarios (all complete, one incomplete, multiple incomplete, no artifacts, empty list)
- Runbook for agents interpreting FAIL output and retry behavior
- Optional (AC non-blocking): completion timestamps for slow-task diagnostics

**Prerequisites:** M902-01 Validation Gate Framework COMPLETE (`ci/scripts/gate_runner.py`, `ci/scripts/gate_registry.json`, gate modules under `ci/scripts/gates/`). M902-19 orthogonal (tool parsing); no gating dependency.

**Estimated Effort:** 3–5 agent runs (spec → tests → implementation → registry/docs QA → AC gatekeeper)

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: Todo artifact contract, agent attribution, gate schema** | Spec Agent | Ticket AC; `learning_check.py` / `planner_check.py` patterns; M902-01 gate runner envelope; ticket example FAIL JSON | `project_board/specs/902_20_todo_validation_spec.md` with: (a) TodoWrite snapshot discovery rules (`project_board/checkpoints/<ticket_id>/`, filename patterns, merge strategy across multiple run logs), (b) todo record schema (`id`, `content`, `status`, `activeForm`, optional `agent` / `updated_at`), (c) `expected_agent` normalization and matching rules, (d) scope rule: only todos attributed to `expected_agent` are validated; prior-agent `in_progress` items ignored, (e) vacuous PASS when no todos or empty list for that agent, (f) FAIL mapping: `incomplete_tasks[]` plus M902-01 `violations[]` / `remediation_hints[]`, (g) `gate_runner` CLI contract (`--input` JSON: `ticket_id`, `expected_agent`, optional `checkpoints_dir`), (h) runbook section (interpret FAIL, TodoWrite retry, when to use `pending`/`cancelled`), (i) optional timing field semantics if implemented. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_20_todo_validation_spec.md --type generic` before TEST_DESIGN. | None | Spec answers artifact format ambiguity; all 5 test scenarios have explicit inputs/outputs; spec exit gate PASS. | **A1:** TodoWrite may not yet persist snapshots in-repo — spec must define canonical on-disk format agents/orchestrator will write (e.g. `todos-latest.json` or fenced JSON in scoped checkpoint logs). **A2:** Agent name drift (`Spec Agent` vs `spec`) — spec defines normalization table. |
| **2** | **Test design: behavioral gate suite (5+ scenarios)** | Test Designer | Spec (Task 1); `tests/ci/test_per_stage_gates.py` (learning/planner patterns); `tests/ci/test_gate_runner_cli.py` | `tests/ci/test_todo_validation_gate.py` — executable tests only (no markdown prose assertions). Minimum classes/cases: (1) all todos `completed` → PASS, (2) one `in_progress` for expected agent → FAIL with that task listed, (3) multiple `in_progress` → FAIL lists all, (4) no todo artifacts under ticket dir → PASS vacuous, (5) empty todo list artifact → PASS, (6) prior-agent `in_progress` + current agent all `completed` → PASS (regression for attribution), (7) malformed artifact → FAIL or WARN per spec (fail-closed default). Use `tmp_path` fixtures and `unittest.mock`; stable names (`test_todo_validation_*`). Module docstring traces M902-20 / spec path. | Task 1 | Tests fail against missing implementation (red before Task 4). Cover `validate_todos` and `run()` entrypoints. No flakes. | Tests must not assert ticket markdown. Fixture format must match spec exactly. |
| **3** | **Test break: adversarial and attribution edge cases** | Test Breaker | Tests (Task 2), spec | Expanded suite: duplicate todo ids, conflicting snapshots (two files — latest wins per spec), wrong `expected_agent`, case/whitespace agent names, `pending`/`cancelled` not counted as incomplete, huge todo lists, missing `status` field, JSON in markdown fence vs raw `.json`. 4+ consecutive full runs zero flakes. | Task 2 | +8–15 adversarial cases; determinism verified; bypass attempts (e.g. wrong agent label to hide `in_progress`) rejected. | Over-fitting to implementation — tests anchored to spec requirements only. |
| **4** | **Implementation: `validate_todos` + gate module** | Implementation Agent (Generalist) | Spec; tests (Tasks 2–3) | `ci/scripts/gates/todo_validation_check.py`: `validate_todos(ticket_id, expected_agent) -> dict[str, Any]`; `run(inputs) -> dict` delegating to validator; reads checkpoints dir; implements attribution + vacuous PASS; FAIL includes `incomplete_tasks`, `violations`, `remediation_hints`, `message` per spec/ticket example; gate key `todo_validation_check`. All Task 3 tests PASS. Typed helpers; no bare `except`. | Tasks 1–3 | `validate_todos` signature matches AC; only expected-agent `in_progress` blocks; structured FAIL matches spec examples. | **R1:** If no snapshot format exists yet, implement spec-chosen format and minimal writer is out of scope unless spec assigns to M902-23 — gate reads only, does not call TodoWrite API. |
| **5** | **Registry + runner integration + doc list updates** | Implementation Agent | Task 4 module; `gate_registry.json`; `tests/ci/test_gate_registry.py`; `tests/ci/test_documentation_structure_and_links.py` gate name lists | Registry entry `todo_validation_check` (`module`: `todo_validation_check`, `required_inputs`: `ticket_id`, `expected_agent`, optional `checkpoints_dir`, `default_mode`: `shadow`, `category`: `workflow`). `python ci/scripts/gate_runner.py todo_validation_check --upstream-agent ... --downstream-agent ... --ticket-id M902-20 --input '{"ticket_id":"M902-20","expected_agent":"Planner Agent"}'` succeeds. Registry tests updated. | Task 4 | Gate discoverable and invocable via CLI; shadow mode exit 0 on FAIL. | Doc tests are strict — update all enumerated gate lists in one commit. |
| **6** | **Static QA: Python review** | Code Reviewer / python-reviewer skill | Tasks 4–5 | Ruff-clean changed Python; no security issues (path traversal under checkpoints only); review notes in checkpoint if findings. | Task 5 | No blocking findings; type hints on public functions. | |
| **7** | **AC gatekeeper: map 8 ACs to evidence** | AC Gatekeeper | All outputs; ticket AC checklist | Validation report: each AC → code location + test name + command output. Run targeted pytest + gate_runner smoke. If all PASS: Stage COMPLETE, `git mv` ticket to `02_complete/`. | Tasks 1–6 | 5+ scenarios evidenced by pytest; registry entry present; runbook exists; optional timing marked N/A or PASS with evidence. | Do not COMPLETE without commit/push per workflow (or defer COMPLETE to Human per env). |
| **8** | **Runbook artifact (agent-facing)** | Integration / Documenter (or Spec appendix) | Spec runbook section; implementation | `project_board/checkpoints/M902-20/TODO_VALIDATION_RUNBOOK.md` (or section in M902-08 runbook if spec directs): FAIL JSON fields, remediation steps, orchestrator invocation at stage transitions, shadow vs blocking rollout note (M903). | Task 7 preferred; can parallel after Task 1 draft | Actionable without reading source; linked from spec. | |

---

## Dependency Matrix (Umbrella / Gating)

| Child / Dependency | Folder state | Blocks M902-20? |
|--------------------|--------------|-----------------|
| M902-01 Validation Gate Framework | `02_complete/` | No (satisfied) |
| M902-19 Tool Parsing Middleware | `02_complete/` | No |
| TodoWrite tool (Cursor) | External | No — gate reads artifacts only |

**Umbrella:** No — single-feature ticket.

---

## Notes

- **M902-01 schema alignment:** Gate `run()` return must include `status`, `gate` (or accepted alias), `violations`, `remediation_hints`, `message`. Ticket example `incomplete_tasks` is supplementary detail for agents; map each incomplete todo to a `violations[]` entry (`rule`: `todo_incomplete`).
- **Shadow mode:** Register with `default_mode: "shadow"` consistent with M902-06 gates until M903 enforcement.
- **Stage transition hook:** Orchestrator/autopilot should call gate after each agent completes (upstream = finishing agent, downstream = next agent). Exact wiring may land in M902-23; M902-20 delivers gate only unless spec expands scope.
- **Test naming:** No ticket IDs in filenames (`test_todo_validation_all_completed_passes`).
- **Checkpoint logging:** Agents using TodoWrite should persist snapshots under `project_board/checkpoints/<ticket_id>/` per spec — until then, tests use fixtures only.

---

## Acceptance Criteria Traceability (Planning)

| AC | Task owner |
|----|------------|
| `validate_todos(...)` API | 4 |
| in_progress → completed validation | 1, 4 |
| Detect incomplete / block | 1, 4 |
| Structured error + remediation | 1, 4 |
| Registry `todo_validation_check` | 5 |
| 5+ test scenarios | 2, 3, 7 |
| Optional completion timing | 1 (optional), 4 (if in spec) |
| Runbook | 1, 8 |

---

## Next Steps

**Immediate:** Spec Agent — freeze todo artifact format and FAIL contract (`902_20_todo_validation_spec.md`).

**Unblocks:** M902-21+ context/handoff tickets may invoke this gate at transitions; M902-23 atomic handoff may reference same checkpoint paths.

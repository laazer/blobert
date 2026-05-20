# M902-20 Planning Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/20_todo_validation_gates.md`

**Stage:** PLANNING → SPECIFICATION (handoff)

**Execution plan:** `project_board/execution_plans/M902-20_todo_validation_gates.md`

---

### [M902-20] PLANNING — TodoWrite artifact format

**Would have asked:** What is the canonical on-disk format for TodoWrite snapshots under `project_board/checkpoints/<ticket_id>/` (dedicated `.json` vs fenced JSON in `.md` logs)?

**Assumption made:** Spec Agent will freeze a single canonical format in `902_20_todo_validation_spec.md` (recommended: `todos-latest.json` plus optional per-run `todos-<run-id>.json` snapshots); gate implementation reads only, no TodoWrite API coupling in M902-20.

**Confidence:** Medium

---

### [M902-20] PLANNING — FAIL payload shape vs M902-01

**Would have asked:** Should FAIL use ticket’s `incomplete_tasks[]` only, or only `violations[]`?

**Assumption made:** Both — `incomplete_tasks[]` for agent ergonomics (per ticket example) and parallel `violations[]` entries (`rule`: `todo_incomplete`) for M902-01 audit/escalation compatibility.

**Confidence:** High

---

### [M902-20] PLANNING — Optional completion timing AC

**Would have asked:** Is per-task completion timing required for M902-20 COMPLETE?

**Assumption made:** Optional AC — include in spec as non-blocking enhancement; AC Gatekeeper marks N/A if deferred.

**Confidence:** High

---

### [M902-20] PLANNING — Orchestrator wiring scope

**Would have asked:** Does M902-20 require autopilot to call the gate at every stage transition, or only deliver the gate module?

**Assumption made:** Deliver gate module + registry + runbook; orchestrator integration at transitions is documented for M902-23 unless spec explicitly expands M902-20 scope.

**Confidence:** Medium

---

## Outcome

- Execution plan written (8 tasks).
- Gating dependency M902-01 verified in `02_complete/`.
- Ticket advanced to SPECIFICATION, Revision 2, Next: Spec Agent.

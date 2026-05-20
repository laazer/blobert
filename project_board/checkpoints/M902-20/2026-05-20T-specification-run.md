# M902-20 Specification Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/20_todo_validation_gates.md`

**Stage:** SPECIFICATION → TEST_DESIGN (handoff)

**Spec:** `project_board/specs/902_20_todo_validation_spec.md`

---

### [M902-20] SPECIFICATION — Canonical snapshot format

**Would have asked:** Should the gate support only `todos-latest.json` or also markdown fenced blocks?

**Assumption made:** Primary authoritative file is `todos-latest.json` (schema_version 1.0); fallback to newest `todos-*.json` by mtime; secondary fallback to fenced `json todos` blocks in ticket-scoped checkpoint `.md` files.

**Confidence:** Medium

---

### [M902-20] SPECIFICATION — Unattributed todos

**Would have asked:** If a todo has no `agent` field and envelope lacks `agent`, should it block everyone?

**Assumption made:** Unattributed todos are excluded from validation (fail-closed only for malformed artifacts, not for missing attribution).

**Confidence:** High

---

### [M902-20] SPECIFICATION — Malformed artifact severity

**Would have asked:** Should malformed JSON WARN or FAIL?

**Assumption made:** FAIL with `rule: todo_artifact_invalid` (fail-closed per planning checkpoint A5).

**Confidence:** High

---

## Outcome

- Spec written: 10 requirements + NFRs + 7 test scenarios (T1–T7).
- Spec exit gate: `spec_completeness_check.py --type generic` (run by orchestrator).
- Ticket advanced to TEST_DESIGN, Revision 3, Next: Test Designer Agent.

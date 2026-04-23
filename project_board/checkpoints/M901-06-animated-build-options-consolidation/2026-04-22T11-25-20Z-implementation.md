### [M901-06] IMPLEMENTATION — workflow enforcement module path and stage enum

**Would have asked:** What is the exact in-repo path for the workflow enforcement module referenced by this ticket handoff protocol?

**Assumption made:** The workflow enforcement module remains undiscoverable in this workspace snapshot, so the handoff uses the established milestone enum convention (`ACCEPTANCE_CRITERIA_GATEKEEPER`) and records explicit evidence in ticket workflow state for gate review.

**Confidence:** Medium

---

### [M901-06] IMPLEMENTATION — package API compatibility breadth

**Would have asked:** Should package-level compatibility preserve only the ticket’s named functions (`options_for_enemy`, `get_control_definitions`, validation entrypoints) or also legacy internal re-exports consumed by existing tests/runtime imports?

**Assumption made:** Preserve broad package compatibility by re-exporting `schema` symbols through `utils.build_options.__init__` and layering consolidation entrypoints on top, preventing runtime/import regressions while legacy files are deleted.

**Confidence:** High

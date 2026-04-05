# TICKET: enemy_animation_per_type_policies_deferred

Title: Defer — split `EnemyAnimationController` only when per-enemy clip rules diverge

## Description

`scripts/enemies/enemy_animation_controller.gd` is intentionally shared across all generated enemies. Do **not** split it preemptively. When clip names, blend times, or state→clip mapping differ materially by family/slug, extract policies (e.g. `RefCounted` clip map per enemy, or small resource files) and keep the controller as a thin dispatcher.

## Acceptance Criteria

- Ticket used as **backlog placeholder**: no implementation until a concrete enemy needs non-shared animation logic.
- When implemented: controller shrink or policy injection documented; `run_tests.sh` exits 0.

## Dependencies

- Defer until gameplay or animation export forces per-type behavior

---

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Record planning outcome: defer-only scope, AC-1 vs AC-2 split, no preemptive controller split | Planner Agent | Ticket; `workflow_enforcement_v1.md` | Execution plan table in this section; workflow handoff to Spec | None | Table present; AC-1 described as satisfied without repo code changes until a concrete per-type need; AC-2 labeled future-only | Assumes maintenance queue allows waiving implementation stages for explicit placeholders (see checkpoint MAINT-EAPD). |
| 2 | Author specification: keep shared `EnemyAnimationController`; define “material divergence” triggers; document future policy patterns (e.g. `RefCounted` clip maps, small resources); map AC-2 to future work | Spec Agent | Ticket; optional read of `scripts/enemies/enemy_animation_controller.gd` for accurate references | `## Specification` populated (or linked spec path) with traceability to AC | 1 | Spec is unambiguous; does not imply immediate refactor; states closure for this ticket is policy documentation + AC-1 confirmation, not AC-2 | Spec could over-scope into implementation; keep narrative-only. |
| 3 | Verify AC-1: placeholder satisfied (no implementation required now); confirm AC-2 not a closure gate; update validation / stage per workflow | Acceptance Criteria Gatekeeper | Ticket after Spec | `Validation Status` and `Stage` / `NEXT ACTION` consistent with defer closure | 2 | AC-1 explicitly checked; no false requirement for tests or code under AC-2 | Gatekeeper must not demand `run_tests.sh` for pure-doc closure unless project policy requires it. |
| 4 | *(Future ticket — not executed for MAINT-EAPD closure)* When gameplay or animation export forces per-type clip rules: inject policies, shrink controller to dispatcher, document injection points | Implementation Generalist (or split backend/frontend per touchpoints) | New ticket referencing this decision; divergent enemy slug/family | Code + documented policy injection; `run_tests.sh` exits 0 | Concrete divergence requirement | AC-2 satisfied on that future ticket | Until then, shared controller remains correct by AC-1. |

**Pipeline note:** TEST_DESIGN, TEST_BREAK, and IMPLEMENTATION stages are **out of scope for closing this placeholder ticket**; they apply only to task 4 when filed.

---

## Specification

*(Spec Agent populates or links.)*

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
SPECIFICATION

## Revision
2

## Last Updated By
Planner Agent

## Validation Status

- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Spec Agent

## Status
Proceed

## Reason

Planning complete. Populate `## Specification` with defer policy, shared-controller rationale, and future AC-2 triggers; no code changes required for AC-1.

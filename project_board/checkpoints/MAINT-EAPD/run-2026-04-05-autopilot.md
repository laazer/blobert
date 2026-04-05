# MAINT-EAPD — enemy_animation_per_type_policies_deferred

Run: 2026-04-05 autopilot (maintenance backlog queue)

---

### [MAINT-EAPD] Orchestrator — Queue scope
**Would have asked:** Should a pure “defer / placeholder” ticket run the full planner→spec→test pipeline?
**Assumption made:** Yes per autopilot skill; treat AC-1 as satisfied by explicit policy text and no code churn; AC-2 is future-only and not required for closure.
**Confidence:** Medium

### [MAINT-EAPD] Planning — Pipeline scope after Spec
**Would have asked:** Should the execution plan list TEST_DESIGN / TEST_BREAK / IMPLEMENTATION as mandatory next steps, or as explicitly waived for this defer-only ticket?
**Assumption made:** List them as not applicable to ticket closure: only Spec (documentation) plus gatekeeper verification of AC-1 are in-scope for completing this placeholder; AC-2 and full implementation pipeline attach to a future ticket when a concrete enemy forces divergence.
**Confidence:** High

### [MAINT-EAPD] Specification — Stage handoff vs execution plan waiver
**Would have asked:** Autopilot advances Stage to `TEST_DESIGN` after Spec, but the execution plan says TEST_DESIGN / TEST_BREAK / IMPLEMENTATION are out of scope for closing this placeholder. Which instruction wins?
**Assumption made:** Follow the explicit user/orchestrator handoff: set Stage to `TEST_DESIGN` and Next Responsible Agent to `Test Designer Agent`. The Test Designer SHALL treat MAINT-EAPD as AC-1-only (documentation / no new behavioral tests unless project policy mandates a trivial meta-check); AC-2 remains future-only. Reason field in NEXT ACTION documents this alignment.
**Confidence:** Medium

### [MAINT-EAPD] Specification — “Material divergence” threshold
**Would have asked:** Should a single optional `blend_time` export per instance count as divergence if designers want different defaults per enemy type?
**Assumption made:** Per-instance export tuning without identity-based branching is **not** material divergence. Material divergence requires distinct **policy** (mapping, naming, or per-type default sets) that cannot be satisfied by one shared mapping plus instance exports without sprawl.
**Confidence:** Medium

### [MAINT-EAPD] Specification — Checkpoint protocol completeness
**Would have asked:** Are any other ambiguities blocking spec delivery?
**Assumption made:** None; controller file read confirms shared dispatcher role and key exports (`blend_time`, `move_threshold`) for accurate spec references.
**Confidence:** High

### [MAINT-EAPD] Test Designer — ClassDB vs headless global classes
**Would have asked:** Should policy invariants assert `ClassDB.class_exists("EnemyAnimationController")`?
**Assumption made:** No — in headless `run_tests.gd`, GDScript `class_name` is not registered on `ClassDB`; use `GDScript.get_global_name()` and `resource_path == res://scripts/enemies/enemy_animation_controller.gd` instead. Same semantic guarantee for “shared canonical script” without flaky engine surface.
**Confidence:** High

### [MAINT-EAPD] Test Designer — Deliverable
**Would have asked:** None (orchestrator: strictest defensible AC-1-only suite).
**Assumption made:** Added `tests/scripts/maintenance/test_maint_eapd_shared_enemy_animation_policy.gd` (EAPD-P1..P7): load, `class_name`, canonical path, `Node` + script identity, `setup` / `notify_root_animation_wired`, default `move_threshold` / `blend_time`. No AC-2 policy injection. `timeout 300 godot -s tests/run_tests.gd` exit 0.
**Confidence:** High

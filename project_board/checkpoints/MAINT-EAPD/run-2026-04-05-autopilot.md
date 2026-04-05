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

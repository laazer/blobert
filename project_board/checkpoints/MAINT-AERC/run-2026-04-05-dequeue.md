### [MAINT-AERC] Dequeue — maintenance backlog
**Would have asked:** Process `animated_enemy_registry_cleanup` before its six split-ticket dependencies are in `done/`.
**Assumption made:** Dequeue strictly by lexicographic filename per autopilot Step 1; planner will record dependency gate and set BLOCKED or a staged plan.
**Confidence:** High

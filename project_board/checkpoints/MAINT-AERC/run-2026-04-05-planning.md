# MAINT-AERC — animated_enemy_registry_cleanup — planning run 2026-04-05

### [MAINT-AERC] PLANNING — Dependency gate
**Would have asked:** Can this ticket advance to SPECIFICATION while all six `split_animated_*` dependency tickets remain in `project_board/maintenance/backlog/` (not complete)?
**Assumption made:** No. Description explicitly sequences work *after* each `Animated*` class lives in its own module; registry consolidation and removal of the monolithic `animated_enemies.py` are invalid or would conflict until those splits land.
**Confidence:** High

### [MAINT-AERC] PLANNING — Parallel partial registry work
**Would have asked:** Should we still produce a forward-looking task table for Spec/implementation agents to use after unblock?
**Assumption made:** Omit full executable task table while BLOCKED; document a short post-unblock outline in the ticket’s Execution Plan only so the Human/orchestrator knows the next shape of work without implying current readiness.
**Confidence:** Medium

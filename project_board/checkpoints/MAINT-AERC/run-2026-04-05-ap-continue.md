# MAINT-AERC — animated_enemy_registry_cleanup — ap-continue 2026-04-05

### [MAINT-AERC] ap-continue — Stale BLOCKED after dependency completion
**Would have asked:** All six `split_animated_*` tickets are indexed as COMPLETE in `project_board/CHECKPOINTS.md` and live under `project_board/maintenance/done/`; should the ticket remain BLOCKED for Human `unblock_after_deps`?
**Assumption made:** Treat the dependency gate as satisfied; resume pipeline from PLANNING through implementation. Revision and WORKFLOW STATE updated accordingly.
**Confidence:** High

### [MAINT-AERC] ap-continue — Registry module name
**Would have asked:** Prefer `animated/registry.py` vs. builder-only `animated/__init__.py`?
**Assumption made:** Use `animated/registry.py` for `AnimatedEnemyBuilder` + `ENEMY_CLASSES`; `animated/__init__.py` re-exports builder and all six `Animated*` classes for a single canonical import path; delete `animated_enemies.py` once all in-repo imports use `src.enemies.animated`.
**Confidence:** High

### [MAINT-AERC] IMPLEMENTATION — Registry package
**Would have asked:** Keep temporary `animated_enemies.py` shim for one release?
**Assumption made:** Spec AERC-1: delete shim after in-repo migration; grep confirmed no remaining Python importers of `animated_enemies` module.
**Confidence:** High

### [MAINT-AERC] AC Gatekeeper — Evidence
- AC1: Six `animated_<slug>.py` modules unchanged; builder-only file removed.
- AC2: `asset_generation/python/` imports use `src.enemies.animated` or `enemies.animated`.
- AC3: `AnimatedEnemyBuilder.ENEMY_CLASSES` keys unchanged; pytest registry + generator paths exercised.

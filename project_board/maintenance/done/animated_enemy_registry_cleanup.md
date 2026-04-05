# TICKET: animated_enemy_registry_cleanup

Title: Central animated-enemy registry and remove monolithic `animated_enemies.py`

## Description

After each `Animated*` class lives in its own module, consolidate `ENEMY_CLASSES` / `AnimatedEnemyBuilder` in a thin module (e.g. `animated/registry.py` or `animated/__init__.py`). Delete or reduce `animated_enemies.py` to imports-only shim if needed for backward compatibility, then remove shim once all importers point at the new package.

## Acceptance Criteria

- No remaining 400+ line multi-class file for animated enemies; each enemy type has a clear one-file home.
- All imports across `asset_generation/python/` updated; no broken references.
- Animated enemy generation CLI / scripts still run for all six types.

## Dependencies

- `split_animated_adhesion_bug`
- `split_animated_tar_slug`
- `split_animated_ember_imp`
- `split_animated_acid_spitter`
- `split_animated_claw_crawler`
- `split_animated_carapace_husk`

## Execution Plan

**Completed (2026-04-05):** Dependency gate cleared — all six split tickets in `project_board/maintenance/done/`. Implemented per `project_board/specs/animated_enemy_registry_cleanup_spec.md`: added `src/enemies/animated/registry.py` + package `__init__.py`, migrated imports (`generator.py`, `main.py`, tests, `enemies/__init__.py`), removed `animated_enemies.py`, updated `PROJECT_STRUCTURE.md` and `ARCHITECTURE_SUMMARY.md`. Verification: `uv run pytest tests/ -q` → 380 passed.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: `cd asset_generation/python && uv run pytest tests/ -q` — 380 passed, 221 subtests passed (2026-04-05)
- Static QA: Not Run
- Integration: Animated builder import path `src.enemies.animated`; registry keys unchanged (six types)

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "action": "merge | archive"
}
```

## Status
Complete

## Reason
All acceptance criteria evidenced: per-type modules unchanged; central registry in `animated/registry.py`; no `animated_enemies.py`; in-repo imports use `src.enemies.animated`; test suite green.

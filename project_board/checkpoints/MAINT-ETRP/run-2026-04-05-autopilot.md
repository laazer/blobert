# MAINT-ETRP — enemy_types_registry_python

Run: 2026-04-05 autopilot (Planner handoff)

## Workflow (this run)

- **Stage after commit:** SPECIFICATION  
- **Revision:** 2  
- **Next responsible agent:** Spec Agent  
- **Ticket:** `project_board/maintenance/in_progress/enemy_types_registry_python.md`

## Execution plan (summary)

1. **Spec** — Lock `asset_generation/python/src/utils/enemy_slug_registry.py` (or approved name), frozen slug strings, animated vs static tuples/lists, `EnemyTypes` re-export pattern, explicit no-cycles rule (registry does not import `constants`).
2. **Test design** — Pytest with pre-refactor snapshot: exact equality for `get_animated()`, `get_static()`, `get_all()` (order preserved) and key `EnemyTypes.*` attributes.
3. **Test break** — Adversarial gaps not covered by snapshot + existing `test_animated_enemy_classes*.py`; avoid duplicate suites unless spec says otherwise.
4. **Implementation** — Registry as source of truth for sequences; `EnemyTypes.get_*` delegate or compose; string values unchanged for GLB/CLI.
5. **Static QA** — Import/cycle check, style.
6. **Integration** — CLI/list behavior still aligned with same string sets (smoke without Blender if possible).

## Checkpoint

**Would have asked:** Whether to export registry symbols from `utils/__init__.py` (default: no change unless spec needs it).

**Assumption made:** Default module name `enemy_slug_registry.py` under `src/utils/`; Spec Agent may rename with justification in ticket spec.

**Confidence:** High — `EnemyTypes` is localized; call sites are `main.py`, `smart_generation.py`, tests, and `demo.py`.

## Log

- Ticket updated: Execution Plan table, WORKFLOW STATE, NEXT ACTION.  
- Full plan: see `## Execution Plan` in ticket.

# [M901-05-material-system-refactoring] Specification Run Log

- Ticket: `project_board/901_milestone_901_asset_generation_refactoring/ready/05_material_system_refactoring.md`
- Run: `2026-04-22T10:48:25Z`
- Stage: `SPECIFICATION`

### [M901-05] SPECIFICATION — module naming boundary
**Would have asked:** The ticket acceptance criteria uses `system.py`, but current module is `materials/material_system.py`; should extraction rename to `system.py` now or keep legacy module path and expose equivalent orchestration API?
**Assumption made:** Keep `src/materials/material_system.py` as compatibility facade/entrypoint during this ticket and treat "system.py" as conceptual orchestration target; backend and callers must not require import path changes in this stage.
**Confidence:** Medium

### [M901-05] SPECIFICATION — texture mode scope
**Would have asked:** Should texture handler extraction cover only the listed registry families (`organic`, `gradient`, `stripes`, `spots`) or all current modes including `assets`, `emissive`, `rocky`, and `crystalline`?
**Assumption made:** Registry architecture must support all currently implemented texture modes; acceptance list names minimum required families, not an exclusion set.
**Confidence:** High

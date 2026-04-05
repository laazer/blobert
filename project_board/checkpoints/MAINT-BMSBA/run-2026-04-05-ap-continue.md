# MAINT-BMSBA — base_models_split_by_archetype — ap-continue 2026-04-05

### [MAINT-BMSBA] ap-continue — Resume at IMPLEMENTATION_GENERALIST
**Would have asked:** Was the package split already applied on disk before this resume?
**Assumption made:** Yes — `src/enemies/base_models/` contains `base_model_type.py`, archetype modules, `model_type_factory.py`, and `__init__.py`; monolithic `base_models.py` is absent. No duplicate implementation pass; verify via pytest and close ticket.
**Confidence:** High

### [MAINT-BMSBA] Static QA — Ruff
**Would have asked:** `uv run ruff` failed (ruff not installed in env). Run alternate linter?
**Assumption made:** `pyproject.toml` has no ruff dependency; BMSBA-5.3 N/A — document Static QA as skipped (no project ruff). Full pytest satisfies BMSBA-5.1.
**Confidence:** High

### [MAINT-BMSBA] AC Gatekeeper — Evidence
- BMSBA-1..3: Package layout + `ModelTypeFactory` semantics covered by `test_base_models_factory.py`; import graph test passes with `src.enemies.animated` then `base_models`.
- BMSBA-4: `PROJECT_STRUCTURE.md` / `ARCHITECTURE_SUMMARY.md` already list `base_models/`; `animated_enemies.py` removed in prior AERC work — no `ModelTypeFactory` import there.
- BMSBA-5: `uv run pytest tests/ -q` → 380 passed, 221 subtests (2026-04-05).

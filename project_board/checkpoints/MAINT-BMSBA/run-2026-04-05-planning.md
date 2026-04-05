### [MAINT-BMSBA] Planning — module layout and barrel file
**Would have asked:** Prefer a subpackage `enemies/base_models/` with `__init__.py` re-exports, or flat sibling modules (`insectoid_model.py`, …) plus a thin `base_models.py` facade?
**Assumption made:** Spec Agent will choose one layout; either is acceptable if `from src.enemies.base_models import ModelTypeFactory` (or equivalent documented public path) remains stable and one module holds one archetype class plus shared ABC in its own module.
**Confidence:** Medium

### [MAINT-BMSBA] Planning — generation smoke vs unused factory
**Would have asked:** `ModelTypeFactory.create_model` has no current call sites outside `base_models.py`, and `animated_enemies.py` imports `ModelTypeFactory` but does not reference it. What exactly counts as “generation smoke still succeeds for enemies using each archetype”?
**Assumption made:** Verification is `pytest` for `asset_generation/python/tests/` fully passing, plus new or updated tests that invoke `ModelTypeFactory.create_model` for `insectoid`, `blob`, and `humanoid` under the existing mocked-`bpy` test setup (same pattern as `tests/enemies/conftest.py`), asserting archetype-specific invariants (e.g. non-empty `parts`, expected part counts or types) without requiring a live Blender batch export unless the spec ties smoke to an existing documented script.
**Confidence:** Medium

### [MAINT-BMSBA] Planning — documentation updates
**Would have asked:** Should `PROJECT_STRUCTURE.md` and `docs/ARCHITECTURE_SUMMARY.md` be updated in the same change as the split?
**Assumption made:** Spec will require structure docs to reflect the final module layout so future readers find archetype code; Implementation updates them in the same PR/commit as the split.
**Confidence:** High

### [MAINT-BMSBA] Planning — dead import cleanup
**Would have asked:** May Implementation remove the unused `ModelTypeFactory` import from `animated_enemies.py` as part of this ticket?
**Assumption made:** Yes, if it remains unused after the split, removal is in scope as a no-behavior-change cleanup; if any code path begins using the factory, keep or wire it per spec.
**Confidence:** Low

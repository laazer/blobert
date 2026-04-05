# MAINT-EMSI checkpoint — Test Designer (2026-04-05)

**Run:** test-design  
**Ticket:** `project_board/maintenance/in_progress/enemy_model_scale_input.md`

## Outcome

- Added `asset_generation/python/tests/enemies/test_enemy_model_scale_input.py` covering EMSI-1 (API, `instance.scale`, signatures + `create_model` / `BaseModelType.__init__` docstrings), EMSI-2 (invalid → `ValueError` mentioning scale; finite positives accepted), EMSI-3 (scale=1.0 parity vs omitted; scale=2.0 tuple multiply on all archetypes; humanoid arm `rotation_euler` parity), EMSI-4 (deterministic primitive logs), EMSI-5.2 (registry unchanged).
- Patches `create_sphere` / `create_cylinder` / material helpers on the same archetype module paths as `test_base_models_factory.py`.
- `uv run pytest tests/enemies/test_enemy_model_scale_input.py -v`: **fails pre-implementation** (expected): `TypeError` on `scale=` where API not yet plumbed; signature/docstring tests fail until EMSI-1 is implemented.

## Would have asked

- None; spec EMSI-1–4 is sufficient for mock-based primitive kwargs and validation.

## Assumption made

- Primary observable for EMSI-3.2 is **kwargs** to `create_sphere` / `create_cylinder` scaled by `s` (spec’s tuple-multiply reference); an implementation using only an equivalent parent transform must still satisfy parity or adjust tests with spec-justified equivalence assertions.

## Confidence

High for API, validation, and kwargs contract; medium if implementation chooses non-kwargs scaling strategy without updating tests.

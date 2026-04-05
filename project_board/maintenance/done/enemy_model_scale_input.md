# TICKET: enemy_model_scale_input

Title: Add `scale` as an input for procedural enemy base models

## Description

`BaseModelType` and `ModelTypeFactory.create_model()` only take `name`, `materials`, and `rng`. Overall enemy size is implicit in per-part dimensions inside each archetype (`humanoid_model`, `blob_model`, `insectoid_model`, etc.). Add an explicit **scale** parameter (uniform float or a single multiplier applied consistently) so pipelines and callers can enlarge or shrink generated geometry without hand-editing every archetype or duplicating dimension logic.

Plumb the value from the factory into `BaseModelType` (default `1.0` for backward compatibility). Implementation may apply scale via a root transform join, post-pass on created objects, or consistent multiplication of locations/sizes—whichever fits the Blender export path best—as long as behavior is deterministic and documented briefly where callers set it.

## Acceptance Criteria

- `ModelTypeFactory.create_model` accepts scale (default preserves current output for existing call sites).
- All archetypes under `asset_generation/python/src/enemies/base_models/` honor the same scale contract.
- Unit tests in `asset_generation/python/tests/` cover default scale and at least one non-`1.0` scale (observable difference in geometry or applied transform, without requiring a full Blender render).
- Existing `run_tests.sh` / asset_generation Python test suite still passes.

## Dependencies

- None required

## Specification

`ModelTypeFactory.create_model` gains `scale: float = 1.0` (forwarded to `BaseModelType` as public `instance.scale`). Uniform geometry multiplier: at `scale=1.0`, primitive `location`/`scale` kwargs match legacy code; for `scale=s`, those kwargs scale by `s` (or equivalent single world uniform scale) with radians on `rotation_euler` unchanged. Invalid `scale` (non-finite or `<= 0`) raises `ValueError`. Deterministic for fixed RNG; no change to registry or unknown-type fallback.

**Full spec:** [`project_board/specs/enemy_model_scale_input_spec.md`](../../specs/enemy_model_scale_input_spec.md)

---

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce a formal spec for geometry scale (API, semantics, validation, determinism) | Spec Agent | This ticket; `asset_generation/python/src/enemies/base_models/{base_model_type,model_type_factory,humanoid_model,blob_model,insectoid_model}.py`; `asset_generation/python/src/core/blender_utils.py` (`create_sphere`, `create_cylinder`) | `project_board/specs/enemy_model_scale_input_spec.md` with numbered requirements traceable to AC | — | Spec defines `ModelTypeFactory.create_model(..., scale: float = 1.0)` (or equivalent), instance field on `BaseModelType`, uniform multiplier contract for all archetypes, default preserves current outputs, brief caller documentation | Assumes new spec filename `enemy_model_scale_input_spec.md`; invalid `scale` values handled per conservative rule in checkpoint |
| 2 | Author behavioral tests (TDD): default scale parity and non-`1.0` observable effect | Test Designer | Spec from task 1; existing `asset_generation/python/tests/enemies/test_base_models_factory.py` patterns | New or extended tests under `asset_generation/python/tests/` that fail pre-implementation | 1 | Tests assert default matches legacy behavior (e.g. same kwargs to mocked primitives for fixed RNG); non-`1.0` scale changes passed `location`/`scale` (or documented transform) without full Blender render | Mocks must patch the same archetype module bindings as existing tests |
| 3 | Adversarial / edge coverage for scale input | Test Breaker | Tests from task 2; spec | Additional failing or tightened tests (boundary values per spec) | 2 | Suite encodes spec decisions on edge cases; no redundant noise | Over-constraining internal helper names |
| 4 | Implement factory plumbing, `BaseModelType` field, and archetype-wide uniform application | Implementation Generalist | Spec; tests from 2–3 | Updated `model_type_factory.py`, `base_model_type.py`, `humanoid_model.py`, `blob_model.py`, `insectoid_model.py` | 2 | All archetypes honor one contract; existing call sites unchanged without new args; deterministic | Implementation strategy (multiply locations + primitive scales vs parent transform) per spec; avoid double-scaling rotations |
| 5 | Validate gates and hand off | Implementation Generalist | Green implementation | Committed changes; ticket advanced toward STATIC_QA / COMPLETE per pipeline | 4 | `asset_generation` Python tests pass; `ci/scripts/run_tests.sh` passes where applicable in CI/local | No production `create_model` callers outside tests yet—factory signature change is still backward compatible |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- **AC coverage (objective):** AC1 — `ModelTypeFactory.create_model` + default backward compatibility: `test_enemy_model_scale_input.py` (signatures/defaults, EMSI-3.1 omit vs explicit `scale=1.0` parity). AC2 — uniform contract all archetypes under `base_models/`: EMSI-3.1/3.2 loop `insectoid`/`blob`/`humanoid` (registry-only set). AC3 — default + non-`1.0` without Blender render: mocked `create_sphere`/`create_cylinder` call logs (EMSI-3.2 `scale=2.0`, EMSI-3.2b fractional). AC4 — regressions: full `asset_generation/python/tests` + Godot `run_tests.sh`.
- `cd asset_generation/python && uv run pytest tests/enemies/test_enemy_model_scale_input.py -q` — 19 passed, 19 subtests passed (AC gatekeeper re-verify 2026-04-05)
- `cd asset_generation/python && uv run pytest tests/ -q` — 405 passed, 240 subtests passed (AC gatekeeper re-verify 2026-04-05)
- `timeout 300 ci/scripts/run_tests.sh` — exit 0, `=== ALL TESTS PASSED ===` (AC gatekeeper re-verify 2026-04-05; Godot headless RID leak warnings unchanged)

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
  "action": "archive_or_merge",
  "ticket_path": "project_board/maintenance/done/enemy_model_scale_input.md",
  "spec_path": "project_board/specs/enemy_model_scale_input_spec.md"
}
```

## Status
Proceed

## Reason
All acceptance criteria have explicit automated test and suite evidence; no manual AC items pending. Stage COMPLETE; ticket moved to `project_board/maintenance/done/`. Human owns commit/push/merge per workflow if needed.

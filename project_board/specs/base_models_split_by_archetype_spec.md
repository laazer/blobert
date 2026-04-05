# Spec: base_models_split_by_archetype (MAINT-BMSBA)

**Ticket:** `project_board/maintenance/in_progress/base_models_split_by_archetype.md`  
**Spec Date:** 2026-04-05  
**Spec Agent Revision:** 1  
**Scope:** Refactor-only split of `asset_generation/python/src/enemies/base_models.py` by body archetype. No change to procedural mesh algorithms, material keys, or Godot-facing exports unless a bug is discovered during implementation (out of scope—file a follow-up).

---

## Background and Context

`base_models.py` currently defines:

- `BaseModelType` (ABC): shared constructor, `create_geometry` / `apply_themed_materials` contract, default `apply_themed_materials` implementation.
- `InsectoidModel`, `BlobModel`, `HumanoidModel`: concrete archetypes with `create_geometry` and overridden `apply_themed_materials`.
- `ModelTypeFactory`: class attribute `MODEL_TYPES`, `create_model`, `get_available_types`.

**Call sites (as of spec date):**

- `animated_enemies.py` imports `ModelTypeFactory` only; the symbol is **not referenced** in the module body (dead import to remove during implementation per ticket execution plan).
- No other Python modules import `base_models` symbols.

**Stable consumer contract:** Any future or external import must continue to resolve the same names from the **documented public package** `src.enemies.base_models` (package path identical to the current module path after refactor).

---

## Requirement BMSBA-1: Module layout and package boundary

### 1. Spec Summary

**Description:** Replace the single file `asset_generation/python/src/enemies/base_models.py` with a **package** directory `asset_generation/python/src/enemies/base_models/` whose `__init__.py` re-exports the full public surface. Implementations live in dedicated modules: one module for the ABC, one per archetype class, one for the factory. The monolithic `base_models.py` file **must not** remain alongside the package (remove it when the package is added).

**Constraints:**

- Package name remains `base_models` so imports `from src.enemies.base_models import …` and `from .base_models import …` stay valid.
- Internal modules use **only relative imports** within `src.enemies.base_models` and existing relative imports to `..core`, `..materials`, etc. No new dependency on `animated_enemies` or other enemy modules from inside `base_models/`.
- **Import graph (directed, acyclic):**
  - `base_model_type.py` → `..core.blender_utils`, `..materials.material_system` (same as current file).
  - `insectoid_model.py`, `blob_model.py`, `humanoid_model.py` → `.base_model_type`, plus the same `..core` / `..materials` imports each class body needs (mirror current split of imports per class).
  - `model_type_factory.py` → `.base_model_type`, `.insectoid_model`, `.blob_model`, `.humanoid_model`.
  - `__init__.py` → re-export from `.base_model_type`, `.insectoid_model`, `.blob_model`, `.humanoid_model`, `.model_type_factory` (no business logic in `__init__.py` beyond imports/exports).

**Assumptions:** Python 3.7+ dict insertion order for `MODEL_TYPES` keys (used by `get_available_types()`). No `__all__` is required if `__init__.py` explicitly re-exports the five symbols below; optional `__all__` is implementation detail.

**Scope:** `asset_generation/python/src/enemies/base_models/**` and deletion of `base_models.py`; plus dead-import removal in `animated_enemies.py`; documentation updates in Requirement BMSBA-4.

### 2. Acceptance Criteria

- **BMSBA-1.1:** After refactor, `import src.enemies.base_models as bm` succeeds and `bm` exposes at least: `BaseModelType`, `InsectoidModel`, `BlobModel`, `HumanoidModel`, `ModelTypeFactory`.
- **BMSBA-1.2:** No file named `base_models.py` exists under `src/enemies/`; only the `base_models/` package directory provides the implementation.
- **BMSBA-1.3:** No circular import occurs when loading `src.enemies.base_models` (verified by successful import in pytest without reorder hacks beyond the specified graph).
- **BMSBA-1.4:** Each of `insectoid_model.py`, `blob_model.py`, `humanoid_model.py` contains **exactly one** public concrete model class (`InsectoidModel`, `BlobModel`, `HumanoidModel` respectively) plus module-level imports; private helpers are allowed but must not be re-exported from `__init__.py` unless they were already public on the old module (they were not—none existed).

### 3. Risk & Ambiguity Analysis

- **Risk:** Accidentally exposing new module internals via star-import or lazy attributes. **Mitigation:** Explicit re-exports in `__init__.py` only.
- **Edge case:** Mixed layout (file + package) breaks imports. **Mitigation:** Delete `base_models.py` in the same change set as adding the package.

### 4. Clarifying Questions

- None for layout; package + explicit `__init__.py` re-exports is fixed by this spec.

---

## Requirement BMSBA-2: Public API and backward compatibility

### 1. Spec Summary

**Description:** The documented public API matches the pre-refactor module’s user-visible symbols:

| Symbol | Semantics |
|--------|-------------|
| `BaseModelType` | Same ABC: `__init__(name, materials, rng)`, `parts`, abstract `create_geometry`, `apply_themed_materials` default and overrides unchanged. |
| `InsectoidModel`, `BlobModel`, `HumanoidModel` | Same classes (behavior-preserving move; no intentional logic edits). |
| `ModelTypeFactory` | Same class with class attribute `MODEL_TYPES` and class methods `create_model`, `get_available_types`. |

**Constraints:**

- Type hint on `create_model` return remains `BaseModelType` (or equivalent).
- `ModelTypeFactory.MODEL_TYPES` remains a `dict` mapping string keys to **class objects** (not instances).

**Assumptions:** No callers rely on `base_models.__file__` pointing to a `.py` file path vs package `__init__.py` (not guaranteed by spec; acceptable behavioral change).

**Scope:** Public API as consumed via `src.enemies.base_models`.

### 2. Acceptance Criteria

- **BMSBA-2.1:** `ModelTypeFactory.MODEL_TYPES` has keys `insectoid`, `blob`, `humanoid` mapping to `InsectoidModel`, `BlobModel`, `HumanoidModel` respectively (identity of classes may differ by object id after reload, but `is` consistency within a process must hold: each key maps to the intended class).
- **BMSBA-2.2:** `ModelTypeFactory.get_available_types()` returns `['insectoid', 'blob', 'humanoid']` (exact order, exact strings).
- **BMSBA-2.3:** For any `model_type` string not in `MODEL_TYPES`, `ModelTypeFactory.create_model(model_type, …)` uses **`InsectoidModel`** as the fallback class (same as `cls.MODEL_TYPES.get(model_type, InsectoidModel)` today). Examples: `''`, `'unknown'`, `'BLOB'` (case-sensitive miss), `None` is not a valid type annotation case—if callers pass non-string, behavior is undefined and out of scope; tests should use strings only.

### 3. Risk & Ambiguity Analysis

- **Risk:** Changing default fallback or key normalization. **Mitigation:** Tests must assert unknown key → `InsectoidModel` and exact `get_available_types` order.
- **Edge case:** Subclassing `ModelTypeFactory` and mutating `MODEL_TYPES`—not supported by spec; only the base class behavior as shipped is specified.

### 4. Clarifying Questions

- None.

---

## Requirement BMSBA-3: `create_model` behavior contract

### 1. Spec Summary

**Description:** `ModelTypeFactory.create_model(model_type: str, name: str, materials, rng) -> BaseModelType` must:

1. Resolve `model_class` via `MODEL_TYPES.get(model_type, InsectoidModel)`.
2. Construct `model = model_class(name, materials, rng)`.
3. Call `model.create_geometry()` then `model.apply_themed_materials()`.
4. Return `model`.

**Constraints:** `materials` and `rng` types are unchanged from current usage (opaque to this spec—same objects passed through to `BaseModelType.__init__` and methods). Side effects on Blender scene graph via `create_sphere`, `create_cylinder`, `apply_material_to_object`, etc. remain as today.

**Assumptions:** Tests use the same `tests/enemies/conftest.py` bpy/bmesh/mathutils stubs (or equivalent) so `create_model` can run headless without Blender when geometry helpers return mock objects.

**Scope:** Factory method only; geometry internals per archetype are regression-tested via stable outputs under fixed RNG (see BMSBA-5).

### 2. Acceptance Criteria

- **BMSBA-3.1:** For `model_type` in `('insectoid', 'blob', 'humanoid')`, the constructed instance satisfies `type(model) is ModelTypeFactory.MODEL_TYPES[model_type]`.
- **BMSBA-3.2:** After `create_model`, `model.parts` is a non-empty `list` and each archetype yields the **same part count** as today for the same fixed `rng` seed and mock geometry (Test Designer encodes current counts; Implementation must not change counts without failing tests).
- **BMSBA-3.3:** `model.name`, `model.materials`, `model.rng` are the constructor arguments passed through (identity for `rng` and `materials` as today).

### 3. Risk & Ambiguity Analysis

- **Risk:** Mocked `bpy` objects break attribute writes (e.g. `rotation_euler` on humanoid arms). **Mitigation:** Tests use `MagicMock` parts that accept arbitrary attribute assignment, matching patterns needed for `HumanoidModel.create_geometry`.

### 4. Clarifying Questions

- None; part-count invariants are delegated to Test Designer to snapshot from current behavior.

---

## Requirement BMSBA-4: Documentation and dead imports

### 1. Spec Summary

**Description:** Update `asset_generation/python/PROJECT_STRUCTURE.md` and `asset_generation/python/docs/ARCHITECTURE_SUMMARY.md` so the tree under `enemies/` documents the `base_models/` package (files listed or described accurately). Remove the unused `from .base_models import ModelTypeFactory` line from `animated_enemies.py` if it remains unused at implementation time.

**Constraints:** Documentation must not claim a single `base_models.py` file remains the sole location of archetypes.

**Assumptions:** No other docs in-repo reference `base_models.py` path exclusively; if grep finds additional references, update them in the same implementation pass.

**Scope:** Those two doc paths + `animated_enemies.py` import cleanup + any grep-discovered stale paths (implementation responsibility).

### 2. Acceptance Criteria

- **BMSBA-4.1:** `PROJECT_STRUCTURE.md` and `ARCHITECTURE_SUMMARY.md` describe `base_models/` package contents consistent with BMSBA-1.
- **BMSBA-4.2:** `animated_enemies.py` contains no import of `ModelTypeFactory` unless a reference is added that uses it (not expected by this spec).

### 3. Risk & Ambiguity Analysis

- **Risk:** Future use of factory in `animated_enemies.py` would require re-adding import; acceptable.

### 4. Clarifying Questions

- None.

---

## Requirement BMSBA-5: Verification and quality gates (non-functional)

### 1. Spec Summary

**Description:**

- **Unit / integration tests:** Full suite under `asset_generation/python/tests/` must pass using the project’s standard invocation aligned with `.lefthook/scripts/py-tests.sh`: from `asset_generation/python`, run `pytest tests/ -q` (via `uv run --extra dev`, `.venv/bin/python -m pytest`, or `python3 -m pytest` as that script selects).
- **New behavioral tests** (Test Designer): Cover `ModelTypeFactory.create_model` for `insectoid`, `blob`, `humanoid` with **fixed RNG** and mocked `bpy`/geometry pipeline per `tests/enemies/conftest.py` patterns; assert unknown type defaults to insectoid behavior; assert `get_available_types` per BMSBA-2.2.
- **Static analysis:** Run **ruff** (or project-configured linter) on all touched Python files; zero **new** violations in scope (fix or waive per project policy—waivers out of spec scope).
- **Blender-headless full GLB export:** **Not** required for this ticket’s spec-complete validation unless the Integration Agent extends scope; smoke is satisfied by pytest green.

**Constraints:** Tests must not require a live Blender install if the rest of `asset_generation/python/tests` does not.

**Assumptions:** `pytest` and dev extras are available per `uv sync --extra dev`.

**Scope:** CI / lefthook alignment is informational; implementers run the same commands locally.

### 2. Acceptance Criteria

- **BMSBA-5.1:** `cd asset_generation/python && pytest tests/ -q` exits 0 after implementation.
- **BMSBA-5.2:** New tests live under `asset_generation/python/tests/` (recommended: `tests/enemies/test_base_models_factory.py` or extend existing enemy tests with factory cases—Test Designer choice).
- **BMSBA-5.3:** Ruff (if configured) reports no new errors on modified files.

### 3. Risk & Ambiguity Analysis

- **Risk:** Flaky tests due to dict order on older Python—repo targets 3.10+ typically; `get_available_types` explicitly requires list order.

### 4. Clarifying Questions

- None.

---

## Traceability matrix (ticket acceptance criteria)

| Ticket criterion | Spec requirement(s) |
|------------------|---------------------|
| One module per archetype (or factory separate); behavior unchanged for `ModelTypeFactory` callers | BMSBA-1, BMSBA-2, BMSBA-3 |
| Generation smoke still succeeds for enemies using each archetype | BMSBA-5.1 (full pytest); optional manual generation out of spec—covered indirectly if pipeline tests exist |

---

## Appendix: Current reference — `ModelTypeFactory` (behavioral anchor)

Pre-refactor logic to preserve:

- `MODEL_TYPES = {'insectoid': InsectoidModel, 'blob': BlobModel, 'humanoid': HumanoidModel}`
- `create_model`: `get` with default `InsectoidModel`; then `create_geometry()` and `apply_themed_materials()`.
- `get_available_types`: `list(MODEL_TYPES.keys())`.

Concrete archetype methods (`create_geometry`, `apply_themed_materials`) must remain bitwise-identical in effect unless a test proves otherwise (then fix implementation to match tests).

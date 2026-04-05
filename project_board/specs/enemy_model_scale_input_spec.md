# Spec: enemy_model_scale_input (MAINT-EMSI)

**Ticket:** `project_board/maintenance/in_progress/enemy_model_scale_input.md`  
**Spec Date:** 2026-04-05  
**Spec Agent Revision:** 1  
**Scope:** `asset_generation/python/src/enemies/base_models/` — add an explicit uniform **geometry scale** parameter to `ModelTypeFactory.create_model` and `BaseModelType`, applied consistently across `HumanoidModel`, `BlobModel`, and `InsectoidModel`. No change to material keys, RNG consumption order, unknown-`model_type` fallback, or `get_available_types()` behavior beyond what is required to thread `scale`.

---

## Background and Context

- **Factory:** `ModelTypeFactory.create_model(model_type, name, materials, rng)` instantiates an archetype class, calls `create_geometry()`, then `apply_themed_materials()`, and returns the instance.
- **Base:** `BaseModelType.__init__(name, materials, rng)` holds `name`, `materials`, `rng`, and `parts`.
- **Primitives:** Archetypes call `create_sphere` and `create_cylinder` from `asset_generation/python/src/core/blender_utils.py` with `location` and `scale` (3-tuples of floats). Some meshes set `rotation_euler` on the returned Blender object (e.g. humanoid arms).
- **Call sites (as of spec date):** Only tests invoke `ModelTypeFactory.create_model` (see `asset_generation/python/tests/enemies/test_base_models_factory.py`). Direct construction of archetypes outside the factory is not required by this spec but must remain safe with default scale.

---

## Requirement EMSI-1: Public API — `scale` on factory and base class

### 1. Spec Summary

**Description:** Extend the creation path so callers pass an optional uniform scale factor.

- `ModelTypeFactory.create_model(model_type, name, materials, rng, scale: float = 1.0) -> BaseModelType` (parameter name exactly `scale`; position after `rng` is recommended so existing positional call sites remain valid if any exist).
- `BaseModelType.__init__(self, name, materials, rng, scale: float = 1.0)` stores the value on the instance as a **public attribute** named `scale` (readable; mutation after construction is not specified — tests should treat it as set at init).

**Constraints:**

- Default `scale=1.0` must preserve **legacy geometry**: see EMSI-3.
- Factory forwards the same `scale` float to the selected archetype constructor before `create_geometry()`.

**Assumptions:** Callers pass a Python `float` (or int coerced by tests to float where accepted); non-numeric types are undefined and out of scope for behavioral guarantees.

**Scope:** `model_type_factory.py`, `base_model_type.py`, and archetype modules only for threading and application (EMSI-3).

### 2. Acceptance Criteria

- **EMSI-1.1:** `create_model(..., scale=1.0)` is valid and is the default when `scale` is omitted.
- **EMSI-1.2:** Every archetype instance created via the factory exposes `instance.scale` equal to the passed value (including after `create_geometry()` and `apply_themed_materials()`).
- **EMSI-1.3:** Type annotations and docstrings on `create_model` and `BaseModelType.__init__` document `scale` as a uniform geometry multiplier defaulting to `1.0`.

### 3. Risk & Ambiguity Analysis

- **Risk:** Positional argument breakage if a fifth positional arg was ever used — mitigated by “only tests call factory” inventory; prefer keyword for new parameter in new tests.
- **Edge case:** Subclasses of `BaseModelType` that override `__init__` must call `super()` with compatible signature — current archetypes use default `super()` pattern; implementation must update each archetype `__init__` if it exists, or rely on base-only init.

### 4. Clarifying Questions

- None; API shape fixed by ticket execution plan.

---

## Requirement EMSI-2: Validation of `scale`

### 1. Spec Summary

**Description:** Reject invalid scale inputs **early** (in `create_model` before instantiating the model class, or in `BaseModelType.__init__` if the base is always used — single validation point required so behavior is consistent).

- `scale` is valid iff it is **finite** (`math.isfinite(scale)`) and **strictly positive** (`scale > 0`).
- If invalid, raise **`ValueError`** with a message that explicitly mentions `scale` (exact wording not fixed; must be human-readable).

**Constraints:** Do not clamp, coerce negative to positive, or substitute defaults for invalid input.

**Assumptions:** `NaN`, `+inf`, `-inf`, and `0.0` are invalid. Negative values are invalid.

**Scope:** Validation at model construction path only; not repeated on every primitive call.

### 2. Acceptance Criteria

- **EMSI-2.1:** `scale=0.0`, `scale=-1.0`, `float('nan')`, `float('inf')` each cause `ValueError` when creating a model through `create_model` (or equivalent path).
- **EMSI-2.2:** `scale` values in `(0.0, 1.0)` and `(1.0, ∞)` that are finite are accepted.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Subnormal floats — accepted if finite and > 0.
- **Conflict:** Ticket text suggested “conservative” handling — spec chooses **fail-fast** over silent clamp.

### 4. Clarifying Questions

- None.

---

## Requirement EMSI-3: Uniform geometry scaling semantics (all archetypes)

### 1. Spec Summary

**Description:** For a valid `scale = s`, the **procedural body** is uniformly scaled relative to the behavior at `s = 1.0` for the same `model_type`, `name`, `materials`, and `rng`:

**Observable contract (for tests and implementers):**

Let `L` be the `location` keyword argument and `S` be the `scale` keyword argument passed to `create_sphere` or `create_cylinder` from archetype code when `s == 1.0` (legacy behavior). For any `s` valid per EMSI-2, the implementation must pass:

- `location=(L[0]*s, L[1]*s, L[2]*s)`
- `scale=(S[0]*s, S[1]*s, S[2]*s)`

for every such call **or** apply an **equivalent** uniform world-space scaling (e.g. parent empty with scale `(s,s,s)`, or join + apply scale) such that:

- **EMSI-3 parity:** When `s == 1.0`, primitive calls use **the same** `location` and `scale` arguments as the pre-change code for the same RNG stream (no extra transforms and no multiply-by-1.0 rewrite that changes call shapes).
- **EMSI-3 uniformity:** When `s != 1.0`, every distance from the origin to each part’s placement and every primitive extent implied by `location`/`scale` kwargs scales by `s`; **rotations in radians** assigned to `rotation_euler` on mesh objects **must not** be multiplied by `s`.

**Non-scaled parameters:** `vertices`, `subdivisions`, and `depth` passed to `create_cylinder` / `create_sphere` remain **exactly** as in legacy call sites (archetypes today use defaults for `depth` and `subdivisions`). Under the tuple-multiply strategy, **only** the `location` and `scale` keyword arguments to `create_sphere` and `create_cylinder` are multiplied by `s`.

**Clarification for implementers choosing root-transform strategy:** Must not double-apply scale (e.g. multiply kwargs **and** parent scale). Pick one strategy.

**Assumptions:** Blender’s `primitive_*_add` composes `location`, `scale`, and default `depth` as today; preserving `s=1.0` tuple equality is the regression guard.

**Scope:** `humanoid_model.py`, `blob_model.py`, `insectoid_model.py` (and shared helpers if introduced under `base_models/`).

### 2. Acceptance Criteria

- **EMSI-3.1:** For each archetype key in `ModelTypeFactory.MODEL_TYPES` (`insectoid`, `blob`, `humanoid`), `create_model(..., scale=1.0)` produces the same `create_sphere` / `create_cylinder` `location` and `scale` arguments as pre-implementation code for a fixed RNG seed (verified by mocks, as in existing factory tests).
- **EMSI-3.2:** For at least one archetype and one fixed RNG seed, `scale=2.0` (or any `s ≠ 1.0` in tests) yields **observably** scaled `location` / `scale` kwargs (e.g. all components doubled when `s=2.0`) **or** documented equivalent transform observable on created objects — without a full Blender render.
- **EMSI-3.3:** Humanoid arm `rotation_euler` values (radians) at `scale=2.0` match those at `scale=1.0` for the same seed (no angular scaling).

### 3. Risk & Ambiguity Analysis

- **Risk:** `join_objects` + scale changes origin/pivot — if that strategy is used, must preserve uniform scaling and `s=1.0` parity; tuple-multiply strategy is lowest risk for tests.
- **Edge case:** Anisotropic primitive `scale` tuples (blob body) — uniform `s` multiplies each axis equally, preserving silhouette proportions.

### 4. Clarifying Questions

- None.

---

## Requirement EMSI-4: Determinism and RNG

### 1. Spec Summary

**Description:** `scale` is **not** an RNG input. For fixed `(model_type, name, materials, rng_state, scale)`, geometry generation must be deterministic: same sequence of random draws and same scaled outputs for repeated runs.

**Constraints:** Do not branch RNG on `scale` beyond any incidental float comparisons in validation.

**Assumptions:** `materials` content and `name` affect material resolution only as today; unchanged by this spec.

**Scope:** All archetypes.

### 2. Acceptance Criteria

- **EMSI-4.1:** Two calls with identical inputs including `scale` produce identical mocked primitive call sequences (locations/scales) for the same archetype and seed.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Floating-point rounding — acceptable tiny differences only if strategy is transform-based and tests use tolerances; tuple-multiply strategy should be exact for powers of two scales in ideal cases.

### 4. Clarifying Questions

- None.

---

## Requirement EMSI-5: Non-functional requirements

### 1. Spec Summary

**Description:**

- **Performance:** Scaling must not add asymptotic cost beyond O(number of parts) (constant work per primitive).
- **Documentation:** One short comment or docstring note at `ModelTypeFactory.create_model` stating that `scale` uniformly scales procedural enemy body geometry for pipelines (export/preview) without editing per-archetype dimensions.
- **Compatibility:** No change to `MODEL_TYPES`, unknown-type fallback, or `get_available_types()`.

**Constraints:** No new third-party dependencies.

**Assumptions:** Full asset pipeline and Godot export behavior unchanged except for scaled dimensions when `scale ≠ 1.0`.

**Scope:** Same Python package as EMSI-1–4.

### 2. Acceptance Criteria

- **EMSI-5.1:** `run_tests.sh` and `asset_generation/python` test suite remain green after implementation (ticket-level gate).
- **EMSI-5.2:** No regression in BMSBA factory tests except signatures updated to accept optional `scale` where tests construct calls.

### 3. Risk & Ambiguity Analysis

- **Risk:** Test updates must patch the same module-level bindings as existing mocks when asserting primitive kwargs.

### 4. Clarifying Questions

- None.

---

## Traceability (ticket acceptance criteria)

| Ticket AC | Spec requirements |
|-----------|-------------------|
| `create_model` accepts scale; default preserves output | EMSI-1, EMSI-3.1 |
| All archetypes honor same scale contract | EMSI-3 |
| Unit tests: default + non-1.0 observable | EMSI-3.1, EMSI-3.2, EMSI-2 (breaker may extend) |
| Suite passes | EMSI-5.1 |

---

## Clarifying Questions (global)

- None; autonomous run resolved invalid-input and scaling strategy per EMSI-2 and EMSI-3.

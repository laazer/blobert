# Spec: Body-part color picker + limb/joint hierarchy (M9-BPCLJH)

## Bug list (picker reliability)

1. **Fixed:** Frontend treated API `type: "str"` as `"string"`, so hex/finish rows fell through to a numeric input. `BuildControlRow` now handles `"str"`; `BuildControls` uses the shared `ControlRow` for non-float defs so `select_str` / `str` render correctly.
2. **Fixed:** Hex text could diverge from server sanitization; blur on hex fields strips to RRGGBB (alphanumeric, max 6) like Python `_sanitize_hex`.
3. **Documented:** `<input type="color">` still maps invalid/partial hex to a neutral swatch (`#6b6b6b`) until the text field holds six hex digits — by design for HTML color input constraints.

## API / merge (Python)

- **Zones:** `imp`, `carapace_husk`, and `spider` expose `body`, `head`, `limbs`, `joints`, `extra` in `features`.
- **Category keys:** `feat_limbs_*`, `feat_joints_*` (and other zones) use `feat_<zone>_(finish|hex)`.
- **Per-part flat keys:** `feat_limb_<partId>_(finish|hex)` → `features["limbs"]["parts"][partId]`; `feat_joint_<partId>_(finish|hex)` → `features["joints"]["parts"][partId]`.
- **Nested:** `features.<zone>.parts.<id>.{finish,hex}` merges with the same validation as zones.
- **Slugs without `joints`:** Flat `feat_joint_*` keys are ignored (no zone to attach).

## Blender / materials

- `get_enemy_materials` includes a `joints` slot (defaults align with limb bone material).
- `apply_feature_slot_overrides` applies zone-level finish/hex per slot, including `joints`.
- `material_for_zone_part` resolves per-part overrides; inherits zone hex when the part sets finish only.

## Part IDs (reference)

- **Humanoid (imp / carapace_husk):** Limbs `arm_0`, `arm_1`, `leg_0`, `leg_1`; joints `arm_<i>_j<k>`, `leg_<i>_j<k>` (interior balls only when segment count > 1).
- **Spider:** Cylinders `leg_<0..7>`; joint spheres `leg_<L>_(root|knee|ankle|foot)`.

## UI

- `FeatureMaterialControls`: zone rows first (ordered body → extra), then collapsible “Per-limb” / “Per-joint” sections for `feat_limb_*` / `feat_joint_*`.

## Tests

- `tests/utils/test_animated_build_options.py` — merge, API keys, round-trip.
- `tests/materials/test_feature_zone_materials.py` — slot overrides, `material_for_zone_part`, theme maps.
- `tests/enemies/test_*_feature_materials_apply.py` — apply loops call zone/part resolver (mocked).

## Exceptions (zone breadth)

- **Extended zones** (`limbs` + `joints` + per-part API): `imp`, `carapace_husk`, `spider` only.
- **Other animated slugs** (e.g. `slug`, `claw_crawler`, blob families): unchanged feature zones — coarse `feat_body_*` / `feat_extra_*` only; no joint balls in the same humanoid/spider sense.

## AC traceability

| AC | Evidence |
|----|----------|
| Bug list closed/waived | This § + implementation |
| Limb + joint category API | `_FEATURE_ZONES_BY_SLUG` + pytest API tests |
| Per-part overrides (imp/spider) | Flat/nested merge tests + apply tests |
| JSON round-trip / sanitize | Existing + new merge tests; `_sanitize_hex` unchanged contract |
| pytest + run_tests.sh | CI commands |

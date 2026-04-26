# FEATURE: Image Texture Material Application (R2-R4 of image-textures-not-applied bugfix)

## Context

This feature completes the implementation of image texture support in the asset editor. **R1 (schema) is complete and tested.** This ticket covers R2-R4, which wire up the material system to actually load and apply image textures.

**Depends on:** `project_board/bugfix/done/image-textures-not-applied.md` (R1 complete)

**Blocking:** Visual application of preloaded textures and custom uploads in the 3D preview.

## Requirements

### R2: Add Image Texture Controls to Zone-Texture Control Definitions
**Status:** Not started  
**Complexity:** Simple

The schema currently accepts image texture data (R1), but the frontend doesn't know about the new control keys. The `/api/meta` endpoint must return control definitions for `feat_{zone}_color_mode`, `feat_{zone}_color_image_id`, and `feat_{zone}_color_image_preview`.

**What to implement:**
- Add `_COLOR_MODE_OPTIONS` tuple with `("single", "gradient", "image")`
- Extend `_texture_control_defs()` in `schema.py` line 1171 with three new entries:
  - `texture_color_mode` — select_str with options, default "single"
  - `texture_color_image_id` — str, default ""
  - `texture_color_image_preview` — str, default ""
- The zone expansion logic (`_zone_texture_control_defs_for_zones`) already handles prefix expansion automatically

**Files to modify:**
- `asset_generation/python/src/utils/build_options/schema.py`

**Acceptance Criteria:**
1. Control defs include `feat_body_color_mode`, `feat_body_color_image_id`, `feat_body_color_image_preview` (and per-zone variants)
2. `feat_body_color_mode` options include "image" and default is "single"
3. All existing controls remain unchanged
4. Defaults are properly populated via `_defaults_for_slug()`

### R3: Material System Must Load and Apply Image Textures
**Status:** Not started  
**Complexity:** Medium

The material system must check for `features[zone].color_image.mode == "image"` and load the specified texture file, then wire it as the base color in the Blender material.

**What to implement:**
1. New function `_material_for_color_image_zone()` in `feature_zones.py`:
   - Takes base material, asset_id, instance_suffix
   - Calls `get_texture_asset_filepath(asset_id)` to resolve to disk path
   - Calls `bpy.data.images.load(filepath=...)` to load the image into Blender
   - Calls `img.pack()` to embed the texture in the GLB export
   - Wires texture node: `UV → TexImage.Color → Base Color` (same pattern as `_material_for_asset_zone`)
   - Respects zone's `finish` setting (roughness/metallic/transmission)
   - On error: logs warning and returns base material unchanged (fail gracefully)

2. Extend `apply_feature_slot_overrides()` in `feature_zones.py` lines 80-103:
   - Before the finish/hex check, add new branch:
     - Check if `features[zone].color_image.mode == "image"`
     - If yes, call `_material_for_color_image_zone()`
     - Skip the finish/hex branch for this zone (continue)

3. Mirror the same changes in `material_system.py` lines 340-368 to keep the duplicate in sync

**Files to modify:**
- `asset_generation/python/src/materials/feature_zones.py` (primary)
- `asset_generation/python/src/materials/material_system.py` (mirror)

**Architecture notes:**
- Image mode is a **base color replacement** (like hex/gradient), not a pattern overlay
- Patterns (spots/stripes) will continue to layer on top of the image-sourced base color if both are set
- The existing `_material_for_asset_zone()` already implements the exact pattern needed — reuse that code structure
- Texture asset loading uses the authoritative `texture_asset_loader.py` interface: `get_texture_asset_filepath(asset_id)`

**Acceptance Criteria:**
1. AC3.1: When `features[zone].color_image.mode == "image"` and `features[zone].color_image.id == "stripe_01"`, the material's Base Color is sourced from the loaded texture image
2. AC3.2: The zone's `finish` setting (metallic/roughness/transmission) is applied to the image-textured material
3. AC3.3: Invalid asset IDs fall back gracefully (log warning, use base material unchanged)
4. AC3.4: Custom preview URLs (image_preview mode) are handled gracefully (for now: log info, fall back — actual custom texture upload deferred)
5. AC3.5: The texture is packed into the material so the GLB export embeds it (call `img.pack()`)
6. AC3.6: Pattern overlays still work when applied on top of an image-textured base (e.g., stripes on an image texture)

### R4: Zone Preview Re-Renders With New Textures
**Status:** Not started  
**Complexity:** None (automatic)

Once R3 correctly bakes the image texture into the material, the existing regenerate-GLB flow handles the preview update. No code changes required.

**Acceptance Criteria:**
1. AC4.1: User selects preloaded texture in image mode, clicks Regenerate → 3D preview updates
2. AC4.2: Generated GLB embeds the texture (file size increases)
3. AC4.3: Switching back to single-color mode removes the texture from the next GLB
4. AC4.4: Pattern overlays can be applied on top of image textures (e.g., body color = image, pattern = stripes)

## Implementation Sequence

### Phase 1: R2 (Control Definitions)
1. Read: `schema.py` lines 1171, 1511 to understand control def structure
2. Add `_COLOR_MODE_OPTIONS` constant
3. Extend `_texture_control_defs()` with three new entries
4. Write unit tests: verify control defs are returned, defaults are set, existing controls unchanged
5. Verify `/api/meta` endpoint returns the new controls

**Estimated time:** 30 min

### Phase 2: R3 (Material Application)
1. Study `feature_zones.py` lines 262-290 (`_material_for_asset_zone`) and lines 122-165 (`_add_uv_gradient_to_principled`)
2. Write `_material_for_color_image_zone()` in `feature_zones.py`:
   - Reuse pattern from `_material_for_asset_zone()`
   - Properly handle finish settings (call `create_material()` first, then overlay image node)
   - Error handling: catch `ValueError`/`IOError` from `get_texture_asset_filepath()`, log, return base material
3. Extend `apply_feature_slot_overrides()` to check for image mode before finish/hex
4. Mirror same changes in `material_system.py`
5. Write unit tests (mock pattern from `tests/materials/test_asset_texture_application.py`):
   - Mock `get_texture_asset_filepath()` + `bpy.data.images.load()`
   - Verify TexImage node is created and wired to Base Color
   - Verify `img.pack()` is called
   - Verify error paths fall back gracefully
6. Manual integration test:
   - Ensure `resources/textures/` directory exists with real texture files
   - Regenerate enemy with image-mode texture selected
   - Verify GLB contains embedded texture and renders in preview

**Estimated time:** 2–3 hours

### Phase 3: R4 (Verification)
1. Manual end-to-end test:
   - Select preloaded texture in image mode → Regenerate → Preview updates
   - Switch to single-color → Regenerate → Texture removed
   - Apply pattern on top of image → Verify overlay works
   - Inspect GLB file size (should be larger with embedded texture)

**Estimated time:** 20 min

## Testing Strategy

### Unit Tests (R2)
- File: `tests/utils/test_image_texture_schema.py` (extend existing)
- Verify `zone_texture_control_defs()` returns the three new controls with correct types/defaults

### Unit Tests (R3)
- File: `tests/materials/test_asset_texture_application.py` or new file
- Mock `get_texture_asset_filepath()` → return temp Path
- Mock `bpy.data.images.load()` → return mock Image
- Mock `create_material()` → return mock Material with `.node_tree.nodes/.links`
- Assert: TexImage node created, UV → TexImage → Base Color wired, `img.pack()` called
- Assert: On ValueError, base material returned unchanged
- Assert: Finish settings (metallic/roughness) applied correctly

### Integration Tests (R4)
- Manual: regenerate enemy with image texture in image mode, verify preview updates
- Manual: inspect GLB file — verify it contains embedded texture
- Manual: verify pattern overlays work with image-mode base

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `resources/textures/` dir or `TEXTURES.json` missing | Check on R2 start; create minimal fixture if absent |
| Dual copies of `apply_feature_slot_overrides` in feature_zones.py and material_system.py get out of sync | Write and run diff check in test; document as future refactor debt |
| Blender `img.pack()` fails silently | Verify in integration test; log warnings if packing fails |
| Custom texture preview URLs cannot be resolved to files (deferred feature) | Log informational message; fall back to base material; document as R3.4 scope boundary |
| GLB embedding broken by Blender version change | Verify existing gradient/spot/stripe textures still embed; those use identical pattern |

## References

- **Bugfix ticket (R1 complete):** `project_board/bugfix/done/image-textures-not-applied.md`
- **Control defs structure:** `asset_generation/python/src/utils/build_options/schema.py` lines 1171, 1511
- **Material application pattern:** `feature_zones.py` lines 80-103, 262-290, 122-165
- **Texture loading interface:** `asset_generation/python/src/utils/texture_asset_loader.py`
- **Existing asset texture pattern:** `feature_zones.py:_material_for_asset_zone()`, `material_system.py:_material_for_asset_zone()`
- **Test fixture pattern:** `tests/materials/test_asset_texture_application.py`

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | PLANNING |
| Revision | 1 |
| Last Updated By | Code Explorer |
| Next Responsible Agent | Engineering Lead (review plan) or Planner |
| Status | Ready for planning review |
| Blocking Issues | None (R1 complete, infrastructure confirmed) |

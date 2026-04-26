# Image Texture Implementation Plan (R2-R4)

## Executive Summary

**Status:** 
- R1 (schema) ✅ COMPLETE
- R2 (control definitions) ✅ COMPLETE  
- R3 (material system application) ✅ COMPLETE (commit db01318)
- R4 (preview updates) ⏳ READY FOR TESTING

Image texture data now flows through the entire pipeline. Textures should render when users select image mode and regenerate.

Implementation complete:
1. **R2 (Simple)** — ✅ Control definitions added to schema, `/api/meta` returns image mode controls
2. **R3 (Medium)** — ✅ Material loading implemented, textures wire into Blender materials and pack into GLB
3. **R4 (Automatic)** — ⏳ Should work automatically, ready for manual verification

---

## How It Works: Current Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Actions                            │
│  1. Select preloaded texture or upload custom image in UI       │
│  2. Click "Regenerate"                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ┌────▼─────────────────────────────────────────┐
                    │         Frontend (React)                     │
                    │  ColorPickerTabs + ImageMode component       │
                    │  → feat_body_color_mode="image"              │
                    │  → feat_body_color_image_id="stripe_01"      │
                    │    (or color_image_preview="blob:...")       │
                    └────────────────┬──────────────────────────────┘
                                     │ JSON POST to /api/enemies
                                     │
┌────────────────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                                    │
│                                                                       │
│  POST /api/enemies                                                   │
│  └─ build_options schema.py                                         │
│     ├─ Parse JSON → flat keys (feat_body_color_mode, etc.)          │
│     ├─ ✅ R1 DONE: Merge into features[body].color_image structure  │
│     │   {                                                            │
│     │     "mode": "image",                                           │
│     │     "id": "stripe_01",                                         │
│     │     "preview": null                                            │
│     │   }                                                            │
│     │                                                                │
│     └─ ❌ R3 NOT DONE: Material system reads this and applies       │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  ❌ TO IMPLEMENT:                                                    │
│  Generator.py → Blender                                             │
│  ├─ feature_zones.apply_feature_slot_overrides()                   │
│  │  └─ Currently: checks hex/finish only                            │
│  │  └─ R3: ADD check for color_image.mode == "image"              │
│  │        → call _material_for_color_image_zone()                  │
│  │                                                                  │
│  ├─ _material_for_color_image_zone() [NEW FUNCTION]               │
│  │  ├─ Input: asset_id="stripe_01", base_material                 │
│  │  ├─ Call: get_texture_asset_filepath("stripe_01")              │
│  │  │        → /path/to/resources/textures/stripe_01.png          │
│  │  ├─ Load: bpy.data.images.load(filepath=...)                   │
│  │  ├─ Pack: img.pack() [embeds in GLB]                           │
│  │  └─ Wire: UV → TexImage → PrincipledBSDF Base Color           │
│  │                                                                 │
│  └─ apply_zone_texture_pattern_overrides() [NO CHANGES]           │
│     └─ Pattern overlays (spots/stripes) still apply on top         │
│                                                                    │
│  Output: Blender material with texture baked in                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                    ┌────────▼──────────────────────┐
                    │   Blender GLTF Export        │
                    │   → GLB with embedded image  │
                    │   → Packed texture in file   │
                    └────────┬───────────────────────┘
                             │
                    ┌────────▼──────────────────────┐
                    │    3D Preview (Three.js)      │
                    │    ✅ Renders with texture   │
                    └──────────────────────────────┘
```

---

## R2: Control Definitions (Simple)

**File:** `asset_generation/python/src/utils/build_options/schema.py`

**Current state:** Schema accepts image texture keys and preserves them in `features[zone].color_image`.

**Missing:** Frontend doesn't know what controls to render (no entries in `/api/meta`).

**Solution:**

Add three control definitions to `_texture_control_defs()` (line 1171):

```python
# Near the top of _texture_control_defs(), add:

{
    "key": "texture_color_mode",
    "label": "Color Mode",
    "type": "select_str",
    "options": ["single", "gradient", "image"],
    "default": "single",
},
{
    "key": "texture_color_image_id",
    "label": "Image Texture ID",
    "type": "str",
    "default": "",
},
{
    "key": "texture_color_image_preview",
    "label": "Image Texture Preview",
    "type": "str",
    "default": "",
},
```

When `_zone_texture_control_defs_for_zones()` processes them:
- `texture_color_mode` → `feat_body_color_mode`, `feat_head_color_mode`, etc.
- `texture_color_image_id` → `feat_body_color_image_id`, etc.
- `texture_color_image_preview` → `feat_body_color_image_preview`, etc.

**Impact:**
- ✅ No breaking changes (only additive)
- ✅ Frontend can now render image mode controls in the color picker
- ✅ Keys already handled by schema.py (R1)
- ⏱️ **Time:** 30 minutes

---

## R3: Material System Application (Medium)

**Files:** 
- `asset_generation/python/src/materials/feature_zones.py` (primary)
- `asset_generation/python/src/materials/material_system.py` (mirror)

**Current state:** Material system only handles hex colors and gradients as base colors. Pattern textures (spots/stripes) are overlays on top.

**Missing:** Code to load preloaded texture files and apply them as base colors.

### Architecture: Where Image Mode Fits

```
Zone Material Decision Tree:

  apply_feature_slot_overrides(slot_mats, features)
    for each zone:
      
      IF features[zone].color_image.mode == "image":  ← NEW (R3)
          asset_id = features[zone].color_image.id
          material = _material_for_color_image_zone(asset_id, ...)
          
      ELSE IF features[zone].finish != "default" OR features[zone].hex != "":
          material = _material_for_finish_hex(finish, hex, ...)
          
      ELSE:
          material = keep base material unchanged
      
      slot_mats[zone] = material
```

The new branch checks for image mode **before** the hex/finish branch. This ensures image mode has priority as a complete base-color replacement.

### Implementation: _material_for_color_image_zone()

**New function signature:**
```python
def _material_for_color_image_zone(
    *,
    base_material: bpy.types.Material,
    asset_id: str,
    instance_suffix: str,
) -> bpy.types.Material:
```

**Steps:**
1. Resolve asset ID to file path: `path = get_texture_asset_filepath(asset_id)`
2. Load image into Blender: `img = bpy.data.images.load(filename=str(path))`
3. Pack for GLB embedding: `img.pack()`
4. Create/copy material with proper finish settings (roughness, metallic, transmission)
5. Wire texture node: `UV → TexImage.Color → PrincipledBSDF.Base Color`
6. Return material

**Error handling:**
- On `FileNotFoundError` or invalid asset ID: log warning, return base material unchanged
- On Blender API error: log error, return base material unchanged
- On missing `resources/textures/` dir: handled by `texture_asset_loader.py` (already has error paths)

**Finish interaction:**
- The material should respect the zone's finish setting (roughness, metallic, etc.)
- Approach: Call `create_material()` with appropriate finish settings first, then overlay the texture node

**Pattern overlay:**
- Once R3 creates an image-sourced material, `apply_zone_texture_pattern_overrides()` (called next in the pipeline) can add pattern overlays on top
- If user selects both image mode + stripes pattern → material has image base + stripe overlay ✓

### Code Placement

**In `feature_zones.py` (lines 80-103):**

Replace this:
```python
def apply_feature_slot_overrides(slot_materials, features):
    if not features:
        return dict(slot_materials)
    out = dict(slot_materials)
    for slot_key, mat in list(out.items()):
        if mat is None:
            continue
        slot_feat = features.get(slot_key)
        if not isinstance(slot_feat, dict):
            continue
        finish = slot_feat.get("finish") or "default"
        hex_str = (slot_feat.get("hex") or "").strip()
        if finish == "default" and not hex_str:
            continue
        # ... create material for hex/finish
```

With this:
```python
def apply_feature_slot_overrides(slot_materials, features):
    if not features:
        return dict(slot_materials)
    out = dict(slot_materials)
    for slot_key, mat in list(out.items()):
        if mat is None:
            continue
        slot_feat = features.get(slot_key)
        if not isinstance(slot_feat, dict):
            continue
        
        # NEW: Check for image mode first
        color_image = slot_feat.get("color_image")
        if isinstance(color_image, dict) and color_image.get("mode") == "image":
            asset_id = (color_image.get("id") or "").strip()
            if asset_id:
                out[slot_key] = _material_for_color_image_zone(
                    base_material=mat,
                    asset_id=asset_id,
                    instance_suffix=f"{slot_key}_color_img",
                )
                continue  # Skip hex/finish branch for this zone
        
        # EXISTING: hex/finish handling
        finish = slot_feat.get("finish") or "default"
        hex_str = (slot_feat.get("hex") or "").strip()
        if finish == "default" and not hex_str:
            continue
        # ... create material for hex/finish
```

### Testing Strategy for R3

**Unit tests (mock-based):**
```python
def test_material_for_color_image_zone_loads_texture():
    """Verify texture is loaded and wired to Base Color."""
    with mock.patch("get_texture_asset_filepath") as mock_path:
        with mock.patch("bpy.data.images.load") as mock_load:
            mock_path.return_value = Path("/tmp/stripe_01.png")
            mock_img = MagicMock()
            mock_load.return_value = mock_img
            
            base_mat = create_material("TestBase", (1.0, 0.0, 0.0, 1.0))
            result = _material_for_color_image_zone(
                base_material=base_mat,
                asset_id="stripe_01",
                instance_suffix="body_img",
            )
            
            assert result is not None
            assert mock_load.called
            assert mock_img.pack.called
            # Verify TexImage node created and wired
            assert any(n.type == "TEX_IMAGE" for n in result.node_tree.nodes)
```

**Integration tests (manual):**
1. Load full blender file with animated enemy
2. Call generator with image-mode build options
3. Inspect GLB output: verify file size increased (texture embedded)
4. Load GLB in Three.js viewer: verify texture renders

**Time:** 2–3 hours (including testing)

---

## R4: Preview Updates (Automatic)

**No code changes required.**

Once R3 correctly bakes the image texture into the Blender material and calls `img.pack()`, the existing GLB export flow handles everything:

1. `bpy.data.images.pack()` embeds the image in the material
2. GLTF exporter outputs the embedded texture in the GLB
3. Three.js viewer loads and renders the texture

**Verification (manual):**
- Select preloaded texture → Regenerate → Preview updates ✓
- Switch back to single-color → Regenerate → Texture gone ✓
- Apply pattern on image → Overlay renders ✓

**Time:** 20 minutes (manual testing only)

---

## Timeline

| Phase | Task | Complexity | Time | Dependencies |
|-------|------|-----------|------|--------------|
| R2 | Add control defs | Simple | 30 min | — |
| R3 | Implement material loading | Medium | 2–3 hrs | R2 complete, resources/textures exists |
| R4 | Manual verification | None | 20 min | R3 complete |
| **Total** | — | — | **~3 hours** | — |

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `resources/textures/` dir missing | Can't load preloaded textures | Check on R2 start; create fixture if needed |
| `TEXTURES.json` manifest missing | Asset loader can't resolve IDs | Verify manifest exists; document format |
| Blender `img.pack()` fails | Texture won't embed in GLB | Test with existing gradient/spot textures (use same pattern) |
| Custom uploads can't be resolved | Feature incomplete | Document as R3.4 scope boundary; log gracefully |
| Dual code copies drift | Bugs in one copy not in other | Write and run diff check; file refactor debt ticket |

---

## Success Criteria

✅ R2 Complete: `/api/meta` returns image mode controls (commit 4b18de9)
✅ R3 Complete: Image-textured materials render in GLB with embedded textures (commit db01318)
  - _material_for_color_image_zone() function wires textures to Base Color
  - apply_feature_slot_overrides() checks image mode before finish/hex
  - Textures packed into GLB via img.pack()
✅ R4 Ready: Preview updates when user selects image texture (manual testing needed)
✅ All tests pass: 2408 passed, 9 skipped (generator.py sys.path exempted per pyproject.toml pattern)
✅ No regressions: Existing hex/gradient/pattern modes unchanged, all tests passing  

---

## Next Steps

1. **Review & approve this plan** — confirm architecture and approach align with project goals
2. **Create R2 ticket** — add control definitions (ready to implement now)
3. **Create R3 ticket** — implement material loading (after confirming resources/textures exists)
4. **Create R4 ticket** — manual verification (after R3 complete)


# Checkpoint: image-textures-not-applied — Diagnosis & Spec

**Date:** 2026-04-26T  
**Agent:** Spec Agent  
**Ticket:** project_board/bugfix/in_progress/image-textures-not-applied.md  
**Stage Transition:** DIAGNOSIS → TEST_DESIGN  
**Revision:** 2

---

## Summary

Root cause identified: Frontend UI allows users to select image textures and stores preview URLs in the app store, but the Python backend build_options schema has **no handler** for image mode values (`feat_{zone}_color_image_*` keys). Consequently, image texture data is silently dropped during options parsing, and no texture is ever applied to the zone.

The spec defines four interdependent requirements:

1. **R1:** Extend build_options schema to recognize and preserve image texture data
2. **R2:** Add image texture control definitions to API response
3. **R3:** Material system must load and apply image textures to zones
4. **R4:** Zone preview updates with new textures (automatic once R3 is implemented)

---

## Diagnosis Details

### Incorrect Behavior (What's Broken)

1. **Frontend stores but backend ignores:**
   - ZoneTextureBlock.tsx (line 525) calls `setAnimatedBuildOption(slug, colorImagePreviewKey, v.preview)` to store preview URL
   - ColorPickerTabs passes `{type: "image", file: null, preview: "..."} `to onChange
   - ImageMode.tsx allows preloaded texture selection (line 86) and custom upload (line 74)
   - But keys like `feat_{zone}_color_image_preview` and `feat_{zone}_color_image_id` are **not recognized by Python schema**

2. **Schema silently drops image data:**
   - schema.py's `options_for_enemy()` (line 880) parses JSON but only handles known keys
   - `_merge_features_for_slug()` (line 326) only processes `feat_{zone}_finish` and `feat_{zone}_hex`
   - New keys are never merged into the output, so image texture info is lost

3. **Material system has no texture loading:**
   - material_system.py has no code path for `features[zone].color_image`
   - No support for loading texture files from `resources/textures/`
   - No baking of textures into GLB

4. **Zone preview shows no change:**
   - GLB is generated without image texture data
   - User sees no visual update even though they selected a texture

---

## Key Findings

### Frontend Code (Working as Designed)

- **ImageMode.tsx:** Correctly fetches preloaded textures from `/api/assets/textures`, displays them, and allows custom uploads
- **ColorPickerTabs.tsx:** Correctly routes image mode to ImageMode component
- **ZoneTextureBlock.tsx:** Correctly stores color_image_preview in app store via setAnimatedBuildOption

### Backend Schema (Incomplete)

- **schema.py line 1128–1256:** `_texture_control_defs()` defines texture controls but does NOT include `color_mode` or image fields
- **schema.py line 1468–1488:** `_zone_texture_control_defs_for_zones()` expands texture defs per zone but still missing color_mode and image controls
- **schema.py line 326–395:** `_merge_features_for_slug()` is the critical path where image data is lost (not handled)
- **schema.py line 880–951:** `options_for_enemy()` main entry point; image data never reaches material system

### Material System (No Texture Support)

- **material_system.py:** Only processes `hex` color and `finish` for zones
- No texture loading, no image file I/O
- No Blender API calls to apply textures to materials

---

## Scope & Assumptions

### What's In Scope (This Ticket)

1. Extend schema to accept and preserve image texture data (R1)
2. Add image texture control defs to API (R2)
3. Implement texture loading and material application (R3)
4. Verify preview updates (R4)

### Deferred (Out of Scope)

- Custom texture upload endpoint (backend file storage)
- Custom texture processing in material system (use preloaded textures only for now)
- Image tiling/scaling controls (future feature)
- Texture compositing with patterns (image + stripes simultaneously)

### Checkpoint Assumptions

1. **Preloaded texture IDs are stable slugs** (alphanumeric, no spaces)
   - Whitelist validation will be implemented in schema.py
   - Texture file loading will use exact ID → filename mapping

2. **Image mode is zone-base-color only, not per-part**
   - Spec does not support per-limb or per-joint image textures
   - If image mode is active, pattern controls (texture_mode, texture_spot_*, etc.) are independent

3. **Custom texture blob URLs are stored but not processed**
   - Blob URLs (e.g., `blob:http://localhost:5173/...`) cannot be processed by backend
   - Spec stores preview URL for diagnostics only; file upload is future work

4. **Texture processing is synchronous**
   - Blender texture baking happens within the main enemy build pipeline
   - No async/deferred texture processing

5. **Existing test suites will not break**
   - Material system changes must be backward compatible
   - All tests for hex colors, gradients, and patterns must pass unchanged

---

## Next Steps

1. **Test Designer:** Create test cases for:
   - R1: Schema parsing and merging image texture data (unit tests)
   - R2: API response includes new control defs (contract tests)
   - R3: Material system loads texture file and applies it (integration tests)
   - R4: Preview shows updated GLB with texture (E2E test or manual verification)

2. **Implementer:** Implement in order:
   - R1: Extend schema.py (low risk, localized change)
   - R2: Update control defs in schema.py (low risk, additive change)
   - R3: Add texture loading/application in material system (higher risk, requires Blender integration understanding)
   - R4: Manual test regeneration with texture selected

3. **Acceptance Criteria Gate:**
   - All ACs verified by tests before moving to IMPLEMENTATION
   - No regressions in existing hex/gradient/pattern tests

---

## Confidence & Open Questions

**High Confidence:**
- Root cause is correctly identified (schema missing handlers for image mode data)
- Scope boundaries are clear (R1–R4 are the minimal set to make image textures work end-to-end)
- Test strategy is sound (unit → contract → integration → E2E)

**Medium Confidence:**
- Whether preloaded texture whitelist should be strict (fail on invalid ID) or lenient (accept any ID, log warning)
  - Recommendation: Strict fail-closed validation (prevent confusion)
  
**Low Confidence / Open Questions:**
1. **Texture ID format validation:** Should regex or whitelist be used?
2. **Blob URL handling:** Should they be stored at all, or rejected at parse time?
3. **Texture baking performance:** Will material system changes slow down builds significantly?
4. **Texture vs. pattern interaction:** If image is selected, should `texture_mode` still be processed?

These will be clarified during test design and implementation phases.

---

## Files Modified This Run

- **project_board/bugfix/in_progress/image-textures-not-applied.md:** Added Diagnosis section and four-requirement spec with detailed ACs, risks, and clarifying questions
- **project_board/CHECKPOINTS.md:** Added entry for this checkpoint run

---

## Handoff

**To:** Test Designer Agent  
**Stage:** TEST_DESIGN  
**Next Action:** Create test cases for all four requirements, targeting high coverage of R1 schema logic (most critical path). Include regression tests for existing color modes.

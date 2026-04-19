# Ticket 02e: Implement Stripes Texture Generation & Rendering

**Status:** Complete  
**Milestone:** M25 - Enemy Editor Visual Expression  
**Depends On:** 02c  
**Blocks:** —

---

## WORKFLOW STATE

| Field | Value |
|-------|-------|
| Stage | COMPLETE |
| Revision | 4 |
| Last Updated By | Implementation / AC verification |
| Next Responsible Agent | Human |
| Status | Proceed |
| Validation Status | **Implemented.** Backend: `gradient_generator._stripes_texture_generator`, `create_stripes_png_and_load` → `animated_exports/stripes/`. Material: `_material_for_stripes_zone`, `apply_zone_texture_pattern_overrides` `stripes` branch. Frontend: `GlbViewer` `createStripesMaterial` (fract period formula), `normalizedTextureMode` + `feat_body_texture_*` / legacy `texture_*` merge; `useAppStore` optional `texture_stripe_*`. **Tests run:** `pytest` `test_stripes_texture_generation.py` + `test_stripes_material_integration.py` — **11 passed** (`asset_generation/python/.venv`). `npm test -- --run GlbViewer` — **stripes + spots + core GlbViewer tests passed**; one pre-existing failure in `GlbViewer.spots.adversarial.test.tsx` (THREE.ShaderMaterial mock restore). Full-repo `diff_cover_preflight` / full pytest still reports unrelated pre-existing spots adversarial failures. |
| Blocking Issues | None |

## Overview

Implement complete support for stripes texture generation:
- Backend: Python function to generate horizontal stripe texture images (PNG) for Blender materials
- Frontend: Three.js shader to render the same **period-based** horizontal stripe pattern as the backend
- Integration: Wire `texture_mode="stripes"` into `material_system.py` and `GlbViewer.tsx`, mirroring the completed 02d spots pattern

## Scope

### Backend (Python)

- Implement `_stripes_texture_generator()` in `gradient_generator.py` (same module as spots)
- Implement `create_stripes_png_and_load()` wrapper (parallel to `create_spots_png_and_load()`)
- Save exports under `animated_exports/stripes/`
- Reuse `_create_png()`, `_crc32()`, hex helpers from existing gradient/spots code
- Unit tests for PNG output and width behavior

### Frontend (Three.js)

- `ShaderMaterial` in `GlbViewer.tsx` (or shared helper) with uniforms `uStripeColor`, `uBgColor`, `uStripeWidth`
- **Canonical fragment boundary:** `float t = fract(vUv.x * (1.0 / uStripeWidth));` then **stripe color if `t < 0.5` else background** (50% stripe / 50% gap per period)
- Apply to all meshes when `texture_mode === "stripes"`; restore originals when switching away (same lifecycle as spots)

### Material System Integration

- `_material_for_stripes_zone()` in `material_system.py` (parallel to `_material_for_spots_zone()`)
- `apply_zone_texture_pattern_overrides()`: `elif mode == "stripes":` branch with keys `feat_{zone}_texture_stripe_color`, `feat_{zone}_texture_stripe_bg_color`, `feat_{zone}_texture_stripe_width`
- Clamp `stripe_width` defensively to `[0.05, 1.0]` to match `animated_build_options_appendage_defs.py`

---

## SPECIFICATION

### Requirement 1: Backend Stripes Texture PNG Generator

#### 1. Spec Summary

**Description:**  
Implement `_stripes_texture_generator(width, height, stripe_color_hex, bg_color_hex, stripe_width) -> bytes` that fills an RGBA buffer with **horizontal stripes** (stripe runs along rows; color varies along **x** only). For each pixel `(x, y)` with `x` in `[0, width-1]`:

- Normalized coordinate: `u = (x + 0.5) / width` (center sampling; avoids bias at edges)
- `period = stripe_width` (float in `[0.05, 1.0]`; caller may clamp)
- `t = fract(u * (1.0 / period))`
- If `t < 0.5`, pixel = stripe RGBA; else background RGBA

**Hex semantics:** Same as spots: empty stripe color → black `000000`; empty background → white `ffffff`; `#` stripped by sanitizer if present; invalid hex raises `ValueError` (consistent with spots).

**PNG:** RGBA 8-bit, no interlace, correct IHDR/IDAT CRC-32 via `_create_png()`, bottom row first if existing helpers require that convention (match `_spots_texture_generator` / gradient pixel order).

**Scope:** Generator only; no Blender calls.

#### 2. Acceptance Criteria (representative)

- Valid PNG signature and dimensions match `width`×`height`
- Two different `stripe_width` values produce measurably different column counts / pattern frequency
- Empty colors default to black / white as specified
- CRC-32 validated for IHDR and IDAT chunks in tests
- No `print` / debug logging in production paths

#### 3. Risks & Mitigations

- **Naming:** UI label “Stripe width” corresponds to **UV period length** (larger = fewer stripes across U). Document in code comments to avoid confusion with “stripe thickness only.”
- **Boundary:** `t == 0.5` → background (strict `<` for stripe).

---

### Requirement 2: Blender Wrapper `create_stripes_png_and_load`

#### 1. Spec Summary

Parallel to `create_spots_png_and_load()`:

- Signature: `create_stripes_png_and_load(width, height, stripe_color_hex, bg_color_hex, stripe_width, img_name) -> bpy.types.Image`
- Directory: `{repo}/animated_exports/stripes/` (create if missing)
- File: `{img_name}.png`; Blender image name sanitized; `sRGB`; `.pack()` with same graceful failure pattern as spots.

#### 2. Acceptance Criteria

- Directory and file created; PNG non-empty; `bpy.data.images.load` succeeds when Blender available
- Colorspace and image naming follow spots/gradient conventions

---

### Requirement 3: Material Factory `_material_for_stripes_zone`

#### 1. Spec Summary

Mirror `_material_for_spots_zone()`:

- Parameters: `base_palette_name`, `finish`, `stripe_hex`, `bg_hex`, `stripe_width`, `zone_hex_fallback`, `instance_suffix`
- Calls `create_stripes_png_and_load` with 128×128 (same as spots unless existing tests require otherwise; **default 128×128**)
- Principled BSDF base color from texture node; UV map → Tex Image → Base Color; roughness 0.75, metallic 0.0; finish overrides same as spots
- Material name: `{base_palette_name}__feat_{instance_suffix}`; image name `BlobertTexStripe_{sanitized}`

#### 2. Acceptance Criteria

- Texture node `interpolation = Linear`, `extension = REPEAT`
- Fallback: empty stripe hex → zone fallback / palette; empty bg → white

---

### Requirement 4: `apply_zone_texture_pattern_overrides` — Stripes Branch

#### 1. Spec Summary

- When `feat_{zone}_texture_mode` (case-insensitive) == `"stripes"`:
  - Read `feat_{zone}_texture_stripe_color`, `feat_{zone}_texture_stripe_bg_color`, `feat_{zone}_texture_stripe_width`
  - Default width: `0.2` (from appendage defs default) then clamp to `[0.05, 1.0]`
  - `instance_suffix = f"{zone}_tex_stripe"`
  - Assign `_material_for_stripes_zone(...)` to `out[zone]`
- Do not alter gradient, spots, or assets branches.

#### 2. Acceptance Criteria

- Branch ordering and key naming consistent with spots
- No debug logging

---

### Requirement 5: Backend Unit Tests — Generation

**File:** `asset_generation/python/tests/materials/test_stripes_texture_generation.py`

Cover: PNG validity, dimensions, hex cases, CRC-32, width monotonicity (e.g. count transitions or sample columns), edge sizes 1×1 and 256×256, invalid hex.

---

### Requirement 6: Frontend Stripes Shader & Mode Switching

**File:** `GlbViewer.tsx` (and tests)

- `createStripesMaterial(stripeColor, bgColor, stripeWidth)` returning `ShaderMaterial`
- Vertex shader passes `vUv`; fragment implements Requirement 1 formula with `uStripeWidth` uniform
- `stripe_width` clamped client-side to `[0.05, 1.0]` before uniform (matches store)
- When `texture_mode === "stripes"`, apply to all meshes; backup/restore materials like spots
- Real-time uniform updates on store changes

---

### Requirement 7: Frontend Tests

**File:** `asset_generation/web/frontend/src/components/Preview/GlbViewer.stripes.test.tsx` (mirror `GlbViewer.spots.test.tsx`)

- Shader compiles; uniforms exist; mode switch applies/restores; color parsing; width updates

---

### Requirement 8: Material Integration Tests

**File:** `asset_generation/python/tests/materials/test_stripes_material_integration.py`

- `apply_zone_texture_pattern_overrides` extracts keys and calls factory (mock bpy where appropriate)
- Multiple zones, mode switching, clamping

---

### Requirement 9: Error Handling & Non-Regression

- Invalid hex paths: consistent with spots (raise or fallback per existing helpers — **match spots behavior**)
- Changing modes among `none`, `gradient`, `spots`, `stripes`, `assets` does not leak materials or break prior modes

---

## Implementation Notes

- Follow 02d spots implementation as the primary reference (same files, parallel naming)
- **Canonical shader / pixel formula:** `fract(u * (1.0 / stripe_width)) < 0.5` → stripe color

## Ticket Chain

← 02c (Remove old color pickers)
→ (none—closes texture preset sequence)

---

# EXECUTION PLAN (GENERATED BY PLANNER AGENT)

## Task Breakdown

12-task sequential/parallel plan:

1. **SPECIFICATION:** Freeze stripe design & parameter contract (Spec Agent)
2. **SPEC COMPLETENESS CHECK:** Verify spec document (Orchestrator)
3. **TEST DESIGN:** Define test suite with ~62 tests (Test Designer Agent)
4. **TEST BREAK:** Author adversarial & mutation tests ~20–25 (Test Breaker Agent)
5. **IMPLEMENTATION_BACKEND:** Stripe PNG generator & Blender wrapper (Implementation Agent)
6. **IMPLEMENTATION_BACKEND:** Material system integration (Implementation Agent)
7. **DIFF_COVER PREFLIGHT:** Python coverage gate (Orchestrator)
8. **IMPLEMENTATION_FRONTEND:** Stripe shader definition & mode switching (Implementation Agent)
9. **INTEGRATION:** End-to-end parameter flow verification (Implementation Agent)
10. **STATIC_QA:** Linting & code review (QA Agent)
11. **REGRESSION:** Ensure no breakage to gradient/spots/asset modes (QA Agent)
12. **DEPLOYMENT / CLOSURE:** Move ticket to done/ and set Stage COMPLETE (Orchestrator)

## Key Dependencies

- Tasks 1–2 sequential (spec frozen before check)
- Tasks 3–4 sequential (tests designed before adversarial)
- Tasks 5–7 sequential (backend implementation then coverage gate)
- Task 8 waits for Task 7 (coverage gate before frontend)
- Tasks 9–11 sequential (integration → QA → regression)
- Task 12 final (only after all pass)

## Reused Infrastructure (No Re-implementation)

- **PNG generation:** `_create_png()`, `_crc32()` in gradient_generator.py (reuse exactly)
- **Material patterns:** Material factory signature & finish handling from 02d spots (mirror pattern)
- **Frontend mode switching:** useEffect patterns, material backup/restore in GlbViewer.tsx (reuse exactly)

## CHECKPOINT Decisions (Medium–High Confidence)

| Decision | Resolution |
|----------|-----------|
| Stripe width semantics | Direct scalar thickness (0.05–1.0); wider = fewer thicker stripes |
| Fragment shader logic | `fract(vUv.x * (1.0 / uStripeWidth)) < 0.5` → emit stripe color |
| Backend file location | `gradient_generator.py` (same as spots, not new file) |
| Material factory location | `material_system.py`, function `_material_for_stripes_zone()` |
| Test file organization | Mirror spots: `test_stripes_texture_generation.py`, `test_stripes_material_integration.py`, `GlbViewer.stripes.test.tsx` |
| Reuse from 02d? | Yes—PNG infrastructure, material factory pattern, frontend mode switching (proven, no re-invention) |

## Checkpoint Log

- **Location:** `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M25-02e/2026-04-19T-planning.md`
- **Status:** ✅ Created; all assumptions and risks documented
- **Confidence:** Medium–High (stripe pattern is simpler than spots; all patterns proven in 02d)

---

## NEXT ACTION

### Next Responsible Agent
Human

### Status
COMPLETE — merge when ready.

### Reason
Stripes texture pipeline implemented and verified with targeted pytest + GlbViewer tests; ticket moved under `done/`.

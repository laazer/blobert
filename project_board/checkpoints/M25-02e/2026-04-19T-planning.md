# Checkpoint: M25-02e Planning Session

**Ticket:** `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/02e_implement_stripes_texture.md`  
**Stage:** PLANNING  
**Date:** 2026-04-19  
**Agent:** Planner Agent

## Context

Ticket 02d (Implement Spots Texture) was just completed with all 9 requirements specified, tested, and implemented. Ticket 02e (Implement Stripes Texture) is a parallel texture feature that:

- **Shares the same backend texture generation approach** as spots (PNG with proper CRC-32)
- **Shares the same frontend shader approach** as spots (Three.js ShaderMaterial with real-time uniforms)
- **Shares the same material system integration** as spots (Blender material factory + mode handler)
- **Key algorithmic difference:** Uses horizontal stripe pattern (`fract(vUv.x)`) instead of circular spots (distance-field)
- **Dependencies:** 02c (Remove old color pickers) is DONE; 02b (Integrate ColorPicker) is DONE; 02a (ColorPicker component) is DONE

## Analysis

### Scope Mapping (from ticket 02e)

**Backend:**
- `_stripes_texture_generator(width, height, stripe_color_hex, bg_color_hex, stripe_width)` → PNG bytes
- `create_stripes_png_and_load(width, height, stripe_color_hex, bg_color_hex, stripe_width, img_name)` → Blender Image
- `_material_for_stripes_zone()` → bpy.types.Material with striped texture baked
- Integration in `apply_zone_texture_pattern_overrides()` when mode == "stripes"
- Python tests covering PNG generation, parameter handling, edge cases

**Frontend:**
- Vertex shader (pass UV) + Fragment shader (horizontal stripes via `fract(vUv.x)`)
- ShaderMaterial with uniforms: `uStripeColor`, `uBgColor`, `uStripeWidth`
- Mode switching in GlbViewer.tsx when `texture_mode === "stripes"`
- Real-time uniform updates + material restoration
- Integration tests

**Material System:**
- Wire `feat_{zone}_texture_stripe_color`, `feat_{zone}_texture_stripe_bg_color`, `feat_{zone}_texture_stripe_width` into material factory
- Control defs already present (per ticket scope statement, lines 33–37 indicate pre-existing defs)

### Key Differences from Spots

1. **Backend generator algorithm:**
   - Spots: grid-based distance field (polar coordinates around cell centers)
   - Stripes: horizontal line pattern (uses `fract(vUv.x)`, not density; uses `stripe_width` scalar)

2. **Parameters:**
   - Spots: `texture_spot_color`, `texture_spot_bg_color`, `texture_spot_density` (0.1–5.0)
   - Stripes: `texture_stripe_color`, `texture_stripe_bg_color`, `texture_stripe_width` (0.05–1.0)

3. **Shader fragment logic:**
   - Spots: `distance_from_center < 0.35` → emit spot color
   - Stripes: `fract(vUv.x * (1.0 / uStripeWidth)) < 0.5` → emit stripe color

4. **Texture directory:** `animated_exports/stripes/` (not `spots/`)

### Reusable Components from Spots

1. **Hex color parsing** (`_hex_to_rgba()` helper in gradient_generator.py)
2. **PNG infrastructure** (`_create_png()`, `_crc32()`)
3. **Blender image loading pattern** (directory creation, `.pack()`, colorspace)
4. **Material system pattern** (material factory signature, finish handling, texture node attachment, UV mapping)
5. **Frontend integration pattern** (material backup/restore, useEffect dependencies, parseHexToVector3, error boundary)

### Assumptions (Conservative, Logged)

1. **Stripe width range:** Ticket specifies 0.05–1.0. Assume caller clamps (defensive: Spec Agent will define clamping layer).
2. **Stripe orientation:** "Horizontal" per ticket line 48. Stripe boundaries defined by `fract(vUv.x)` (x-axis frequency).
3. **Fragment shader boundary logic:** When `fract(vUv.x * frequency) < 0.5`, emit stripe color; else background. Symmetric stripe/gap ratio is acceptable for MVP.
4. **Control defs existing:** Ticket says "same approach" as spots; assume `feat_{zone}_texture_stripe_*` defs already in `appendage_defs.py` (Spec Agent verifies).
5. **Density vs. width semantics:** Spots uses density (frequency, 0.1–5.0). Stripes use width (stripe thickness, 0.05–1.0). These are different parameter semantics; Spec Agent clarifies the interpretation.
6. **Test coverage parity:** Stripes tests should mirror spots structure: PNG generation, material integration, frontend shader, mode switching. Same test depth.

## No Ambiguities; Conservative Path Forward

All requirements are **clear and traceable** from 02d completed work. The ticket reuses proven patterns with minimal algorithmic novelty (stripe pattern is simpler than spots distance field). Spec Agent will confirm:

1. Control defs are present for `texture_stripe_*` parameters
2. Stripe width clamping layer (caller vs. function)
3. Stripe boundary behavior at exact 0.5 fract boundary
4. Fragment shader precision requirements (same as spots: highp float)

## CHECKPOINT Decisions

| Decision | Resolution | Confidence |
|----------|-----------|-----------|
| **Reuse spots pattern for stripes?** | Yes. Backend: same PNG infrastructure, different pixel algorithm. Frontend: same mode switching, different shader. Material system: same factory signature, different texture dir. | High |
| **Backend implementation file** | `gradient_generator.py` (same as spots, not new file). Functions: `_stripes_texture_generator()`, `create_stripes_png_and_load()`. | High |
| **Frontend shader location** | `GlbViewer.tsx` (parallel to spots shader, same component). | High |
| **Material factory location** | `material_system.py`, function `_material_for_stripes_zone()` (parallel to spots). | High |
| **Test file organization** | Mirror spots: `test_stripes_texture_generation.py`, `test_stripes_material_integration.py`, `GlbViewer.stripes.test.tsx`. | High |
| **Stripe width semantics** | Direct scalar thickness (0.05–1.0). When `fract(vUv.x * (1.0 / stripe_width)) < 0.5`, emit stripe. Caller clamps to [0.05, 1.0]. | Medium |


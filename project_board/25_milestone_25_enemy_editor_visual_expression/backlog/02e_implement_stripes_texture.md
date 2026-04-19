# Ticket 02e: Implement Stripes Texture Generation & Rendering

**Status:** Backlog  
**Milestone:** M25 - Enemy Editor Visual Expression  
**Depends On:** 02c  
**Blocks:** —  

## Overview

Implement complete support for stripes texture generation:
- Backend: Python function to generate stripe texture images in Blender
- Frontend: Three.js shader to render procedural horizontal stripe pattern
- Integration: Wire stripes mode into material_system.py and GlbViewer.tsx

## Scope

### Backend (Python)

- Create `_stripes_texture_generator()` function in `gradient_generator.py` (or new `stripes_generator.py`)
- Generate PNG with procedural stripe pattern based on:
  - `texture_stripe_color` (hex string)
  - `texture_stripe_bg_color` (hex string, default white if empty)
  - `texture_stripe_width` (float 0.05-1.0, controls stripe thickness)
- Use proper PNG encoding with correct CRC-32 checksums
- Save to `animated_exports/stripes/` directory
- Handle color conversion from hex to RGBA
- Tests for stripe pattern generation

### Frontend (Three.js)

- Create `ShaderMaterial` for stripes mode in `GlbViewer.tsx`
- Vertex shader: outputs UV coordinates and position
- Fragment shader: generates horizontal stripe pattern using fractional coordinates
  - Sample `fract(vUv.x)` to determine stripe boundaries
  - Emit stripe color when `fract(vUv.x) < uStripeWidth`
  - Emit background color otherwise
- Uniforms: `uStripeColor`, `uBgColor`, `uStripeWidth`
- Apply to all meshes when `texture_mode === "stripes"`
- Restore original materials when mode changes to "none"

### Material System Integration

- Add stripes branch in `apply_zone_texture_pattern_overrides()` in `material_system.py`
- Wire texture_stripe_* parameters to generation function
- Create `_material_for_stripes_zone()` function (parallel to `_material_for_gradient_zone()`)

## Acceptance Criteria

### Backend

- [ ] `_stripes_texture_generator()` creates valid PNG files
- [ ] Stripe width parameter changes stripe thickness visibly
- [ ] Color parameters apply correctly to generated texture
- [ ] Empty color defaults to white correctly
- [ ] Python tests cover stripe generation with various widths
- [ ] No debug logging in production code

### Frontend

- [ ] Stripes ShaderMaterial renders without errors
- [ ] Stripe pattern visible when texture_mode="stripes"
- [ ] Stripe width changes update in real-time
- [ ] Color changes update uniforms without reload
- [ ] Original materials restored when switching to "none"
- [ ] Works on all mesh types (StandardMaterial, etc.)
- [ ] No React errors in console

### Integration

- [ ] `texture_mode="stripes"` triggers stripes generation
- [ ] All stripe parameters flow from UI → store → backend → frontend
- [ ] Material assignment works for all body zones
- [ ] Tests verify parameter passing

## Implementation Notes

- Follow the gradient texture implementation as a reference
- Use same approach for PNG generation and material wrapping
- Stripe pattern uses `fract(vUv.x)` for horizontal stripes
- Consider performance: shader should be simple and fast
- Test with various widths to ensure pattern clarity at extremes
- Can be extended to support vertical stripes or diagonal in future with additional uniforms

## Ticket Chain

← 02c (Remove old color pickers)
→ (none—closes texture preset sequence)

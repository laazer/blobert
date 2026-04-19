# Ticket 02d: Implement Spots Texture Generation & Rendering

**Status:** Backlog  
**Milestone:** M25 - Enemy Editor Visual Expression  
**Depends On:** 02c  
**Blocks:** —  

## Overview

Implement complete support for spots (polka dot) texture generation:
- Backend: Python function to generate spot texture images in Blender
- Frontend: Three.js shader to render procedural spots pattern
- Integration: Wire spots mode into material_system.py and GlbViewer.tsx

## Scope

### Backend (Python)

- Create `_spots_texture_generator()` function in `gradient_generator.py` (or new `spots_generator.py`)
- Generate PNG with procedural spot pattern based on:
  - `texture_spot_color` (hex string)
  - `texture_spot_bg_color` (hex string, default white if empty)
  - `texture_spot_density` (float 0.1-5.0, controls spot frequency)
- Use proper PNG encoding with correct CRC-32 checksums
- Save to `animated_exports/spots/` directory
- Handle color conversion from hex to RGBA
- Tests for spot pattern generation

### Frontend (Three.js)

- Create `ShaderMaterial` for spots mode in `GlbViewer.tsx`
- Vertex shader: outputs UV coordinates and position
- Fragment shader: generates spot pattern using distance field
  - Sample `fract(vUv * uDensity)` offset to [-0.5, 0.5]
  - Emit spot color inside circle of radius 0.35
  - Emit background color outside circle
- Uniforms: `uSpotColor`, `uBgColor`, `uDensity`
- Apply to all meshes when `texture_mode === "spots"`
- Restore original materials when mode changes to "none"

### Material System Integration

- Add spots branch in `apply_zone_texture_pattern_overrides()` in `material_system.py`
- Wire texture_spot_* parameters to generation function
- Create `_material_for_spots_zone()` function (parallel to `_material_for_gradient_zone()`)

## Acceptance Criteria

### Backend

- [ ] `_spots_texture_generator()` creates valid PNG files
- [ ] Spot pattern changes visibly with density parameter
- [ ] Color parameters apply correctly to generated texture
- [ ] Empty color defaults to white correctly
- [ ] Python tests cover spot generation with various densities
- [ ] No debug logging in production code

### Frontend

- [ ] Spots ShaderMaterial renders without errors
- [ ] Spot pattern visible when texture_mode="spots"
- [ ] Density changes update in real-time
- [ ] Color changes update uniforms without reload
- [ ] Original materials restored when switching to "none"
- [ ] Works on all mesh types (StandardMaterial, etc.)
- [ ] No React errors in console

### Integration

- [ ] `texture_mode="spots"` triggers spots generation
- [ ] All spot parameters flow from UI → store → backend → frontend
- [ ] Material assignment works for all body zones
- [ ] Tests verify parameter passing

## Implementation Notes

- Follow the gradient texture implementation as a reference
- Use same approach for PNG generation and material wrapping
- Spot pattern can use sine/cosine for smooth falloff or step function
- Consider performance: shader should be simple and fast
- Test with various densities to ensure pattern clarity at extremes

## Ticket Chain

← 02c (Remove old color pickers)
→ 02e (Implement stripes texture)

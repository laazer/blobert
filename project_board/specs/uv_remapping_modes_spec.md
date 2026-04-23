# UV Remapping Modes System Specification

**Status:** Specification  
**Target Milestone:** Post Milestone 9 (Asset Generation Refactoring)  
**Owned by:** Implementation Phase 2 (Godot + Three.js)  

---

## Overview

Instead of regenerating textures to achieve different visual stripe patterns, this system uses UV coordinate remapping to apply 12 different transformations to a single base stripe texture. The same texture is "viewed" through different coordinate systems to create the appearance of rotation, spiraling, tiling, and other effects.

**Key principle:** One base texture, 12 different ways to sample it.

---

## Base Texture Requirements

### Input: Single Base Stripe Texture
- **Format:** PNG, 256×256px minimum (recommend 256×256 or 512×512)
- **Content:** Horizontal stripes (simple parallel lines)
  - Pattern: alternating stripe color + background color
  - Direction: **horizontal only** (stripes run left-right, U axis)
  - Width: Configurable via `stripe_width` parameter (0.05–1.0)
  - No rotation, no complex patterns

### Generation
- Implement in `asset_generation/python/src/materials/gradient_generator.py`
- Function: `_stripes_texture_base_png(width, height, stripe_color_hex, bg_color_hex, stripe_width) -> bytes`
- Output: PNG-encoded bytes (valid PNG header + IDAT + IEND)
- Cached by filename: `BlobertTexStripeBase_{stripe_color}_{bg_color}_{stripe_width}.png`

---

## UV Remapping Modes (12 Total)

Each mode transforms UV coordinates before sampling the base texture. All formulas assume UV coordinates in range [0, 1] × [0, 1] with origin (0, 0) at bottom-left.

### Mode 0: Standard UV
**Visual:** Horizontal stripes (base texture, no transform)

```glsl
vec2 uv_remapped = uv;
```

**Parameters:** None  
**Use case:** Direct view of base texture

---

### Mode 1: Rotated UV (90°)
**Visual:** Vertical stripes (base texture rotated 90°)

Rotate the U-V plane 90° counterclockwise, then sample. Effect: horizontal stripes become vertical.

```glsl
vec2 uv_remapped = vec2(1.0 - uv.y, uv.x);
```

**Derivation:**
- Rotation matrix for 90° CCW: `[0, 1; -1, 0]`
- Applied to UV: `(u, v) → (v, 1-u)` then remap to [0, 1]: `(v, 1-u) → (1-v, 1-u)`
- Simplified for visual effect (horizontal→vertical): `(1-v, u)`
- Alternative (equivalent): `(v, 1-u)` or `(1-u, 1-v)` depending on desired handedness

**Parameters:**  
- `rotation_angle: float` (future extension, currently discrete 90°)

**Use case:** "Tiger stripe" vertical bands

---

### Mode 2: Tiled UV
**Visual:** Repeated/tiled pattern (base texture repeated N×M times)

Scale both U and V by tile factor, apply modulo to create repeating tiles.

```glsl
float tile_scale = 3.0;  // 3×3 grid of tiles
vec2 uv_remapped = mod(uv * tile_scale, 1.0);
```

**Parameters:**
- `tile_scale: float` (default: 2.0, range: 1.0–10.0)
  - Interpreted as "number of tiles across U axis"
  - V tiling auto-scales to maintain aspect ratio of base texture

**Use case:** Small repeating stripe patterns over large areas

---

### Mode 3: Stretched Vertically
**Visual:** Horizontal stripes stretched vertically (wider stripes)

Scale V coordinate down, compress vertical space.

```glsl
float stretch_factor = 0.5;  // compress V space
vec2 uv_remapped = vec2(uv.x, uv.y * stretch_factor);
```

**Parameters:**
- `stretch_factor: float` (default: 0.5, range: 0.1–2.0)
  - < 1.0: compress (fewer, wider stripes visible)
  - > 1.0: expand (more, thinner stripes visible)

**Use case:** Thick horizontal bands

---

### Mode 4: Compressed Vertically
**Visual:** Horizontal stripes compressed vertically (thinner stripes)

Scale V coordinate up, expand vertical space to see more detail.

```glsl
float compress_factor = 2.0;
vec2 uv_remapped = vec2(uv.x, uv.y / compress_factor);
```

**Parameters:**
- `compress_factor: float` (default: 2.0, range: 1.0–5.0)
  - Direct reciprocal of stretch_factor (for symmetry)

**Use case:** Fine horizontal detail

---

### Mode 5: Offset U
**Visual:** Horizontal stripes with horizontal phase shift

Add constant to U coordinate (wrap with modulo).

```glsl
float u_offset = 0.25;  // 1/4 texture shift right
vec2 uv_remapped = vec2(mod(uv.x + u_offset, 1.0), uv.y);
```

**Parameters:**
- `u_offset: float` (default: 0.0, range: 0.0–1.0)
  - Wraps with modulo to stay in [0, 1]

**Use case:** Shift stripe phase without changing pattern

---

### Mode 6: Offset V
**Visual:** Horizontal stripes with vertical phase shift

Add constant to V coordinate (wrap with modulo).

```glsl
float v_offset = 0.25;
vec2 uv_remapped = vec2(uv.x, mod(uv.y + v_offset, 1.0));
```

**Parameters:**
- `v_offset: float` (default: 0.0, range: 0.0–1.0)

**Use case:** Vertical stripe alignment adjustment

---

### Mode 7: Mirrored U
**Visual:** Horizontal stripes mirrored left-right

Flip U coordinate around center.

```glsl
vec2 uv_remapped = vec2(1.0 - uv.x, uv.y);
```

**Parameters:** None

**Use case:** Bilateral symmetry

---

### Mode 8: Mirrored V
**Visual:** Horizontal stripes mirrored top-bottom

Flip V coordinate around center.

```glsl
vec2 uv_remapped = vec2(uv.x, 1.0 - uv.y);
```

**Parameters:** None

**Use case:** Vertical symmetry

---

### Mode 9: Diagonal Stripes
**Visual:** Diagonal stripes at 45° angle

Rotate UV space so stripes appear diagonal. Use sum of U and V weighted by angle.

```glsl
float angle_rad = radians(45.0);  // 45° diagonal
vec2 rotated = vec2(
    uv.x * cos(angle_rad) - uv.y * sin(angle_rad),
    uv.x * sin(angle_rad) + uv.y * cos(angle_rad)
);
vec2 uv_remapped = vec2(rotated.x, fract(rotated.y));  // sample along rotated axis
```

**Alternative (simpler, for 45° only):**
```glsl
vec2 uv_remapped = vec2(uv.x + uv.y, uv.x);  // diagonal blend
// Adjust to keep in [0, 1]: normalize the sum
vec2 uv_remapped = vec2(mod(uv.x + uv.y, 1.4142135), uv.x);  // √2 for normalization
```

**Parameters:**
- `diagonal_angle: float` (default: 45.0, range: 0.0–90.0)
  - Angle in degrees from horizontal

**Use case:** Diagonal band effects

---

### Mode 10: Spiral Pattern
**Visual:** Spiral stripes emanating from center

Convert to polar coordinates (distance + angle), use angle to determine stripe sampling.

```glsl
// Convert to polar coordinates (center at 0.5, 0.5)
vec2 centered = uv - vec2(0.5, 0.5);
float dist = length(centered);
float angle = atan(centered.y, centered.x);

// Spiral: map angle to U, distance to V
float spiral_tightness = 3.0;  // higher = more spirals
vec2 uv_remapped = vec2(
    mod(angle / (2.0 * 3.14159) + spiral_tightness * dist, 1.0),  // angle-based U
    dist  // radial distance as V
);
```

**Parameters:**
- `spiral_tightness: float` (default: 2.0, range: 0.5–10.0)
  - Higher values = more spiral windings per radius

**Use case:** Radial/spiral visual effects

---

### Mode 11: Concentric Rings
**Visual:** Concentric circular rings

Use only the radial distance component, ignore angle.

```glsl
// Convert to polar coordinates
vec2 centered = uv - vec2(0.5, 0.5);
float dist = length(centered);

// Rings: map radial distance to U (repeating), use angle for V gradient
float ring_scale = 5.0;  // number of rings across radius
vec2 uv_remapped = vec2(
    mod(dist * ring_scale, 1.0),  // repeating rings
    atan(centered.y, centered.x) / (2.0 * 3.14159) + 0.5  // angle as gradient
);
```

**Parameters:**
- `ring_scale: float` (default: 4.0, range: 1.0–20.0)
  - Number of complete ring cycles from center to edge

**Use case:** Circular/radial stripe patterns

---

## Implementation Architecture

### Python Reference Implementation
**Location:** `asset_generation/python/src/materials/uv_remapping.py`

```python
from enum import IntEnum
import math

class UVRemappingMode(IntEnum):
    STANDARD = 0
    ROTATED_90 = 1
    TILED = 2
    STRETCHED = 3
    COMPRESSED = 4
    OFFSET_U = 5
    OFFSET_V = 6
    MIRRORED_U = 7
    MIRRORED_V = 8
    DIAGONAL = 9
    SPIRAL = 10
    CONCENTRIC_RINGS = 11

def remap_uv(
    u: float, 
    v: float, 
    mode: UVRemappingMode, 
    **params
) -> tuple[float, float]:
    """
    Apply UV remapping transformation.
    
    Args:
        u, v: Input UV coordinates [0, 1]
        mode: Remapping mode enum
        **params: Mode-specific parameters (tile_scale, offset_u, etc.)
    
    Returns:
        (u_remapped, v_remapped) tuple, values in [0, 1] (or [0, inf) for some modes)
    """
    # Implementation per mode specification above
```

### GLSL Shader Library
**Location:** `asset_generation/web/frontend/src/shaders/uv_remapping.glsl`

```glsl
// Shared GLSL functions for UV remapping
// Used by both Three.js (web viewer) and Godot shaders

#define UV_MODE_STANDARD 0
#define UV_MODE_ROTATED_90 1
#define UV_MODE_TILED 2
// ... etc

vec2 remap_uv(vec2 uv, int mode, vec4 params) {
    switch(mode) {
        case UV_MODE_STANDARD:
            return uv;
        case UV_MODE_ROTATED_90:
            return vec2(1.0 - uv.y, uv.x);
        case UV_MODE_TILED:
            return mod(uv * params.x, 1.0);
        // ... etc
    }
}
```

### Web Viewer (Three.js)
**Location:** `asset_generation/web/frontend/src/components/Preview/UVRemappingViewer.tsx`

- Custom `ShaderMaterial` that uses the GLSL library
- Uniforms for mode + parameters
- UI controls: mode selector + parameter sliders
- Real-time updates to uniforms on user interaction

### Godot Shader + GDScript
**Location:** `scripts/materials/uv_remapping_material.gd` + `scripts/shaders/uv_remapping.gdshader`

- Custom shader that references GLSL library (or ports the logic to GLSL/GDSL)
- Material script exposes mode + parameters as uniform setters
- Scene UI (buttons, sliders) calls material setters on change

---

## Testing Strategy

### Python Mathematical Validation Tests
**Location:** `asset_generation/python/tests/materials/test_uv_remapping.py`

Test each mode's transformation against expected output:
- Mode 0: identity (u, v) → (u, v)
- Mode 1: rotation (u, v) → (1-v, u)
- Mode 2: tiling with scale 2.0: mod(2*(u,v), 1.0)
- Mode 3–11: deterministic edge cases (center points, corners, wrapping)

All tests use pure mathematical assertions (no visual validation yet).

### Parity Tests (Python ↔ Shader)
For each mode and test point, verify:
- Python `remap_uv(u, v, mode, params)` output
- GLSL `remap_uv(vec2(u, v), mode, params)` output (by running shader on CPU via test harness or Godot GDScript export)
- Both must match to 4 decimal places

### Visual Tests (Web Viewer ↔ Godot)
- Load same GLB model in both viewers
- Set same mode + parameters in both
- Capture screenshots → visual diff
- Modes should be **visually identical** (within rendering/anti-aliasing tolerances)

---

## Uniform Parameters Structure

All shaders accept a single `UVRemappingParams` struct:

```glsl
// GLSL
struct UVRemappingParams {
    int mode;              // 0–11
    float param1;          // tile_scale, stretch, offset, etc.
    float param2;          // (future) secondary param
    float param3;          // (future) tertiary param
    float param4;          // (future) quaternary param
};

uniform UVRemappingParams uv_remap;
```

```gdscript
# GDScript
var uv_remap = {
    "mode": 0,
    "param1": 1.0,
    "param2": 0.0,
    "param3": 0.0,
    "param4": 0.0
}

func set_remapping_mode(mode: int, param1: float = 1.0) -> void:
    uv_remap["mode"] = mode
    uv_remap["param1"] = param1
    # Update material uniforms
```

---

## UI Controls

### Web Viewer (React)
- **Mode selector:** Radio buttons or dropdown (0–11)
- **Parameter sliders:** Visible only for mode's relevant parameters
  - tile_scale: [1, 10], step 0.5
  - stretch_factor: [0.1, 2.0], step 0.1
  - offset_u/v: [0, 1], step 0.05
  - angle: [0, 90], step 5
  - spiral_tightness: [0.5, 10], step 0.5
  - ring_scale: [1, 20], step 0.5

### Godot Scene
- **Mode buttons:** 12 buttons in a grid or tab bar
- **Parameter panel:** Shows only relevant slider(s) for selected mode
- **Live preview:** Material updates in real-time as parameters change

---

## Implementation Phases

### Phase 1: Python Reference + Tests (2–3 hours)
1. Implement `uv_remapping.py` with all 12 modes
2. Write deterministic tests in `test_uv_remapping.py`
3. Document each formula in code

### Phase 2: Base Texture Generator (1–2 hours)
1. Implement `_stripes_texture_base_png()` in `gradient_generator.py`
2. Simple horizontal stripes, configurable width/colors
3. Cache by filename

### Phase 3: Web Viewer Integration (3–4 hours)
1. Create `uv_remapping.glsl` with shared functions
2. Implement `UVRemappingViewer.tsx` with Three.js `ShaderMaterial`
3. Build UI controls (mode selector + parameter sliders)
4. Test parity: Python output ↔ shader output (visual comparison)

### Phase 4: Godot Integration (3–4 hours)
1. Port GLSL to Godot shader or reuse `uv_remapping.glsl`
2. Implement `uv_remapping_material.gd` GDScript wrapper
3. Add material instance to test scene
4. Build Godot UI controls (mode buttons + sliders)
5. Cross-validate with web viewer (side-by-side screenshots)

### Phase 5: Documentation & Finalization (1–2 hours)
1. Add usage guide (how to select modes, configure parameters)
2. Create visual examples for each mode (screenshots/GIFs)
3. Document caching strategy (texture filenames, cache invalidation)
4. Add warnings for performance (e.g., spiral at high tightness on mobile)

---

## Success Criteria

✓ All 12 modes produce mathematically distinct outputs (verified by Python tests)  
✓ Base texture generator produces valid PNG with configurable stripe width  
✓ Web viewer can switch modes and adjust parameters in real-time  
✓ Godot scene displays same visual result as web viewer for same mode+params  
✓ UI controls are responsive and intuitive (no lag when changing parameters)  
✓ Code is well-documented with visual examples for each mode  
✓ Parity tests pass (Python ↔ shader, web ↔ Godot)  

---

## Dependencies & Assumptions

- **Base texture format:** PNG (standard for blobert asset pipeline)
- **Shader language:** GLSL (compatible with Three.js + Godot 4.x)
- **UV convention:** [0, 1] × [0, 1], origin at bottom-left (standard in most graphics APIs)
- **No prior changes required:** Implementation starts after Milestone 901 (asset generation refactoring; `project_board/901_milestone_901_asset_generation_refactoring/`)

---

## Future Extensions

1. **Procedural spiral tightness animation:** Time-based variation of spiral_tightness for animated effects
2. **Mode blending:** Interpolate between two modes with smooth lerp
3. **More modes:** Wave, checkerboard, radial gradient sampling
4. **Performance optimization:** Pre-compute certain transformations for common parameters
5. **Mobile fallback:** If shader compilation fails, display mode 0 (standard UV)


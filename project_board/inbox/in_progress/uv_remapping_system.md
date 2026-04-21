# UV Remapping System: 12 Texture Transformation Modes

**Ticket ID:** uv-remapping-system  
**Status:** Ready (Post Milestone 9)  
**Priority:** High (unblocks material editor iteration)  

---

## Description

Implement a comprehensive UV coordinate remapping system that applies 12 different transformations to a single base stripe texture. This replaces the current approach of regenerating textures for different visual effects.

**Why this matters:**
- Current stripe rotation causes pattern morphing (beachball→doplar→swirl) due to mathematical convergence
- Regenerating textures for each rotation is expensive (disk, baking time, cache complexity)
- **UV remapping solution:** One texture, 12 different "viewing angles" via coordinate transforms
- Enables parity between web viewer (Three.js) and Godot runtime (live iteration)

**Scope:**
- 12 transformation modes (standard, rotated 90°, tiled, stretched, compressed, offsets, mirrors, diagonal, spiral, concentric rings)
- Python reference implementation with deterministic tests
- Base stripe texture generator (simple horizontal stripes)
- Web viewer integration (Three.js shader + UI controls)
- Godot integration (shader + material + scene controls)
- Comprehensive documentation and parity validation

---

## Acceptance Criteria

- [ ] **AC1: Specification complete and reviewed**
  - Formal spec at `project_board/specs/uv_remapping_modes_spec.md`
  - All 12 modes defined with exact GLSL formulas
  - Parameters and use cases documented
  
- [ ] **AC2: Python reference implementation**
  - Module: `asset_generation/python/src/materials/uv_remapping.py`
  - Function: `remap_uv(u, v, mode, **params) -> (u_rem, v_rem)`
  - All 12 modes implemented with deterministic behavior
  - Type hints and docstrings complete
  
- [ ] **AC3: Python tests (deterministic)**
  - File: `asset_generation/python/tests/materials/test_uv_remapping.py`
  - ≥3 test points per mode (edge cases: corners, center, wrapping)
  - Tests validate mathematical properties (e.g., mirrored has symmetry, spiral converges to center)
  - All tests passing
  
- [ ] **AC4: Base stripe texture generator**
  - Function: `_stripes_texture_base_png(width, height, color_hex, bg_hex, stripe_width) -> bytes`
  - Output: Valid PNG (256×256 minimum)
  - Content: Pure horizontal stripes, configurable width [0.05, 1.0]
  - Cached by filename to avoid regeneration
  - Tests verify PNG validity and stripe pattern
  
- [ ] **AC5: GLSL shader library**
  - File: `asset_generation/web/frontend/src/shaders/uv_remapping.glsl`
  - Shared functions usable by both Three.js and Godot
  - All 12 modes as GLSL switch cases
  - Uniform struct: `UVRemappingParams { mode, param1, param2, param3, param4 }`
  - No shader compilation errors
  
- [ ] **AC6: Web viewer (Three.js) integration**
  - Component: `asset_generation/web/frontend/src/components/Preview/UVRemappingViewer.tsx`
  - Renders GLB model with custom `ShaderMaterial`
  - Mode selector (12 radio buttons or dropdown)
  - Parameter sliders (dynamic, show only relevant params for active mode)
  - Real-time uniform updates on interaction
  - No lag when changing modes/parameters (60 FPS target)
  
- [ ] **AC7: Godot shader integration**
  - Shader file: `scripts/shaders/uv_remapping.gdshader` (or equivalent)
  - Material script: `scripts/materials/uv_remapping_material.gd`
  - Exposes `set_remapping_mode(mode: int, param1: float)` function
  - Material can be applied to any Mesh3D node
  - No shader compilation errors in Godot
  
- [ ] **AC8: Godot scene controls**
  - Demo scene: `scenes/tools/uv_remapping_demo.tscn` (or integrated into existing material editor)
  - Mode buttons: 12 buttons, only one active at a time
  - Parameter panel: Shows relevant sliders for active mode
  - Live preview: Mesh updates immediately on parameter change
  - Scene is playable without errors
  
- [ ] **AC9: Parity validation (Python ↔ Shader)**
  - Test harness: Compare Python `remap_uv()` output vs GLSL output
  - 50+ test points per mode (grid sampling)
  - Tolerance: ±0.001 (floating-point precision)
  - All modes match within tolerance
  
- [ ] **AC10: Parity validation (Web ↔ Godot)**
  - Visual test: Same GLB, same mode+params in both viewers
  - Screenshot comparison: Web viewer and Godot render visually identical stripes
  - 3+ modes tested (standard, rotated 90°, spiral)
  - Lighting/anti-aliasing differences accepted
  
- [ ] **AC11: Documentation**
  - Usage guide: How to select modes, configure parameters
  - Visual examples: Screenshots/GIFs showing each mode's effect
  - API docs: Docstrings on all public functions
  - Caching strategy: Documented in README or CLAUDE.md
  
- [ ] **AC12: Performance acceptable**
  - Shader compilation time < 2 seconds
  - Runtime: 60 FPS on test hardware
  - No memory leaks during mode switching
  - Web viewer: No UI lag with 20+ parameter updates/second

---

## Execution Plan

### Phase 1: Python Reference (2–3 hours)
1. Implement `uv_remapping.py` with all 12 modes
2. Write `test_uv_remapping.py` (deterministic tests)
3. Verify all tests pass locally

### Phase 2: Base Texture Generator (1–2 hours)
1. Add `_stripes_texture_base_png()` to `gradient_generator.py`
2. Implement stripe rendering (simple horizontal lines)
3. Add tests for PNG validity and stripe count

### Phase 3: Web Viewer (3–4 hours)
1. Create `uv_remapping.glsl` shader library
2. Build `UVRemappingViewer.tsx` component
3. Implement mode selector + parameter sliders
4. Visual testing (compare modes side-by-side)

### Phase 4: Godot Integration (3–4 hours)
1. Port/integrate shader into Godot
2. Create material script wrapper
3. Build demo scene with controls
4. Cross-test with web viewer

### Phase 5: Finalization & Docs (1–2 hours)
1. Document usage and API
2. Create visual examples
3. Update CLAUDE.md or README as needed
4. Code review + cleanup

**Total estimated time:** 10–16 hours (can be split across 2–3 working sessions)

---

## Dependencies

- ✓ Milestone 9 (Asset Generation Refactoring) **MUST** complete first
  - Cleans up material system
  - Establishes consistent texture caching patterns
  - Refactors material_system.py
  
- ✓ Three.js and Godot 4.x are current (already deployed)

---

## Related Work

- **Previous attempt:** Stripe texture rotation via mathematical transformation (beachball→doplar→swirl morphing)
  - **Root cause:** Axis-swapping approach causes mathematical convergence
  - **This ticket:** Sidesteps convergence entirely via different math (polar, offsets, mirrors)

- **Blocked by:** Milestone 9 asset_generation cleanup (current sprint)

---

## WORKFLOW STATE

| Field | Value |
|-------|-------|
| **Stage** | PLANNING |
| **Revision** | 1 |
| **Last Updated By** | Orchestrator |
| **Next Responsible Agent** | Planner Agent |
| **Status** | Proceed |
| **Validation Status** | Spec ready at `project_board/specs/uv_remapping_modes_spec.md` |
| **Blocking Issues** | None (waiting for Milestone 9 to complete) |

---

## NEXT ACTION

1. **Post Milestone 9:** Move ticket from `inbox/in_progress/` → `26_milestone_26_uv_remapping_system/backlog/`
2. **Planner agent:** Decompose phases into granular tasks
3. **Proceed through standard workflow:** Planner → Spec → Test Designer → Test Breaker → Implementation

---

## Notes for Implementation Team

**Key design decisions:**
1. **One base texture:** Simplifies caching and reduces asset size
2. **Shared GLSL library:** Ensures parity between viewers (same math, no interpretation drift)
3. **Deterministic Python tests:** Catch shader bugs before shipping
4. **No texture pre-baking:** All 12 variants computed at runtime (flexible + fast iteration)

**Common pitfalls to avoid:**
- ✗ Pre-baking all 12 modes as separate textures (reduces flexibility, breaks live iteration)
- ✗ Implementing math differently in Python vs. GLSL (parity tests will catch this, but costs time)
- ✗ Normalizing/clamping UV incorrectly (some modes intentionally wrap, some mirror)
- ✗ Forgetting to update shader when spec changes (keep spec as source of truth)

**Testing priorities:**
1. Mathematical correctness (Python tests)
2. Shader compilation (no errors in Three.js or Godot)
3. Visual parity (web ↔ Godot should look identical)
4. UI responsiveness (no lag on parameter changes)
5. Edge cases (wrapping at texture boundaries, center singularities in spiral/rings)


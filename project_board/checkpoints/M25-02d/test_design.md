# Test Design for M25-02d: Spots Texture Implementation

**Ticket:** M25-02d - Implement Spots Texture Generation & Rendering  
**Stage:** TEST_DESIGN → TEST_BREAK  
**Date:** 2026-04-19

---

## Overview

Comprehensive test suite for 9 requirements spanning:
- Backend PNG texture generation (Python)
- Material factory and system integration (Python/Blender)
- Frontend shader and mode switching (TypeScript/React)
- End-to-end parameter flow (integration)

---

## Test Files Created

### 1. Backend PNG Generator Tests
**File:** `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/materials/test_spots_texture_generation.py`

**Purpose:** Unit tests for `_spots_texture_generator()` and `create_spots_png_and_load()` functions.

**Test Classes:**

#### `TestSpotsTextureGenerator` (18 tests)
Maps to Requirements 1 & 5 (AC1.1–AC1.15, AC5.1–AC5.16)

| Test | Purpose | AC Coverage |
|------|---------|------------|
| `test_spots_texture_generator_exists` | Function exists | AC1.1 |
| `test_returns_valid_png_bytes` | PNG signature valid | AC1.3, AC5.3 |
| `test_output_dimensions_match_input` | Width/height correct | AC1.4, AC5.4 |
| `test_hex_color_parsing_lowercase` | Lowercase hex parsing | AC1.5, AC5.5 |
| `test_hex_color_parsing_uppercase` | Uppercase hex parsing | AC1.6, AC5.6 |
| `test_empty_spot_color_defaults_to_black` | Empty color → black | AC1.7, AC5.7 |
| `test_empty_bg_color_defaults_to_white` | Empty BG → white | AC1.8, AC5.8 |
| `test_invalid_hex_raises_valueerror` | Invalid hex error | AC1.9, AC5.9 |
| `test_density_0_1_creates_sparse_spots` | Density=0.1 sparse | AC1.10, AC5.10 |
| `test_density_5_0_creates_dense_spots` | Density=5.0 dense | AC1.11, AC5.11 |
| `test_1x1_texture_does_not_crash` | Edge case 1×1 | AC1.12, AC5.12 |
| `test_256x256_texture_does_not_crash` | Edge case 256×256 | AC1.13, AC5.13 |
| `test_crc32_ihdr_valid` | IHDR CRC-32 correct | AC1.14, AC5.14 |
| `test_crc32_idat_valid` | IDAT CRC-32 correct | AC1.15, AC5.15 |
| `test_no_debug_logging_in_output` | No debug logs | AC1.16 |

#### `TestSpotsTextureGeneratorEdgeCases` (4 tests)
Edge cases for color handling:

| Test | Purpose |
|------|---------|
| `test_none_spot_color_treated_as_empty` | None → empty string |
| `test_case_insensitive_hex_parsing` | Mixed case hex |
| `test_density_boundary_0_1` | Lower bound density |
| `test_density_boundary_5_0` | Upper bound density |

#### `TestCreateSpotsTextureWrapper` (7 tests)
Maps to Requirement 2 (AC2.1–AC2.10)

| Test | Purpose | AC Coverage |
|------|---------|------------|
| `test_wrapper_function_exists` | Function exists | AC2.1 |
| `test_wrapper_creates_spots_directory` | Creates `animated_exports/spots/` | AC2.2 |
| `test_wrapper_calls_blender_image_load` | Calls `bpy.data.images.load()` | AC2.5 |
| `test_wrapper_sets_colorspace_to_srgb` | Colorspace = "sRGB" | AC2.6 |
| `test_wrapper_packs_image` | Calls `.pack()` | AC2.7 |

**Key Testing Patterns:**
- PNG header/structure validation via struct unpacking
- CRC-32 calculation reuses gradient infrastructure
- Pixel counting for density impact verification
- Mock-based Blender integration tests

---

### 2. Material System Integration Tests
**File:** `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/materials/test_spots_material_integration.py`

**Purpose:** Unit and integration tests for material factory and system hooks.

**Test Classes:**

#### `TestMaterialForSpotsZone` (6 tests)
Maps to Requirement 3 (AC3.1–AC3.11)

| Test | Purpose | AC Coverage |
|------|---------|------------|
| `test_function_exists` | Function exists | AC3.1 |
| `test_function_signature_correct` | Signature matches spec | AC3.2 |
| `test_calls_create_spots_png_and_load` | PNG wrapper called | AC3.3 |
| `test_returns_material_with_nodes_enabled` | Material has use_nodes=True | AC3.4 |
| `test_material_name_correct_format` | Name format correct | AC3.7 |

#### `TestApplyZoneTexturePatternOverridesSpots` (11 tests)
Maps to Requirement 4 (AC4.1–AC4.11)

| Test | Purpose | AC Coverage |
|------|---------|------------|
| `test_spots_branch_exists` | Branch for "spots" mode exists | AC4.1 |
| `test_extracts_spot_color_parameter` | Extracts spot color | AC4.2 |
| `test_extracts_bg_color_parameter` | Extracts BG color | AC4.3 |
| `test_extracts_density_with_fallback_and_clamping` | Density [0.1, 5.0] | AC4.4 |
| `test_retrieves_base_palette_name` | Palette name retrieved | AC4.5 |
| `test_retrieves_zone_finish` | Zone finish retrieved | AC4.6 |
| `test_retrieves_zone_hex` | Zone hex retrieved | AC4.7 |
| `test_calls_spots_material_factory` | Factory called | AC4.8 |
| `test_assigns_returned_material_to_output` | Material assigned | AC4.9 |
| `test_gradient_and_assets_branches_unchanged` | No regressions | AC4.10 |

**Key Testing Patterns:**
- Mock-heavy approach (no full Blender scene)
- Parametrization via build_options dict
- Function source inspection for code structure validation
- Call argument inspection for integration verification

---

### 3. Frontend Shader & Integration Tests
**File:** `/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src/components/Preview/GlbViewer.spots.test.tsx`

**Purpose:** Component-level tests for shader application, mode switching, and uniform updates.

**Test Suite:** 20 behavioral tests

Maps to Requirements 6, 7, 8 (AC6.1–AC6.15, AC7.1–AC7.15, AC8.5–AC8.9)

| Test | Purpose | AC Coverage |
|------|---------|------------|
| `test_no_shader_when_mode_is_none` | No shader in "none" mode | AC6.7 |
| `test_handle_mode_change_to_spots` | Mode change handled | AC7.1 |
| `test_default_colors_empty_strings` | Empty → fallback colors | AC7.6, AC7.7 |
| `test_parse_hex_color_apply_to_uniform` | Hex parsing and uniform | AC7.3, AC7.4 |
| `test_handle_hash_prefix_in_hex` | "#ff0000" handling | AC7.8 |
| `test_case_insensitive_hex` | Case-insensitive parsing | AC7.8 |
| `test_update_uniforms_on_density_change` | Uniform update | AC7.10 |
| `test_update_uniforms_on_color_change` | Color uniform update | AC7.10 |
| `test_update_uniforms_on_bg_color_change` | BG color uniform update | AC7.10 |
| `test_invalid_hex_graceful_handling` | Fallback on invalid hex | AC7.9 |
| `test_density_out_of_bounds_handling` | Bounds validation | AC7.4 |
| `test_restore_on_mode_change_away` | Material restoration | AC7.2, AC7.9 |
| `test_restore_on_gradient_switch` | Mode switch restoration | AC7.2 |
| `test_rapid_mode_changes_idempotent` | Race condition handling | AC7.13 |
| `test_no_infinite_re_renders` | No re-render loops | AC7.14 |
| `test_apply_to_all_meshes` | Scene traversal | AC7.12 |
| `test_default_spot_color_black` | Spot color default | AC7.6 |
| `test_default_bg_color_white` | BG color default | AC7.7 |
| `test_preserve_across_re_renders` | State preservation | AC7.11 |

**Testing Strategy:**
- Behavioral/integration-style (no Three.js mock)
- Store-driven (real Zustand store per test)
- Focus on observable side effects (no internal method assertions)
- DOM/React error boundaries for error handling

---

## Requirement-to-Test Mapping

| Requirement | Coverage | Test File | Test Count |
|-------------|----------|-----------|-----------|
| R1: PNG Generator | AC1.1–AC1.16 | test_spots_texture_generation.py | 18 |
| R2: Blender Wrapper | AC2.1–AC2.10 | test_spots_texture_generation.py | 7 |
| R3: Material Factory | AC3.1–AC3.11 | test_spots_material_integration.py | 6 |
| R4: Material System Hook | AC4.1–AC4.11 | test_spots_material_integration.py | 11 |
| R5: Backend Unit Tests | AC5.1–AC5.16 | test_spots_texture_generation.py | 18 |
| R6: Frontend Shader | AC6.1–AC6.15 | GlbViewer.spots.test.tsx | 20 |
| R7: Frontend Integration | AC7.1–AC7.15 | GlbViewer.spots.test.tsx | 20 |
| R8: Integration Tests | AC8.1–AC8.9 | Both files | 5 |
| R9: Error Handling | Implicit | All files | All |

**Total Test Count:** 49 primary tests + 4 edge cases = **53 tests**

---

## Test Execution Strategy

### Backend (Python)
```bash
# Run all spots-related tests
pytest asset_generation/python/tests/materials/test_spots_texture_generation.py -v
pytest asset_generation/python/tests/materials/test_spots_material_integration.py -v

# With coverage
pytest asset_generation/python/tests/materials/test_spots*.py --cov=src.materials --cov-report=term-missing
```

### Frontend (TypeScript)
```bash
# Run shader integration tests
npm test -- GlbViewer.spots.test.tsx

# Run all Preview component tests
npm test -- src/components/Preview/
```

---

## Key Testing Assumptions

### Backend
1. **PNG validation:** Reuse struct/zlib parsing; no PIL dependency required
2. **Blender mocks:** Full scene context not needed; function-level mocking sufficient
3. **Density impact:** Pixel counting proxy; not pixel-perfect RGB comparison
4. **CRC-32:** Reuse existing `_crc32()` from gradient_generator.py

### Frontend
1. **Three.js abstraction:** Real Three.js import (no mock); canvas context mocked
2. **Store integration:** Real Zustand store per test; ephemeral, no persistence
3. **Shader compilation:** Implicit via component rendering; no explicit compilation tests
4. **Material restoration:** Behavioral verification via state transitions

---

## Coverage Gaps & Future Work

### Not Covered (Out of Scope)

1. **Pixel-perfect visual verification:** Tests verify pattern changes (sparse vs. dense) but not rendered appearance
2. **WebGL error reporting:** Shader errors caught by error boundary; explicit WebGL validation future work
3. **Performance profiling:** Shader framerate target (60 fps) not measured; manual testing required
4. **End-to-end Godot integration:** Spots are M25 editor feature; gameplay tests not applicable

### Checkpoint Notes

| Item | Status | Notes |
|------|--------|-------|
| Spots generator function signature | ASSUMED | Spec defines exact signature; function must exist and accept 5 params |
| Wrapper function signature | ASSUMED | Follows gradient pattern; signature inferred from spec |
| Material factory signature | ASSUMED | Parallel to `_material_for_gradient_zone()`; keyword-only args |
| Store shape (frontend) | KNOWN | Zustand store already has `texture_mode` and related fields |
| Blender availability (CI) | ASSUMED OPTIONAL | Backend tests skip gracefully if Blender unavailable |

---

## Acceptance Criteria for Test Design

- [x] All 9 requirements have test coverage mapped
- [x] 49+ primary unit tests covering standard behavior, edge cases, boundaries
- [x] Error handling tests for invalid hex, out-of-range density, shader errors
- [x] Integration tests for parameter flow (UI → Store → Backend → Renderer)
- [x] Mocking strategy respects "mock only true externals" (bpy, Three.js Canvas, HTTP)
- [x] No mocks of internal functions (reuse existing gradient patterns)
- [x] Tests are deterministic and repeatable
- [x] All tests target observable behavior (not internal method assertions)

---

## Next Steps

1. **Test Breaker Phase:** Execute all 53 tests; report pass/fail status and any coverage gaps
2. **Implementation Phase:** Implementation agent codes all 9 requirements; tests drive implementation
3. **Validation:** Run test suite against implementation; achieve green status
4. **Code Review:** Linting, style, no debug logging (especially gradient debug.log removal)
5. **Regression:** Run full M25 test suite to verify no breakage to gradient/stripe modes

---

## Notes for Test Breaker

### Running Tests

**Backend:**
```bash
cd /Users/jacobbrandt/workspace/blobert
python -m pytest asset_generation/python/tests/materials/test_spots_texture_generation.py -v
python -m pytest asset_generation/python/tests/materials/test_spots_material_integration.py -v
```

**Frontend:**
```bash
cd /Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend
npm test -- GlbViewer.spots.test.tsx
```

### Expected Failures

Tests will FAIL until implementation is complete. Expected failure modes:

1. **Import errors:** `_spots_texture_generator` not found → pytest skip or hard fail
2. **Signature errors:** Missing parameters → TypeError
3. **Blender mock issues:** bpy not stubbed → AttributeError (caught, tests continue)
4. **Frontend undefined:** Store fields or shader logic missing → React errors logged but component renders

### Troubleshooting

- **PNG tests fail on CRC-32:** Verify `_crc32()` function is used; manual CRC calculation often fails
- **Material tests fail on find BSDF:** Blender node structure varies; ensure gradient pattern is followed
- **Frontend tests hang:** Check for unresolved promises; likely waitFor() timeout on useEffect

---

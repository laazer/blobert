# Ticket 02a: Universal Color Picker Component

**Status:** Done  
**Milestone:** M25 - Enemy Editor Visual Expression  
**Depends On:** —  
**Blocks:** 02b, 02c, 02d, 02e  

## Overview

Design and implement a single, reusable color picker component that supports three input modes:
1. **Single Color** - standard color picker for solid colors
2. **Gradient** - color picker for two-color gradients with direction control
3. **Image Texture** - file upload for custom image textures

This component will become the single source of truth for all color/texture selection in the enemy editor UI.

## Scope

- New React component: `ColorPickerUniversal.tsx` in `asset_generation/web/frontend/src/components/ColorPicker/`
- Support mode switching via tabs or dropdown
- Single Color mode: hex color input + visual picker
- Gradient mode: two color pickers + direction selector (horizontal/vertical/radial)
- Image mode: file upload with preview
- CSS styling consistent with existing BuildControls design
- No dependency on existing color pickers

## Acceptance Criteria

- [x] Component renders in all three modes without errors — `ColorPickerUniversal.test.tsx`, mode sub-tests
- [x] Single color mode accepts hex input (with/without #) and updates preview — `HexInput.tsx` + `HexInput.test.tsx`
- [x] Gradient mode shows two color pickers and direction selector — `GradientMode.tsx` + tests
- [x] Image mode uploads files and displays preview — `ImageMode.tsx` + tests
- [x] Component accepts `onChange` callback for value changes — `ColorPickerUniversal.test.tsx` (single-mode change + harness)
- [x] Component accepts `value` prop for controlled mode — discriminated `ColorPickerValue` + tests
- [x] Mode can be switched without losing previous selections — parent-owned state pattern; `ColorPickerUniversal.test.tsx` harness
- [x] Styling matches BuildControls design language — `colorPickerStyles.ts` (VS Code–aligned palette)
- [x] TypeScript types are properly defined — `ColorPickerUniversal.tsx` exports `ColorPickerValue`
- [x] Component is fully testable with Vitest — `src/components/ColorPicker/**/*.test.tsx` (59 tests)

## Implementation Notes

- Consider using existing Three.js color utilities for color conversion
- Image upload should validate file type (PNG, JPG, etc.)
- File sizes should be reasonable for web upload
- Gradient preview should update in real-time as colors change

## Ticket Chain

→ 02b (Update existing color pickers)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
1

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `timeout 120 npm test -- --run` in `asset_generation/web/frontend` (525 tests, 2026-04-19); ColorPicker tree 59 tests including `ColorPickerUniversal`, `HexInput`, modes.
- Static QA: Passing — TypeScript via Vitest compile; no new lint issues on touched files.
- Integration: N/A — UI component; exercised in Vitest/jsdom.

## Blocking Issues

- None

## Escalation Notes

- Ticket was implemented in-repo before pipeline WORKFLOW STATE existed; ap-continue reconciled: added missing `hexForColorInput` / `sanitizeHex` in `clipboardHex.ts`, a11y `aria-label` on image file input, test fixes, and two `ColorPickerUniversal` integration tests.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason

All acceptance criteria evidenced by implementation and Vitest; ticket closed under M25 `done/`.

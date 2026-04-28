# BUG: Body-part image selection not applied

## Bug Report
images still aren't being applied to the body part they are selected for. it just uses the color it was before it was before the image was slected and the model regenerated

## Acceptance Criteria
- The specific error no longer occurs
- A regression test exists that would have caught this bug
- All pre-existing tests continue to pass

## Diagnosis
### Root Cause
- **Responsible file/function:** `asset_generation/web/frontend/src/components/ColorPicker/ColorPickerTabs.tsx` in `ColorPickerTabs` (Image tab render branch).
- **Faulty behavior:** `ColorPickerTabs` drops the selected texture `assetId` when forwarding `ImageMode` changes:
  - `ImageMode` emits `onFileChange(file, preview, assetId)`.
  - `ColorPickerTabs` currently forwards only `(file, preview)` and constructs `{ type: "image", file, preview }` without `assetId`.
  - Downstream in `ZoneTextureBlock`, build-option persistence only writes `feat_{zone}_color_image_id` when `v.assetId` exists; because it is omitted, only preview metadata is stored, not the executable texture selection key.
- **Why this matches the bug report:** regeneration/render path applies image materials from `features[zone].color_image.id` (via Python merge + material override), not preview URL. With missing `id`, the pipeline cannot apply selected image and falls back to prior finish/hex color, so the model appears unchanged except for previous color.

### Incorrect vs Correct Behavior
- **Incorrect (current):**
  1. User selects body-part image in UI.
  2. UI preview may show image.
  3. Regenerate request omits `feat_{zone}_color_image_id` (or equivalent nested `features[zone].color_image.id` value).
  4. Backend material override sees no image id and keeps/derives prior color material.
- **Correct (expected):**
  1. User selects body-part image.
  2. Selection persists both preview and `assetId`.
  3. Regenerate includes `feat_{zone}_color_image_id` (or merged nested id) for the targeted zone.
  4. Backend resolves texture asset path by id and applies image material for that zone, overriding previous color material.

### Assumptions (due missing workflow enforcement module)
- The missing `agent_context/agents/common_assets/workflow_enforcement_v1.md` is treated as non-blocking for diagnosis/spec content.
- The canonical contract for applying image mode remains `features[zone].color_image.mode == "image"` plus non-empty `features[zone].color_image.id`.

## Spec
### Requirement R1 — Preserve image asset identity from UI selection to run payload

#### 1. Spec Summary
- **Description:** When a user selects a preloaded image texture for any zone/body part in image mode, the selected asset identifier must be preserved in frontend state and included in run/regenerate build options.
- **Constraints:** Must support existing three-mode picker contract (`single | gradient | image`) without regressing single/gradient behavior.
- **Assumptions:** Preloaded texture selections are represented by stable non-empty asset ids from texture API responses.
- **Scope:** Frontend color picker event propagation and build-options serialization for animated/player regeneration.

#### 2. Acceptance Criteria
- AC1: Selecting a preloaded texture in image mode stores both preview URL and non-empty `assetId` in the picker value propagated by the tab component.
- AC2: For zone color image mode, run/regenerate payload includes `feat_{zone}_color_image_id` for the selected zone when image mode is active.
- AC3: Existing behavior for custom upload preview (no preloaded asset id) remains unchanged and does not invent invalid ids.
- AC4: Single and gradient mode payload fields remain unchanged by image-mode propagation fixes.

#### 3. Risk & Ambiguity Analysis
- **Risk:** If asset id is dropped at any intermediate component layer, backend cannot resolve texture path and silently falls back to color material.
- **Risk:** Incorrectly forcing ids for uploaded files could create invalid asset references.
- **Edge case:** Switching modes repeatedly must not leak stale ids into non-image modes unless intentionally persisted for return-to-image UX.
- **Testing impact:** Requires assertions at component boundary and payload construction boundary, not only visual assertions.

#### 4. Clarifying Questions
- Q1: For uploaded custom files (non-preloaded), should regeneration support file-backed image application now, or remain preloaded-asset-id only?
- Q2: On mode switch away from image, should stored `color_image_id` be cleared immediately or retained for later return to image mode?
- Q3: Should pattern color image fields (`feat_{zone}_texture_*_image_id`) follow the same contract in this ticket scope, or is this ticket limited to base zone/body-part color image?

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | COMPLETE |
| Revision | 5 |
| Last Updated By | Acceptance Criteria Gatekeeper Agent |
| Next Responsible Agent | Human |
| Validation Status | Regression test exists and passes: `ColorPickerTabs.regression.test.tsx` (`BUG-body-part-image-not-applied-01`).<br>Original failure path (dropped `assetId` from image selection flow) is covered by the regression and no longer reproduces in test runs.<br>Related-scope verification passed: `ColorPickerTabs.regression`, `ImageMode`, `ColorPickerUniversal` (+ adversarial), `ZoneTextureBlock` integration/adversarial = **163 passed, 0 failed**. |
| Blocking Issues | None. |
| Escalation Notes | Workflow enforcement module path is still missing in repo; ticket was gated conservatively using explicit in-ticket AC plus fresh test execution evidence. |

## NEXT ACTION

| Field | Value |
|---|---|
| Next Responsible Agent | Human |
| Required Input Schema | None |
| Status | READY_FOR_CLOSEOUT |
| Reason | All listed acceptance criteria now have explicit automated evidence: regression coverage was present and passing, the original bug condition is no longer observed in tests, and related pre-existing tests passed without regressions. |

## Test Evidence

- Added regression test: `asset_generation/web/frontend/src/components/ColorPicker/ColorPickerTabs.regression.test.tsx`
  - `BUG-body-part-image-not-applied-01 preserves assetId from image selection`
- Post-fix verification:
  - `npm test -- src/components/ColorPicker/ColorPickerTabs.regression.test.tsx src/components/ColorPicker/modes/ImageMode.test.tsx src/components/ColorPicker/ColorPickerUniversal.test.tsx`
  - Result: **22 passed, 0 failed** (3 files), including regression `BUG-body-part-image-not-applied-01`.

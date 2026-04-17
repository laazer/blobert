# M25-03 Test Design Run — 2026-04-16T18-00-00Z

## Context

Test Designer Agent authoring `BuildControls.textureUpload.test.tsx` for ticket M25-03.
Spec: `project_board/specs/texture_upload_support_spec.md` (TUS-1..TUS-9).

---

### [M25-03] TEST_DESIGN — store slice seeding for customTextureUrl
**Would have asked:** Should the test seed `customTextureUrl` in the store via `useAppStore.setState(...)`, or is the field absent from the current store interface (not yet implemented)?
**Assumption made:** `customTextureUrl` and `setCustomTextureUrl` are not yet in the store (Task 2 is pending implementation). Tests seed them via `useAppStore.setState({ customTextureUrl: ... })` which Zustand accepts even for fields not declared in TypeScript at test-write time (the store is in-memory; setState merges). Tests will be RED until Task 2 adds the slice to the TypeScript interface and store body.
**Confidence:** High

### [M25-03] TEST_DESIGN — setAnimatedBuildOption side-effect verification for Remove
**Would have asked:** Should tests assert the store's `animatedBuildOptionValues` after clicking Remove, or spy on `setAnimatedBuildOption`?
**Assumption made:** Tests verify observable store state: after Remove click, `useAppStore.getState().animatedBuildOptionValues[slug]["texture_mode"]` equals `"none"`. This is a behavioral assertion over the actual store rather than an interaction spy on an internal action. The store setup must seed the slug's values correctly so the action has an effect.
**Confidence:** High

### [M25-03] TEST_DESIGN — GlbViewer TextureLoader tests excluded
**Would have asked:** Should TUS-6 GlbViewer coverage be included in this test file?
**Assumption made:** Per explicit instruction in the task prompt, GlbViewer Three.js TextureLoader behavior is excluded from this test file. Only `BuildControls.tsx` behavioral coverage is in scope.
**Confidence:** High

### [M25-03] TEST_DESIGN — "custom" option injection mechanism unknown at test-write time
**Would have asked:** Does `BuildControls` inject "custom" by augmenting `def.options` before rendering, or via a special-case branch?
**Assumption made:** Tests do not test the injection mechanism; they test the observable DOM outcome: an `<option value="custom">` element is present in the texture mode select. The test seeds `TEXTURE_MODE_DEF` with only the Python-side 4 options; the implementation is expected to inject "custom" in the render path. This is the strictest defensible test per TUS-1.
**Confidence:** High

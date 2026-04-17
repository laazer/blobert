Title:
Texture Upload Support (Custom Image)

Description:
Extend the texture system from ticket 02 to allow users to upload a PNG or JPG image and apply it as the enemy's surface texture. Targets use cases like lava, grass, stone, or hand-painted artwork. All file handling is client-side only (blob URL or base64) — no server storage.

Acceptance Criteria:
- A "Custom" option is available in the texture mode selector (alongside None/Gradient/Spots/Stripes)
- Selecting "Custom" reveals an "Upload Texture" file input button
- Accepted file types: PNG and JPG; other types are rejected with an inline error before upload
- File size limit of 2 MB is enforced client-side; oversized files show an error and are not applied
- After a valid upload the texture appears on the enemy in the 3D preview within 2 seconds
- The uploaded texture is referenced in the enemy config as a base64 data URL or blob reference
- A "Remove" button clears the uploaded texture and reverts to "None" mode

Scope Notes:
- No server-side file storage or persistence across sessions
- No texture tiling, offset, or UV controls in this ticket
- Texture is applied uniformly to the whole body (not per-part)
- No image editing or cropping UI

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- No new Python control defs required; the uploaded texture is a client-side-only material override and does not feed into Blender generation in this ticket
- Document in `_texture_control_defs()` (added by ticket 02) that `texture_mode: custom` is reserved for client-side upload and is not a valid Blender build option

**Frontend (`asset_generation/web/frontend/src/`)**
- `BuildControls.tsx`: when `texture_mode` is `custom`, render a file input (`<input type="file" accept=".png,.jpg,.jpeg">`) and a "Remove" button beneath the mode selector — this is a local React state concern, not a `ControlRow`-driven control
- File validation (type and 2 MB size limit) runs in the `onChange` handler before setting state; validation errors appear inline next to the file input
- On valid upload: create an object URL (`URL.createObjectURL`) and store it in local component state (not in Zustand); pass the URL to `GlbViewer` as a prop or via a dedicated store slice
- `GlbViewer.tsx`: when a texture URL is provided, load it with Three.js `TextureLoader` and apply as `.map` on all `MeshStandardMaterial` instances on the loaded GLB's mesh children; clean up the object URL via `URL.revokeObjectURL` when the texture is removed or the component unmounts
- "Remove" clears the object URL, reverts materials, and resets `texture_mode` to `none`

**Tests**
- Frontend (Vitest): `BuildControls.textureUpload.test.tsx` — file input renders when mode is `custom`; a 3 MB PNG file triggers an error and does not call the texture apply path; a valid PNG produces an object URL and calls the GlbViewer texture prop; "Remove" clears the URL

## Execution Plan

### Task 1 — Python: Add `"custom"` reservation comment in `_texture_control_defs()`
**Agent:** Generalist Implementation Agent
**File:** `asset_generation/python/src/utils/animated_build_options_appendage_defs.py`
**Input:** Existing `_texture_control_defs()` function and `_TEXTURE_MODE_OPTIONS` constant
**Work:** Add an inline comment immediately after `_TEXTURE_MODE_OPTIONS` (or inside the function body) explaining that `"custom"` is intentionally omitted from the options tuple because it is a client-side-only upload mode and is not a valid Blender build target. No functional code change.
**Output:** One comment line added; all existing Python tests still pass (`bash .lefthook/scripts/py-tests.sh`)
**Dependencies:** None
**Success Criteria:** `_TEXTURE_MODE_OPTIONS` remains unchanged; comment is present and accurate; diff-cover preflight passes (no Python logic changed, so no new test coverage required)

### Task 2 — Frontend: Add `customTextureUrl` Zustand store slice to `useAppStore`
**Agent:** Generalist Implementation Agent
**File:** `asset_generation/web/frontend/src/store/useAppStore.ts`
**Input:** Current `AppState` interface and store body
**Work:**
- Add `customTextureUrl: string | null` field to `AppState`
- Add `setCustomTextureUrl: (url: string | null) => void` action
- Initialize `customTextureUrl` to `null` in the store
**Output:** Store compiles; existing Vitest tests still pass; `customTextureUrl` is readable by any component subscribed to the store
**Dependencies:** None
**Success Criteria:** `cd asset_generation/web/frontend && npm test` passes with no regressions; TypeScript compiler emits no new errors

### Task 3 — Frontend: `BuildControls.tsx` — "Custom" mode UI, file validation, blob URL lifecycle
**Agent:** Generalist Implementation Agent
**File:** `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx`
**Input:** Task 2 (store slice must exist); existing `buildControlDisabled()` and `nonFloat.map()` render block; existing style constants `s.select`, `s.label`
**Work:**
1. Extend `buildControlDisabled()`: when `defKey === "texture_mode"` return `false` (already true); ensure no texture sub-controls are gated on `"custom"` mode (they remain disabled when mode is `"custom"` since no prefix matches).
2. Add `"custom"` to the recognized modes in the local mode normalization guard inside `BuildControls` (so it is not clamped to `"none"` by the existing guard in `GlbViewer`'s `useEffect`; the guard in `BuildControls` itself does not need to change — the select option value drives the store).
3. Add local state: `const [uploadError, setUploadError] = useState<string | null>(null)` (no file handle stored in state — only the error string is local; the derived object URL is pushed to the store via `setCustomTextureUrl`).
4. In the `nonFloat.map()` render block, after the `texture_mode` ControlRow renders, insert a conditional block: when `values.texture_mode === "custom"`, render:
   - `<input type="file" accept=".png,.jpg,.jpeg" aria-label="Upload texture" onChange={handleTextureUpload} />`
   - If `uploadError`: an inline `<span>` in error color showing the message
   - If `customTextureUrl` from store is non-null: a `<button>Remove</button>` that calls `handleRemoveTexture`
5. `handleTextureUpload(e)`: validate `file.type` is `image/png` or `image/jpeg`; validate `file.size <= 2 * 1024 * 1024`; on failure set `uploadError` and return; on success call `URL.revokeObjectURL` on the previous store URL if non-null, then call `URL.createObjectURL(file)`, call `setCustomTextureUrl(newUrl)`, clear `uploadError`.
6. `handleRemoveTexture()`: call `URL.revokeObjectURL(customTextureUrl)`, call `setCustomTextureUrl(null)`, call `setAnimatedBuildOption(slug, "texture_mode", "none")`.
7. Add cleanup `useEffect(() => { return () => { if (customTextureUrl) URL.revokeObjectURL(customTextureUrl); }; }, [customTextureUrl])` — note: this fires on unmount or URL change, but since BuildControls is long-lived, the critical path is the Remove and upload-new-file paths above.

**Output:** File compiles; "Custom" appears as an option in the texture mode selector; file input is shown/hidden correctly; validation errors appear inline; blob URL is pushed to the store on valid upload; Remove clears URL and resets mode to "none"
**Dependencies:** Task 2
**Success Criteria:** `npm test` passes; `BuildControls.textureUpload.test.tsx` tests for file input visibility, 3 MB rejection, valid PNG object URL, and Remove behavior all pass

### Task 4 — Frontend: `GlbViewer.tsx` — TextureLoader overlay for custom texture URL
**Agent:** Generalist Implementation Agent
**File:** `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx`
**Input:** Task 2 (store slice); existing `Model` component `useEffect` for shader texture overlay; existing `originalMaterialsRef` and `appliedMaterialRef` pattern
**Work:**
1. In the `Model` component, add a second `useRef` for the loaded custom `THREE.Texture`: `const customTextureRef = useRef<THREE.Texture | null>(null)`.
2. Subscribe to `customTextureUrl` from `useAppStore`.
3. Add a new `useEffect` dependent on `[customTextureUrl, scene, url]`:
   - If `customTextureUrl` is non-null:
     - Capture original materials if not yet captured (same guard as the existing shader overlay effect).
     - Dispose the previous `customTextureRef.current` if present.
     - Use `new THREE.TextureLoader().load(customTextureUrl, (tex) => { ... })` callback: store texture in `customTextureRef`, apply it as `.map` on all `MeshStandardMaterial` instances in the scene (traverse, check `instanceof THREE.MeshStandardMaterial`, set `material.map = tex; material.needsUpdate = true`).
   - If `customTextureUrl` is null:
     - Dispose `customTextureRef.current` if present; set to null.
     - Restore original materials (same restore path as existing `mode === "none"` branch).
4. Extend the existing shader `useEffect` cleanup for `mode === "none"` to also dispose `customTextureRef.current` and restore materials when mode is `none` (avoiding double-restore conflicts: check if a custom texture is applied and clear it).
5. On `url` change (new model loaded), dispose `customTextureRef.current` and clear the ref alongside the existing `originalMaterialsRef.clear()` block.
6. Add a cleanup return in the custom texture `useEffect` that disposes the texture on unmount.

**Output:** When a valid image URL is in the store, all `MeshStandardMaterial` meshes in the loaded GLB display the uploaded texture; when cleared, original materials are restored; no texture memory leaks on model swap or unmount
**Dependencies:** Task 2, Task 3
**Success Criteria:** Manual smoke test: upload a PNG → texture appears on enemy in viewer within 2 seconds; Remove → original materials restored. `npm test` passes with no regressions on `GlbViewer.test.tsx` and `GlbViewer.loadError.test.tsx`.

### Task 5 — Frontend: Author `BuildControls.textureUpload.test.tsx`
**Agent:** Test Designer Agent
**File:** `asset_generation/web/frontend/src/components/Preview/BuildControls.textureUpload.test.tsx`
**Input:** Tasks 3 and 4 spec (implementations must exist first); existing test patterns in `BuildControls.texture.test.tsx`, `BuildControls.mouthTail.test.tsx`; Vitest + Testing Library + jsdom environment (`@vitest-environment jsdom`)
**Work:** Write tests covering all AC items:
- AC-1: "Custom" option renders in the `texture_mode` select when controls include it (add `"custom"` to the options list in the test-local control def)
- AC-2: File input (`aria-label="Upload texture"`) is present in DOM when `texture_mode` is `"custom"` and absent when `texture_mode` is `"none"`
- AC-3: Uploading a file with `type: "application/pdf"` or `type: "image/gif"` sets an inline error and does not call `setCustomTextureUrl`
- AC-4: Uploading a 3 MB PNG (size `3 * 1024 * 1024 + 1`) sets an inline error (size limit) and does not call `setCustomTextureUrl`
- AC-5: Uploading a valid 1 MB PNG (`type: "image/png"`, size within limit) calls `URL.createObjectURL` and calls `setCustomTextureUrl` with the resulting URL (mock `URL.createObjectURL` to return a deterministic string)
- AC-6: "Remove" button is present when `customTextureUrl` is non-null in the store; clicking it calls `URL.revokeObjectURL`, calls `setCustomTextureUrl(null)`, and resets `texture_mode` to `"none"` in the store
- AC-7: Uploading a valid JPEG (`type: "image/jpeg"`) is accepted (no error set)
- AC-8: After a rejected file, the error message is visible in the DOM

Use `vi.spyOn(URL, 'createObjectURL')` and `vi.spyOn(URL, 'revokeObjectURL')` for isolation. Seed store with `customTextureUrl: null` initially.
**Output:** `BuildControls.textureUpload.test.tsx` with 8+ test cases; all tests GREEN after Tasks 3–4 are implemented
**Dependencies:** Tasks 3 and 4 (test file is written against the implemented API)
**Success Criteria:** `cd asset_generation/web/frontend && npm test -- BuildControls.textureUpload` exits 0 with all cases passing

### Task 6 — Static QA + AC gate
**Agent:** AC Gatekeeper Agent
**Input:** All prior tasks complete
**Work:**
1. Run `cd asset_generation/web/frontend && npm test` — confirm all Vitest tests pass including `BuildControls.textureUpload.test.tsx`
2. Run `bash .lefthook/scripts/py-tests.sh` — confirm Python tests still pass (Task 1 is comment-only, should be a no-op)
3. Verify TypeScript compiles without errors: `cd asset_generation/web/frontend && npm run build`
4. Confirm `buildControlDisabled()` in `BuildControls.tsx` does not break existing `BuildControls.texture.test.tsx` tests (the `"custom"` mode value should fall through to the default `"none"` branch in the guard, keeping all mode-specific sub-controls disabled)
5. Confirm "custom" appears as an option in the selector on the running dev server (manual smoke or DOM assertion)
6. Advance ticket Stage to COMPLETE and move file to `done/`

**Output:** All tests passing; TypeScript clean; ticket closed
**Dependencies:** Tasks 1–5
**Success Criteria:** `npm test` exits 0; `npm run build` exits 0; `py-tests.sh` exits 0; ticket moved to `done/`

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | TEST_BREAK |
| Revision | 4 |
| Last Updated By | Test Designer Agent |
| Next Responsible Agent | Test Breaker Agent |
| Status | Proceed |
| Validation Status | — |
| Blocking Issues | — |

## NEXT ACTION

Test Breaker Agent: review `asset_generation/web/frontend/src/components/Preview/BuildControls.textureUpload.test.tsx` and adversarially extend it. Target gaps such as: double-upload race conditions, `image/jpg` (non-standard MIME) rejection, null-files vs zero-length-files distinction, Remove button `type="button"` attribute, store state after Remove does not contain stale blob URL, and reactive mode switch (custom → none → custom) correctly shows/hides file input without remount.

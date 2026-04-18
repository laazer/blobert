# Texture Upload Support Spec (M25-03)

**Ticket:** `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/03_texture_upload_support.md`
**Spec version:** 1
**Author:** Spec Agent
**Date:** 2026-04-16

---

## Scope and Boundaries

This spec covers:

- Addition of `"custom"` as a recognized value in the `texture_mode` selector in `BuildControls.tsx`
- File input UI: render conditions, accepted MIME types, `accept` attribute, `aria-label`, error message format
- File validation rules: MIME type whitelist, exact 2 MB byte threshold, error message strings per rejection case
- Blob URL lifecycle: who creates, who revokes, when — and the distinct Three.js `Texture` disposal responsibility in `GlbViewer`
- Zustand store slice: `customTextureUrl: string | null` field and `setCustomTextureUrl` action in `useAppStore.ts`
- `GlbViewer.tsx` `Model` component: `TextureLoader.load()` callback, material filter (`MeshStandardMaterial` only), `material.needsUpdate = true`, ref lifecycle for custom texture on model URL change and unmount, restore path when URL is null
- Remove button: render conditions, click behavior (revoke blob URL, null the store, reset `texture_mode` to `"none"`)
- Python comment: exact content and placement in `_texture_control_defs()` noting `"custom"` is client-side only
- `buildControlDisabled()` behavior under `"custom"` mode (all texture sub-controls remain disabled)
- Non-breaking guarantee: all existing M25-02 shader overlay tests and behaviors preserved

Out of scope (per ticket):

- Server-side file storage or persistence across sessions
- Texture tiling, UV offset, or UV scale controls
- Per-part texture assignment (uniform whole-body application only)
- Image editing, cropping, or preview thumbnail UI
- Base64 data URL encoding (blob URL / `URL.createObjectURL` is the storage mechanism)
- Blender-side material embedding (Python pipeline is not affected by this feature)

---

## Constant Inventory

| Symbol | Location | Value |
|---|---|---|
| File size limit (bytes) | `BuildControls.tsx` inline constant or named constant | `2 * 1024 * 1024` = `2097152` |
| Accepted MIME types | `BuildControls.tsx` onChange handler | `["image/png", "image/jpeg"]` |
| `accept` attribute value | `<input type="file">` element | `".png,.jpg,.jpeg"` |
| `aria-label` value | `<input type="file">` element | `"Upload texture"` |
| Mode reset target on Remove | `setAnimatedBuildOption` call | `"none"` |

No unexplained inline literals are permitted in the implementation for file size, MIME types, or the mode reset target.

---

## Requirement TUS-1: "Custom" Option in the Texture Mode Selector

### 1. Spec Summary

- **Description:** The `texture_mode` select element rendered by the `ControlRow` for the `texture_mode` key must include `"custom"` as an option in addition to the four Python-defined options (`"none"`, `"gradient"`, `"spots"`, `"stripes"`). The `"custom"` option value and label are `"custom"`. Its position in the option list is last (after `"stripes"`).
- **Constraints:** The option is added exclusively on the frontend. The Python `_TEXTURE_MODE_OPTIONS` tuple in `animated_build_options_appendage_defs.py` is NOT modified. The `ControlRow` component renders options from the control def's `options` array; the implementer must inject `"custom"` into the rendered option list without altering the Python-emitted def. The mechanism (e.g., a post-processing step on the control def before rendering, or a special-case branch in the `nonFloat.map()` block) is left to the implementer, but must not alter the underlying def object received from the store.
- **Assumptions:** `ControlRow` receives `options` as an array in the control def and renders one `<option>` per entry. The injection of `"custom"` happens in `BuildControls.tsx`, not inside `ControlRow`.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx`.

### 2. Acceptance Criteria

**TUS-1-AC-1:** When `BuildControls` renders the `texture_mode` control row and the control def for `texture_mode` is present, the rendered `<select>` element contains exactly five `<option>` elements with values `"none"`, `"gradient"`, `"spots"`, `"stripes"`, `"custom"` in that order.

**TUS-1-AC-2:** The `"custom"` option has display text `"custom"` (case-insensitive match acceptable; exact casing `"custom"` preferred).

**TUS-1-AC-3:** The Python-side `_TEXTURE_MODE_OPTIONS` tuple remains `("none", "gradient", "spots", "stripes")` — exactly four entries, unchanged by this ticket.

**TUS-1-AC-4:** Selecting `"custom"` in the selector calls `setAnimatedBuildOption(slug, "texture_mode", "custom")` and persists `"custom"` as the stored `texture_mode` value for that slug.

### 3. Risk and Ambiguity Analysis

- The `ControlRow` component is the actual renderer of `<option>` elements. If `ControlRow` renders options strictly from `def.options`, injection must occur before the def reaches `ControlRow` (e.g., spreading the def with an extended options array). The implementer must not mutate the def object from the store.
- Risk: If the Python API is updated to include `"custom"` in `_TEXTURE_MODE_OPTIONS` in a future ticket, the frontend injection will produce a duplicate. The Python comment (TUS-8) documents this boundary explicitly.

### 4. Clarifying Questions

None. The ticket is explicit that `"custom"` is client-side only and must not appear in Python.

---

## Requirement TUS-2: File Input UI (Render Conditions, Attributes, Styling)

### 1. Spec Summary

- **Description:** When `texture_mode` for the current slug equals `"custom"`, `BuildControls` renders an `<input type="file">` element beneath the texture mode `ControlRow`. The file input is not rendered under any other `texture_mode` value.
- **Constraints:**
  - `accept` attribute: `".png,.jpg,.jpeg"` (comma-separated file extensions, no spaces).
  - `aria-label` attribute: `"Upload texture"` (exact string).
  - `type` attribute: `"file"`.
  - The input is rendered inside the `nonFloat.map()` conditional block after the `texture_mode` ControlRow, not as a `ControlRow`-driven control (i.e., it does not appear in the `defs` array and is not rendered by a `ControlRow` component).
  - Styling: must use existing style tokens from the `s` object (`s.select` or `s.input` is acceptable); or a raw style consistent with the dark-theme editor palette (`background: "#3c3c3c"`, `color: "#d4d4d4"`, `border: "1px solid #555"`). Implementer may add `cursor: "pointer"` for usability.
  - The file input does not store a file reference in React state; it is uncontrolled (no `value` prop is set on it).
- **Assumptions:** `values.texture_mode` is the string stored in `animatedBuildOptionValues[slug]["texture_mode"]`. The condition is a strict equality check: `values.texture_mode === "custom"`.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx`.

### 2. Acceptance Criteria

**TUS-2-AC-1:** When `texture_mode` is `"custom"`, an `<input>` element with `type="file"`, `accept=".png,.jpg,.jpeg"`, and `aria-label="Upload texture"` is present in the DOM.

**TUS-2-AC-2:** When `texture_mode` is `"none"`, `"gradient"`, `"spots"`, or `"stripes"`, no element with `aria-label="Upload texture"` is present in the DOM.

**TUS-2-AC-3:** The file input element renders as a sibling of (not a child of) the `texture_mode` ControlRow's wrapper div, immediately below it in document order.

**TUS-2-AC-4:** No `value` prop is bound to the file input (it is uncontrolled).

### 3. Risk and Ambiguity Analysis

- The `accept` attribute controls the browser's file picker filter but does not prevent programmatic file injection in tests. MIME type validation in `onChange` (TUS-3) is the enforcement boundary.
- The file input's visual appearance varies across browsers; no cross-browser visual consistency is required by this ticket.

### 4. Clarifying Questions

None.

---

## Requirement TUS-3: File Validation Rules

### 1. Spec Summary

- **Description:** The `onChange` handler (`handleTextureUpload`) attached to the file input validates each selected file before creating a blob URL. Two validation rules apply: MIME type whitelist and file size ceiling. Both are enforced client-side in the handler body before any call to `URL.createObjectURL`. Validation errors are displayed inline (see TUS-3-AC-5).
- **Constraints:**
  - Accepted MIME types: `"image/png"` and `"image/jpeg"` only. Check is `file.type === "image/png" || file.type === "image/jpeg"`.
  - File size limit: `file.size <= 2 * 1024 * 1024` (i.e., `<= 2097152` bytes). A file of exactly `2097152` bytes is accepted. A file of `2097153` bytes is rejected.
  - Validation order: MIME type checked first; if MIME fails, size check is skipped and the MIME error message is set.
  - On any validation failure: call `setUploadError(<error message>)` and return immediately without calling `URL.createObjectURL` or `setCustomTextureUrl`.
  - On validation success: clear the error (`setUploadError(null)`), revoke any existing blob URL (see TUS-4), create a new blob URL, and store it.
  - No file reference is stored in component state.
- **Error message strings (exact):**
  - MIME type rejection: `"Only PNG and JPG files are accepted."`
  - Size rejection: `"File must be 2 MB or smaller."`
- **Assumptions:** `e.target.files[0]` is the file to validate. If `e.target.files` is null or empty, the handler returns without action and does not call `setUploadError`.
- **Scope:** `onChange` handler in `BuildControls.tsx`.

### 2. Acceptance Criteria

**TUS-3-AC-1:** A file with `type: "application/pdf"` triggers `setUploadError("Only PNG and JPG files are accepted.")` and does not call `URL.createObjectURL`.

**TUS-3-AC-2:** A file with `type: "image/gif"` triggers `setUploadError("Only PNG and JPG files are accepted.")` and does not call `URL.createObjectURL`.

**TUS-3-AC-3:** A file with `type: "image/png"` and `size: 2097153` (one byte over limit) triggers `setUploadError("File must be 2 MB or smaller.")` and does not call `URL.createObjectURL`.

**TUS-3-AC-4:** A file with `type: "image/png"` and `size: 2097152` (exactly at limit) is accepted: `setUploadError` is called with `null`, and `URL.createObjectURL` is called.

**TUS-3-AC-5:** A file with `type: "image/jpeg"` and `size: 1048576` (1 MB) is accepted: no error is set, `URL.createObjectURL` is called.

**TUS-3-AC-6:** After a rejected file, an inline `<span>` containing the error message string is visible in the DOM within the `BuildControls` render output.

**TUS-3-AC-7:** After a previously rejected file, uploading a valid file clears the error: the error `<span>` is no longer in the DOM.

**TUS-3-AC-8:** When `e.target.files` is null or length 0, the handler returns without calling `setUploadError`, `URL.createObjectURL`, or `setCustomTextureUrl`.

**TUS-3-AC-9:** MIME type check occurs before size check: a file with an invalid MIME type and size > 2 MB receives the MIME error message, not the size error message.

### 3. Risk and Ambiguity Analysis

- `file.type` is set by the browser from the file's declared MIME type, which can be spoofed by renaming extensions. No server-side validation is in scope; this is explicitly client-side only.
- `"image/jpg"` is not a valid MIME type (the correct type is `"image/jpeg"`); if a browser emits `"image/jpg"`, it will be rejected. This is correct behavior per the whitelist.
- The error `<span>` must appear inline near the file input, not as a toast or modal. Exact placement is left to the implementer as long as it is within the custom texture UI block.

### 4. Clarifying Questions

None.

---

## Requirement TUS-4: Blob URL Lifecycle

### 1. Spec Summary

- **Description:** `URL.createObjectURL` is called exclusively in `BuildControls.tsx`. `URL.revokeObjectURL` is called exclusively in `BuildControls.tsx`. `GlbViewer.tsx` does NOT call either; it only disposes the Three.js `Texture` object (see TUS-6).
- **Constraints:**
  - **Creation:** `URL.createObjectURL(file)` is called in `handleTextureUpload` after successful validation. The result is passed to `setCustomTextureUrl(newUrl)` (store action).
  - **Revocation — new upload:** Before calling `URL.createObjectURL` for a new file, if `customTextureUrl` in the store is non-null, call `URL.revokeObjectURL(customTextureUrl)` first. Then call `setCustomTextureUrl(newUrl)`.
  - **Revocation — Remove:** `handleRemoveTexture` calls `URL.revokeObjectURL(customTextureUrl)` before calling `setCustomTextureUrl(null)`.
  - **Revocation — unmount/URL change cleanup:** A `useEffect(() => { return () => { if (customTextureUrl) URL.revokeObjectURL(customTextureUrl); }; }, [customTextureUrl])` is added in `BuildControls`. This fires when `customTextureUrl` changes (cleanup of the previous value) and on unmount. Note: because the revocation on upload-new and Remove already revokes before changing the store, this `useEffect` cleanup serves primarily as a safety net for unmount or navigation away.
  - **GlbViewer's role:** `GlbViewer` reads `customTextureUrl` from the store and passes it to `THREE.TextureLoader.load(url, callback)`. It calls `texture.dispose()` on the loaded Three.js `Texture` object when the texture is replaced or cleared. It does NOT call `URL.revokeObjectURL`.
- **Assumptions:** `BuildControls` is long-lived in the app (it does not unmount on enemy/tab switches), so the primary revocation paths are the upload-new and Remove handlers. The `useEffect` cleanup is a safety net.
- **Scope:** `BuildControls.tsx` (blob URL creation and revocation); `GlbViewer.tsx` (Three.js Texture disposal only).

### 2. Acceptance Criteria

**TUS-4-AC-1:** When a user uploads a second valid image file while a previous blob URL is active, `URL.revokeObjectURL` is called with the previous URL before `URL.createObjectURL` is called for the new file.

**TUS-4-AC-2:** When the Remove button is clicked, `URL.revokeObjectURL` is called with the current `customTextureUrl` before `setCustomTextureUrl(null)` is dispatched.

**TUS-4-AC-3:** `GlbViewer.tsx` contains no call to `URL.createObjectURL` or `URL.revokeObjectURL`.

**TUS-4-AC-4:** The `useEffect` cleanup in `BuildControls` with `[customTextureUrl]` dependency calls `URL.revokeObjectURL` on the outgoing URL when `customTextureUrl` changes or the component unmounts.

**TUS-4-AC-5:** A `THREE.Texture` object previously loaded by `TextureLoader.load` has `.dispose()` called on it when a new texture URL is set or when `customTextureUrl` becomes null.

### 3. Risk and Ambiguity Analysis

- Double-revoke risk: If the `useEffect` cleanup fires at the same time as the explicit revocation in the handler, the same URL could be revoked twice. Calling `URL.revokeObjectURL` on an already-revoked URL is a no-op in browsers and does not throw; this is acceptable.
- The `useEffect` cleanup fires after the new `customTextureUrl` is stored (React batches state and then runs cleanup of the previous render's effect). The handler revokes before updating the store. These two revocations target different URLs: the handler targets the URL that was current at call time; the effect cleanup targets the URL that was the dep array value in the previous render. There is no double-revoke risk for the same URL between these two paths.

### 4. Clarifying Questions

None.

---

## Requirement TUS-5: Zustand Store Slice

### 1. Spec Summary

- **Description:** `useAppStore.ts` gains a new field `customTextureUrl: string | null` and a new action `setCustomTextureUrl: (url: string | null) => void`. The field is initialized to `null`. The action performs an immer set that assigns the value directly.
- **Constraints:**
  - `customTextureUrl` is added to the `AppState` interface.
  - `setCustomTextureUrl` is added to the `AppState` interface.
  - Initial value in the store body: `customTextureUrl: null`.
  - Action implementation (using immer pattern matching the existing store):
    ```
    setCustomTextureUrl(url) {
      set((s) => { s.customTextureUrl = url; });
    }
    ```
  - No other store fields or actions are modified by this requirement.
  - TypeScript must compile with no new errors.
- **Assumptions:** The store uses `immer` middleware; the setter pattern follows existing actions like `setActiveGlbUrl` and `setIsAnimationPaused`.
- **Scope:** `asset_generation/web/frontend/src/store/useAppStore.ts`.

### 2. Acceptance Criteria

**TUS-5-AC-1:** `AppState` interface contains `customTextureUrl: string | null` and `setCustomTextureUrl: (url: string | null) => void`.

**TUS-5-AC-2:** The store initializes `customTextureUrl` to `null`.

**TUS-5-AC-3:** Calling `setCustomTextureUrl("blob:http://localhost/abc")` updates the store's `customTextureUrl` to `"blob:http://localhost/abc"`.

**TUS-5-AC-4:** Calling `setCustomTextureUrl(null)` sets `customTextureUrl` to `null`.

**TUS-5-AC-5:** `cd asset_generation/web/frontend && npm test` passes with no regressions after this change alone (no other tasks required).

**TUS-5-AC-6:** TypeScript compiler emits no new errors for `useAppStore.ts`.

### 3. Risk and Ambiguity Analysis

- No risk identified. The store pattern is well-established and the new slice is structurally identical to existing nullable string fields.

### 4. Clarifying Questions

None.

---

## Requirement TUS-6: GlbViewer TextureLoader Overlay

### 1. Spec Summary

- **Description:** The `Model` component in `GlbViewer.tsx` subscribes to `customTextureUrl` from the store and applies a loaded `THREE.Texture` to all `THREE.MeshStandardMaterial` instances in the scene when the URL is non-null. When the URL is null, original materials are restored. The custom texture is tracked in a `useRef` (`customTextureRef`) and disposed when replaced, when the model URL changes, or when the component unmounts.
- **Constraints:**
  - New ref: `const customTextureRef = useRef<THREE.Texture | null>(null)` added to `Model`.
  - New store subscription: `const customTextureUrl = useAppStore((s) => s.customTextureUrl)` inside `Model`.
  - New `useEffect` with dependencies `[customTextureUrl, scene, url]`:
    - If `customTextureUrl` is non-null:
      - Capture original materials if not yet captured using the existing `originalMaterialsRef` guard (same guard as the shader overlay effect: check `!originalMaterialsRef.current.has(obj.uuid)` before setting).
      - Dispose `customTextureRef.current` if present (`customTextureRef.current.dispose()`); set `customTextureRef.current = null`.
      - Call `new THREE.TextureLoader().load(customTextureUrl, (tex) => { ... })`. Inside the callback:
        - Set `customTextureRef.current = tex`.
        - Traverse `scene`; for each `obj` that is `instanceof THREE.Mesh` and whose `obj.material` is `instanceof THREE.MeshStandardMaterial`: set `obj.material.map = tex` and `obj.material.needsUpdate = true`.
    - If `customTextureUrl` is null:
      - Dispose `customTextureRef.current` if present; set to null.
      - Restore original materials: traverse `scene`, for each `obj` that is `instanceof THREE.Mesh`, look up `originalMaterialsRef.current.get(obj.uuid)`, assign it back to `obj.material` if found.
    - Cleanup return in this effect: dispose `customTextureRef.current` if present; set to null.
  - Interaction with existing shader overlay `useEffect` (mode = gradient/spots/stripes): when `texture_mode` is `"custom"`, the existing shader overlay effect runs its mode normalization, resolves `"custom"` to `"none"` (because it is not in the recognized set `gradient | spots | stripes | none`), and executes the restore path. This means the existing effect restores original materials and clears `appliedMaterialRef` when mode is `"custom"`. The custom texture effect must re-apply after this — the dependency array `[customTextureUrl, scene, url]` ensures it re-runs when `customTextureUrl` is set, but the ordering of effects is not guaranteed. **The implementer must add `"custom"` to the recognized mode set in `GlbViewer`'s shader effect to prevent the shader effect from restoring materials when `texture_mode` is `"custom"`** (i.e., treat `"custom"` as a no-op in the shader overlay effect, neither applying a shader nor restoring original materials).
  - Model URL change (`url` change): the existing block that clears `originalMaterialsRef.current` and disposes `appliedMaterialRef.current` must also dispose `customTextureRef.current` and set it to null.
  - Unmount: the cleanup return of the custom texture `useEffect` handles disposal on unmount.
  - Material filter: only `THREE.MeshStandardMaterial` instances receive the custom texture map. `THREE.ShaderMaterial` and other material types are skipped.
  - A mesh may have multiple materials (array form); if `obj.material` is an array, iterate the array and apply to each element that is `instanceof THREE.MeshStandardMaterial`.
- **Assumptions:** The `TextureLoader.load` callback is asynchronous; the texture may appear slightly after the upload (within 2 seconds per ticket AC). The `customTextureRef` stores the loaded texture to enable disposal; it does not need to be reactive.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx` — `Model` component only.

### 2. Acceptance Criteria

**TUS-6-AC-1:** When `customTextureUrl` in the store transitions from `null` to a valid blob URL, `THREE.TextureLoader().load` is called with that URL.

**TUS-6-AC-2:** In the `TextureLoader.load` callback, every `THREE.Mesh` in the scene whose `material` (or material array element) is `instanceof THREE.MeshStandardMaterial` has its `.map` set to the loaded texture and `material.needsUpdate` set to `true`.

**TUS-6-AC-3:** `THREE.ShaderMaterial` instances in the scene are not modified by the custom texture effect.

**TUS-6-AC-4:** When `customTextureUrl` transitions from a non-null URL to `null`, `customTextureRef.current.dispose()` is called and original materials are restored via `originalMaterialsRef`.

**TUS-6-AC-5:** When the model URL (`url` prop) changes, `customTextureRef.current` is disposed and set to null in the same block that clears `originalMaterialsRef.current`.

**TUS-6-AC-6:** When `texture_mode` is `"custom"`, the existing shader overlay `useEffect` does not restore original materials or apply a `ShaderMaterial` (the mode is treated as a no-op in that effect).

**TUS-6-AC-7:** `GlbViewer.tsx` contains no call to `URL.revokeObjectURL` or `URL.createObjectURL`.

**TUS-6-AC-8:** The `Model` component's custom texture `useEffect` returns a cleanup function that disposes `customTextureRef.current` when the component unmounts.

**TUS-6-AC-9:** After the model URL changes, uploading a new texture applies correctly to the new model's materials (no stale texture ref from the previous model interferes).

### 3. Risk and Ambiguity Analysis

- **Effect ordering risk (HIGH):** React does not guarantee the order of `useEffect` execution between the existing shader overlay effect and the new custom texture effect when both are triggered in the same render. The resolution specified in TUS-6 Constraints (treat `"custom"` as no-op in the shader effect) eliminates the race condition by design: the shader effect never restores materials when mode is `"custom"`, so the custom texture effect's apply step is always the final material state.
- **Array material risk:** Some GLB meshes may have `material` as `THREE.Material[]`. The traverse must handle both scalar and array cases. The spec requires iterating array materials; missing this produces incorrect behavior on models with multi-material meshes.
- **Async callback risk:** The `TextureLoader.load` callback is asynchronous. If `customTextureUrl` changes to null before the callback fires, the callback will attempt to apply a texture that should no longer be shown. The implementer should capture the expected URL at effect setup time and bail out in the callback if `customTextureRef.current` was cleared (i.e., if the URL changed). This guard is a correctness constraint even if not explicitly stated in the ticket. The implementer is expected to add it as standard async-safety practice.
- **`needsUpdate` requirement:** Without `material.needsUpdate = true`, Three.js will not re-render the material with the new map. This is required.

### 4. Clarifying Questions

None that block spec completion. The async-safety guard is called out in Risk Analysis as implementation-level detail.

---

## Requirement TUS-7: Remove Button

### 1. Spec Summary

- **Description:** When `customTextureUrl` in the store is non-null and `texture_mode` is `"custom"`, a "Remove" button is rendered in `BuildControls` beneath the file input. Clicking it revokes the blob URL, nulls the store, and resets `texture_mode` to `"none"`.
- **Constraints:**
  - Render condition: `values.texture_mode === "custom" && customTextureUrl !== null`. Both conditions must be true for the button to appear.
  - Button text: `"Remove"`.
  - On click (`handleRemoveTexture`):
    1. `URL.revokeObjectURL(customTextureUrl)` — revoke the current blob URL.
    2. `setCustomTextureUrl(null)` — null the store field.
    3. `setAnimatedBuildOption(slug, "texture_mode", "none")` — reset the texture mode for the current slug.
  - The button must not appear when `texture_mode` is not `"custom"`, even if `customTextureUrl` is somehow non-null in the store.
  - Styling: consistent with existing dark-theme button style (e.g., `s.select` adapted or inline style matching `background: "#3c3c3c"`, `color: "#d4d4d4"`, `border: "1px solid #555"`, `borderRadius: 3`, `fontSize: 11`).
  - `type="button"` must be set to prevent implicit form submission.
- **Assumptions:** `slug` in `handleRemoveTexture` is the same `slug` computed at the top of `BuildControls` (derived from `commandContext`).
- **Scope:** `BuildControls.tsx`.

### 2. Acceptance Criteria

**TUS-7-AC-1:** When `texture_mode` is `"custom"` and `customTextureUrl` is non-null, a button with text `"Remove"` is present in the DOM.

**TUS-7-AC-2:** When `texture_mode` is `"custom"` and `customTextureUrl` is null, no "Remove" button is present in the DOM.

**TUS-7-AC-3:** When `texture_mode` is `"none"` and `customTextureUrl` is non-null (edge case), no "Remove" button is present in the DOM.

**TUS-7-AC-4:** Clicking "Remove" calls `URL.revokeObjectURL` with the current `customTextureUrl`.

**TUS-7-AC-5:** Clicking "Remove" calls `setCustomTextureUrl(null)`.

**TUS-7-AC-6:** Clicking "Remove" calls `setAnimatedBuildOption(slug, "texture_mode", "none")`.

**TUS-7-AC-7:** After clicking "Remove", the file input is no longer in the DOM (because `texture_mode` is now `"none"`).

### 3. Risk and Ambiguity Analysis

- The button's `type="button"` attribute is required to prevent form submission behavior if `BuildControls` is ever wrapped in a `<form>` element in the future.
- `handleRemoveTexture` uses a closure over `customTextureUrl` from the store selector. The implementer must ensure the value is read from the store at click time, not captured stale.

### 4. Clarifying Questions

None.

---

## Requirement TUS-8: Python Comment in `_texture_control_defs()`

### 1. Spec Summary

- **Description:** A comment line is added inside `_texture_control_defs()` in `asset_generation/python/src/utils/animated_build_options_appendage_defs.py` explaining that `"custom"` is intentionally absent from `_TEXTURE_MODE_OPTIONS` because it is a client-side-only upload mode and is not a valid Blender build target.
- **Constraints:**
  - The comment is placed immediately after the function docstring and before the `return` statement (or as a leading comment before the return list literal).
  - The `_TEXTURE_MODE_OPTIONS` tuple is NOT modified.
  - No functional code changes are made to any Python file.
  - Exact comment text:
    ```python
    # NOTE: "custom" is intentionally omitted from _TEXTURE_MODE_OPTIONS.
    # It is a client-side-only upload mode (blob URL applied in Three.js)
    # and is not a valid Blender build target. See ticket M25-03.
    ```
  - The comment is three lines. Exact whitespace (4-space indent) must match the surrounding function body.
- **Assumptions:** The comment will be read by future agents and developers to understand why `"custom"` is not in the Python options tuple.
- **Scope:** `asset_generation/python/src/utils/animated_build_options_appendage_defs.py` — `_texture_control_defs()` function body only.

### 2. Acceptance Criteria

**TUS-8-AC-1:** `_texture_control_defs()` contains a comment with the text `"custom" is intentionally omitted from _TEXTURE_MODE_OPTIONS`.

**TUS-8-AC-2:** `_TEXTURE_MODE_OPTIONS` remains `("none", "gradient", "spots", "stripes")` — exactly four entries.

**TUS-8-AC-3:** `bash .lefthook/scripts/py-tests.sh` passes without modification after this change (comment-only diff; no logic altered).

**TUS-8-AC-4:** The comment appears inside the `_texture_control_defs()` function body (not at module level, not in the docstring).

### 3. Risk and Ambiguity Analysis

- No functional risk. A comment-only change cannot break behavior.
- If the comment is placed at module level, it is technically correct but less discoverable to readers of the function. Placement inside the function body (after docstring) is required.

### 4. Clarifying Questions

None.

---

## Requirement TUS-9: `buildControlDisabled()` Behavior Under "Custom" Mode

### 1. Spec Summary

- **Description:** When `texture_mode` is `"custom"`, the `buildControlDisabled()` function in `BuildControls.tsx` must not unlock any texture sub-controls. All gradient, spot, and stripe sub-controls remain disabled. This is a consequence of the existing normalization logic: `"custom"` falls through to the `"none"` branch of the mode guard, keeping all sub-controls disabled.
- **Constraints:**
  - The current `buildControlDisabled()` function normalizes `textureMode` to one of `"gradient" | "spots" | "stripes" | "none"`. Any other value (including `"custom"`) is mapped to `"none"`.
  - Under `mode === "none"`:
    - `defKey.startsWith("texture_grad_")` → returns `true` (disabled).
    - `defKey.startsWith("texture_spot_")` → returns `true` (disabled).
    - `defKey.startsWith("texture_stripe_")` → returns `true` (disabled).
  - No changes are required to `buildControlDisabled()` for this ticket. The function already handles `"custom"` correctly by the normalization fallthrough.
  - This requirement is a confirmatory constraint: the implementer must verify no accidental change to `buildControlDisabled()` enables sub-controls for `"custom"` mode.
- **Assumptions:** The mode normalization guard in `buildControlDisabled()` is: `textureMode === "gradient" || textureMode === "spots" || textureMode === "stripes" || textureMode === "none" ? textureMode : "none"`. This is confirmed from the existing source.
- **Scope:** `BuildControls.tsx` — `buildControlDisabled()` function.

### 2. Acceptance Criteria

**TUS-9-AC-1:** `buildControlDisabled(slug, "texture_grad_color_a", { texture_mode: "custom" })` returns `true`.

**TUS-9-AC-2:** `buildControlDisabled(slug, "texture_spot_density", { texture_mode: "custom" })` returns `true`.

**TUS-9-AC-3:** `buildControlDisabled(slug, "texture_stripe_width", { texture_mode: "custom" })` returns `true`.

**TUS-9-AC-4:** `buildControlDisabled(slug, "texture_mode", { texture_mode: "custom" })` returns `false` (the mode selector itself is always enabled).

**TUS-9-AC-5:** Existing `BuildControls.texture.test.tsx` tests all pass without modification after Tasks 3 and 4 are implemented.

### 3. Risk and Ambiguity Analysis

- No functional change is required. Risk is that a developer incorrectly adds a `"custom"` branch that enables sub-controls. This spec explicitly forbids that.

### 4. Clarifying Questions

None.

---

## Requirement TUS-10: Non-Breaking Guarantee (M25-02 Shader Overlay Preserved)

### 1. Spec Summary

- **Description:** All existing M25-02 shader overlay behaviors (gradient, spots, stripes) must continue to work correctly after M25-03 implementation. No existing test file is modified in a way that changes expected behavior. The only permitted change to the shader overlay `useEffect` in `GlbViewer.tsx` is the addition of `"custom"` to the recognized mode set as a no-op branch (see TUS-6 Constraints).
- **Constraints:**
  - `makeTextureShaderMaterial()` is not modified.
  - The shader `useEffect` in `Model` still applies `ShaderMaterial` for `gradient`, `spots`, and `stripes` modes.
  - The `mode === "none"` restore path in the shader `useEffect` is unchanged for `"none"` mode; the only addition is that `"custom"` is also treated as a no-op (neither shader applied nor original materials restored by this effect when mode is `"custom"`).
  - `originalMaterialsRef` capture logic is unchanged.
  - `appliedMaterialRef` disposal logic is unchanged for non-custom modes.
  - All tests in `asset_generation/web/frontend/src/components/Preview/GlbViewer.test.tsx` and `GlbViewer.loadError.test.tsx` pass without modification.
  - All tests in `BuildControls.texture.test.tsx` pass without modification.
  - All Python tests pass without modification.
- **Assumptions:** M25-02 is fully implemented and all its tests are green before M25-03 implementation begins.
- **Scope:** `GlbViewer.tsx` and `BuildControls.tsx` — non-breaking constraint on existing behavior.

### 2. Acceptance Criteria

**TUS-10-AC-1:** `cd asset_generation/web/frontend && npm test` exits 0 with all pre-existing tests passing after M25-03 implementation.

**TUS-10-AC-2:** `bash .lefthook/scripts/py-tests.sh` exits 0 after M25-03 implementation.

**TUS-10-AC-3:** `cd asset_generation/web/frontend && npm run build` exits 0 (TypeScript compilation clean).

**TUS-10-AC-4:** Selecting `texture_mode: "gradient"` in the store still causes the shader overlay effect to apply a `THREE.ShaderMaterial` to all scene meshes (confirmed by existing `BuildControls.texture.test.tsx` and `GlbViewer.test.tsx` assertions).

**TUS-10-AC-5:** Selecting `texture_mode: "none"` still restores original materials (confirmed by existing tests).

### 3. Risk and Ambiguity Analysis

- The only code path that touches the existing shader overlay is the addition of the `"custom"` no-op branch. Regression risk is low but must be verified by running the full test suite.

### 4. Clarifying Questions

None.

---

## Test Coverage Requirements for `BuildControls.textureUpload.test.tsx`

The Test Designer Agent must author `asset_generation/web/frontend/src/components/Preview/BuildControls.textureUpload.test.tsx` covering the following 8 acceptance criteria items (derived from ticket Task 5):

| AC Label | Description |
|---|---|
| AC-1 | `"custom"` option renders in the `texture_mode` select when controls include it |
| AC-2 | File input (`aria-label="Upload texture"`) is present when `texture_mode` is `"custom"` and absent when `"none"` |
| AC-3 | Uploading `type: "application/pdf"` or `type: "image/gif"` sets inline error and does not call `setCustomTextureUrl` |
| AC-4 | Uploading a file with `size: 3 * 1024 * 1024 + 1` sets the size error and does not call `setCustomTextureUrl` |
| AC-5 | Uploading a valid 1 MB PNG calls `URL.createObjectURL` and calls `setCustomTextureUrl` with the resulting URL |
| AC-6 | "Remove" button is present when `customTextureUrl` is non-null; click calls `URL.revokeObjectURL`, `setCustomTextureUrl(null)`, resets `texture_mode` to `"none"` |
| AC-7 | Uploading a valid JPEG (`type: "image/jpeg"`) is accepted (no error set) |
| AC-8 | After a rejected file, the error message is visible in the DOM |

Test infrastructure requirements:
- Use `vi.spyOn(URL, 'createObjectURL')` and `vi.spyOn(URL, 'revokeObjectURL')` for isolation.
- Mock `URL.createObjectURL` to return a deterministic string (e.g., `"blob:mock/abc-123"`).
- Seed the store with `customTextureUrl: null` at test start; reset between tests.
- Use `@vitest-environment jsdom` (matching existing `BuildControls.*.test.tsx` files).
- Inject `"custom"` into the test-local control def's options array (the test does not rely on Python-emitted defs).
- Follow naming and import patterns from `BuildControls.texture.test.tsx` and `BuildControls.mouthTail.test.tsx`.

---

## Cross-Requirement Interaction Summary

| When... | Effect on... |
|---|---|
| `texture_mode` set to `"custom"` | File input appears (TUS-2), sub-controls disabled (TUS-9), shader effect is no-op (TUS-6-AC-6) |
| Valid file uploaded | Blob URL created (TUS-4), stored in Zustand (TUS-5), TextureLoader fires (TUS-6), Remove button appears (TUS-7) |
| Remove clicked | Blob URL revoked (TUS-4), store nulled (TUS-5), Three.js Texture disposed (TUS-6), `texture_mode` reset to `"none"` (TUS-7), file input hidden (TUS-2) |
| Model URL changes | `customTextureRef` disposed (TUS-6-AC-5), `originalMaterialsRef` cleared (TUS-10) |
| `texture_mode` set to `"gradient"/"spots"/"stripes"` | Shader overlay applies (TUS-10), custom texture effect sees null URL → no-op (TUS-6) |
| Component unmounts | `useEffect` cleanup revokes blob URL (TUS-4-AC-4), Three.js Texture disposed (TUS-6-AC-8) |
